"""Dark Blue theme: deep navy, gradient panels with glowing blue frames, blue/purple gradient actions."""
from PySide6.QtGui import QColor
from PySide6.QtWidgets import QGraphicsDropShadowEffect

BG = "#060b1d"          # window background
PANEL_TOP = "#0e1a3d"   # panel gradient
PANEL_BOTTOM = "#0a1230"
FIELD = "#0b1430"       # inputs
LINE = "#1c3577"        # borders
GLOW = "#3b82f6"        # frame glow
ACCENT = "#3b82f6"
ACCENT_2 = "#2563eb"
AI = "#7c3aed"
AI_2 = "#a855f7"
TEXT = "#e6edff"
MUTED = "#8a9bc7"

ACCENT_TEXT = "#60a5fa"
STATUS_COLORS = {"pending": "#334155", "running": "#f59e0b", "done": "#10b981", "failed": "#ef4444",
                 "draft": "#475569", "queued": "#8b5cf6", "rendering": "#2563eb", "review": "#d97706"}
# story list badges: (label, background, text colour)
BADGES = {"done": ("Done", "#0f3d2e", "#34d399"), "rendering": ("Rendering", "#102a5c", "#60a5fa"),
          "queued": ("Queued", "#2a1d5c", "#a78bfa"), "failed": ("Failed", "#4a1420", "#f87171"),
          "draft": ("Draft", "#1e293b", "#94a3b8"), "review": ("Review images", "#3d2a0a", "#fbbf24")}

QSS = f"""
* {{ font-family: "Helvetica Neue", Arial; font-size: 13px; color: {TEXT}; }}
QMainWindow, QDialog, QMessageBox, QWidget#page, QWidget#root, QScrollArea, QScrollArea > QWidget > QWidget {{ background: {BG}; }}
QToolTip {{ background: {PANEL_TOP}; color: {TEXT}; border: 1px solid {LINE}; padding: 4px; }}

/* sidebar */
QWidget#sidebar {{ background: qlineargradient(x1:0,y1:0,x2:0,y2:1, stop:0 #0b1533, stop:1 #070e24);
    border: 1px solid {LINE}; border-radius: 18px; }}
QLabel#brand {{ font-size: 20px; font-weight: 700; }}
QPushButton#nav {{ text-align: left; padding: 10px 14px; border: none; border-radius: 10px; background: transparent;
    color: #c7d2f0; font-size: 13px; }}
QPushButton#nav:hover {{ background: rgba(59,130,246,0.10); }}
QPushButton#nav:checked {{ background: qlineargradient(x1:0,y1:0,x2:1,y2:0, stop:0 {ACCENT_2}, stop:1 #1d4ed8);
    color: white; font-weight: 600; }}

/* panels */
QFrame#card, QFrame#panel {{ background: qlineargradient(x1:0,y1:0,x2:0,y2:1, stop:0 {PANEL_TOP}, stop:1 {PANEL_BOTTOM});
    border: 1px solid {LINE}; border-radius: 16px; }}
QFrame#panel QLabel, QFrame#card QLabel, QWidget#formBody, QScrollArea#formScroll,
QScrollArea#formScroll > QWidget {{ background: transparent; }}
QFrame#banner {{ background: qlineargradient(x1:0,y1:0,x2:1,y2:1, stop:0 #1e3a8a, stop:0.55 #1d2f73, stop:1 #3b1d7a);
    border: none; border-top-left-radius: 16px; border-top-right-radius: 16px; }}
QFrame#storycard {{ background: rgba(13,26,61,0.85); border: 1px solid #1a2d63; border-radius: 12px; }}
QFrame#storycard[selected="true"] {{ background: qlineargradient(x1:0,y1:0,x2:1,y2:0, stop:0 #13306f, stop:1 #0f2156);
    border: 1px solid {ACCENT}; }}

/* type */
QLabel#h1 {{ font-size: 22px; font-weight: 700; }}
QLabel#h2 {{ font-size: 15px; font-weight: 600; color: {ACCENT_TEXT}; }}
QLabel#panelTitle {{ font-size: 17px; font-weight: 700; }}
QLabel#bannerTitle {{ font-size: 20px; font-weight: 700; color: white; }}
QLabel#bannerSub {{ color: #c7d2fe; }}
QLabel#fieldLabel {{ font-weight: 600; color: #dbe4ff; }}
QLabel#muted, QLabel#counter {{ color: {MUTED}; }}
QLabel#cardTitle {{ font-size: 14px; font-weight: 600; }}
QLabel#cardMeta {{ color: {MUTED}; font-size: 12px; }}
QLabel#error {{ color: #f87171; }}

/* inputs */
QLineEdit, QPlainTextEdit, QComboBox, QSpinBox, QTimeEdit, QDateTimeEdit {{ background: {FIELD};
    border: 1px solid {LINE}; border-radius: 10px; padding: 7px 10px; selection-background-color: {ACCENT_2}; }}
QLineEdit:focus, QPlainTextEdit:focus, QComboBox:focus, QTimeEdit:focus, QDateTimeEdit:focus {{ border-color: {ACCENT}; }}
QLineEdit#search {{ border-radius: 12px; padding-left: 10px; }}
QComboBox::drop-down {{ border: none; width: 26px; }}
QComboBox QAbstractItemView {{ background: {PANEL_TOP}; border: 1px solid {LINE}; selection-background-color: {ACCENT_2}; }}

/* buttons */
QPushButton {{ background: #13214a; border: 1px solid {LINE}; border-radius: 10px; padding: 7px 14px; }}
QPushButton:hover {{ border-color: {ACCENT}; }}
QPushButton:disabled {{ color: #5b6b94; border-color: #16275a; }}
QPushButton#primary {{ background: qlineargradient(x1:0,y1:0,x2:1,y2:0, stop:0 {ACCENT}, stop:1 {ACCENT_2});
    color: white; font-weight: 600; border: none; padding: 9px 18px; }}
QPushButton#primary:hover {{ background: qlineargradient(x1:0,y1:0,x2:1,y2:0, stop:0 #60a5fa, stop:1 {ACCENT}); }}
QPushButton#primary:disabled {{ background: #1e3a6e; color: #8aa0cf; }}
QPushButton#ai {{ background: qlineargradient(x1:0,y1:0,x2:1,y2:0, stop:0 {AI}, stop:1 {AI_2});
    color: white; font-weight: 600; border: none; padding: 9px 18px; }}
QPushButton#ai:hover {{ background: qlineargradient(x1:0,y1:0,x2:1,y2:0, stop:0 #8b5cf6, stop:1 #c084fc); }}
QPushButton#ai:disabled {{ background: #3b2a6e; color: #b3a6d9; }}
QPushButton#danger {{ background: #b91c1c; color: white; font-weight: 600; border: none; padding: 7px 14px; }}
QPushButton#danger:hover {{ background: #dc2626; }}
QPushButton#danger:disabled {{ background: #3a1a1f; color: #a37b80; }}
QPushButton#pill {{ background: {FIELD}; border: 1px solid {LINE}; border-radius: 10px; padding: 7px 12px; }}
QPushButton#pill:checked {{ background: rgba(59,130,246,0.18); border: 1px solid {ACCENT}; color: white; font-weight: 600; }}

QToolButton#dots {{ border: none; border-radius: 8px; padding: 4px; background: transparent; }}
QToolButton#dots:hover {{ background: rgba(59,130,246,0.15); }}
QToolButton#dots::menu-indicator {{ image: none; width: 0; }}
QMenu {{ background: {PANEL_TOP}; border: 1px solid {LINE}; border-radius: 8px; padding: 4px; }}
QMenu::item {{ padding: 7px 18px; border-radius: 6px; }}
QMenu::item:selected {{ background: {ACCENT_2}; }}
QMenu::separator {{ height: 1px; background: {LINE}; margin: 4px 8px; }}

/* lists / tables */
QListWidget {{ background: transparent; border: none; outline: none; }}
QListWidget::item {{ border: none; padding: 0; margin: 0; }}
QListWidget::item:selected {{ background: transparent; }}
QTableWidget {{ background: {FIELD}; alternate-background-color: #0d1838; border: 1px solid {LINE};
    border-radius: 12px; gridline-color: #16275a; selection-background-color: #173a80; }}
QHeaderView::section {{ background: {PANEL_TOP}; color: {MUTED}; border: none; border-bottom: 1px solid {LINE}; padding: 7px; }}
QTableCornerButton::section {{ background: {PANEL_TOP}; border: none; }}
QGroupBox {{ border: 1px solid {LINE}; border-radius: 12px; margin-top: 10px; padding-top: 8px; }}
QGroupBox::title {{ subcontrol-origin: margin; left: 12px; color: {ACCENT_TEXT}; font-weight: 600; }}
QGroupBox::indicator, QCheckBox::indicator {{ width: 16px; height: 16px; border-radius: 5px;
    border: 1px solid {LINE}; background: {FIELD}; }}
QGroupBox::indicator:checked, QCheckBox::indicator:checked {{ background: {ACCENT}; border-color: {ACCENT}; }}
QRadioButton::indicator {{ width: 14px; height: 14px; border-radius: 8px; border: 1px solid {LINE}; background: {FIELD}; }}
QRadioButton::indicator:checked {{ background: qradialgradient(cx:0.5,cy:0.5,radius:0.5,fx:0.5,fy:0.5,
    stop:0 white, stop:0.35 white, stop:0.45 {ACCENT}, stop:1 {ACCENT}); border-color: {ACCENT}; }}
QProgressBar {{ background: #13214a; border: none; border-radius: 4px; height: 8px; }}
QProgressBar::chunk {{ background: qlineargradient(x1:0,y1:0,x2:1,y2:0, stop:0 {ACCENT}, stop:1 {AI_2}); border-radius: 4px; }}
QScrollBar:vertical {{ background: transparent; width: 10px; margin: 2px; }}
QScrollBar::handle:vertical {{ background: #22397a; border-radius: 4px; min-height: 30px; }}
QScrollBar::add-line:vertical, QScrollBar::sub-line:vertical {{ height: 0; }}
QScrollBar:horizontal {{ background: transparent; height: 10px; margin: 2px; }}
QScrollBar::handle:horizontal {{ background: #22397a; border-radius: 4px; min-width: 30px; }}
QScrollBar::add-line:horizontal, QScrollBar::sub-line:horizontal {{ width: 0; }}
QStatusBar {{ background: {BG}; color: {MUTED}; }}
"""


def glow(widget, color=GLOW, radius=36, alpha=140):
    """Soft blue halo around a panel (QSS has no box-shadow)."""
    effect = QGraphicsDropShadowEffect(widget)
    c = QColor(color)
    c.setAlpha(alpha)
    effect.setColor(c)
    effect.setBlurRadius(radius)
    effect.setOffset(0, 0)
    widget.setGraphicsEffect(effect)
    return effect


def chip_style(status: str) -> str:
    return (f"background:{STATUS_COLORS.get(status, '#334155')}; color:white; border-radius:9px;"
            "padding:2px 8px; font-size:11px; font-weight:600;")


def badge_style(status: str) -> tuple[str, str]:
    label, bg, fg = BADGES.get(status, (status.title(), "#1e293b", "#94a3b8"))
    return label, f"background:{bg}; color:{fg}; border-radius:8px; padding:2px 8px; font-size:11px; font-weight:600;"
