from datetime import datetime, timedelta

import pytest

from desktop.core import db
from desktop.tests.test_ui import FakeBridge

T0 = datetime(2026, 11, 7, 10, 0)


@pytest.fixture
def page(qtbot, Session):
    from desktop.ui import dashboard
    rows = [("Banana short", "9:16", "done", None, 0), ("Apple wide", "16:9", "failed", None, 1),
            ("Cherry short", "9:16", "done", "completed", 2), ("Date wide", "16:9", "rendering", None, 3),
            ("Elder short", "9:16", "review", "manual", 4)]
    with Session() as s:
        for title, ar, status, up, h in rows:
            s.add(db.Story(title=title, content="c", aspect_ratio=ar, status=status, youtube_upload_status=up,
                           created_at=T0 + timedelta(hours=h)))
        s.commit()
    p = dashboard.DashboardPage(FakeBridge(), open_story=lambda i: None)
    qtbot.addWidget(p)
    return p


def visible(page):
    return [page.stories.itemWidget(page.stories.item(i)).title.text()
            for i in range(page.stories.count()) if not page.stories.item(i).isHidden()]


def test_default_newest_first(page):
    assert visible(page) == ["Elder short", "Date wide", "Cherry short", "Apple wide", "Banana short"]


def test_sort_options(page):
    page.sort.setCurrentIndex(page.sort.findData("oldest"))
    assert visible(page)[0] == "Banana short"
    page.sort.setCurrentIndex(page.sort.findData("title"))
    assert visible(page) == ["Apple wide", "Banana short", "Cherry short", "Date wide", "Elder short"]
    page.sort.setCurrentIndex(page.sort.findData("status"))
    assert visible(page)[0] == "Date wide"          # rendering first, then review, failed, done


def test_format_and_status_filters(page):
    page.format_filter.setCurrentIndex(page.format_filter.findData("9:16"))
    assert visible(page) == ["Elder short", "Cherry short", "Banana short"]
    page.status_filter.setCurrentIndex(page.status_filter.findData("uploaded"))
    assert visible(page) == ["Elder short", "Cherry short"]
    page.status_filter.setCurrentIndex(page.status_filter.findData("not_uploaded"))
    assert visible(page) == ["Banana short"]
    page.format_filter.setCurrentIndex(page.format_filter.findData(""))
    page.status_filter.setCurrentIndex(page.status_filter.findData("failed"))
    assert visible(page) == ["Apple wide"]
    assert page.count_label.text() == "1 of 5 stories"


def test_filters_combine_with_search(page):
    page.format_filter.setCurrentIndex(page.format_filter.findData("9:16"))
    page.search.setText("cherry")
    assert visible(page) == ["Cherry short"]


def test_select_all_and_delete_selected(qtbot, page, Session, monkeypatch):
    from desktop.ui import dashboard
    page.select_btn.click()
    assert page.select_mode and not page.bulk_bar.isHidden()
    page.format_filter.setCurrentIndex(page.format_filter.findData("9:16"))
    page.select_all_btn.click()                     # only the visible (filtered) stories
    assert page.selected_count.text() == "3 selected"
    asked = []
    monkeypatch.setattr(dashboard.QMessageBox, "question",
                        lambda parent, title, text, *a, **k: asked.append(text) or dashboard.QMessageBox.Yes)
    page.delete_selected_btn.click()
    assert "3 stories" in asked[0]
    qtbot.waitUntil(lambda: page.stories.count() == 2, timeout=3000)
    page.format_filter.setCurrentIndex(page.format_filter.findData(""))
    assert sorted(visible(page)) == ["Apple wide", "Date wide"]


def test_delete_selected_skips_rendering(qtbot, page, Session, monkeypatch):
    from desktop.ui import dashboard
    page.select_btn.click()
    page.select_all_btn.click()
    monkeypatch.setattr(dashboard.QMessageBox, "question", lambda *a, **k: dashboard.QMessageBox.Yes)
    page.delete_selected_btn.click()
    qtbot.waitUntil(lambda: page.stories.count() == 1, timeout=3000)
    assert visible(page) == ["Date wide"]
    assert "rendering" in page.error.text().lower()


def test_cancel_select_mode_clears_selection(page):
    page.select_btn.click()
    page.select_all_btn.click()
    page.select_btn.click()
    assert not page.select_mode and page.bulk_bar.isHidden() and page.stories.selectedItems() == []
