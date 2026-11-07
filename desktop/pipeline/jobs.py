"""Render jobs with per-scene, per-stage tracking. Runs inside the worker process; the DB is the
source of truth and every change is announced with an event dict passed to `emit`."""
import random
import traceback
from pathlib import Path
from typing import Callable

from desktop.core import db, paths
from desktop.pipeline import export, images, render, voice

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
        provider = scene.image_provider or story.image_provider      # per-scene, then per-story, then Settings
        if provider:
            cfg = dict(cfg, image_provider=provider)
        hit = images.fetch_scene_image(scene.image_prompt or scene.narration, out, story.aspect_ratio, cfg,
                                       previous_image=previous_image,
                                       image_style=images.resolve_style(story.image_style, story.style))
        scene.image_path, scene.image_source = str(out), hit.source
        scene.image_source_url, scene.image_license = hit.url, hit.license
        return {"source": hit.source, "license": hit.license, "url": hit.url, "warning": hit.note}
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


def _render_scene(s, emit, story, scene, cfg, engine, previous_image, stages=db.STAGES) -> bool:
    for stage in stages:
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
        warning = info.pop("warning", None)   # done, but with a note (e.g. Gemini fell back to free images)
        _set_stage(s, emit, scene, stage, "done", error=warning, **info)
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


def _export(story, cfg):
    """Copy the finished video to the output folder from Settings, if one is set. Never fails the render."""
    try:
        export.export_story(story, cfg.get("output_dir"))
    except OSError as e:
        story.error = f"Video is ready, but copying it to your output folder failed: {e}"


def _finish(s, emit, story, cfg, failed: int):
    if failed:
        story.error = f"{failed} of {len(story.scenes)} scenes failed"
        _story_event(emit, story, "failed")
    elif story.final_path and Path(story.final_path).exists():
        story.error = None
        if cfg.get("output_dir") and not (story.export_path and Path(story.export_path).exists()):
            _export(story, cfg)
        _story_event(emit, story, "done")
    else:
        emit({"type": "assemble", "story_id": story.id, "status": "running"})
        try:
            _assemble(s, emit, story, cfg)
            story.error = None
            _export(story, cfg)
            _story_event(emit, story, "done")
        except Exception as e:
            story.error = f"assembly failed: {e}"
            _story_event(emit, story, "failed")
    s.commit()


def render_story(Session, story_id: int, emit: Emit, cfg: dict, engine, images_only: bool = False) -> None:
    """Render every unfinished stage. images_only=True is the review step: fetch images, then stop at 'review'."""
    with Session() as s:
        story = s.get(db.Story, story_id)
        # the story's own voice sample, else the current Settings default
        engine = voice.engine_for(engine, story.voice_sample or cfg.get("voice_sample"))
        _story_event(emit, story, "rendering")
        story.error = None
        s.commit()
        failed, previous_image = 0, None
        stages = ("image",) if images_only else db.STAGES
        for scene in story.scenes:
            if not _render_scene(s, emit, story, scene, cfg, engine, previous_image, stages):
                failed += 1
            if scene.image_status == "done":
                previous_image = scene.image_path
        if images_only:
            story.error = f"{failed} of {len(story.scenes)} images failed" if failed else None
            _story_event(emit, story, "review")
            s.commit()
            return
        _finish(s, emit, story, cfg, failed)


def redo_scene(Session, scene_id: int, from_stage: str, emit: Emit, cfg: dict, engine,
               image_provider: str | None = None) -> None:
    """Re-run `from_stage` and later stages of one scene. While the story is in review only images are
    redone; after it has been built, the scene is re-rendered and the final video rebuilt."""
    with Session() as s:
        scene = s.get(db.Scene, scene_id)
        if image_provider is not None:
            scene.image_provider = image_provider or None      # "" = back to the story/Settings default
        scene.reset_from(from_stage)
        # never narrated yet = still in the review step (the status may already say "queued")
        reviewing = from_stage == "image" and all(sc.voice_status == "pending" for sc in scene.story.scenes)
        s.commit()
        story_id = scene.story_id
    render_story(Session, story_id, emit, cfg, engine, images_only=reviewing)
