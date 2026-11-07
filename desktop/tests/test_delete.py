import pytest

from desktop.core import db, paths
from desktop.services import stories


def _story(Session, status="done", export=None):
    with Session() as s:
        st = db.Story(title="Bye", content="x", status=status, export_path=export)
        st.scenes = [db.Scene(order=0, narration="n", image_prompt="p")]
        s.add(st)
        s.commit()
        sid, scene_id = st.id, st.scenes[0].id
    (paths.scene_dir(sid, scene_id) / "image.jpg").write_bytes(b"img")
    return sid


def test_delete_removes_story_scenes_and_files(Session, tmp_path):
    exported = tmp_path / "out" / "Bye (1).mp4"
    exported.parent.mkdir()
    exported.write_bytes(b"mine")
    sid = _story(Session, export=str(exported))
    folder = paths.data_dir() / "stories" / str(sid)
    assert folder.exists()
    stories.delete_story(sid)
    with Session() as s:
        assert s.get(db.Story, sid) is None and s.query(db.Scene).count() == 0
    assert not folder.exists()
    assert exported.exists()            # the user's own output-folder copy is kept


@pytest.mark.parametrize("status", ["rendering", "queued"])
def test_cannot_delete_while_rendering(Session, status):
    sid = _story(Session, status=status)
    with pytest.raises(stories.StoryBusyError):
        stories.delete_story(sid)
    with Session() as s:
        assert s.get(db.Story, sid) is not None


def test_card_menu_delete(qtbot, Session, monkeypatch):
    from desktop.tests.test_ui import FakeBridge
    from desktop.ui import dashboard
    keep, gone = _story(Session), _story(Session)
    page = dashboard.DashboardPage(FakeBridge(), open_story=lambda i: None)
    qtbot.addWidget(page)

    def card_for(story_id):
        for i in range(page.stories.count()):
            if page.stories.item(i).data(dashboard.Qt.UserRole) == story_id:
                return page.stories.itemWidget(page.stories.item(i))

    monkeypatch.setattr(dashboard.QMessageBox, "question", lambda *a, **k: dashboard.QMessageBox.No)
    card_for(keep).action("Delete story…").trigger()
    qtbot.wait(50)
    assert page.stories.count() == 2
    monkeypatch.setattr(dashboard.QMessageBox, "question", lambda *a, **k: dashboard.QMessageBox.Yes)
    card_for(gone).action("Delete story…").trigger()
    qtbot.waitUntil(lambda: page.stories.count() == 1, timeout=3000)
    assert card_for(keep) is not None and card_for(gone) is None


def test_delete_disabled_while_rendering(qtbot, Session):
    from desktop.tests.test_ui import FakeBridge
    from desktop.ui import dashboard
    _story(Session, status="rendering")
    page = dashboard.DashboardPage(FakeBridge(), open_story=lambda i: None)
    qtbot.addWidget(page)
    action = page.stories.itemWidget(page.stories.item(0)).action("Delete story…")
    assert action is not None and not action.isEnabled()
