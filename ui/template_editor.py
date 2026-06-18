import re
from typing import List, Optional

from PyQt6.QtCore import Qt
from PyQt6.QtWidgets import (
    QComboBox, QDialog, QHBoxLayout, QLabel,
    QLineEdit, QMessageBox, QPushButton,
    QSizePolicy, QTextEdit, QVBoxLayout, QWidget,
)

from template_loader import Template
from ui import theme

STYLE = f"""
* {{ font-family: {theme.FONT_FAMILY}; font-size: 13px; }}
QDialog {{ background: {theme.WHITE}; color: {theme.TEXT_PRIMARY}; }}
QLabel {{ color: {theme.TEXT_PRIMARY}; }}
QLabel#section {{
    color: {theme.TEXT_MUTED};
    font-size: 10px;
    font-weight: 600;
    letter-spacing: 1px;
}}
QLabel#title {{
    font-size: 16px;
    font-weight: 600;
    color: {theme.TEXT_PRIMARY};
}}
QLineEdit, QComboBox {{
    background: {theme.BG_SUBTLE};
    color: {theme.TEXT_PRIMARY};
    border: 1px solid {theme.BORDER};
    border-radius: 8px;
    padding: 7px 12px;
    font-size: 13px;
}}
QLineEdit:focus, QComboBox:focus {{ border-color: {theme.ACCENT}; background: {theme.WHITE}; }}
QComboBox::drop-down {{ border: none; padding-right: 8px; }}
QComboBox QAbstractItemView {{
    background: {theme.WHITE};
    color: {theme.TEXT_PRIMARY};
    selection-background-color: {theme.ACCENT_50};
    selection-color: {theme.ACCENT_TEXT};
    border: 1px solid {theme.BORDER};
    border-radius: 6px;
}}
QTextEdit {{
    background: {theme.BG_SUBTLE};
    color: {theme.TEXT_SECONDARY};
    border: 1px solid {theme.BORDER};
    border-radius: 8px;
    font-family: Consolas, monospace;
    font-size: 12px;
    padding: 8px;
}}
QTextEdit:focus {{ border-color: {theme.ACCENT}; background: {theme.WHITE}; }}
QPushButton {{
    background: {theme.BG_SUBTLE};
    color: {theme.TEXT_SECONDARY};
    border: 1px solid {theme.BORDER};
    border-radius: 8px;
    padding: 8px 18px;
}}
QPushButton:hover {{ background: {theme.BORDER}; }}
QPushButton#save {{
    background: {theme.ACCENT};
    color: {theme.WHITE};
    border: none;
    font-weight: 600;
}}
QPushButton#save:hover {{ background: {theme.ACCENT_HOVER}; }}
QLabel#preview_label {{
    color: {theme.TEXT_SECONDARY};
    font-family: Consolas;
    font-size: 12px;
    background: {theme.BG_SUBTLE};
    border: 1px solid {theme.BORDER};
    border-radius: 8px;
    padding: 8px;
}}
"""

_VAR_RE = re.compile(r"\[([A-Z0-9_ÉÈÊÀÂÙÛÎÔÇ]+)\]", re.IGNORECASE)


def _extract_vars(body: str) -> List[str]:
    seen = []
    for m in _VAR_RE.finditer(body):
        v = m.group(1).upper()
        if v not in seen:
            seen.append(v)
    return seen


class TemplateEditorDialog(QDialog):
    def __init__(
        self,
        existing_categories: List[str],
        template: Optional[Template] = None,
        parent=None,
    ):
        super().__init__(parent)
        self._template = template
        self._existing_categories = existing_categories
        self.result_template: Optional[Template] = None
        self.setWindowTitle("Modifier le modèle" if template else "Nouveau modèle")
        self.setMinimumWidth(620)
        self.setStyleSheet(STYLE)
        self.setWindowFlags(self.windowFlags() | Qt.WindowType.WindowStaysOnTopHint)
        self._build_ui()
        if template:
            self._populate(template)

    def _build_ui(self):
        layout = QVBoxLayout(self)
        layout.setContentsMargins(24, 20, 24, 20)
        layout.setSpacing(14)

        title = QLabel("Modifier le modèle" if self._template else "Nouveau modèle")
        title.setObjectName("title")
        layout.addWidget(title)

        # Code + Catégorie row
        row1 = QHBoxLayout()
        col_code = QVBoxLayout()
        col_code.addWidget(self._lbl("CODE DÉCLENCHEUR"))
        self._code = QLineEdit()
        self._code.setPlaceholderText("/renou1")
        col_code.addWidget(self._code)
        row1.addLayout(col_code)

        col_cat = QVBoxLayout()
        col_cat.addWidget(self._lbl("CATÉGORIE"))
        self._cat = QComboBox()
        self._cat.setEditable(True)
        self._cat.addItems(sorted(set(self._existing_categories)))
        self._cat.setCurrentText("")
        col_cat.addWidget(self._cat)
        row1.addLayout(col_cat)
        layout.addLayout(row1)

        # Nom
        layout.addWidget(self._lbl("NOM DU MODÈLE"))
        self._nom = QLineEdit()
        self._nom.setPlaceholderText("Ex. : Rappel renouvellement — automobile")
        layout.addWidget(self._nom)

        # Objet
        layout.addWidget(self._lbl("OBJET DU COURRIEL (optionnel)"))
        self._objet = QLineEdit()
        self._objet.setPlaceholderText("Ex. : Votre police arrive à échéance")
        layout.addWidget(self._objet)

        # Corps
        layout.addWidget(self._lbl("CORPS DU COURRIEL (HTML supporté — utilisez [NOM_VARIABLE] pour les variables)"))
        self._corps = QTextEdit()
        self._corps.setMinimumHeight(180)
        self._corps.setPlaceholderText("<p>Bonjour [NOM_CLIENT],</p><p>Votre police [NUMÉRO_POLICE]…</p>")
        self._corps.textChanged.connect(self._sync_vars)
        layout.addWidget(self._corps)

        # Variables (auto-detected)
        layout.addWidget(self._lbl("VARIABLES DÉTECTÉES (automatique)"))
        self._vars_display = QLabel("—")
        self._vars_display.setObjectName("preview_label")
        self._vars_display.setWordWrap(True)
        self._vars_display.setMinimumHeight(32)
        layout.addWidget(self._vars_display)

        # Buttons
        btn_row = QHBoxLayout()
        btn_row.addStretch()
        btn_cancel = QPushButton("Annuler")
        btn_cancel.clicked.connect(self.reject)
        btn_row.addWidget(btn_cancel)
        btn_save = QPushButton("Enregistrer")
        btn_save.setObjectName("save")
        btn_save.clicked.connect(self._save)
        btn_row.addWidget(btn_save)
        layout.addLayout(btn_row)

    def _lbl(self, text: str) -> QLabel:
        l = QLabel(text)
        l.setObjectName("section")
        return l

    def _populate(self, t: Template):
        self._code.setText(t.code)
        self._cat.setCurrentText(t.categorie)
        self._nom.setText(t.nom)
        self._objet.setText(t.objet)
        self._corps.setPlainText(t.corps)
        self._sync_vars()

    def _sync_vars(self):
        body = self._corps.toPlainText()
        vars_ = _extract_vars(body)
        if vars_:
            self._vars_display.setText("  •  ".join(v.replace("_", " ") for v in vars_))
        else:
            self._vars_display.setText("—  (aucune variable détectée)")

    def _save(self):
        code = self._code.text().strip()
        cat = self._cat.currentText().strip()
        nom = self._nom.text().strip()
        corps = self._corps.toPlainText().strip()

        if not code or not cat or not nom or not corps:
            QMessageBox.warning(self, "Champs manquants",
                                "Le code, la catégorie, le nom et le corps sont obligatoires.")
            return

        if not code.startswith("/"):
            code = "/" + code

        vars_ = _extract_vars(corps)
        self.result_template = Template(
            code=code,
            categorie=cat,
            nom=nom,
            objet=self._objet.text().strip(),
            corps=corps,
            variables=vars_,
        )
        self.accept()
