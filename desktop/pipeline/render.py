"""Scene clips (Ken Burns + subtitles) and final assembly. Ported from ai_worker/worker.py."""
import os
import re
import shutil
from pathlib import Path

from desktop.core import paths
from desktop.pipeline import ffmpeg
from desktop.pipeline.voice import is_devanagari

FPS = 30
CROSSFADE = 0.3

# Six motion patterns, picked by scene index for variety.
def _motion(i: int, frames: int) -> tuple[str, str, str]:
    patterns = [
        ("min(zoom+0.0015,1.35)", "iw/2-(iw/zoom/2)", "ih/2-(ih/zoom/2)"),
        ("max(1.35-0.0015*on,1.0)", "iw/2-(iw/zoom/2)", "ih/2-(ih/zoom/2)"),
        ("min(zoom+0.0008,1.20)", f"on/({frames})*iw/3", "ih/2-(ih/zoom/2)"),
        ("min(zoom+0.0008,1.20)", f"iw/3-on/({frames})*iw/3", "ih/2-(ih/zoom/2)"),
        ("min(zoom+0.0012,1.3)", "iw/2-(iw/zoom/2)", "ih/4-(ih/zoom/2)"),
        ("min(zoom+0.0012,1.3)", "iw/2-(iw/zoom/2)", "ih*3/4-(ih/zoom/2)"),
    ]
    return patterns[i % len(patterns)]


def _font(hindi: bool) -> str:
    fonts = ["/System/Library/Fonts/Supplemental/Arial Bold.ttf", "/System/Library/Fonts/Helvetica.ttc",
             "/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf"]
    if hindi:
        fonts = [str(paths.assets_dir() / "fonts" / "NotoSansDevanagari-Bold.ttf"),
                 "/System/Library/Fonts/Supplemental/DevanagariMT.ttc",
                 "/System/Library/Fonts/Kohinoor.ttc"] + fonts
    return next((f for f in fonts if os.path.exists(f)), "Arial")


def _escape(txt: str) -> str:
    return (txt.replace("\\", "\\\\").replace("'", "'\\\\\\''").replace(":", "\\:")
            .replace(",", "\\,").replace("%", "\\%"))


def _subtitles(narration: str, duration: float, aspect_ratio: str) -> str:
    """3 words at a time, white with black outline (Shorts style)."""
    words = re.sub(r"\s+", " ", narration).strip().split()
    if not words:
        return ""
    per_word = duration / len(words)
    size = 64 if aspect_ratio == "16:9" else 80
    y = "h-150" if aspect_ratio == "16:9" else "(h-text_h)/2+300"
    font = _font(is_devanagari(narration))
    parts = []
    for i in range(0, len(words), 3):
        start, end = i * per_word, min((i + 3) * per_word, duration)
        parts.append(
            f"drawtext=text='{_escape(' '.join(words[i:i + 3]))}':fontfile='{font}':"
            f"fontcolor=white:fontsize={size}:borderw=4:bordercolor=black:"
            f"shadowcolor=black@0.8:shadowx=2:shadowy=2:x=(w-text_w)/2:y={y}:"
            f"enable='between(t,{start:.3f},{end:.3f})'")
    return ",".join(parts)


def render_scene_clip(image, audio, out, narration, scene_index=0, aspect_ratio="16:9", preset="slow"):
    width, height = (1920, 1080) if aspect_ratio == "16:9" else (1080, 1920)
    base_w, base_h = (3840, 2160) if aspect_ratio == "16:9" else (2160, 3840)
    duration = max(ffmpeg.probe_duration(audio), 1.0)
    frames = int(duration * FPS)
    z, x, y = _motion(scene_index, frames)
    vf = [
        f"scale=w={base_w}:h={base_h}:force_original_aspect_ratio=increase",
        f"crop={base_w}:{base_h}",
        "eq=contrast=1.08:saturation=1.15:brightness=0.01,curves=preset=lighter,unsharp=5:5:0.8:5:5:0.4",
        f"zoompan=z='{z}':x='{x}':y='{y}':d={frames}:s={width}x{height}:fps={FPS}",
        "fade=t=in:st=0:d=0.4",
        f"fade=t=out:st={max(0, duration - 0.4)}:d=0.4",
    ]
    subs = _subtitles(narration, duration, aspect_ratio)
    if subs:
        vf.append(subs)
    vf += [f"fps={FPS}", "format=yuv420p"]
    ffmpeg.run(["-loop", "1", "-i", image, "-i", audio, "-vf", ",".join(vf),
                "-c:v", "libx264", "-preset", preset, "-crf", "17", "-profile:v", "high", "-level", "4.1",
                "-tune", "film", "-movflags", "+faststart", "-t", f"{duration:.3f}", "-pix_fmt", "yuv420p",
                "-c:a", "aac", "-b:a", "256k", "-ar", "48000", "-shortest", out])


def _merge(clips: list[Path], out: Path, preset: str) -> None:
    if len(clips) == 1:
        shutil.copy(clips[0], out)
        return
    durations = [ffmpeg.probe_duration(c) for c in clips]
    parts, offset, v, a = [], 0.0, "0:v", "0:a"
    for i in range(1, len(clips)):
        offset += durations[i - 1] - CROSSFADE
        nv, na = ("v", "a") if i == len(clips) - 1 else (f"v{i}", f"a{i}")
        parts.append(f"[{v}][{i}:v]xfade=transition=fade:duration={CROSSFADE}:offset={offset:.3f}[{nv}]")
        parts.append(f"[{a}][{i}:a]acrossfade=d={CROSSFADE}[{na}]")
        v, a = nv, na
    inputs = [arg for c in clips for arg in ("-i", c)]
    try:
        ffmpeg.run([*inputs, "-filter_complex", ";".join(parts), "-map", "[v]", "-map", "[a]",
                    "-c:v", "libx264", "-preset", preset, "-crf", "18", "-c:a", "aac", "-b:a", "256k", out])
    except ffmpeg.FFmpegError:
        concat = out.with_suffix(".txt")
        concat.write_text("".join(f"file '{Path(c).resolve()}'\n" for c in clips))
        ffmpeg.run(["-f", "concat", "-safe", "0", "-i", concat, "-c", "copy", out])
        concat.unlink(missing_ok=True)


def assemble(clips, out, aspect_ratio="16:9", music=None, logo=None, preset="slow") -> Path:
    """Crossfade clips, then overlay logo and mix background music in one pass."""
    clips, out = [Path(c) for c in clips], Path(out)
    if not clips:
        raise ValueError("no clips to assemble")
    merged = out.with_name("merged.tmp.mp4")
    _merge(clips, merged, preset)
    has_logo = bool(logo) and Path(logo).exists()
    has_music = bool(music) and Path(music).exists()
    if not (has_logo or has_music):
        merged.replace(out)
        return out
    inputs, filters, vmap, amap = ["-i", merged], [], "0:v", "0:a"
    if has_logo:
        width = 1920 if aspect_ratio == "16:9" else 1080
        inputs += ["-i", logo]
        filters.append(f"[1:v]scale={int(width * 0.08)}:-1,format=rgba,colorchannelmixer=aa=0.7[logo];"
                       "[0:v][logo]overlay=W-w-25:H-h-25[v]")
        vmap = "[v]"
    if has_music:
        idx = 2 if has_logo else 1
        inputs += ["-stream_loop", "-1", "-i", music]
        fade_out = max(0, ffmpeg.probe_duration(merged) - 3)
        filters.append(f"[{idx}:a]volume=0.25,afade=t=in:d=2,afade=t=out:st={fade_out:.2f}:d=3[bg];"
                       "[0:a]volume=1.5,dynaudnorm=p=0.9[narr];"
                       "[narr][bg]amix=inputs=2:duration=first:dropout_transition=2,volume=2[a]")
        amap = "[a]"
    vcodec = ["-c:v", "libx264", "-preset", preset, "-crf", "18"] if has_logo else ["-c:v", "copy"]
    acodec = ["-c:a", "aac", "-b:a", "256k", "-ar", "48000"] if has_music else ["-c:a", "copy"]
    try:
        ffmpeg.run([*inputs, "-filter_complex", ";".join(filters), "-map", vmap, "-map", amap,
                    *vcodec, *acodec, "-movflags", "+faststart", "-shortest", out])
    finally:
        merged.unlink(missing_ok=True)
    return out
