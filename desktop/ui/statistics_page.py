from PySide6.QtCore import Qt
from PySide6.QtWidgets import (QAbstractItemView, QFrame, QGridLayout, QHeaderView, QLabel, QTableWidget,
                               QTableWidgetItem, QVBoxLayout, QWidget)

from desktop.core import db
from desktop.services import stats

TILES = [("stories", "Stories"), ("done", "Rendered"), ("failed", "Failed"), ("uploaded", "On YouTube"),
         ("channels", "Channels"), ("minutes", "Minutes of video")]


class StatisticsPage(QWidget):
    def __init__(self):
        super().__init__(objectName="page")
        grid = QGridLayout()
        self.tiles = {}
        for i, (key, label) in enumerate(TILES):
            card = QFrame(objectName="card")
            box = QVBoxLayout(card)
            value = QLabel("0", objectName="h1")
            box.addWidget(value)
            box.addWidget(QLabel(label, objectName="muted"))
            self.tiles[key] = value
            grid.addWidget(card, 0, i)
        self.table = QTableWidget(0, 4)
        self.table.setHorizontalHeaderLabels(["Date", "Created", "Rendered", "Uploaded"])
        self.table.horizontalHeader().setSectionResizeMode(QHeaderView.Stretch)
        self.table.setEditTriggers(QAbstractItemView.NoEditTriggers)
        self.table.verticalHeader().hide()
        root = QVBoxLayout(self)
        root.setContentsMargins(24, 20, 24, 20)
        root.addWidget(QLabel("Statistics", objectName="h1"))
        root.addLayout(grid)
        root.addWidget(QLabel("Last 30 days", objectName="h2"))
        root.addWidget(self.table, 1)

    def refresh(self):
        for key, value in stats.summary(db.Session).items():
            if key in self.tiles:
                self.tiles[key].setText(str(value))
        rows = stats.daily(db.Session, 30)
        self.table.setRowCount(len(rows))
        for r, row in enumerate(rows):
            for c, v in enumerate([row["date"].strftime("%a %b %d"), row["created"], row["rendered"], row["uploaded"]]):
                item = QTableWidgetItem(str(v))
                if c:
                    item.setTextAlignment(Qt.AlignCenter)
                self.table.setItem(r, c, item)
