"""Dark theme with the cyan accent of the old web UI."""

ACCENT = "#22d3ee"
STATUS_COLORS = {"pending": "#4b5563", "running": "#f59e0b", "done": "#10b981", "failed": "#ef4444",
                 "draft": "#4b5563", "queued": "#8b5cf6", "rendering": "#f59e0b"}

QSS = f"""
* {{ font-family: "SF Pro Text", "Helvetica Neue", Arial; font-size: 13px; color: #e5e7eb; }}
QMainWindow, QWidget#page, QScrollArea, QScrollArea > QWidget > QWidget {{ background: #0b0f17; }}
QWidget#sidebar {{ background: #070a10; border-right: 1px solid #1f2937; }}
QPushButton#nav {{ text-align: left; padding: 10px 16px; border: none; border-radius: 8px; background: transparent; }}
QPushButton#nav:checked {{ background: #0e2a33; color: {ACCENT}; }}
QPushButton#nav:disabled {{ color: #4b5563; }}
QLabel#h1 {{ font-size: 22px; font-weight: 600; }}
QLabel#h2 {{ font-size: 15px; font-weight: 600; color: {ACCENT}; }}
QLabel#muted {{ color: #9ca3af; }}
QLabel#error {{ color: #f87171; }}
QFrame#card {{ background: #111827; border: 1px solid #1f2937; border-radius: 10px; }}
QPushButton {{ background: #1f2937; border: 1px solid #374151; border-radius: 6px; padding: 6px 12px; }}
QPushButton:hover {{ border-color: {ACCENT}; }}
QPushButton:disabled {{ color: #6b7280; border-color: #1f2937; }}
QPushButton#primary {{ background: {ACCENT}; color: #031014; font-weight: 600; border: none; }}
QPushButton#primary:disabled {{ background: #164e63; color: #6b7280; }}
QLineEdit, QPlainTextEdit, QComboBox, QSpinBox {{ background: #0b1220; border: 1px solid #374151;
    border-radius: 6px; padding: 5px; selection-background-color: #0e7490; }}
QLineEdit:focus, QPlainTextEdit:focus, QComboBox:focus {{ border-color: {ACCENT}; }}
QListWidget {{ background: #0b1220; border: 1px solid #1f2937; border-radius: 8px; }}
QListWidget::item {{ padding: 8px; border-bottom: 1px solid #111827; }}
QListWidget::item:selected {{ background: #0e2a33; }}
QProgressBar {{ background: #1f2937; border: none; border-radius: 4px; height: 8px; text-align: center; }}
QProgressBar::chunk {{ background: {ACCENT}; border-radius: 4px; }}
QStatusBar {{ background: #070a10; color: #9ca3af; }}
"""


def chip_style(status: str) -> str:
    return (f"background:{STATUS_COLORS.get(status, '#4b5563')}; color:white; border-radius:9px;"
            "padding:2px 8px; font-size:11px; font-weight:600;")
