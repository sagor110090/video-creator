from desktop.core import settings


def test_defaults_without_file():
    cfg = settings.load()
    assert cfg["ai_provider"] == "deepseek"
    assert cfg["voice_engine"] == "chatterbox"
    assert cfg["image_sources"].startswith("pexels,pixabay,openverse")


def test_save_round_trip():
    cfg = settings.load()
    cfg["pexels_api_key"] = "abc"
    settings.save(cfg)
    assert settings.load()["pexels_api_key"] == "abc"


def test_seed_from_env(tmp_path, data_dir):
    root = tmp_path / "laravel"
    (root / "public" / "audio").mkdir(parents=True)
    (root / "public" / "audio" / "my-voice.wav").write_bytes(b"RIFFfake")
    env = root / ".env"
    env.write_text('DEEPSEEK_API_KEY=sk-1\nAI_STORY_PROVIDER=deepseek\nPEXELS_API_KEY=\n'
                   'IMAGE_SOURCES=openverse,pollinations\n')
    assert settings.seed_from_env(env) is True
    cfg = settings.load()
    assert cfg["deepseek_api_key"] == "sk-1"
    assert cfg["image_sources"] == "openverse,pollinations"
    assert cfg["voice_sample"].endswith("voice/sample.wav")
    assert (data_dir / "voice" / "sample.wav").read_bytes() == b"RIFFfake"
    # second call never overwrites an existing settings file
    env.write_text("DEEPSEEK_API_KEY=sk-2\n")
    assert settings.seed_from_env(env) is False
    assert settings.load()["deepseek_api_key"] == "sk-1"
