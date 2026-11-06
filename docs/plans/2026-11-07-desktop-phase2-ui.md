# Desktop App Phase 2 — Story AI + Main Window + Scene Tracking — Implementation Plan

> **For Claude:** REQUIRED SUB-SKILL: Use superpowers:executing-plans to implement this plan task-by-task.

**Goal:** A runnable PySide6 desktop app: create a story (AI-written or pasted), render it in the
background worker, and watch/inspect every scene's image, voice and clip live, with per-scene
editing and redo.

**Architecture:** `services/story_ai.py` ports `AiStoryService.php` + the scene parser from
`ProcessStoryJob.php` (no Qt). `ui/` holds the Qt layer: `bridge.py` (WorkerHandle → Qt
signals), `main_window.py` (sidebar + stacked pages + tray), `dashboard.py` (story list +
create form), `story_view.py` (tracking grid + players). Network calls from the UI run in a
`QThreadPool` task (`ui/tasks.py`) so the window never blocks. DB is the source of truth;
events only trigger refreshes.

**Tech Stack:** PySide6 6.12 (QtWidgets, QtMultimedia, QtMultimediaWidgets), pytest-qt,
responses; phase 1 core/pipeline.

---

### Task 1: `services/story_ai.py`

API (all take `cfg` = settings dict):
- `chat(cfg, system, user, temperature, json_mode=True, timeout=120) -> str` — OpenAI-style POST
  to DeepSeek (`https://api.deepseek.com/chat/completions`, `deepseek-chat`) or Groq
  (`https://api.groq.com/openai/v1/chat/completions`, `llama-3.3-70b-versatile`); raises
  `StoryAIError` with the response body on failure or missing key.
- `generate_story(cfg, topic, style, aspect_ratio, talking_style) -> dict(title, content,
  youtube_title, youtube_description, youtube_tags)` — prompts ported verbatim
  (style prompts, talking-style patterns incl. Bollywood Hindi overrides, common rules,
  random perspective, word counts 140–160 for 9:16 and 500–600 for 16:9).
- `generate_topic(cfg, context, style) -> str` (fallback list on error).
- `generate_metadata(cfg, content) -> dict` (fallback dict on error).
- `search_news(cfg, query, style) -> list[dict]` (unwraps `news/results/items/...` keys;
  returns `[]` on error — the PHP hardcoded fake headlines are dropped).
- `generate_image_prompts(cfg, narrations) -> list[str]` (chunks of 20; per-index fallback
  to `clean_image_prompt(text)`).
- `split_scenes(content, style, talking_style, cfg) -> list[dict(narration, image_prompt)]` —
  sentence split, drop < 10 chars, AI prompts, max 50 scenes. Style hint words go at the
  **end** of the prompt (e.g. `"<prompt>, news celebrity"`) so Openverse narrowing keeps the
  subject. Constants: `STYLES`, `TALKING_STYLES` (value → label) for the UI.

Tests (`responses` mocks): story JSON parsed + `response_format` json_object sent + Bearer
key; missing key raises; `generate_image_prompts` maps "0","1" keys and falls back for a
missing index; `split_scenes` drops short sentences, appends style hint; news unwraps
`{"news":[...]}`; topic fallback on 500. Commit.

### Task 2: `ui/bridge.py` + `ui/tasks.py`

- `WorkerBridge(QObject)`: owns `WorkerHandle`; `QTimer` 100 ms drains `events()` and emits
  `event(dict)`, `storyChanged(int)`, `sceneChanged(int, int)`; every 2 s checks `is_alive()`
  — if dead: `recover_interrupted`, restart, emit `workerCrashed(str)`. `submit_render(id)`
  sets story `queued` in DB first. `stop()` on quit.
- `run_async(fn, *args, on_done, on_error)`: `QRunnable` + signal object, results delivered
  on the GUI thread.

Tests (pytest-qt): bridge with stub settings renders a 1-scene story and `storyChanged`
fires with `done` within 90 s; `run_async` delivers result and error. Commit.

### Task 3: `ui/main_window.py` + `desktop/main.py`

Dark theme (QSS in `ui/style.py`, cyan accent like the current UI). Left sidebar:
Dashboard, Settings (Schedules/Channels/Statistics come in phases 3–4, shown disabled).
`QStackedWidget` pages. Tray icon (`QSystemTrayIcon`, logo) with Show/Quit; closing the
window hides to tray only if a job is running, otherwise quits. Status bar shows worker
state ("Voice model loading…", "Idle", "Rendering story 3").
`main.py`: `multiprocessing.freeze_support()`, seed settings from `.env`, `init_db`,
`recover_interrupted`, start bridge, show window. Run with
`desktop/.venv/bin/python -m desktop.main`.

Tests: window constructs, sidebar switches pages. Commit.

### Task 4: `ui/dashboard.py`

Left: story list (`QListWidget`, newest first): title, status chip, scene count, aspect,
created date; double-click opens the story view. Right: create form — topic, content style
(combo from `STYLES`), talking style, format (Landscape 16:9 / Shorts 9:16), buttons
**Write with AI** (fills title + script via `generate_story` in `run_async`, button shows
"Writing…"), script editor, **Create & Render** (runs `split_scenes` async, saves story +
scenes, submits render, opens story view). Errors shown in a red label, never a crash.
Refreshes on `storyChanged`.

Tests: with story_ai functions monkeypatched — Write with AI fills fields; Create & Render
creates a story with N scenes and calls `submit_render`. Commit.

### Task 5: `ui/story_view.py`

Header: back button, title, status, progress bar (done stages / total stages), error text,
buttons **Render / Resume**, **Rebuild final**, **Open folder**. Final-video player
(`QMediaPlayer` + `QVideoWidget` + play/pause + slider) shown when `final_path` exists.

Scene list (scroll area of `SceneRow` widgets), each row:
- thumbnail 192×108 (click → full-size dialog), image source + license badge (link to source
  URL), stage chips Image / Voice / Clip coloured by status with tooltip = error.
- narration `QPlainTextEdit` and image prompt `QLineEdit` (Save marks the right stage stale:
  narration change → `reset_from("voice")`, prompt change → `reset_from("image")`).
- buttons: ▶ voice (QMediaPlayer audio), ▶ clip (opens clip in the player area),
  **Replace image…** (file dialog → copy to scene dir, source `manual`, `reset_from("voice")`
  but keep image done), **Re-fetch image**, **Re-voice**, **Re-render clip** →
  `submit redo_scene(from_stage)`.
- disabled while that story is rendering.
`sceneChanged` refreshes only the affected row; `storyChanged` refreshes the header.

Tests: seeded story with one done + one failed scene renders 2 rows, failed chip has the
error tooltip; editing narration + Save sets voice/clip pending; redo button submits the
right job (bridge mocked). Commit.

### Task 6: `ui/settings_page.py`

Form for API keys (masked), AI provider, image source order, voice engine, voice sample
(file picker + ▶ preview), background music on/off, render quality (slow/medium/fast).
Save writes `settings.json`; the worker re-reads it per job. Test: save round-trip. Commit.

### Task 7: Manual end-to-end

Launch the app, create a Shorts story with **Write with AI** (DeepSeek), render it, watch the
rows fill in, replace one image from file, re-render that clip, rebuild final, play it.
Fix what breaks. Commit.
