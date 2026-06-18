import os
from typing import Callable

from PyQt6.QtGui import QColor, QIcon, QPainter, QPixmap
from PyQt6.QtWidgets import QMenu, QSystemTrayIcon

from ui import theme

_LOGO_PATH = os.path.join(os.path.dirname(os.path.dirname(__file__)), "icon.ico")


def _make_icon(warning: bool = False) -> QIcon:
    if not warning and os.path.exists(_LOGO_PATH):
        return QIcon(_LOGO_PATH)
    # Fallback envelope icon
    color = "#E24B4A" if warning else theme.ACCENT
    px = QPixmap(32, 32)
    px.fill(QColor("transparent"))
    p = QPainter(px)
    p.setRenderHint(QPainter.RenderHint.Antialiasing)
    p.setPen(QColor(color))
    p.setBrush(QColor(color))
    p.drawRoundedRect(2, 8, 28, 18, 3, 3)
    p.setPen(QColor("#1E1E2E"))
    p.drawLine(2, 8, 16, 20)
    p.drawLine(30, 8, 16, 20)
    p.end()
    return QIcon(px)


class TrayIcon(QSystemTrayIcon):
    def __init__(
        self,
        on_open: Callable,
        on_settings: Callable,
        on_reload: Callable,
        on_about: Callable,
        on_quit: Callable,
        parent=None,
    ):
        super().__init__(parent)
        self._on_open = on_open
        self._on_settings = on_settings
        self._on_reload = on_reload
        self._on_about = on_about
        self._on_quit = on_quit
        self.setIcon(_make_icon())
        self.setToolTip("Envelop — Actif")
        self._build_menu()
        self.activated.connect(self._on_activated)
        self.setVisible(True)

    def _on_activated(self, reason):
        if reason == QSystemTrayIcon.ActivationReason.DoubleClick:
            self._on_open()

    def _build_menu(self):
        menu = QMenu()
        menu.setStyleSheet("""
            QMenu {
                background-color: #1E1E2E;
                color: #CDD6F4;
                border: 1px solid #313244;
                font-family: Segoe UI;
                font-size: 13px;
            }
            QMenu::item { padding: 6px 20px; }
            QMenu::item:selected { background-color: #313244; }
            QMenu::separator { height: 1px; background: #313244; margin: 4px 0; }
        """)
        menu.addAction("Ouvrir Envelop", self._on_open)
        menu.addSeparator()
        menu.addAction("Paramètres", self._on_settings)
        menu.addAction("Recharger les modèles", self._on_reload)
        menu.addSeparator()
        menu.addAction("À propos", self._on_about)
        menu.addSeparator()
        menu.addAction("Quitter", self._on_quit)
        self.setContextMenu(menu)

    def set_warning(self, warning: bool):
        self.setIcon(_make_icon(warning))
        self.setToolTip("Envelop — Fichier indisponible" if warning else "Envelop — Actif")
