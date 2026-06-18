import json
import os

CONFIG_DIR = os.path.join(os.environ.get("APPDATA", ""), "FCFModeles")
CONFIG_FILE = os.path.join(CONFIG_DIR, "config.json")

DEFAULTS = {
    "xlsx_path": "",
    "trigger_char": "/",
    "autostart": False,
}


def load_config() -> dict:
    if not os.path.exists(CONFIG_FILE):
        return dict(DEFAULTS)
    try:
        with open(CONFIG_FILE, "r", encoding="utf-8") as f:
            data = json.load(f)
        return {**DEFAULTS, **data}
    except Exception:
        return dict(DEFAULTS)


def validate_xlsx_path(path: str) -> bool:
    """Return True only if path points to an existing .xlsx file."""
    if not path:
        return False
    path = os.path.abspath(path)
    if not path.lower().endswith(".xlsx"):
        return False
    if not os.path.isfile(path):
        return False
    # Reject paths outside the user profile and common safe locations
    allowed_roots = (
        os.environ.get("USERPROFILE", ""),
        os.environ.get("OneDrive", ""),
        os.environ.get("OneDriveCommercial", ""),
    )
    if not any(path.startswith(r) for r in allowed_roots if r):
        import logging
        logging.getLogger("fcf").warning("Rejected xlsx path outside user profile: %s", path)
        return False
    return True


def save_config(cfg: dict) -> None:
    os.makedirs(CONFIG_DIR, exist_ok=True)
    with open(CONFIG_FILE, "w", encoding="utf-8") as f:
        json.dump(cfg, f, ensure_ascii=False, indent=2)


def set_autostart(enabled: bool, exe_path: str) -> None:
    import winreg
    key_path = r"Software\Microsoft\Windows\CurrentVersion\Run"
    app_name = "FCFModeles"
    try:
        key = winreg.OpenKey(winreg.HKEY_CURRENT_USER, key_path, 0, winreg.KEY_SET_VALUE)
        if enabled:
            winreg.SetValueEx(key, app_name, 0, winreg.REG_SZ, f'"{exe_path}"')
        else:
            try:
                winreg.DeleteValue(key, app_name)
            except FileNotFoundError:
                pass
        winreg.CloseKey(key)
    except Exception as e:
        import logging
        logging.getLogger("fcf").error(f"Autostart error: {e}")
