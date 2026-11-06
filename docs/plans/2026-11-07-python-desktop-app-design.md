# Python Desktop App — Design

Date: 2026-11-07
Status: Approved (sections 1 and choices below); sections 2–5 drafted for review during implementation.

## Goal

Replace the Laravel + Vue + queue stack with one native Python desktop app (PySide6) that
creates AI story videos and lets you **see and inspect every artifact**: each scene's image
(and where it came from), voice clip, rendered clip, and the final video, with live progress.

## Decisions

| Question | Decision |
|---|---|
| v1 scope | Create/generate videos, scene tracking + editing, recurring schedules, YouTube upload (all four) |
| UI | Native Qt (PySide6). No Node, no web server. |
| Background work | Only while the app is open (menu-bar icon). Missed schedules run on next launch. |
| Transition | Build in `desktop/` alongside Laravel; import existing data once; delete Laravel after parity. |
| Execution model | One long-lived worker **process** holding the voice model; jobs and events over queues. |

## 1. Architecture and layout (approved)

Two processes:

- **UI process** — Qt window, SQLite database, scheduler timer, tray icon. Never does heavy work.
- **Worker process** — started via `multiprocessing` (spawn) on launch. Loads Chatterbox once,
  runs one job at a time. Talks to the UI over two `multiprocessing.Queue`s (jobs in, events out).
  A `QThread` reads events and re-emits them as Qt signals.

```
desktop/
  main.py              # entry: QApplication, tray icon, starts worker
  core/
    db.py              # SQLAlchemy models: Story, Scene, Schedule, Channel
    paths.py           # data dir ~/Library/Application Support/VideoCreator
    settings.py        # keys + options (JSON file; seeded once from project .env)
  services/            # ported from PHP; no Qt imports
    story_ai.py        # DeepSeek/Groq: topic, story, image prompts, metadata, news
    youtube.py         # OAuth (loopback), upload, scheduled publish
    scheduler.py       # recurring schedules + publish queue; tick every 60s
  pipeline/            # ported from ai_worker/worker.py; no Qt imports
    images.py          # Pexels → Pixabay → Openverse → Pollinations → LoremFlickr
    voice.py           # Chatterbox clone + Edge TTS fallback
    render.py          # scene clip (crop, zoompan, subtitles) + assembly (xfade, music, logo)
    worker.py          # worker loop; emits events
  ui/                  # main_window, story_view, schedules, channels, statistics, settings
  tests/
```

Rule: `services/` and `pipeline/` never import Qt, so they are testable headless.

## 2. Data model and per-scene tracking

Per-story folder: `<data>/stories/<id>/scene_<n>/{image.jpg, voice.wav, clip.mp4}` and
`<data>/stories/<id>/final.mp4`.

**Story**: id, title, content, style, talking_style, aspect_ratio, status
(`draft|queued|rendering|done|failed`), error, final_path, youtube_* fields
(title, description, tags, video_id, upload_status, error, channel_id, publish_at),
schedule_id, created_at, updated_at.

**Scene**: id, story_id, order, narration, image_prompt, and for each stage
(`image`, `voice`, `clip`): `<stage>_status` (`pending|running|done|failed|skipped`),
`<stage>_path`, `<stage>_error`; plus `image_source` (pexels/openverse/…), `image_source_url`,
`image_license`, `voice_engine` (chatterbox/edge), `duration_s`.

**Schedule**: as today (topic, style, talking_style, aspect_ratio, channel_id, daily time,
last_run_at, status, last_error). **Channel**: as today's `youtube_tokens`.

**Story view (the tracking screen)**: header with status, progress bar, and final-video player;
then a grid with one row per scene: thumbnail (click → full view), source + license badge,
narration (editable), image prompt (editable), voice play button, clip play button, stage
status chips, and per-scene actions: *replace image from file*, *re-fetch image*,
*re-voice*, *re-render scene*. Editing marks downstream stages stale; "Rebuild final" re-runs
assembly only. Players use `QMediaPlayer` + `QVideoWidget`.

## 3. Data flow and job lifecycle

Jobs (dicts, picklable): `render_story(story_id, only_missing=True)`,
`redo_scene(scene_id, stages=[...])`, `assemble(story_id)`.

1. UI writes story + scenes to DB (story text/scenes come from `services/story_ai.py`, run in a
   `QThreadPool` task since it is network I/O), then puts a job on the queue.
2. Worker reads the job, loads rows itself (opens its own DB session), and for each scene and
   stage: skip if `done` and file exists, else run, write file, update the row, and emit
   `{"type":"stage","scene_id",..,"stage","status","info"}`.
3. Worker emits `{"type":"story","status"}` at start/end; UI refreshes the affected widgets
   from the DB on each event (DB is the source of truth; events are just "something changed").
4. One job at a time; further jobs wait in the queue and show as `queued`.

Scheduler (UI process, `QTimer` 60s): for each due schedule → generate topic + story →
enqueue render; when a story with a schedule and channel finishes → enqueue upload
(a `QThreadPool` task; YouTube upload is network-only, no need for the worker).

## 4. Error handling

- A stage failure marks that scene stage `failed` with the error text and continues to other
  scenes where possible; assembly runs only if every scene has a clip. Story → `failed` with a
  summary; the user can fix and press Retry (resumes, done stages skipped).
- Image stage never hard-fails: falls back through sources, then previous scene's image, then
  a solid frame — recorded as `image_source` so it is visible.
- Voice: Chatterbox error → Edge TTS, recorded as `voice_engine`.
- Worker crash (process exits): UI detects via `is_alive()` poll, marks the running story
  `failed: worker crashed`, restarts the worker, shows a toast.
- On app launch, any story left `rendering` is reset to `failed: interrupted` (resumable).
- Network calls: timeouts everywhere; DeepSeek/YouTube errors shown inline, never crash the UI.

## 5. Testing

- `pytest` for `pipeline/` and `services/` with network mocked (`responses`) and tiny fixtures
  (a 2-scene story rendered with a stub voice that writes a 1s sine wave — exercises ffmpeg
  end to end in seconds).
- Worker protocol test: start the real worker process with a stub voice engine, send
  `render_story`, assert event sequence and DB state.
- UI: `pytest-qt` smoke tests (window opens, story view renders rows from a seeded DB, an event
  updates a row).
- Manual check per phase: render a real 3-scene story with Chatterbox and inspect it in the UI.

## Phases

1. **Core + pipeline + worker** — db, paths, settings, port `worker.py` into `pipeline/` with
   per-stage tracking, worker process + events, import of existing Laravel data. Tests.
2. **Story view** — main window, dashboard list, create story (AI + manual), tracking grid,
   players, per-scene edit/redo.
3. **Schedules + Statistics + Settings.**
4. **YouTube** — OAuth loopback flow, upload, scheduled publish, metadata generation.
5. **Parity check, packaging (`desktop.py` replaced), delete Laravel/Vue.**
