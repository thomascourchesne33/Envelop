import re
from typing import Callable

from PyQt6.QtCore import Qt
from PyQt6.QtWidgets import (
    QComboBox, QDialog, QHBoxLayout, QLabel, QLineEdit,
    QPushButton, QScrollArea, QTextEdit,
    QVBoxLayout, QWidget,
)

from template_loader import Template

STYLE = """
* { font-family: "Segoe UI", sans-serif; font-size: 13px; }
QDialog { background: #FFFFFF; color: #1E293B; }
QLabel { color: #1E293B; }
QLabel#title {
    font-size: 16px;
    font-weight: bold;
    color: #1E293B;
}
QLabel#var_label {
    color: #94A3B8;
    font-size: 10px;
    font-weight: bold;
    letter-spacing: 1px;
}
QLabel#section {
    color: #94A3B8;
    font-size: 10px;
    font-weight: bold;
    letter-spacing: 1px;
}
QLineEdit {
    background: #F8FAFC;
    color: #1E293B;
    border: 1px solid #E2E8F0;
    border-radius: 8px;
    padding: 8px 12px;
    font-size: 13px;
}
QLineEdit:focus { border-color: #2563EB; background: #FFFFFF; }
QComboBox {
    background: #F8FAFC;
    color: #1E293B;
    border: 1px solid #E2E8F0;
    border-radius: 8px;
    padding: 8px 12px;
    font-size: 13px;
}
QComboBox:focus { border-color: #2563EB; background: #FFFFFF; }
QComboBox::drop-down {
    border: none;
    width: 28px;
}
QComboBox::down-arrow {
    image: none;
    border-left: 5px solid transparent;
    border-right: 5px solid transparent;
    border-top: 6px solid #94A3B8;
    margin-right: 8px;
}
QComboBox QAbstractItemView {
    background: #FFFFFF;
    color: #1E293B;
    border: 1px solid #E2E8F0;
    border-radius: 8px;
    selection-background-color: #EFF6FF;
    selection-color: #2563EB;
    padding: 4px;
}
QTextEdit {
    background: #F8FAFC;
    color: #475569;
    border: 1px solid #E2E8F0;
    border-radius: 8px;
    font-family: Consolas, monospace;
    font-size: 12px;
    padding: 8px;
}
QPushButton {
    background: #F1F5F9;
    color: #475569;
    border: 1px solid #E2E8F0;
    border-radius: 8px;
    padding: 8px 18px;
    font-size: 13px;
}
QPushButton:hover { background: #E2E8F0; }
QPushButton#insert {
    background: #2563EB;
    color: #FFFFFF;
    border: none;
    font-weight: bold;
}
QPushButton#insert:hover { background: #1D4ED8; }
QScrollArea { border: none; background: transparent; }
"""

# Dropdown definitions — matched against the normalized variable name (lowercase, underscores)
# "other": True adds an "Autre…" option that reveals a free-text field
_DROPDOWNS: dict[str, dict] = {
    "assureur": {
        "options": [
            "Promutuel Assurance Bagot",
            "Intact Assurance",
            "Economical",
            "L'Unique assurances générales",
        ],
        "other": True,
        "other_label": "Précisez le nom de l'assureur…",
    },
    "mode_de_paiement": {
        "options": [
            "à régler auprès de l'assureur",
            "1 paiement",
            "3 paiements",
            "4 paiements",
            "prélèvements mensuels",
        ],
        "other": False,
    },
    "mode_paiement": {
        "options": [
            "à régler auprès de l'assureur",
            "1 paiement",
            "3 paiements",
            "4 paiements",
            "prélèvements mensuels",
        ],
        "other": False,
    },
    "methode_paiement": {
        "options": [
            "à régler auprès de l'assureur",
            "1 paiement",
            "3 paiements",
            "4 paiements",
            "prélèvements mensuels",
        ],
        "other": False,
    },
}

_AUTRE = "Autre…"


def _dropdown_key(var_name: str) -> str | None:
    """Return the matching dropdown key for a variable name, or None."""
    norm = var_name.lower().replace(" ", "_")
    # Exact match first
    if norm in _DROPDOWNS:
        return norm
    # Contains match — e.g. "NOM_ASSUREUR" → matches "assureur"
    for key in _DROPDOWNS:
        if key in norm:
            return key
    return None


class VariablePopup(QDialog):
    def __init__(
        self,
        template: Template,
        on_insert: Callable[[str, str], None],
        on_cancel: Callable,
        parent=None,
    ):
        super().__init__(parent)
        self.setWindowTitle("Insérer un modèle")
        self.setFixedWidth(480)
        self.setStyleSheet(STYLE)
        self.setWindowFlags(
            self.windowFlags()
            | Qt.WindowType.WindowStaysOnTopHint
        )
        self._template = template
        self._on_insert = on_insert
        self._on_cancel = on_cancel
        # Maps var name → callable that returns the current string value
        self._value_getters: dict[str, Callable[[], str]] = {}
        # Keep first focusable widget
        self._first_widget = None
        self._build_ui()

    def _build_ui(self):
        layout = QVBoxLayout(self)
        layout.setContentsMargins(24, 20, 24, 20)
        layout.setSpacing(14)

        title = QLabel(self._template.nom)
        title.setObjectName("title")
        title.setWordWrap(True)
        layout.addWidget(title)

        inputs_widget = QWidget()
        inputs_layout = QVBoxLayout(inputs_widget)
        inputs_layout.setContentsMargins(0, 0, 0, 0)
        inputs_layout.setSpacing(10)

        for var in self._template.variables:
            label_text = var.replace("_", " ").title()
            lbl = QLabel(label_text)
            lbl.setObjectName("var_label")
            inputs_layout.addWidget(lbl)

            dk = _dropdown_key(var)
            if dk is not None:
                getter = self._add_dropdown(inputs_layout, var, _DROPDOWNS[dk])
            else:
                getter = self._add_lineedit(inputs_layout, var, label_text)

            self._value_getters[var] = getter

        layout.addWidget(inputs_widget)

        preview_label = QLabel("Aperçu :")
        preview_label.setObjectName("section")
        layout.addWidget(preview_label)

        self._preview = QTextEdit()
        self._preview.setReadOnly(True)
        self._preview.setMaximumHeight(120)
        layout.addWidget(self._preview)

        btn_row = QHBoxLayout()
        btn_row.addStretch()
        btn_cancel = QPushButton("Annuler")
        btn_cancel.clicked.connect(self._cancel)
        btn_row.addWidget(btn_cancel)
        btn_insert = QPushButton("Insérer")
        btn_insert.setObjectName("insert")
        btn_insert.clicked.connect(self._insert)
        btn_row.addWidget(btn_insert)
        layout.addLayout(btn_row)

        self._update_preview()

        if self._first_widget:
            self._first_widget.setFocus()

    def _add_lineedit(self, layout: QVBoxLayout, var: str, label_text: str) -> Callable[[], str]:
        inp = QLineEdit()
        inp.setPlaceholderText(f"Entrez {label_text.lower()}…")
        inp.textChanged.connect(self._update_preview)
        layout.addWidget(inp)
        if self._first_widget is None:
            self._first_widget = inp
        return inp.text

    def _add_dropdown(self, layout: QVBoxLayout, var: str, config: dict) -> Callable[[], str]:
        combo = QComboBox()
        combo.setMaxVisibleItems(8)

        for opt in config["options"]:
            combo.addItem(opt)

        has_other = config.get("other", False)
        other_placeholder = config.get("other_label", "Précisez…")

        other_field: QLineEdit | None = None
        if has_other:
            combo.addItem(_AUTRE)
            other_field = QLineEdit()
            other_field.setPlaceholderText(other_placeholder)
            other_field.setVisible(False)
            other_field.textChanged.connect(self._update_preview)

        combo.currentTextChanged.connect(self._update_preview)

        if has_other and other_field is not None:
            def on_combo_change(text: str, f=other_field):
                f.setVisible(text == _AUTRE)
                self._update_preview()
            combo.currentTextChanged.connect(on_combo_change)

        layout.addWidget(combo)
        if has_other and other_field is not None:
            layout.addWidget(other_field)

        if self._first_widget is None:
            self._first_widget = combo

        if has_other and other_field is not None:
            def getter(c=combo, f=other_field) -> str:
                if c.currentText() == _AUTRE:
                    return f.text().strip() or _AUTRE
                return c.currentText()
        else:
            def getter(c=combo) -> str:
                return c.currentText()

        return getter

    def _get_value(self, var: str) -> str:
        return self._value_getters[var]()

    def _filled_body(self) -> str:
        body = self._template.corps
        for var in self._value_getters:
            body = body.replace(f"[{var}]", self._get_value(var))
        return body

    def _update_preview(self):
        body = self._filled_body()
        plain = re.sub(r"<[^>]+>", "", body)
        self._preview.setPlainText(plain[:400] + ("…" if len(plain) > 400 else ""))

    def _insert(self):
        body = self._filled_body()
        subject = self._template.objet
        if subject:
            for var in self._value_getters:
                subject = subject.replace(f"[{var}]", self._get_value(var))
        self._on_insert(body, subject)
        self.accept()

    def _cancel(self):
        self._on_cancel()
        self.reject()

    def keyPressEvent(self, event):
        if event.key() == Qt.Key.Key_Escape:
            self._cancel()
        else:
            super().keyPressEvent(event)
