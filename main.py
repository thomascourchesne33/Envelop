import logging
import os
import sys
import threading

from PyQt6.QtCore import QEvent, Qt, QTimer
from PyQt6.QtWidgets import QApplication, QMessageBox

import config as cfg
from file_watcher import FileWatcher
from keyboard_hook import KeyboardHook
from template_loader import Template, filter_templates, load_templates
from ui.main_window import MainWindow, make_app_icon
from ui.settings import FirstRunDialog, SettingsWindow
from ui.template_picker import TemplatePicker
from ui.tray import TrayIcon
from ui.variable_popup import VariablePopup

_log_dir = os.path.join(os.environ.get("APPDATA", ""), "FCFModeles")
os.makedirs(_log_dir, exist_ok=True)
# Rotating log: max 1 MB, keep 2 backups — logs never grow out of control
from logging.handlers import RotatingFileHandler
_handler = RotatingFileHandler(
    os.path.join(_log_dir, "app.log"),
    maxBytes=1_000_000,
    backupCount=2,
    encoding="utf-8",
)
_handler.setFormatter(logging.Formatter("%(asctime)s %(levelname)s %(name)s: %(message)s"))
logging.getLogger().addHandler(_handler)
logging.getLogger().setLevel(logging.INFO)
log = logging.getLogger("fcf")

_CALLBACK_EVENT_TYPE = QEvent.Type(QEvent.registerEventType())


class _CallbackEvent(QEvent):
    def __init__(self, fn):
        super().__init__(_CALLBACK_EVENT_TYPE)
        self.fn = fn


class _App(QApplication):
    def event(self, e: QEvent) -> bool:
        if e.type() == _CALLBACK_EVENT_TYPE:
            e.fn()
            return True
        return super().event(e)


class App:
    def __init__(self, qt_app: _App) -> None:
        self._qt = qt_app
        self._config = cfg.load_config()
        self._templates: list[Template] = []
        self._watcher = FileWatcher()
        self._hook: KeyboardHook | None = None
        self._main_window: MainWindow | None = None
        self._picker: TemplatePicker | None = None
        self._tray: TrayIcon | None = None

    def run(self) -> int:
        # First launch setup
        if not self._config.get("xlsx_path"):
            dlg = FirstRunDialog()
            if dlg.exec() != FirstRunDialog.DialogCode.Accepted:
                return 0
            self._config = cfg.load_config()

        # Show window immediately — load templates in background
        self._main_window = MainWindow(
            get_templates=lambda: self._templates,
            on_insert=self._on_template_selected,
            on_save=self._save_templates,
            on_file_change=self._change_file,
        )
        self._main_window.show()

        # Load templates + start watcher in background thread
        threading.Thread(target=self._load_and_watch, daemon=True).start()

        # Floating picker (keyboard trigger)
        self._picker = TemplatePicker(
            on_select=self._on_template_selected,
            on_close=self._clear_capture,
        )

        # Tray
        self._tray = TrayIcon(
            on_open=self._open_main_window,
            on_settings=self._open_settings,
            on_reload=self._manual_reload,
            on_about=self._show_about,
            on_quit=self._quit,
        )

        # Keyboard hook
        self._hook = KeyboardHook(
            get_trigger_char=lambda: self._config.get("trigger_char", "/"),
            get_templates=lambda: self._templates,
            on_buffer_update=self._on_buffer_update,   # (buffer, matches)
            on_clear=self._clear_capture,
        )
        threading.Thread(target=self._hook.start, daemon=True).start()

        # Auto-update: check on startup, then every 6 hours
        self._update_timer = QTimer()
        self._update_timer.timeout.connect(
            lambda: threading.Thread(target=self._check_for_update, daemon=True).start()
        )
        self._update_timer.start(6 * 60 * 60 * 1000)

        return self._qt.exec()

    def _load_and_watch(self) -> None:
        """Run in background thread on startup."""
        self._load_templates()
        self._start_watcher()
        self._check_for_update()

    def _check_for_update(self) -> None:
        """Run in background thread — checks GitHub Releases, then asks the user before installing."""
        from updater import check_for_update
        info = check_for_update()
        if not info:
            return
        log.info("Update available: %s", info["version"])
        self._qt.postEvent(self._qt, _CallbackEvent(lambda i=info: self._prompt_update(i)))

    def _prompt_update(self, info: dict) -> None:
        reply = QMessageBox.question(
            self._main_window,
            "Mise à jour disponible",
            f"Une nouvelle version d'Envelop ({info['version']}) est disponible.\n\n"
            "Voulez-vous l'installer maintenant ? La fenêtre d'installation va "
            "s'afficher puis Envelop redémarrera automatiquement.",
            QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No,
        )
        if reply == QMessageBox.StandardButton.Yes:
            threading.Thread(target=self._run_update, args=(info,), daemon=True).start()

    def _run_update(self, info: dict) -> None:
        from updater import download_and_install
        if download_and_install(info["download_url"]):
            self._qt.postEvent(self._qt, _CallbackEvent(self._quit))
        else:
            self._qt.postEvent(self._qt, _CallbackEvent(
                lambda: self._show_toast("Échec du téléchargement de la mise à jour.")
            ))

    def _load_templates(self) -> None:
        path = self._config.get("xlsx_path", "")
        if not path or not os.path.exists(path):
            log.warning("Template file not found: %s", path)
            if self._tray:
                self._tray.set_warning(True)
            return
        try:
            self._templates = load_templates(path)
            if self._tray:
                self._tray.set_warning(False)
            if self._main_window:
                self._main_window.refresh_templates()
        except Exception as e:
            log.error("Load error: %s", e)
            if self._tray:
                self._tray.set_warning(True)

    def _start_watcher(self) -> None:
        path = self._config.get("xlsx_path", "")
        if path and os.path.exists(path):
            self._watcher.start(path, lambda: self._qt.postEvent(
                self._qt, _CallbackEvent(self._load_templates)
            ))

    def _on_buffer_update(self, buffer: str, matches: list) -> None:
        self._qt.postEvent(self._qt, _CallbackEvent(
            lambda b=buffer, m=list(matches): self._picker.update_results(b, m)
        ))

    def _clear_capture(self) -> None:
        self._qt.postEvent(self._qt, _CallbackEvent(
            lambda: self._picker.hide() if self._picker else None
        ))

    def _on_template_selected(self, template: Template) -> None:
        if self._hook:
            self._hook.pause()
        if self._picker:
            self._picker.hide()
        if not template.variables:
            self._do_insert(template.corps, template.objet)
            if self._hook:
                self._hook.resume()
            return
        try:
            popup = VariablePopup(
                template=template,
                on_insert=self._do_insert,
                on_cancel=lambda: None,
            )
            popup.exec()
        finally:
            if self._hook:
                self._hook.resume()

    def _change_file(self, path: str) -> None:
        self._config["xlsx_path"] = path
        cfg.save_config(self._config)
        self._watcher.stop()
        self._load_templates()
        self._start_watcher()
        self._show_toast(f"Fichier chargé : {os.path.basename(path)}")

    def _save_templates(self, templates: list[Template]) -> None:
        from template_saver import save_templates
        path = self._config.get("xlsx_path", "")
        if not path:
            return
        try:
            save_templates(path, templates)
            self._templates = templates
        except Exception as e:
            self._show_toast(f"Erreur de sauvegarde : {e}")

    def _do_insert(self, body: str, subject: str = "") -> None:
        from outlook_inserter import insert_into_outlook
        ok, msg = insert_into_outlook(body, subject)
        if not ok:
            self._show_toast(msg)

    def _open_main_window(self) -> None:
        if self._main_window:
            self._main_window.refresh_templates()
            self._main_window.show()
            self._main_window.raise_()
            self._main_window.activateWindow()

    def _open_settings(self) -> None:
        dlg = SettingsWindow()
        if dlg.exec() == SettingsWindow.DialogCode.Accepted:
            self._config = cfg.load_config()
            self._watcher.stop()
            self._load_templates()
            self._start_watcher()

    def _manual_reload(self) -> None:
        self._load_templates()
        self._show_toast("Modèles rechargés.")

    def _show_about(self) -> None:
        from version import APP_VERSION
        path = self._config.get("xlsx_path", "Non configuré")
        QMessageBox.information(
            None, "À propos — Envelop",
            f"Envelop v{APP_VERSION}\n\nFichier : {path}\nModèles chargés : {len(self._templates)}",
        )

    def _quit(self) -> None:
        if self._hook:
            self._hook.stop()
        self._watcher.stop()
        self._qt.quit()

    def _show_toast(self, message: str) -> None:
        if self._tray:
            self._tray.showMessage("Envelop", message, TrayIcon.MessageIcon.Warning, 3000)


def main() -> None:
    app = _App(sys.argv)
    app.setQuitOnLastWindowClosed(False)
    app.setWindowIcon(make_app_icon())
    controller = App(app)
    sys.exit(controller.run())


if __name__ == "__main__":
    main()
