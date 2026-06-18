import os
import sys
from PyQt6.QtCore import Qt
from PyQt6.QtWidgets import (
    QCheckBox, QDialog, QFileDialog, QFormLayout,
    QHBoxLayout, QLabel, QLineEdit, QPushButton,
    QVBoxLayout, QWidget,
)

import config as cfg
from ui import theme


STYLE = f"""
QDialog, QWidget {{
    background-color: {theme.WHITE};
    color: {theme.TEXT_PRIMARY};
    font-family: {theme.FONT_FAMILY};
    font-size: 13px;
}}
QLineEdit {{
    background-color: {theme.BG_SUBTLE};
    color: {theme.TEXT_PRIMARY};
    border: 1px solid {theme.BORDER};
    border-radius: 6px;
    padding: 6px 10px;
}}
QLineEdit:focus {{ border-color: {theme.ACCENT}; }}
QPushButton {{
    background-color: {theme.BG_SUBTLE};
    color: {theme.TEXT_SECONDARY};
    border: 1px solid {theme.BORDER};
    border-radius: 6px;
    padding: 6px 14px;
}}
QPushButton:hover {{ background-color: {theme.BORDER}; }}
QPushButton#primary {{
    background-color: {theme.ACCENT};
    color: {theme.WHITE};
    border: none;
    font-weight: 600;
}}
QPushButton#primary:hover {{ background-color: {theme.ACCENT_HOVER}; }}
QCheckBox {{ spacing: 8px; }}
QCheckBox::indicator {{
    width: 16px; height: 16px;
    border: 1px solid {theme.BORDER};
    border-radius: 3px;
    background: {theme.BG_SUBTLE};
}}
QCheckBox::indicator:checked {{ background: {theme.ACCENT}; }}
"""


class FirstRunDialog(QDialog):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setWindowTitle("Envelop — Configuration")
        self.setFixedWidth(460)
        self.setStyleSheet(STYLE)
        self.setWindowFlags(self.windowFlags() | Qt.WindowType.WindowStaysOnTopHint)
        self._path = ""
        self._build_ui()

    def _build_ui(self):
        layout = QVBoxLayout(self)
        layout.setContentsMargins(24, 24, 24, 24)
        layout.setSpacing(16)

        title = QLabel("Bienvenue dans Envelop")
        title.setStyleSheet(f"font-size: 16px; font-weight: 600; color: {theme.ACCENT_TEXT};")
        layout.addWidget(title)

        layout.addWidget(QLabel("Choisissez le fichier de modèles (.xlsx) :"))

        row = QHBoxLayout()
        self._path_label = QLabel("Aucun fichier sélectionné")
        self._path_label.setStyleSheet(f"color: {theme.TEXT_MUTED}; font-size: 12px;")
        self._path_label.setWordWrap(True)
        row.addWidget(self._path_label, 1)
        btn_browse = QPushButton("Parcourir…")
        btn_browse.clicked.connect(self._browse)
        row.addWidget(btn_browse)
        layout.addLayout(row)

        btn_confirm = QPushButton("Confirmer")
        btn_confirm.setObjectName("primary")
        btn_confirm.clicked.connect(self._confirm)
        layout.addWidget(btn_confirm)

    def _browse(self):
        path, _ = QFileDialog.getOpenFileName(
            self, "Sélectionner le fichier de modèles", "", "Fichiers Excel (*.xlsx)"
        )
        if path:
            self._path = path
            self._path_label.setText(path)
            self._path_label.setStyleSheet(f"color: {theme.TEXT_PRIMARY}; font-size: 12px;")

    def _confirm(self):
        if not self._path:
            self._path_label.setText("Veuillez sélectionner un fichier.")
            self._path_label.setStyleSheet("color: #A32D2D; font-size: 12px;")
            return
        c = cfg.load_config()
        c["xlsx_path"] = self._path
        cfg.save_config(c)
        self.accept()


class SettingsWindow(QDialog):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setWindowTitle("Paramètres — Envelop")
        self.setFixedWidth(480)
        self.setStyleSheet(STYLE)
        self._config = cfg.load_config()
        self._build_ui()

    def _build_ui(self):
        layout = QVBoxLayout(self)
        layout.setContentsMargins(24, 24, 24, 24)
        layout.setSpacing(20)

        title = QLabel("Paramètres")
        title.setStyleSheet(f"font-size: 15px; font-weight: 600; color: {theme.ACCENT_TEXT};")
        layout.addWidget(title)

        # Fichier de modèles
        section1 = QLabel("FICHIER DE MODÈLES")
        section1.setStyleSheet(f"color: {theme.TEXT_MUTED}; font-size: 11px; font-weight: 600;")
        layout.addWidget(section1)

        file_row = QHBoxLayout()
        self._path_label = QLabel(self._config.get("xlsx_path") or "Non configuré")
        self._path_label.setWordWrap(True)
        self._path_label.setStyleSheet(f"color: {theme.TEXT_PRIMARY}; font-size: 12px;")
        file_row.addWidget(self._path_label, 1)
        btn_modify = QPushButton("Modifier")
        btn_modify.clicked.connect(self._change_file)
        file_row.addWidget(btn_modify)
        layout.addLayout(file_row)

        # Caractère déclencheur
        section2 = QLabel("CARACTÈRE DÉCLENCHEUR")
        section2.setStyleSheet(f"color: {theme.TEXT_MUTED}; font-size: 11px; font-weight: 600;")
        layout.addWidget(section2)

        self._trigger_input = QLineEdit(self._config.get("trigger_char", "/"))
        self._trigger_input.setMaxLength(1)
        self._trigger_input.setFixedWidth(60)
        layout.addWidget(self._trigger_input)
        note = QLabel("Le code doit commencer par ce caractère")
        note.setStyleSheet(f"color: {theme.TEXT_MUTED}; font-size: 11px;")
        layout.addWidget(note)

        # Démarrage automatique
        section3 = QLabel("DÉMARRAGE AUTOMATIQUE")
        section3.setStyleSheet(f"color: {theme.TEXT_MUTED}; font-size: 11px; font-weight: 600;")
        layout.addWidget(section3)

        self._autostart_cb = QCheckBox("Lancer Envelop au démarrage de Windows")
        self._autostart_cb.setChecked(self._config.get("autostart", False))
        layout.addWidget(self._autostart_cb)

        layout.addStretch()

        btn_save = QPushButton("Sauvegarder")
        btn_save.setObjectName("primary")
        btn_save.clicked.connect(self._save)
        layout.addWidget(btn_save)

    def _change_file(self):
        path, _ = QFileDialog.getOpenFileName(
            self, "Sélectionner le fichier de modèles", "", "Fichiers Excel (*.xlsx)"
        )
        if path:
            self._config["xlsx_path"] = path
            self._path_label.setText(path)

    def _save(self):
        self._config["trigger_char"] = self._trigger_input.text() or "/"
        self._config["autostart"] = self._autostart_cb.isChecked()
        cfg.save_config(self._config)
        exe = sys.executable
        cfg.set_autostart(self._config["autostart"], exe)
        self.accept()
