from pathlib import Path

from PIL import Image

from desktop.core import characters


def _photo(tmp_path: Path, name="me.jpg") -> Path:
    src = tmp_path / name
    Image.new("RGB", (64, 64), (5, 5, 5)).save(src)
    return src


def test_add_image_creates_library_and_copies(data_dir, tmp_path):
    out = characters.add_image(_photo(tmp_path))
    assert out.exists() and out.parent == characters.library_dir()
    assert out.read_bytes() == (tmp_path / "me.jpg").read_bytes()


def test_add_image_same_file_twice_reuses_one_copy(data_dir, tmp_path):
    src = _photo(tmp_path)
    assert characters.add_image(src) == characters.add_image(src)
    assert len(list(characters.library_dir().iterdir())) == 1
