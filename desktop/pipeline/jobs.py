"""Render jobs with per-scene, per-stage tracking. Runs inside the worker process; the DB is the
source of truth and every change is announced with an event dict passed to `emit`."""
import random
import traceback
from pathlib import Path
from typing import Callable

from desktop.core import db, paths
from desktop.pipeline import images, render, voice

Emit = Callable[[dict], None]


def _story_event(emit, story, status):
    story.status = status
    if status == "done":
        from datetime import datetime
        story.rendered_at = datetime.now()
    emit({"type": "story", "story_id": story.id, "status": status})


def _set_stage(s, emit, scene, stage, status, error=None, **info):
    setattr(scene, f"{stage}_status", status)
    setattr(scene, f"{stage}_error", error)
    s.commit()
    emit({"type": "stage", "story_id": scene.story_id, "scene_id": scene.id, "stage": stage,
          "status": status, "info": {k: v for k, v in info.items() if v is not None} | (
              {"error": error} if error else {})})


def _is_done(scene, stage) -> bool:
    p = getattr(scene, f"{stage}_path")
    return getattr(scene, f"{stage}_status") == "done" and bool(p) and Path(p).exists()


def _run_stage(scene, stage, story, cfg, engine, previous_image):
    d = paths.scene_dir(story.id, scene.id)
    if stage == "image":
        out = d / "image.jpg"
        hit = images.fetch_scene_image(scene.image_prompt or scene.narration, out, story.aspect_ratio, cfg,
                                       previous_image=previous_image)
        scene.image_path, scene.image_source = str(out), hit.source
        scene.image_source_url, scene.image_license = hit.url, hit.license
        return {"source": hit.source, "license": hit.license, "url": hit.url}
    if stage == "voice":
        out = d / "voice.wav"
        used, dur = voice.make_voice(out, scene.narration, style=story.style or "story",
                                     scene_index=scene.order, engine=engine)
        scene.voice_path, scene.voice_engine, scene.duration_s = str(out), used, dur
        return {"engine": used, "duration_s": round(dur, 2)}
    out = d / "clip.mp4"
    render.render_scene_clip(scene.image_path, scene.voice_path, out, scene.narration, scene.order,
                             story.aspect_ratio, preset=cfg.get("render_preset", "slow"))
    scene.clip_path = str(out)
    return {}


def _render_scene(s, emit, story, scene, cfg, engine, previous_image) -> bool:
    for stage in db.STAGES:
        if _is_done(scene, stage):
            continue
        _set_stage(s, emit, scene, stage, "running")
        try:
            info = _run_stage(scene, stage, story, cfg, engine, previous_image)
        except Exception as e:
            _set_stage(s, emit, scene, stage, "failed", error=f"{type(e).__name__}: {e}")
            traceback.print_exc()
            return False
        story.final_path = None  # anything re-rendered makes the final video stale
        _set_stage(s, emit, scene, stage, "done", **info)
    return True


def _assemble(s, emit, story, cfg):
    music = None
    if cfg.get("background_music", True):
        tracks = sorted((paths.assets_dir() / "music").glob("*.mp3"))
        music = random.choice(tracks) if tracks else None
    out = paths.story_dir(story.id) / "final.mp4"
    render.assemble([sc.clip_path for sc in story.scenes], out, story.aspect_ratio, music=music,
                    logo=paths.assets_dir() / "logo.png", preset=cfg.get("render_preset", "slow"))
    story.final_path = str(out)


def _finish(s, emit, story, cfg, failed: int):
    if failed:
        story.error = f"{failed} of {len(story.scenes)} scenes failed"
        _story_event(emit, story, "failed")
    elif story.final_path and Path(story.final_path).exists():
        story.error = None
        _story_event(emit, story, "done")
    else:
        emit({"type": "assemble", "story_id": story.id, "status": "running"})
        try:
            _assemble(s, emit, story, cfg)
            story.error = None
            _story_event(emit, story, "done")
        except Exception as e:
            story.error = f"assembly failed: {e}"
            _story_event(emit, story, "failed")
    s.commit()


def render_story(Session, story_id: int, emit: Emit, cfg: dict, engine) -> None:
    with Session() as s:
        story = s.get(db.Story, story_id)
        _story_event(emit, story, "rendering")
        story.error = None
        s.commit()
        failed, previous_image = 0, None
        for scene in story.scenes:
            if not _render_scene(s, emit, story, scene, cfg, engine, previous_image):
                failed += 1
            if scene.image_status == "done":
                previous_image = scene.image_path
        _finish(s, emit, story, cfg, failed)


def redo_scene(Session, scene_id: int, from_stage: str, emit: Emit, cfg: dict, engine) -> None:
    """Re-run `from_stage` and later stages of one scene, then rebuild the final video."""
    with Session() as s:
        scene = s.get(db.Scene, scene_id)
        scene.reset_from(from_stage)
        s.commit()
    render_story(Session, scene.story_id, emit, cfg, engine)
