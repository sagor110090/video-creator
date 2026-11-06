# Desktop App Phase 3 — Schedules, Statistics, YouTube — Implementation Plan

> **For Claude:** REQUIRED SUB-SKILL: Use superpowers:executing-plans to implement this plan task-by-task.

**Goal:** Recurring auto-generated videos, a statistics page, and YouTube channel connect /
upload / scheduled publish — the remaining Laravel features — in the desktop app.

**Architecture:** Three Qt-free services: `services/youtube.py` (OAuth loopback + PKCE, token
refresh, resumable upload, publish — plain `requests`, no Google SDK), `services/scheduler.py`
(pure functions that find due work and run it), `services/stats.py`. The UI process runs
`scheduler.tick()` every 60 s from a `QTimer`; network work goes through `run_async`. Rendering
still goes through the worker process. Ported from `ProcessVideoSchedulesCommand`,
`ProcessScheduledUploadsCommand`, `YouTubeService`, `StatisticsController`.

**Tech Stack:** requests, PySide6, responses (tests).

---

### Task 1: DB additions + lightweight migration
`Story.uploaded_at` (DateTime), `Story.rendered_at` (DateTime, set when status → done).
`db.init_db()` adds missing columns to existing tables (`ALTER TABLE … ADD COLUMN`) so the
real DB created in phase 1 keeps working. Settings: `youtube_client_id`,
`youtube_client_secret`. Test: an old-schema DB gains the columns. Commit.

### Task 2: `services/youtube.py`
- `auth_url(cfg, redirect_uri, state, code_challenge)`; `connect_channel(cfg, Session,
  open_browser=webbrowser.open, timeout=300)`: starts a one-shot HTTP server on
  `127.0.0.1:<free port>`, opens the consent page (scopes `youtube.upload`,
  `youtube.readonly`, `access_type=offline`, `prompt=consent`, PKCE S256), receives `code`,
  exchanges it, reads `channels?part=snippet&mine=true`, upserts `Channel` by `channel_id`.
- `access_token(cfg, Session, channel_id)`: refreshes when < 60 s left; on `invalid_grant`
  raises `YouTubeAuthError("…reconnect…")` (channel kept, marked needing reconnect).
- `upload(cfg, Session, story_id, progress=None)`: resumable upload in 8 MB chunks; privacy
  `private` if `publish_at` is in the future else `public`; sets `youtube_video_id`,
  `youtube_upload_status` = `scheduled|completed`, `uploaded_at`; on error status `failed` +
  readable `youtube_error` (quota message for `uploadLimitExceeded`).
- `publish(cfg, Session, story_id)`: `videos?part=status` → public, status `completed`.
Tests with `responses`: token exchange + channel upsert (server simulated by calling the
redirect URL), refresh, upload private-vs-public + session URI chunking, quota error text,
publish. Commit.

### Task 3: `services/scheduler.py`
- `due_schedules(Session, now)` — active, `scheduled_time <= now.time()`, `last_run_at` null
  or < today.
- `run_schedule(cfg, Session, schedule_id, now)` — marks `last_run_at=today` first (no double
  run), news search for news styles, `generate_story`, `create_story`, sets `schedule_id`,
  `channel_id`, YouTube metadata, `publish_at=now`; returns story id; on error sets schedule
  `last_error`.
- `due_uploads(Session, now)` — `done`, has channel, `publish_at <= now`, no upload status.
- `due_publishes(Session, now)` — status `scheduled`, `publish_at <= now`.
Tests with a fixed `now`. Commit.

### Task 4: `services/stats.py`
`summary(Session)` (stories, done, failed, uploaded, channels, minutes of video) and
`daily(Session, days=30)` rows (date, created, rendered, uploaded). Test. Commit.

### Task 5: UI — `ui/schedules_page.py`, `ui/statistics_page.py`, `ui/channels_page.py`
- Schedules: table (topic, style, format, time, channel, last run, status/error) + form
  (topic, style, talking style, format, `QTimeEdit`, channel combo incl. "No upload") with
  Add, Delete, Pause/Resume, Run now.
- Channels: list with thumbnail/title/status, **Connect channel** (runs `connect_channel`
  async, button shows "Waiting for browser…"), Remove; help text when no client ID is set.
- Statistics: summary tiles + 30-day table.
- `ui/scheduler_runner.py`: `QTimer` 60 s → due schedules (async generate → `submit_render`),
  due uploads / publishes (async). Guards against overlapping runs.
- Story view: YouTube panel — channel combo, title, description, tags, publish time
  (now / later), **Generate metadata**, **Upload**; shows upload status, error, and a
  link to the video.
- Enable the three sidebar items. Settings: client ID/secret fields + help link.
pytest-qt tests for each page with services mocked. Commit.

### Task 6: Verify
Full suite; launch app; add a schedule set to "now" with no channel → story is generated and
rendered automatically; statistics show it. YouTube connect needs the user's Desktop OAuth
client — verified with mocks only until then.
