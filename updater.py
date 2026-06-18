import json
import logging
import os
import subprocess
import tempfile
import urllib.request
from typing import Optional, Tuple

from version import APP_VERSION, GITHUB_REPO

log = logging.getLogger("fcf")

_API_URL = f"https://api.github.com/repos/{GITHUB_REPO}/releases/latest"
_ASSET_NAME = "envelop_setup.exe"
_REQUEST_TIMEOUT = 10
_DOWNLOAD_TIMEOUT = 120
_MIN_INSTALLER_SIZE = 1_000_000  # sanity check — a real installer is several MB


def _parse_version(v: str) -> Tuple[int, ...]:
    v = v.strip().lstrip("vV")
    parts = []
    for p in v.split("."):
        digits = "".join(c for c in p if c.isdigit())
        parts.append(int(digits) if digits else 0)
    return tuple(parts)


def check_for_update() -> Optional[dict]:
    """Return {"version": tag, "download_url": url} if a newer release exists on GitHub, else None."""
    try:
        req = urllib.request.Request(
            _API_URL,
            headers={"Accept": "application/vnd.github+json", "User-Agent": "Envelop-Updater"},
        )
        with urllib.request.urlopen(req, timeout=_REQUEST_TIMEOUT) as resp:
            data = json.loads(resp.read().decode("utf-8"))

        tag = data.get("tag_name", "")
        if _parse_version(tag) <= _parse_version(APP_VERSION):
            return None

        for asset in data.get("assets", []):
            if asset.get("name", "").lower() == _ASSET_NAME:
                return {"version": tag, "download_url": asset.get("browser_download_url")}

        log.warning("Update %s found but no installer asset attached", tag)
        return None
    except Exception as e:
        log.info("Update check skipped: %s", e)
        return None


def download_and_install(download_url: str) -> bool:
    """Download the installer from GitHub and launch a silent install. Returns True on success."""
    try:
        req = urllib.request.Request(download_url, headers={"User-Agent": "Envelop-Updater"})
        with urllib.request.urlopen(req, timeout=_DOWNLOAD_TIMEOUT) as resp:
            data = resp.read()

        # Integrity sanity check — must look like a real Windows executable of plausible size
        if len(data) < _MIN_INSTALLER_SIZE or data[:2] != b"MZ":
            log.error("Downloaded update failed integrity check (size=%d)", len(data))
            return False

        installer_path = os.path.join(tempfile.gettempdir(), "Envelop_Setup_update.exe")
        with open(installer_path, "wb") as f:
            f.write(data)

        subprocess.Popen(
            [installer_path, "/VERYSILENT", "/SUPPRESSMSGBOXES", "/NORESTART",
             "/CLOSEAPPLICATIONS", "/RESTARTAPPLICATIONS"],
            close_fds=True,
        )
        log.info("Update installer launched: %s", installer_path)
        return True
    except Exception as e:
        log.error("Update download/install failed: %s", e)
        return False
