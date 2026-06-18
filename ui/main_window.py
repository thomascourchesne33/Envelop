import os
import re
from typing import Callable, List, Optional

from PyQt6.QtCore import Qt, QSize
from PyQt6.QtGui import QColor, QIcon, QPainter, QPixmap, QFont, QPainterPath
from PyQt6.QtWidgets import (
    QFileDialog, QFrame, QGraphicsDropShadowEffect, QHBoxLayout,
    QLabel, QLineEdit, QListWidget, QListWidgetItem, QMainWindow,
    QMessageBox, QPushButton, QScrollArea, QSizePolicy,
    QSplitter, QTextEdit, QVBoxLayout, QWidget, QStatusBar,
    QGridLayout,
)

from template_loader import Template

_LOGO_PATH = os.path.join(os.path.dirname(os.path.dirname(__file__)), "envelop_logo.svg")

STYLE = """
* {
    font-family: "Segoe UI", sans-serif;
    font-size: 13px;
}
QMainWindow, QWidget#root {
    background: #F0F2F5;
}

/* ── Sidebar ── */
QWidget#sidebar {
    background: #FFFFFF;
    border-right: 1px solid #E2E8F0;
}
QLabel#sidebar_title {
    font-size: 11px;
    font-weight: bold;
    color: #94A3B8;
    letter-spacing: 1px;
    padding: 0 4px;
}
QListWidget {
    background: transparent;
    border: none;
    outline: none;
}
QListWidget::item {
    padding: 9px 12px;
    border-radius: 8px;
    color: #374151;
    margin: 1px 0;
}
QListWidget::item:selected {
    background: #EFF6FF;
    color: #2563EB;
}
QListWidget::item:hover:!selected {
    background: #F8FAFC;
}

/* ── Header ── */
QWidget#header {
    background: #FFFFFF;
    border-bottom: 1px solid #E2E8F0;
}
QLabel#app_name {
    font-size: 17px;
    font-weight: bold;
    color: #1E293B;
}
QLabel#count_lbl {
    font-size: 12px;
    color: #94A3B8;
    background: #F1F5F9;
    border-radius: 10px;
    padding: 2px 10px;
}

/* ── Search ── */
QLineEdit#search {
    background: #F8FAFC;
    border: 1px solid #E2E8F0;
    border-radius: 8px;
    padding: 8px 14px;
    color: #1E293B;
    font-size: 13px;
}
QLineEdit#search:focus {
    border-color: #2563EB;
    background: #FFFFFF;
}

/* ── Buttons ── */
QPushButton {
    border-radius: 8px;
    padding: 8px 16px;
    font-size: 13px;
}
QPushButton#btn_new {
    background: #2563EB;
    color: #FFFFFF;
    border: none;
    font-weight: bold;
    padding: 8px 18px;
}
QPushButton#btn_new:hover { background: #1D4ED8; }
QPushButton#btn_file {
    background: #F8FAFC;
    color: #475569;
    border: 1px solid #E2E8F0;
    font-size: 12px;
    padding: 7px 14px;
}
QPushButton#btn_file:hover { background: #F1F5F9; color: #1E293B; }
QPushButton#btn_edit {
    background: #EFF6FF;
    color: #2563EB;
    border: 1px solid #BFDBFE;
    padding: 6px 14px;
}
QPushButton#btn_edit:hover { background: #DBEAFE; }
QPushButton#btn_delete {
    background: #FFF1F2;
    color: #E11D48;
    border: 1px solid #FECDD3;
    padding: 6px 14px;
}
QPushButton#btn_delete:hover { background: #FFE4E6; }
QPushButton#btn_insert {
    background: #2563EB;
    color: #FFFFFF;
    border: none;
    font-weight: bold;
    font-size: 13px;
    padding: 10px 28px;
    border-radius: 10px;
}
QPushButton#btn_insert:hover { background: #1D4ED8; }
QPushButton#btn_insert:disabled {
    background: #E2E8F0;
    color: #94A3B8;
}
QPushButton:disabled { color: #94A3B8; }

/* ── Detail panel ── */
QWidget#detail_bg { background: #F0F2F5; }
QWidget#detail_card {
    background: #FFFFFF;
    border-radius: 14px;
}
QLabel#tmpl_title {
    font-size: 18px;
    font-weight: bold;
    color: #1E293B;
}
QLabel#code_pill {
    background: #EFF6FF;
    color: #2563EB;
    border-radius: 8px;
    padding: 3px 10px;
    font-family: Consolas, monospace;
    font-size: 12px;
    font-weight: bold;
}
QLabel#cat_pill {
    background: #F1F5F9;
    color: #64748B;
    border-radius: 8px;
    padding: 3px 10px;
    font-size: 12px;
}
QLabel#field_label {
    color: #94A3B8;
    font-size: 10px;
    font-weight: bold;
    letter-spacing: 1px;
}
QLabel#field_value {
    color: #334155;
    font-size: 13px;
}
QLabel#var_chip {
    background: #F0FDF4;
    color: #16A34A;
    border: 1px solid #BBF7D0;
    border-radius: 6px;
    padding: 2px 9px;
    font-family: Consolas, monospace;
    font-size: 11px;
}
QTextEdit#preview {
    background: #F8FAFC;
    border: 1px solid #E2E8F0;
    border-radius: 8px;
    color: #475569;
    font-size: 12px;
    padding: 10px;
}

/* ── Empty state ── */
QLabel#empty_state {
    color: #CBD5E1;
    font-size: 15px;
}

/* ── Status bar ── */
QStatusBar {
    background: #FFFFFF;
    color: #94A3B8;
    font-size: 11px;
    border-top: 1px solid #E2E8F0;
}
QStatusBar::item { border: none; }

/* ── Scrollbar ── */
QScrollBar:vertical { width: 5px; background: transparent; }
QScrollBar::handle:vertical { background: #CBD5E1; border-radius: 3px; min-height: 20px; }
QScrollBar::add-line:vertical, QScrollBar::sub-line:vertical { height: 0; }
QScrollBar:horizontal { height: 0; }

/* ── Divider ── */
QFrame#divider { background: #E2E8F0; max-height: 1px; }
"""


def make_app_icon() -> QIcon:
    if os.path.exists(_LOGO_PATH):
        return QIcon(_LOGO_PATH)
    return QIcon()


def _shadow(widget, radius=16, y=4, alpha=25):
    eff = QGraphicsDropShadowEffect(widget)
    eff.setBlurRadius(radius)
    eff.setOffset(0, y)
    eff.setColor(QColor(0, 0, 0, alpha))
    widget.setGraphicsEffect(eff)


def _divider_h() -> QFrame:
    f = QFrame()
    f.setObjectName("divider")
    f.setFixedHeight(1)
    f.setSizePolicy(QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Fixed)
    return f


class MainWindow(QMainWindow):
    def __init__(
        self,
        get_templates: Callable[[], List[Template]],
        on_insert: Callable,
        on_save: Callable[[List[Template]], None],
        on_file_change: Callable[[str], None],
        parent=None,
    ):
        super().__init__(parent)
        self._get_templates = get_templates
        self._on_insert = on_insert
        self._on_save = on_save
        self._on_file_change = on_file_change
        self._current: Optional[Template] = None
        self.setWindowTitle("Envelop")
        self.setMinimumSize(1000, 660)
        self.setStyleSheet(STYLE)
        self.setWindowIcon(make_app_icon())
        self._build_ui()
        self.refresh_templates()

    # ── Build ────────────────────────────────────────────────────────────────

    def _build_ui(self):
        root = QWidget()
        root.setObjectName("root")
        self.setCentralWidget(root)
        rl = QVBoxLayout(root)
        rl.setContentsMargins(0, 0, 0, 0)
        rl.setSpacing(0)

        rl.addWidget(self._build_header())

        body = QHBoxLayout()
        body.setContentsMargins(0, 0, 0, 0)
        body.setSpacing(0)
        body.addWidget(self._build_sidebar())
        body.addWidget(self._build_detail(), 1)

        body_widget = QWidget()
        body_widget.setObjectName("root")
        body_widget.setLayout(body)
        rl.addWidget(body_widget, 1)

        self._status = QStatusBar()
        self.setStatusBar(self._status)

    def _build_header(self) -> QWidget:
        h = QWidget()
        h.setObjectName("header")
        h.setFixedHeight(64)
        hl = QHBoxLayout(h)
        hl.setContentsMargins(24, 0, 24, 0)
        hl.setSpacing(12)

        if os.path.exists(_LOGO_PATH):
            logo = QLabel()
            px = QPixmap(_LOGO_PATH).scaled(32, 32, Qt.AspectRatioMode.KeepAspectRatio, Qt.TransformationMode.SmoothTransformation)
            logo.setPixmap(px)
            hl.addWidget(logo)

        name = QLabel("Envelop")
        name.setObjectName("app_name")
        hl.addWidget(name)

        self._count_lbl = QLabel("0 modèles")
        self._count_lbl.setObjectName("count_lbl")
        hl.addWidget(self._count_lbl)

        hl.addStretch()

        btn_file = QPushButton("📂  Changer de fichier Excel")
        btn_file.setObjectName("btn_file")
        btn_file.clicked.connect(self._change_file)
        hl.addWidget(btn_file)

        btn_new = QPushButton("＋  Nouveau modèle")
        btn_new.setObjectName("btn_new")
        btn_new.setFixedHeight(36)
        btn_new.clicked.connect(self._new_template)
        hl.addWidget(btn_new)

        return h

    def _build_sidebar(self) -> QWidget:
        sidebar = QWidget()
        sidebar.setObjectName("sidebar")
        sidebar.setFixedWidth(268)
        sl = QVBoxLayout(sidebar)
        sl.setContentsMargins(16, 20, 16, 16)
        sl.setSpacing(12)

        self._search = QLineEdit()
        self._search.setObjectName("search")
        self._search.setPlaceholderText("🔍  Rechercher un modèle…")
        self._search.textChanged.connect(lambda t: self._filter(t))
        sl.addWidget(self._search)

        lbl = QLabel("MODÈLES")
        lbl.setObjectName("sidebar_title")
        sl.addWidget(lbl)

        self._list = QListWidget()
        self._list.currentItemChanged.connect(self._on_select)
        sl.addWidget(self._list)

        return sidebar

    def _build_detail(self) -> QWidget:
        bg = QWidget()
        bg.setObjectName("detail_bg")
        bl = QVBoxLayout(bg)
        bl.setContentsMargins(28, 28, 28, 28)
        bl.setSpacing(0)

        # Empty state
        self._empty = QLabel("← Sélectionnez un modèle")
        self._empty.setObjectName("empty_state")
        self._empty.setAlignment(Qt.AlignmentFlag.AlignCenter)
        bl.addWidget(self._empty, 1)

        # Card
        self._card = QWidget()
        self._card.setObjectName("detail_card")
        self._card.setVisible(False)
        _shadow(self._card, radius=20, y=4, alpha=20)
        cl = QVBoxLayout(self._card)
        cl.setContentsMargins(28, 24, 28, 24)
        cl.setSpacing(16)

        # ── Title row
        title_row = QHBoxLayout()
        title_row.setSpacing(10)
        self._tmpl_title = QLabel()
        self._tmpl_title.setObjectName("tmpl_title")
        self._tmpl_title.setWordWrap(True)
        title_row.addWidget(self._tmpl_title, 1)
        self._btn_edit = QPushButton("Modifier")
        self._btn_edit.setObjectName("btn_edit")
        self._btn_edit.clicked.connect(self._edit_template)
        title_row.addWidget(self._btn_edit)
        self._btn_delete = QPushButton("Supprimer")
        self._btn_delete.setObjectName("btn_delete")
        self._btn_delete.clicked.connect(self._delete_template)
        title_row.addWidget(self._btn_delete)
        cl.addLayout(title_row)

        # ── Pills row
        pills_row = QHBoxLayout()
        pills_row.setSpacing(8)
        self._code_pill = QLabel()
        self._code_pill.setObjectName("code_pill")
        pills_row.addWidget(self._code_pill)
        self._cat_pill = QLabel()
        self._cat_pill.setObjectName("cat_pill")
        pills_row.addWidget(self._cat_pill)
        pills_row.addStretch()
        cl.addLayout(pills_row)

        cl.addWidget(_divider_h())

        # ── Subject
        self._subj_block = QWidget()
        sb_l = QVBoxLayout(self._subj_block)
        sb_l.setContentsMargins(0, 0, 0, 0)
        sb_l.setSpacing(4)
        lbl_s = QLabel("OBJET DU COURRIEL")
        lbl_s.setObjectName("field_label")
        sb_l.addWidget(lbl_s)
        self._subj_val = QLabel()
        self._subj_val.setObjectName("field_value")
        self._subj_val.setWordWrap(True)
        sb_l.addWidget(self._subj_val)
        cl.addWidget(self._subj_block)

        # ── Variables
        self._vars_block = QWidget()
        vb_l = QVBoxLayout(self._vars_block)
        vb_l.setContentsMargins(0, 0, 0, 0)
        vb_l.setSpacing(6)
        lbl_v = QLabel("VARIABLES")
        lbl_v.setObjectName("field_label")
        vb_l.addWidget(lbl_v)
        self._vars_chips = QHBoxLayout()
        self._vars_chips.setSpacing(6)
        self._vars_chips.setContentsMargins(0, 0, 0, 0)
        vb_l.addLayout(self._vars_chips)
        cl.addWidget(self._vars_block)

        # ── Preview
        lbl_p = QLabel("APERÇU DU CORPS")
        lbl_p.setObjectName("field_label")
        cl.addWidget(lbl_p)
        self._preview = QTextEdit()
        self._preview.setObjectName("preview")
        self._preview.setReadOnly(True)
        self._preview.setMinimumHeight(140)
        cl.addWidget(self._preview, 1)

        # ── Insert button
        btn_row = QHBoxLayout()
        btn_row.addStretch()
        self._btn_insert = QPushButton("Insérer dans Outlook  →")
        self._btn_insert.setObjectName("btn_insert")
        self._btn_insert.setFixedHeight(42)
        self._btn_insert.clicked.connect(self._insert)
        btn_row.addWidget(self._btn_insert)
        cl.addLayout(btn_row)

        bl.addWidget(self._card, 1)
        return bg

    # ── List management ──────────────────────────────────────────────────────

    def refresh_templates(self, select_code: str = ""):
        self._filter(self._search.text() if hasattr(self, "_search") else "", select_code)

    def _filter(self, text: str, select_code: str = ""):
        templates = self._get_templates()
        self._count_lbl.setText(f"{len(templates)} modèles")

        q = text.lower().strip()
        if q:
            templates = [t for t in templates if
                         q in t.nom.lower() or q in t.code.lower() or q in t.categorie.lower()]

        self._list.blockSignals(True)
        self._list.clear()
        target = None

        groups: dict[str, list[Template]] = {}
        for t in templates:
            groups.setdefault(t.categorie, []).append(t)

        for cat in sorted(groups.keys()):
            hdr = QListWidgetItem(cat.upper())
            hdr.setFlags(Qt.ItemFlag.NoItemFlags)
            hdr.setForeground(QColor("#94A3B8"))
            f = hdr.font()
            f.setPointSize(9)
            f.setBold(True)
            hdr.setFont(f)
            self._list.addItem(hdr)
            for tmpl in sorted(groups[cat], key=lambda x: x.nom):
                item = QListWidgetItem(f"   {tmpl.nom}")
                item.setData(Qt.ItemDataRole.UserRole, tmpl)
                self._list.addItem(item)
                if tmpl.code == select_code:
                    target = item

        self._list.blockSignals(False)
        if target:
            self._list.setCurrentItem(target)

    def _on_select(self, current, _prev):
        if not current:
            return
        tmpl: Optional[Template] = current.data(Qt.ItemDataRole.UserRole)
        if not tmpl:
            return
        self._current = tmpl
        self._empty.setVisible(False)
        self._card.setVisible(True)

        self._tmpl_title.setText(tmpl.nom)
        self._code_pill.setText(tmpl.code)
        self._cat_pill.setText(tmpl.categorie)

        self._subj_block.setVisible(bool(tmpl.objet))
        self._subj_val.setText(tmpl.objet or "")

        # Variable chips
        while self._vars_chips.count():
            w = self._vars_chips.takeAt(0)
            if w.widget():
                w.widget().deleteLater()
        self._vars_block.setVisible(bool(tmpl.variables))
        for v in tmpl.variables:
            chip = QLabel(v.replace("_", " "))
            chip.setObjectName("var_chip")
            self._vars_chips.addWidget(chip)
        self._vars_chips.addStretch()

        plain = re.sub(r"<[^>]+>", "", tmpl.corps)
        self._preview.setPlainText(plain)
        self._status.showMessage(f"{tmpl.categorie}  ·  {tmpl.code}  ·  {len(tmpl.variables)} variable(s)")

    # ── CRUD ─────────────────────────────────────────────────────────────────

    def _new_template(self):
        from ui.template_editor import TemplateEditorDialog
        cats = sorted({t.categorie for t in self._get_templates()})
        dlg = TemplateEditorDialog(cats, parent=self)
        if dlg.exec() == TemplateEditorDialog.DialogCode.Accepted and dlg.result_template:
            self._on_save(self._get_templates() + [dlg.result_template])
            self.refresh_templates(select_code=dlg.result_template.code)

    def _edit_template(self):
        if not self._current:
            return
        from ui.template_editor import TemplateEditorDialog
        cats = sorted({t.categorie for t in self._get_templates()})
        dlg = TemplateEditorDialog(cats, template=self._current, parent=self)
        if dlg.exec() == TemplateEditorDialog.DialogCode.Accepted and dlg.result_template:
            old = self._current.code
            templates = [dlg.result_template if t.code == old else t for t in self._get_templates()]
            self._on_save(templates)
            self.refresh_templates(select_code=dlg.result_template.code)

    def _delete_template(self):
        if not self._current:
            return
        reply = QMessageBox.question(
            self, "Supprimer",
            f"Supprimer « {self._current.nom} » ?",
            QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.Cancel,
        )
        if reply == QMessageBox.StandardButton.Yes:
            templates = [t for t in self._get_templates() if t.code != self._current.code]
            self._on_save(templates)
            self._current = None
            self._empty.setVisible(True)
            self._card.setVisible(False)
            self.refresh_templates()

    def _change_file(self):
        path, _ = QFileDialog.getOpenFileName(
            self, "Choisir le fichier de modèles", "", "Fichiers Excel (*.xlsx)"
        )
        if path:
            self._on_file_change(path)

    def _insert(self):
        if self._current:
            self._on_insert(self._current)

    def closeEvent(self, event):
        event.ignore()
        self.hide()
