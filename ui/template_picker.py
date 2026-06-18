import ctypes
import ctypes.wintypes
import logging
from typing import Callable, List

from PyQt6.QtCore import Qt
from PyQt6.QtGui import QColor, QCursor
from PyQt6.QtWidgets import (
    QApplication, QGraphicsDropShadowEffect, QLabel,
    QScrollArea, QVBoxLayout, QWidget,
)

from template_loader import Template

log = logging.getLogger("fcf")

PICKER_WIDTH  = 420
PICKER_HEIGHT = 380   # fixed — never shrinks

STYLE = """
QWidget#picker_outer { background: transparent; }

QWidget#picker {
    background: #FFFFFF;
    border: 2px solid #93C5FD;
    border-radius: 12px;
}
QLabel#search {
    background: #EFF6FF;
    color: #1D4ED8;
    font-size: 13px;
    font-weight: bold;
    font-family: "Segoe UI";
    padding: 10px 14px;
    border-bottom: 1px solid #BFDBFE;
    border-top-left-radius: 10px;
    border-top-right-radius: 10px;
}
QLabel#category {
    color: #94A3B8;
    font-size: 10px;
    font-weight: bold;
    font-family: "Segoe UI";
    letter-spacing: 1px;
    padding: 8px 14px 3px 14px;
    background: transparent;
}
QLabel#template_row {
    color: #1E293B;
    font-size: 13px;
    font-family: "Segoe UI";
    padding: 8px 14px 8px 26px;
    background: transparent;
}
QLabel#empty_msg {
    color: #94A3B8;
    font-size: 13px;
    font-family: "Segoe UI";
    padding: 20px 14px;
    background: transparent;
}
QScrollArea { border: none; background: transparent; }
QWidget#scroll_content { background: #FFFFFF; }
QScrollBar:vertical { width: 4px; background: transparent; }
QScrollBar::handle:vertical { background: #CBD5E1; border-radius: 2px; min-height: 20px; }
QScrollBar::add-line:vertical, QScrollBar::sub-line:vertical { height: 0; }
"""


class _GuiThreadInfo(ctypes.Structure):
    _fields_ = [
        ("cbSize",       ctypes.wintypes.DWORD),
        ("flags",        ctypes.wintypes.DWORD),
        ("hwndActive",   ctypes.wintypes.HWND),
        ("hwndFocus",    ctypes.wintypes.HWND),
        ("hwndCapture",  ctypes.wintypes.HWND),
        ("hwndMenuOwner",ctypes.wintypes.HWND),
        ("hwndMoveSize", ctypes.wintypes.HWND),
        ("hwndCaret",    ctypes.wintypes.HWND),
        ("rcCaret",      ctypes.wintypes.RECT),
    ]


def _caret_screen_pos():
    """Return (x, y) of the text caret in the foreground window, or None."""
    try:
        hwnd = ctypes.windll.user32.GetForegroundWindow()
        tid  = ctypes.windll.user32.GetWindowThreadProcessId(hwnd, None)
        gti  = _GuiThreadInfo()
        gti.cbSize = ctypes.sizeof(_GuiThreadInfo)
        if ctypes.windll.user32.GetGUIThreadInfo(tid, ctypes.byref(gti)) and gti.hwndCaret:
            pt = ctypes.wintypes.POINT(gti.rcCaret.left, gti.rcCaret.bottom)
            ctypes.windll.user32.ClientToScreen(gti.hwndCaret, ctypes.byref(pt))
            return pt.x, pt.y
    except Exception:
        pass
    return None


class TemplateRow(QLabel):
    def __init__(self, template: Template, on_select: Callable, parent=None):
        super().__init__(f"  {template.nom}", parent)
        self.setObjectName("template_row")
        self._template = template
        self._on_select = on_select
        self.setCursor(Qt.CursorShape.PointingHandCursor)
        self.setFixedHeight(36)
        self._selected = False

    def set_selected(self, sel: bool):
        self._selected = sel
        self._refresh()

    def _refresh(self):
        if self._selected:
            self.setStyleSheet(
                "background:#EFF6FF; color:#2563EB; "
                "padding:8px 14px 8px 26px; border-radius:6px; margin:0 6px;"
            )
        else:
            self.setStyleSheet("")

    def mousePressEvent(self, _):
        self._on_select(self._template)

    def enterEvent(self, _):
        if not self._selected:
            self.setStyleSheet(
                "background:#F1F5F9; color:#1E293B; "
                "padding:8px 14px 8px 26px; border-radius:6px; margin:0 6px;"
            )

    def leaveEvent(self, _):
        if not self._selected:
            self.setStyleSheet("")


class TemplatePicker(QWidget):
    def __init__(self, on_select: Callable[[Template], None], on_close: Callable, parent=None):
        super().__init__(
            parent,
            Qt.WindowType.Tool
            | Qt.WindowType.FramelessWindowHint
            | Qt.WindowType.WindowStaysOnTopHint,
        )
        self.setAttribute(Qt.WidgetAttribute.WA_ShowWithoutActivating, True)
        self.setAttribute(Qt.WidgetAttribute.WA_TranslucentBackground, True)
        self.setObjectName("picker_outer")
        self.setStyleSheet(STYLE)
        # Fixed total size (outer includes shadow padding)
        self.setFixedSize(PICKER_WIDTH + 24, PICKER_HEIGHT + 24)
        self._on_select = on_select
        self._on_close = on_close
        self._rows: List[TemplateRow] = []
        self._selected_idx = -1
        self._build_ui()

    def _build_ui(self):
        outer = QVBoxLayout(self)
        outer.setContentsMargins(12, 12, 12, 12)

        self._inner = QWidget()
        self._inner.setObjectName("picker")
        self._inner.setFixedSize(PICKER_WIDTH, PICKER_HEIGHT)

        shadow = QGraphicsDropShadowEffect(self._inner)
        shadow.setBlurRadius(28)
        shadow.setOffset(0, 6)
        shadow.setColor(QColor(0, 0, 0, 55))
        self._inner.setGraphicsEffect(shadow)

        inner_layout = QVBoxLayout(self._inner)
        inner_layout.setContentsMargins(0, 0, 0, 0)
        inner_layout.setSpacing(0)

        self._search_label = QLabel("🔍")
        self._search_label.setObjectName("search")
        self._search_label.setFixedHeight(42)
        inner_layout.addWidget(self._search_label)

        self._scroll = QScrollArea()
        self._scroll.setWidgetResizable(True)
        self._scroll.setHorizontalScrollBarPolicy(Qt.ScrollBarPolicy.ScrollBarAlwaysOff)

        self._content = QWidget()
        self._content.setObjectName("scroll_content")
        self._content_layout = QVBoxLayout(self._content)
        self._content_layout.setContentsMargins(0, 4, 0, 8)
        self._content_layout.setSpacing(0)
        self._scroll.setWidget(self._content)
        inner_layout.addWidget(self._scroll, 1)

        outer.addWidget(self._inner)

    def update_results(self, buffer: str, templates: List[Template]):
        self._search_label.setText(f"🔍   {buffer}")
        self._rows.clear()
        self._selected_idx = -1

        # Clear previous items
        while self._content_layout.count():
            item = self._content_layout.takeAt(0)
            if item.widget():
                item.widget().deleteLater()

        if not templates:
            msg = QLabel("  Aucun modèle trouvé")
            msg.setObjectName("empty_msg")
            self._content_layout.addWidget(msg)
        else:
            groups: dict[str, List[Template]] = {}
            for t in templates:
                groups.setdefault(t.categorie, []).append(t)
            for cat in sorted(groups.keys()):
                lbl = QLabel(cat.upper())
                lbl.setObjectName("category")
                self._content_layout.addWidget(lbl)
                for tmpl in sorted(groups[cat], key=lambda x: x.nom):
                    row = TemplateRow(tmpl, self._select, self._content)
                    self._content_layout.addWidget(row)
                    self._rows.append(row)

        self._content_layout.addStretch()
        self._reposition()
        self.show()
        self.raise_()

    def _select(self, template: Template):
        self._on_select(template)
        self.hide()

    def _reposition(self):
        """Position just below the text cursor; fall back to bottom-center of active screen."""
        caret = _caret_screen_pos()

        # Determine which screen to use
        cursor_pos = QCursor.pos()
        screen = QApplication.screenAt(cursor_pos) or QApplication.primaryScreen()
        geom = screen.availableGeometry()

        w = self.width()
        h = self.height()

        if caret:
            x, y = caret
            # Offset down slightly so the menu appears below the typed character
            y += 6
            # Clamp to screen bounds
            if x + w > geom.right():
                x = geom.right() - w
            if x < geom.left():
                x = geom.left()
            if y + h > geom.bottom():
                y = caret[1] - h - 6   # flip above caret if no space below
        else:
            # Fallback: bottom-center of the active screen
            x = geom.x() + (geom.width() - w) // 2
            y = geom.bottom() - h - 80

        self.move(x, y)

    def navigate(self, direction: int):
        if not self._rows:
            return
        if self._selected_idx >= 0:
            self._rows[self._selected_idx].set_selected(False)
        self._selected_idx = (self._selected_idx + direction) % len(self._rows)
        self._rows[self._selected_idx].set_selected(True)

    def select_current(self):
        if 0 <= self._selected_idx < len(self._rows):
            self._select(self._rows[self._selected_idx]._template)
