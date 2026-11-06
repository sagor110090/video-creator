"""Small line icons drawn as SVG (24x24 grid, stroke-based) and turned into QIcons."""
from functools import lru_cache

from PySide6.QtCore import QByteArray, QRectF, Qt
from PySide6.QtGui import QIcon, QPainter, QPixmap
from PySide6.QtSvg import QSvgRenderer

PATHS = {
    "dashboard": '<rect x="3" y="3" width="7" height="9" rx="1.5"/><rect x="14" y="3" width="7" height="5" rx="1.5"/>'
                 '<rect x="14" y="12" width="7" height="9" rx="1.5"/><rect x="3" y="16" width="7" height="5" rx="1.5"/>',
    "calendar": '<rect x="3" y="5" width="18" height="16" rx="2"/><path d="M3 10h18M8 3v4M16 3v4"/>',
    "youtube": '<rect x="2.5" y="5" width="19" height="14" rx="4"/><path d="M10 9.2v5.6l5-2.8z" fill="currentColor"/>',
    "chart": '<path d="M4 20V10M10 20V4M16 20v-7M22 20H2"/>',
    "settings": '<circle cx="12" cy="12" r="3"/><path d="M12 2.5v2.2M12 19.3v2.2M4.6 4.6l1.6 1.6M17.8 17.8l1.6 1.6'
                'M2.5 12h2.2M19.3 12h2.2M4.6 19.4l1.6-1.6M17.8 6.2l1.6-1.6"/><circle cx="12" cy="12" r="7"/>',
    "book": '<path d="M2 5.5C4.5 4 7.5 4 12 6c4.5-2 7.5-2 10-.5V19c-2.5-1.5-5.5-1.5-10 .5C7.5 17.5 4.5 17.5 2 19z"/>'
            '<path d="M12 6v13.5"/>',
    "search": '<circle cx="11" cy="11" r="7"/><path d="M20 20l-4-4"/>',
    "wand": '<path d="M4 20L16 8M14 6l4 4"/><path d="M19 2v3M17.5 3.5h3M6 3v2M5 4h2M20 13v2M19 14h2"/>',
    "sparkles": '<path d="M12 3l1.8 4.7L18.5 9.5l-4.7 1.8L12 16l-1.8-4.7L5.5 9.5l4.7-1.8z"/>'
                '<path d="M19 15l.8 2.2L22 18l-2.2.8L19 21l-.8-2.2L16 18l2.2-.8z"/>',
    "tag": '<path d="M3 12V4a1 1 0 011-1h8l9 9-9 9z"/><circle cx="7.5" cy="7.5" r="1.5"/>',
    "mic": '<rect x="9" y="3" width="6" height="11" rx="3"/><path d="M5 11a7 7 0 0014 0M12 18v3"/>',
    "palette": '<path d="M12 3a9 9 0 100 18c1.2 0 1.8-.9 1.4-2-.5-1.3.3-2.5 1.7-2.5H18a3 3 0 003-3c0-5.5-4-10.5-9-10.5z"/>'
               '<circle cx="7.5" cy="11" r="1"/><circle cx="10" cy="7" r="1"/><circle cx="15" cy="7" r="1"/>',
    "pencil": '<path d="M4 20h4L19 9l-4-4L4 16z"/><path d="M13.5 6.5l4 4"/>',
    "lines": '<path d="M4 6h16M4 10h16M4 14h10M4 18h7"/>',
    "monitor": '<rect x="3" y="5" width="18" height="12" rx="2"/><path d="M9 21h6"/>',
    "phone": '<rect x="7" y="2.5" width="10" height="19" rx="2"/><path d="M11 18.5h2"/>',
    "info": '<circle cx="12" cy="12" r="9"/><path d="M12 11v5M12 7.5v.5"/>',
    "check": '<circle cx="12" cy="12" r="10" fill="currentColor" stroke="none"/>'
             '<path d="M7.5 12.5l3 3 6-6.5" stroke="#ffffff"/>',
    "dots": '<circle cx="12" cy="5" r="1.4" fill="currentColor"/><circle cx="12" cy="12" r="1.4" fill="currentColor"/>'
            '<circle cx="12" cy="19" r="1.4" fill="currentColor"/>',
    "arrow": '<path d="M5 12h14M13 6l6 6-6 6"/>',
    "eye": '<path d="M2 12s3.6-7 10-7 10 7 10 7-3.6 7-10 7S2 12 2 12z"/><circle cx="12" cy="12" r="3"/>',
    "image": '<rect x="3" y="4" width="18" height="16" rx="2"/><circle cx="8.5" cy="9.5" r="1.8"/><path d="M21 16l-5-5-9 9"/>',
    "key": '<circle cx="8" cy="15" r="4"/><path d="M11 12l9-9M17 6l3 3M15 8l2 2"/>',
    "plus": '<path d="M12 5v14M5 12h14"/>',
    "trash": '<path d="M4 7h16M9 7V4h6v3M6 7l1 13h10l1-13"/>',
    "refresh": '<path d="M20 11a8 8 0 10-2.3 5.7M20 4v7h-7"/>',
    "save": '<path d="M5 3h11l3 3v15H5z"/><path d="M8 3v6h8V3M8 21v-7h8v7"/>',
    "play": '<path d="M7 4.5v15l12-7.5z" fill="currentColor"/>',
    "film": '<rect x="3" y="4" width="18" height="16" rx="2"/><path d="M7 4v16M17 4v16M3 9h4M3 15h4M17 9h4M17 15h4"/>',
}


def svg(name: str, color: str = "#e6edff", stroke: float = 1.8) -> str:
    body = PATHS[name].replace("currentColor", color)
    return (f'<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 24 24" fill="none" stroke="{color}" '
            f'stroke-width="{stroke}" stroke-linecap="round" stroke-linejoin="round">{body}</svg>')


@lru_cache(maxsize=256)
def pixmap(name: str, color: str = "#e6edff", size: int = 18, stroke: float = 1.8) -> QPixmap:
    ratio = 2  # render at 2x for Retina
    pm = QPixmap(size * ratio, size * ratio)
    pm.fill(Qt.transparent)
    renderer = QSvgRenderer(QByteArray(svg(name, color, stroke).encode()))
    p = QPainter(pm)
    renderer.render(p, QRectF(0, 0, size * ratio, size * ratio))
    p.end()
    pm.setDevicePixelRatio(ratio)
    return pm


def icon(name: str, color: str = "#e6edff", size: int = 18) -> QIcon:
    ic = QIcon(pixmap(name, color, size))
    return ic
