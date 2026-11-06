"""Narration audio. Chatterbox voice cloning, with Edge TTS as fallback. Ported from ai_worker/worker.py."""
import asyncio
import re
from pathlib import Path

from desktop.pipeline import ffmpeg

# Same mastering chain as the old worker: loud, normalized, slight room, trimmed lows/highs.
MASTER_FILTER = ("volume=4.5,dynaudnorm=p=0.95:s=5,aecho=0.8:0.88:6:0.4,"
                 "highpass=f=80,lowpass=f=15000")


class VoiceError(RuntimeError):
    pass


def is_devanagari(text: str) -> bool:
    return any("ऀ" <= ch <= "ॿ" for ch in text)


def detect_language(text: str, default: str = "en") -> str:
    return "hi" if default == "en" and is_devanagari(text) else default


class StubEngine:
    """Tests only: a 440 Hz tone, 0.3s per word."""
    name = "stub"

    def synthesize(self, text, out_wav, language="en", style="story", scene_index=0):
        dur = max(0.3 * len(text.split()), 0.3)
        ffmpeg.run(["-f", "lavfi", "-i", f"sine=frequency=440:duration={dur}", "-ar", "24000", out_wav])


class ChatterboxEngine:
    name = "chatterbox"
    _model = None  # loaded once per process

    def __init__(self, sample_path: str | None = None):
        self.sample_path = sample_path if sample_path and Path(sample_path).exists() else None

    @classmethod
    def model(cls):
        if cls._model is None:
            import torch
            if not torch.cuda.is_available():
                # Checkpoints were saved on CUDA and chatterbox omits map_location on some loads.
                orig = torch.load

                def cpu_load(*a, **k):
                    k.setdefault("map_location", torch.device("cpu"))
                    return orig(*a, **k)
                torch.load = cpu_load
            from chatterbox.mtl_tts import ChatterboxMultilingualTTS
            cls._model = ChatterboxMultilingualTTS.from_pretrained("cuda" if torch.cuda.is_available() else "cpu")
        return cls._model

    def synthesize(self, text, out_wav, language="en", style="story", scene_index=0):
        import numpy as np
        from scipy.io import wavfile
        m = self.model()
        wav = m.generate(text, language_id=language, audio_prompt_path=self.sample_path)
        wavfile.write(out_wav, m.sr, wav.squeeze(0).numpy().astype(np.float32))


class EdgeEngine:
    name = "edge"
    VOICES = {"en": {"science_short": "en-US-SteffanNeural", "hollywood_hype": "en-US-AvaNeural",
                     "trade_wave": "en-GB-RyanNeural", "story": "en-US-AndrewNeural"},
              "hi": {"science_short": "hi-IN-MadhurNeural", "hollywood_hype": "hi-IN-SwaraNeural",
                     "trade_wave": "hi-IN-MadhurNeural", "story": "hi-IN-MadhurNeural",
                     "bollywood_masala": "hi-IN-SwaraNeural"}}
    PROSODY = {"science_short": (-5, -1), "hollywood_hype": (0, 2), "trade_wave": (-5, -2),
               "story": (-10, 1), "bollywood_masala": (0, 2)}

    def synthesize(self, text, out_wav, language="en", style="story", scene_index=0):
        import edge_tts
        voices = self.VOICES["hi" if language.startswith("hi") else "en"]
        rate, pitch = self.PROSODY.get(style, self.PROSODY["story"])
        rate += (scene_index % 2) * 2           # small per-scene variation, as before
        pitch += (scene_index % 3 - 1) * 2
        tmp = str(out_wav) + ".edge.mp3"
        clean = re.sub(r"<[^>]*>", "", text).strip()
        comm = edge_tts.Communicate(clean, voices.get(style, voices["story"]),
                                    rate=f"{rate:+d}%", pitch=f"{pitch:+d}Hz")
        asyncio.run(comm.save(tmp))
        try:
            ffmpeg.run(["-i", tmp, out_wav])
        finally:
            Path(tmp).unlink(missing_ok=True)


def engine_for(engine, sample_path):
    """The engine to use for one story: Chatterbox clones `sample_path`; other engines don't clone."""
    if getattr(engine, "name", "") == "chatterbox":
        return ChatterboxEngine(sample_path)   # cheap: the model is loaded once per process
    return engine


def get_engine(cfg: dict):
    kind = cfg.get("voice_engine", "chatterbox")
    if kind == "stub":
        return StubEngine()
    if kind == "edge":
        return EdgeEngine()
    return ChatterboxEngine(cfg.get("voice_sample"))


def make_voice(out_path, text, language=None, style="story", scene_index=0, engine=None):
    """Synthesize + master into out_path (48 kHz stereo WAV). Returns (engine_name, duration_s)."""
    out_path = Path(out_path)
    language = language or detect_language(text)
    raw = out_path.with_suffix(".raw.wav")
    used, errors = None, []
    chain = [engine] if engine is not None else []
    if not chain or getattr(engine, "name", "") != "edge":
        chain.append(EdgeEngine())
    for eng in chain:
        try:
            eng.synthesize(text, str(raw), language, style, scene_index)
            used = eng.name
            break
        except Exception as e:  # fall through to Edge once
            errors.append(f"{getattr(eng, 'name', '?')}: {e}")
    if used is None:
        raise VoiceError("; ".join(errors))
    try:
        filt = MASTER_FILTER if used != "stub" else "anull"
        ffmpeg.run(["-i", raw, "-af", filt, "-ar", "48000", "-ac", "2", "-c:a", "pcm_s16le", out_path])
    finally:
        raw.unlink(missing_ok=True)
    return used, ffmpeg.probe_duration(out_path)
