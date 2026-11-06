# Desktop App Phase 1 — Core, Pipeline, Worker — Implementation Plan

> **For Claude:** REQUIRED SUB-SKILL: Use superpowers:executing-plans to implement this plan task-by-task.

**Goal:** A headless, tested Python core for the new desktop app: data storage, the media
pipeline ported from `ai_worker/worker.py` with per-scene/per-stage tracking, a long-lived
worker process that emits progress events, and a one-time import of the Laravel data.

**Architecture:** Package `desktop/` at the repo root, run with `python -m desktop...` from the
repo root. `core/` (paths, settings, SQLAlchemy models), `pipeline/` (images, voice, render,
jobs, worker) — no Qt anywhere in this phase. A tiny CLI (`desktop/cli.py`) stands in for the
UI until phase 2. Design: `docs/plans/2026-11-07-python-desktop-app-design.md`.

**Tech Stack:** Python 3.11, SQLAlchemy 2, requests, Pillow, chatterbox-tts + torch, edge-tts,
ffmpeg (system), pytest, responses. PySide6 is installed now but first used in phase 2.

**Conventions**
- Run everything from the repo root with the desktop venv: `desktop/.venv/bin/python`.
- Tests: `desktop/.venv/bin/python -m pytest desktop/tests -q`.
- `VC_DATA_DIR` env var overrides the data dir (tests point it at `tmp_path`).
- Media per scene lives in `<data>/stories/<story_id>/scenes/<scene_id>/` (scene **id**, not
  order, so reordering/editing never mixes up files). Final video: `<data>/stories/<id>/final.mp4`.
- Deliberate drops vs. `worker.py` (YAGNI): Yahoo scraping and `clean_watermark` (only needed
  for scraped images), Picsum, macOS `say` fallback, the unused `ChatterboxVC` path.

---

### Task 0: Project setup

**Files:** Create `desktop/__init__.py`, `desktop/requirements.txt`, `desktop/pytest.ini`,
`desktop/tests/__init__.py`, `desktop/tests/conftest.py`, `desktop/assets/` (copied files).

1. `desktop/requirements.txt`: the `ai_worker/requirements.txt` set (incl. `setuptools<81`)
   plus `PySide6`, `SQLAlchemy>=2`, `pytest`, `responses`. Drop `openai`, `tabulate`.
2. `uv venv --python 3.11 desktop/.venv`; install numpy/setuptools/wheel/cython first, then
   `uv pip install --no-build-isolation-package pkuseg -r desktop/requirements.txt`.
3. Copy assets: `public/logo.png` → `desktop/assets/logo.png`,
   `public/audio/background/*.mp3` → `desktop/assets/music/`.
4. `conftest.py`: autouse fixture setting `VC_DATA_DIR` to `tmp_path` and clearing settings
   caches; fixture `db` returning a fresh session factory.
5. Add `desktop/.venv/` and `__pycache__/` to `.gitignore`.
6. Verify: `desktop/.venv/bin/python -c "import PySide6, sqlalchemy, chatterbox"` → no error.
7. Commit: `chore(desktop): scaffold package, venv requirements, assets`.

### Task 1: `core/paths.py`

API: `data_dir() -> Path` (env `VC_DATA_DIR` or `~/Library/Application Support/VideoCreator`,
created on call), `db_path()`, `story_dir(story_id)`, `scene_dir(story_id, scene_id)`,
`assets_dir()`, `REPO_ROOT`.

Test (`tests/test_paths.py`): with `VC_DATA_DIR=tmp_path`, `scene_dir(3, 7)` ==
`tmp_path/"stories/3/scenes/7"` and exists. Red → implement → green → commit.

### Task 2: `core/settings.py`

JSON file `<data>/settings.json`. API: `load() -> dict` (defaults merged), `save(dict)`,
`get(key)`. Defaults: `ai_provider="deepseek"`, `deepseek_api_key=""`, `groq_api_key=""`,
`pexels_api_key=""`, `pixabay_api_key=""`, `pollinations_token=""`,
`image_sources="pexels,pixabay,openverse,pollinations,loremflickr"`,
`voice_engine="chatterbox"` (`chatterbox|edge|stub`), `voice_sample=""`,
`background_music=True`, `render_preset="slow"`.
`seed_from_env(env_path)`: on first load only (no settings file yet), read the Laravel `.env`
keys `DEEPSEEK_API_KEY, GROQ_API_KEY, AI_STORY_PROVIDER, PEXELS_API_KEY, PIXABAY_API_KEY,
POLLINATIONS_TOKEN, IMAGE_SOURCES` and set `voice_sample` to `public/audio/my-voice.wav` if
it exists (copy it to `<data>/voice/sample.wav`).

Tests: defaults when no file; save→load round trip; `seed_from_env` with a temp `.env` maps
keys and does not overwrite an existing settings file. Commit.

### Task 3: `core/db.py`

SQLAlchemy 2 declarative models per design section 2: `Story`, `Scene`, `Schedule`, `Channel`.
Scene stage columns: for `stage in (image, voice, clip)`: `<stage>_status` (default
`"pending"`), `<stage>_path`, `<stage>_error`; plus `image_source`, `image_source_url`,
`image_license`, `voice_engine`, `duration_s`. Story: `status` default `"draft"`, `error`,
`final_path`, youtube fields, `schedule_id`, timestamps.
`engine()` uses `sqlite:///<db_path>` with `PRAGMA journal_mode=WAL` and `busy_timeout=5000`
(UI and worker processes both write). `init_db()`, `Session = sessionmaker(...)`.
Helpers: `Scene.reset_from(stage)` sets that stage and all later ones to `pending`
(order image→voice→clip) and the story's `final_path=None`.

Tests: create story + 2 scenes, query back ordered by `order`; `reset_from("voice")` leaves
image `done` and sets voice/clip `pending`; two engines (simulating two processes) can both
write. Commit.

### Task 4: `pipeline/ffmpeg.py`

Port `run_command` (worker.py 282–298) as `run(args) -> None` raising `FFmpegError(stderr
tail)` instead of returning False; `probe_duration(path) -> float`; ffmpeg/ffprobe located
with `shutil.which` then `/opt/homebrew/bin`.

Test: generate a 1s sine with `run([... 'sine=d=1' ...])`, `probe_duration` ≈ 1.0; bad args
raise `FFmpegError`. Commit.

### Task 5: `pipeline/images.py`

Port the source functions from worker.py (`_image_from_pexels/_pixabay/_openverse/
_pollinations/_loremflickr`, `_save_image_bytes`, `_clean_query`), but each returns
`ImageHit(source, url, license) | None` instead of bool, reading keys from a `cfg` dict
(settings) instead of `os.getenv`.
`fetch_scene_image(prompt, out_path, aspect_ratio, cfg, previous_image=None) -> ImageHit`:
tries full prompt, then `extract_keywords(prompt, 3)`, then `"cinematic background"` across
sources; then copies `previous_image` (`source="previous_scene"`); then writes a solid dark
frame via ffmpeg (`source="placeholder"`). Never raises.

Tests (network mocked with `responses`):
- Openverse returns a result → hit.source == "openverse", license "cc0", file is JPEG.
- All sources 500 + previous image given → `previous_scene`, file copied.
- All fail, no previous → `placeholder`, valid image of target size.
- Pexels skipped (no request made) when key empty.
Commit.

### Task 6: `pipeline/voice.py`

`is_devanagari`, `detect_language(text, default="en")`.
Engines with `synthesize(text, out_wav, language, style, scene_index) -> str` (engine name):
- `ChatterboxEngine(sample_path)` — lazy-loads `ChatterboxMultilingualTTS` once (with the CPU
  `torch.load` map_location patch from worker.py 55–64), writes wav.
- `EdgeEngine` — port voices/prosody from worker.py 372–445.
- `StubEngine` — writes a sine of `0.3s * word_count` via ffmpeg (tests only).
`make_voice(out_path, text, ..., engine)`: try engine, on exception fall back to `EdgeEngine`,
then post-process with the same ffmpeg filter chain as worker.py 530–544 into
`voice.wav` (48 kHz stereo PCM). Returns `(engine_used, duration_s)`.
`get_engine(cfg)` builds from `cfg["voice_engine"]`.

Tests: Stub → file exists, duration ≈ 0.3×words; engine raising → falls back (EdgeEngine
monkeypatched to stub) and reports `"edge"`; `detect_language("नमस्ते")=="hi"`. Commit.

### Task 7: `pipeline/render.py`

Port `create_scene_video` (worker.py 674–837) as `render_scene_clip(image, audio, out,
narration, scene_index, aspect_ratio, preset)` raising on failure (no "mock" file), and
`step4_automatic_assembly` (839–982) as `assemble(clips, out, aspect_ratio, music, logo)`.
Font search uses `desktop/assets/fonts` then system fonts. Add `preset` param so tests can
use `ultrafast`.

Tests (real ffmpeg, small): placeholder image + 1s stub voice → clip exists, duration ≈ 1s,
has video+audio streams; two clips → assemble → duration ≈ sum − 0.3s crossfade; logo and
music optional. Commit.

### Task 8: `pipeline/jobs.py` — stage tracking

`render_story(Session, story_id, emit, cfg, voice_engine)`:
- story.status = `rendering`, emit `{"type":"story","story_id","status"}`.
- For each scene in order, for stage in image→voice→clip: if `status=="done"` and file
  exists → skip; else set `running`, emit, run, store path + metadata, set `done`, emit.
  On exception: set `failed` + error, emit, continue to next scene (skip later stages of
  this scene).
- If every scene has a clip → assemble into `final.mp4`, story `done`; else story `failed`
  with "N scenes failed".
- `redo_scene(Session, scene_id, stages, ...)`: `reset_from(min stage)`, then run that scene
  and re-assemble.
Events: `{"type":"stage","story_id","scene_id","stage","status","info":{...}}`.

Tests (stub voice, images monkeypatched to write placeholder): 2-scene story → all stages
`done`, final exists, event sequence starts with story/rendering and ends story/done;
re-run skips everything (no `running` events); voice failure on scene 1 → story `failed`,
scene 0 fully done; `redo_scene(voice)` re-runs only voice+clip. Commit.

### Task 9: `pipeline/worker.py` — worker process

`worker_main(job_q, event_q, data_dir)`: sets `VC_DATA_DIR`, builds engine once from
settings, loops `job = job_q.get()`; `None` → exit. Dispatches `render_story`/`redo_scene`/
`assemble`; wraps each in try/except emitting `{"type":"job_error", ...}`; always emits
`{"type":"job_done","job_id"}`.
`WorkerHandle`: `start()` (spawn context), `submit(kind, **kw) -> job_id`, `events()`
non-blocking drain, `is_alive()`, `restart()`, `stop()`.
`recover_interrupted(Session)`: stories left `rendering` → `failed` "interrupted"; scene
stages left `running` → `pending`.

Tests: real spawned process with `voice_engine=stub` and images patched via
`cfg["image_sources"]="placeholder-only"` (add a hidden `placeholder` source used only when
listed): submit render of a 1-scene story → receive `job_done` within 60s and DB story is
`done`; `recover_interrupted` resets states. Commit.

### Task 10: `core/import_laravel.py`

`import_laravel(sqlite_path, laravel_root, Session) -> dict(counts)`: copies `youtube_tokens`
→ Channel, `video_schedules` → Schedule, `stories` → Story (status: `completed`→`done`,
`processing`/`pending`→`draft`, `failed`→`failed`), `scenes` → Scene. If
`storage/app/public/videos/<story_id>/scene_<order>_{img.jpg,aud.mp3,vid.mp4}` exist, copy
them into the new scene dir (aud converted to `voice.wav`) and mark those stages `done`;
copy `final_video.mp4` → `final.mp4`. Idempotent: skips if a marker
`<data>/.imported_laravel` exists.

Tests with a fixture SQLite built in the test (2 stories, 3 scenes, 1 token, 1 schedule)
and a fake files tree: counts match, file stages marked done, second run imports nothing.
Commit.

### Task 11: `desktop/cli.py` + real render check

`python -m desktop.cli import-laravel`, `create --title T --text "..." [--aspect 9:16]`
(splits into scenes by sentence, image prompt = `extract_keywords` for now; AI prompts come
with `services/story_ai.py` in phase 2), `render <story_id>` (starts `WorkerHandle`, prints
events live), `show <story_id>` (table of scenes × stages with source/engine).

Verify: run the full test suite; then `create` a 3-sentence story and `render` it with
Chatterbox and the real image sources; `show` lists every stage `done`; open `final.mp4`.
Commit: `feat(desktop): phase 1 core pipeline, worker, import, CLI`.
