from desktop.core import paths


def test_scene_dir_under_data_dir(data_dir):
    d = paths.scene_dir(3, 7)
    assert d == data_dir / "stories" / "3" / "scenes" / "7"
    assert d.is_dir()


def test_db_path_and_assets(data_dir):
    assert paths.db_path() == data_dir / "videocreator.db"
    assert (paths.assets_dir() / "logo.png").exists()
