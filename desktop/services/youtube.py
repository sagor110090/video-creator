"""YouTube: connect a channel (OAuth loopback + PKCE), refresh tokens, resumable upload, publish.
Ported from app/Services/YouTubeService.php using plain HTTP (no Google SDK).

Needs an OAuth client of type "Desktop app" (Google Cloud Console → APIs & Services → Credentials);
web-type clients reject the http://127.0.0.1:<port> redirect this uses."""
import base64
import hashlib
import http.server
import json
import secrets
import socket
import threading
import urllib.parse
import webbrowser
from datetime import datetime, timedelta
from pathlib import Path

import requests

from desktop.core import db

AUTH_URL = "https://accounts.google.com/o/oauth2/v2/auth"
TOKEN_URL = "https://oauth2.googleapis.com/token"
API = "https://www.googleapis.com/youtube/v3"
UPLOAD_URL = "https://www.googleapis.com/upload/youtube/v3/videos"
SCOPES = "https://www.googleapis.com/auth/youtube.upload https://www.googleapis.com/auth/youtube.readonly"
CHUNK = 8 * 1024 * 1024  # must be a multiple of 256 KiB except in tests


class YouTubeError(RuntimeError):
    pass


class YouTubeAuthError(YouTubeError):
    pass


def _client(cfg):
    cid, secret = cfg.get("youtube_client_id", "").strip(), cfg.get("youtube_client_secret", "").strip()
    if not cid:
        raise YouTubeError("No YouTube OAuth client ID. Add a 'Desktop app' OAuth client in Settings.")
    return cid, secret


def _api_error(res) -> str:
    try:
        err = res.json().get("error")
        if isinstance(err, dict):
            return err.get("message") or json.dumps(err)
        return res.json().get("error_description") or str(err)
    except ValueError:
        return res.text[:300] or f"HTTP {res.status_code}"


# ---------------------------------------------------------------- connect (OAuth)

def _free_port() -> int:
    with socket.socket() as s:
        s.bind(("127.0.0.1", 0))
        return s.getsockname()[1]


def _wait_for_code(port, state, timeout) -> str:
    result = {}

    class Handler(http.server.BaseHTTPRequestHandler):
        def do_GET(self):
            q = urllib.parse.parse_qs(urllib.parse.urlparse(self.path).query)
            if q.get("state", [None])[0] != state:
                self.send_response(400)
                self.end_headers()
                return
            result["code"] = q.get("code", [None])[0]
            result["error"] = q.get("error", [None])[0]
            ok = bool(result["code"])
            self.send_response(200)
            self.send_header("Content-Type", "text/html; charset=utf-8")
            self.end_headers()
            msg = "Channel connected. You can close this tab and go back to AI Video Creator." if ok \
                else f"Connection failed: {result['error']}. You can close this tab."
            self.wfile.write(f"<html><body style='font-family:sans-serif;padding:40px'><h2>{msg}</h2></body></html>".encode())

        def log_message(self, *a):
            pass

    server = http.server.HTTPServer(("127.0.0.1", port), Handler)
    server.timeout = 1
    deadline = datetime.now() + timedelta(seconds=timeout)
    try:
        while "code" not in result and datetime.now() < deadline:
            server.handle_request()
    finally:
        server.server_close()
    if result.get("error"):
        raise YouTubeError(f"Google sign-in was cancelled or failed: {result['error']}")
    if not result.get("code"):
        raise YouTubeError("Timed out waiting for Google sign-in.")
    return result["code"]


def connect_channel(cfg, Session, open_browser=webbrowser.open, timeout=300) -> int:
    """Open Google's consent page, wait for the redirect, store the channel. Returns Channel.id."""
    cid, secret = _client(cfg)
    port = _free_port()
    redirect = f"http://127.0.0.1:{port}"
    state = secrets.token_urlsafe(16)
    verifier = secrets.token_urlsafe(64)
    challenge = base64.urlsafe_b64encode(hashlib.sha256(verifier.encode()).digest()).rstrip(b"=").decode()
    url = AUTH_URL + "?" + urllib.parse.urlencode({
        "client_id": cid, "redirect_uri": redirect, "response_type": "code", "scope": SCOPES,
        "access_type": "offline", "prompt": "select_account consent", "state": state,
        "code_challenge": challenge, "code_challenge_method": "S256"})
    holder = {}
    t = threading.Thread(target=lambda: holder.update(code=_safe(_wait_for_code, port, state, timeout)), daemon=True)
    t.start()
    open_browser(url)
    t.join(timeout + 5)
    code = holder.get("code")
    if isinstance(code, Exception):
        raise code
    res = requests.post(TOKEN_URL, timeout=30, data={
        "code": code, "client_id": cid, "client_secret": secret, "redirect_uri": redirect,
        "grant_type": "authorization_code", "code_verifier": verifier})
    if res.status_code != 200:
        raise YouTubeError(f"Token exchange failed: {_api_error(res)}")
    tok = res.json()
    info = requests.get(f"{API}/channels", params={"part": "snippet", "mine": "true"}, timeout=30,
                        headers={"Authorization": f"Bearer {tok['access_token']}"})
    if info.status_code != 200:
        raise YouTubeError(f"Could not read your channel: {_api_error(info)}")
    items = info.json().get("items") or []
    if not items:
        raise YouTubeError("That Google account has no YouTube channel.")
    item = items[0]
    with Session() as s:
        ch = s.query(db.Channel).filter_by(channel_id=item["id"]).first() or db.Channel(channel_id=item["id"])
        ch.title = item["snippet"].get("title")
        ch.thumbnail = item["snippet"].get("thumbnails", {}).get("default", {}).get("url")
        ch.access_token = tok["access_token"]
        if tok.get("refresh_token"):
            ch.refresh_token = tok["refresh_token"]
        ch.expires_at = datetime.now() + timedelta(seconds=int(tok.get("expires_in", 3600)))
        ch.status = "ok"
        s.add(ch)
        s.commit()
        return ch.id


def _safe(fn, *a):
    try:
        return fn(*a)
    except Exception as e:
        return e


# ---------------------------------------------------------------- tokens

def access_token(cfg, Session, channel_id: int) -> str:
    with Session() as s:
        ch = s.get(db.Channel, channel_id)
        if ch is None:
            raise YouTubeError("That YouTube channel is no longer connected.")
        if ch.access_token and ch.expires_at and ch.expires_at - datetime.now() > timedelta(seconds=60):
            return ch.access_token
        if not ch.refresh_token:
            ch.status = "reconnect"
            s.commit()
            raise YouTubeAuthError(f"Please reconnect the channel '{ch.title}'.")
        cid, secret = _client(cfg)
        res = requests.post(TOKEN_URL, timeout=30, data={
            "client_id": cid, "client_secret": secret, "refresh_token": ch.refresh_token,
            "grant_type": "refresh_token"})
        if res.status_code != 200:
            ch.status = "reconnect"
            s.commit()
            raise YouTubeAuthError(f"YouTube connection for '{ch.title}' expired or was revoked. "
                                   f"Please reconnect it ({_api_error(res)}).")
        tok = res.json()
        ch.access_token = tok["access_token"]
        ch.expires_at = datetime.now() + timedelta(seconds=int(tok.get("expires_in", 3600)))
        if tok.get("refresh_token"):
            ch.refresh_token = tok["refresh_token"]
        ch.status = "ok"
        s.commit()
        return ch.access_token


# ---------------------------------------------------------------- upload / publish

def _fail(Session, story_id, msg):
    with Session() as s:
        st = s.get(db.Story, story_id)
        st.youtube_upload_status, st.youtube_error = "failed", msg
        s.commit()


def upload(cfg, Session, story_id: int, progress=None) -> str:
    """Resumable upload of the story's final video. Private if publish_at is in the future."""
    with Session() as s:
        st = s.get(db.Story, story_id)
        if not st.channel_id:
            raise YouTubeError("Choose a YouTube channel for this story first.")
        if not st.final_path or not Path(st.final_path).is_file():
            raise YouTubeError("This story has no final video yet.")
        future = bool(st.publish_at and st.publish_at > datetime.now())
        tags = [t.strip() for t in (st.youtube_tags or "").split(",") if t.strip()]
        meta = {"snippet": {"title": (st.youtube_title or st.title or "Untitled")[:100],
                            "description": st.youtube_description or st.content, "tags": tags},
                "status": {"privacyStatus": "private" if future else "public", "selfDeclaredMadeForKids": False,
                           "containsSyntheticMedia": True}}   # every video is AI-made: disclose at platform level
        path, channel_id = Path(st.final_path), st.channel_id
        ch = s.get(db.Channel, st.channel_id)
        channel_title = ch.title if ch else "your channel"
        st.youtube_upload_status, st.youtube_error = "uploading", None
        s.commit()
    try:
        token = access_token(cfg, Session, channel_id)
        size = path.stat().st_size
        init = requests.post(UPLOAD_URL, params={"uploadType": "resumable", "part": "snippet,status"},
                             json=meta, timeout=60, headers={
                                 "Authorization": f"Bearer {token}", "X-Upload-Content-Length": str(size),
                                 "X-Upload-Content-Type": "video/mp4"})
        if init.status_code != 200 or "Location" not in init.headers:
            raise YouTubeError(_api_error(init))
        session_url, start, video_id = init.headers["Location"], 0, None
        with open(path, "rb") as f:
            while start < size:
                f.seek(start)
                chunk = f.read(CHUNK)
                end = start + len(chunk) - 1
                res = requests.put(session_url, data=chunk, timeout=300, headers={
                    "Authorization": f"Bearer {token}", "Content-Range": f"bytes {start}-{end}/{size}"})
                if res.status_code in (200, 201):
                    video_id = res.json()["id"]
                    start = size
                elif res.status_code == 308:
                    rng = res.headers.get("Range")
                    start = int(rng.split("-")[1]) + 1 if rng else 0
                else:
                    raise YouTubeError(_api_error(res))
                if progress:
                    progress(min(start / size, 1.0))
        if not video_id:
            raise YouTubeError("Upload finished without a video id.")
    except YouTubeError as e:
        msg = str(e)
        if "exceeded the number of videos" in msg or "uploadLimitExceeded" in msg:
            msg = (f"YouTube API upload limit reached for '{channel_title}'. API upload limits are separate "
                   "from (and stricter than) YouTube Studio uploads. Try again in 24 hours or request a quota "
                   "increase in Google Cloud Console.")
        _fail(Session, story_id, msg)
        raise YouTubeError(msg) from e
    except Exception as e:
        _fail(Session, story_id, f"{type(e).__name__}: {e}")
        raise
    with Session() as s:
        st = s.get(db.Story, story_id)
        st.youtube_video_id = video_id
        st.youtube_upload_status = "scheduled" if future else "completed"
        st.uploaded_at = datetime.now()
        s.commit()
    return video_id


def publish(cfg, Session, story_id: int) -> None:
    """Make a privately uploaded (scheduled) video public."""
    with Session() as s:
        st = s.get(db.Story, story_id)
        video_id, channel_id = st.youtube_video_id, st.channel_id
    token = access_token(cfg, Session, channel_id)
    res = requests.put(f"{API}/videos", params={"part": "status"}, timeout=60,
                       headers={"Authorization": f"Bearer {token}"},
                       json={"id": video_id, "status": {"privacyStatus": "public"}})
    if res.status_code != 200:
        _fail(Session, story_id, f"Publishing failed: {_api_error(res)}")
        raise YouTubeError(_api_error(res))
    with Session() as s:
        st = s.get(db.Story, story_id)
        st.youtube_upload_status, st.youtube_error = "completed", None
        s.commit()


def video_url(video_id: str) -> str:
    return f"https://youtu.be/{video_id}"
