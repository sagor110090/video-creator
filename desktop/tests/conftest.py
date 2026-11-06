import pytest


@pytest.fixture(autouse=True)
def data_dir(tmp_path, monkeypatch):
    """Every test gets its own empty data dir."""
    d = tmp_path / "data"
    monkeypatch.setenv("VC_DATA_DIR", str(d))
    from desktop.core import db
    db.reset_engine()
    yield d
    db.reset_engine()


@pytest.fixture
def Session(data_dir):
    from desktop.core import db
    db.init_db()
    return db.Session
