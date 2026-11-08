import json
import threading
import urllib.parse
import urllib.request
from datetime import datetime, timedelta

import pytest
import responses

from desktop.core import db
from desktop.services import youtube

CFG = {"youtube_client_id": "cid.apps.googleusercontent.com", "youtube_client_secret": "csecret"}
CHANNELS = "https://www.googleapis.com/youtube/v3/channels"
UPLOAD = "https://www.googleapis.com/upload/youtube/v3/videos"
VIDEOS = "https://www.googleapis.com/youtube/v3/videos"


def _channel_payload(cid="UC1", title="My Channel"):
    return {"items": [{"id": cid, "snippet": {"title": title, "thumbnails": {"default": {"url": "https://t/x.jpg"}}}}]}


def _fake_browser(code="auth-code"):
    """Instead of a real browser: follow the consent URL's redirect_uri back to the app."""
    seen = {}

    def open_browser(url):
        q = urllib.parse.parse_qs(urllib.parse.urlparse(url).query)
        seen.update({k: v[0] for k, v in q.items()})
        target = f"{q['redirect_uri'][0]}?code={code}&state={q['state'][0]}"
        threading.Thread(target=lambda: urllib.request.urlopen(target, timeout=5).read(), daemon=True).start()
        return True
    return open_browser, seen


@responses.activate
def test_connect_channel(Session):
    responses.add_passthru("http://127.0.0.1")
    responses.add(responses.POST, youtube.TOKEN_URL, json={
        "access_token": "at1", "refresh_token": "rt1", "expires_in": 3600})
    responses.add(responses.GET, CHANNELS, json=_channel_payload())
    open_browser, seen = _fake_browser()
    ch_id = youtube.connect_channel(CFG, Session, open_browser=open_browser, timeout=10)
    assert seen["client_id"] == CFG["youtube_client_id"]
    assert seen["code_challenge_method"] == "S256" and seen["access_type"] == "offline"
    assert "youtube.upload" in seen["scope"]
    body = urllib.parse.parse_qs(responses.calls[0].request.body)
    assert body["code"] == ["auth-code"] and "code_verifier" in body
    with Session() as s:
        ch = s.get(db.Channel, ch_id)
        assert (ch.channel_id, ch.title, ch.access_token, ch.refresh_token) == ("UC1", "My Channel", "at1", "rt1")
    # connecting the same channel again updates it instead of duplicating
    responses.replace(responses.POST, youtube.TOKEN_URL, json={"access_token": "at2", "expires_in": 3600})
    open_browser, _ = _fake_browser()
    assert youtube.connect_channel(CFG, Session, open_browser=open_browser, timeout=10) == ch_id
    with Session() as s:
        ch = s.get(db.Channel, ch_id)
        assert ch.access_token == "at2" and ch.refresh_token == "rt1"


def test_connect_needs_client_id(Session):
    with pytest.raises(youtube.YouTubeError, match="client ID"):
        youtube.connect_channel({}, Session)


def _channel(Session, expires_in=3600, refresh="rt1"):
    with Session() as s:
        ch = db.Channel(channel_id="UC1", title="My Channel", access_token="at1", refresh_token=refresh,
                        expires_at=datetime.now() + timedelta(seconds=expires_in))
        s.add(ch)
        s.commit()
        return ch.id


@responses.activate
def test_access_token_refreshes_when_expired(Session):
    ch_id = _channel(Session, expires_in=-10)
    responses.add(responses.POST, youtube.TOKEN_URL, json={"access_token": "fresh", "expires_in": 3600})
    assert youtube.access_token(CFG, Session, ch_id) == "fresh"
    assert youtube.access_token(CFG, Session, ch_id) == "fresh"  # cached until expiry
    assert len(responses.calls) == 1


@responses.activate
def test_revoked_refresh_token_asks_to_reconnect(Session):
    ch_id = _channel(Session, expires_in=-10)
    responses.add(responses.POST, youtube.TOKEN_URL, status=400, json={"error": "invalid_grant"})
    with pytest.raises(youtube.YouTubeAuthError, match="reconnect"):
        youtube.access_token(CFG, Session, ch_id)
    with Session() as s:
        assert s.get(db.Channel, ch_id).status == "reconnect"


def _story(Session, data_dir, ch_id, publish_at=None, size=20):
    video = data_dir / "final.mp4"
    video.write_bytes(b"v" * size)
    with Session() as s:
        st = db.Story(title="T", content="c", status="done", final_path=str(video), channel_id=ch_id,
                      youtube_title="YT title", youtube_description="desc", youtube_tags="a, b ,c",
                      publish_at=publish_at)
        s.add(st)
        s.commit()
        return st.id


@responses.activate
def test_upload_public_now_in_chunks(Session, data_dir, monkeypatch):
    monkeypatch.setattr(youtube, "CHUNK", 8)
    ch_id = _channel(Session)
    sid = _story(Session, data_dir, ch_id)
    responses.add(responses.POST, UPLOAD, headers={"Location": "https://upload.example/session1"})
    responses.add(responses.PUT, "https://upload.example/session1", status=308, headers={"Range": "bytes=0-7"})
    responses.add(responses.PUT, "https://upload.example/session1", status=308, headers={"Range": "bytes=0-15"})
    responses.add(responses.PUT, "https://upload.example/session1", status=200, json={"id": "vid123"})
    progress = []
    assert youtube.upload(CFG, Session, sid, progress=progress.append) == "vid123"
    meta = json.loads(responses.calls[0].request.body)
    assert meta["status"]["privacyStatus"] == "public"
    assert meta["status"]["containsSyntheticMedia"] is True   # AI disclosure flag on every upload
    assert meta["snippet"]["tags"] == ["a", "b", "c"] and meta["snippet"]["title"] == "YT title"
    ranges = [c.request.headers["Content-Range"] for c in responses.calls[1:]]
    assert ranges == ["bytes 0-7/20", "bytes 8-15/20", "bytes 16-19/20"]
    assert progress[-1] == 1.0
    with Session() as s:
        st = s.get(db.Story, sid)
        assert (st.youtube_video_id, st.youtube_upload_status) == ("vid123", "completed")
        assert st.uploaded_at is not None


@responses.activate
def test_upload_future_is_private_then_publish(Session, data_dir):
    ch_id = _channel(Session)
    sid = _story(Session, data_dir, ch_id, publish_at=datetime.now() + timedelta(days=1))
    responses.add(responses.POST, UPLOAD, headers={"Location": "https://upload.example/s2"})
    responses.add(responses.PUT, "https://upload.example/s2", json={"id": "vid9"})
    youtube.upload(CFG, Session, sid)
    assert json.loads(responses.calls[0].request.body)["status"]["privacyStatus"] == "private"
    with Session() as s:
        assert s.get(db.Story, sid).youtube_upload_status == "scheduled"
    responses.add(responses.PUT, VIDEOS, json={"id": "vid9"})
    youtube.publish(CFG, Session, sid)
    assert json.loads(responses.calls[-1].request.body) == {"id": "vid9", "status": {"privacyStatus": "public"}}
    with Session() as s:
        assert s.get(db.Story, sid).youtube_upload_status == "completed"


@responses.activate
def test_upload_quota_error_is_readable(Session, data_dir):
    ch_id = _channel(Session)
    sid = _story(Session, data_dir, ch_id)
    responses.add(responses.POST, UPLOAD, status=400, json={"error": {
        "message": "The user has exceeded the number of videos they may upload.",
        "errors": [{"reason": "uploadLimitExceeded"}]}})
    with pytest.raises(youtube.YouTubeError):
        youtube.upload(CFG, Session, sid)
    with Session() as s:
        st = s.get(db.Story, sid)
        assert st.youtube_upload_status == "failed"
        assert "upload limit" in st.youtube_error and "My Channel" in st.youtube_error
