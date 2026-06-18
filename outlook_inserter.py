import logging
import os

log = logging.getLogger("fcf")
ERROR_LOG = os.path.join(os.environ.get("APPDATA", ""), "FCFModeles", "error.log")


def _log_error(msg: str) -> None:
    os.makedirs(os.path.dirname(ERROR_LOG), exist_ok=True)
    with open(ERROR_LOG, "a", encoding="utf-8") as f:
        import datetime
        f.write(f"[{datetime.datetime.now().isoformat()}] {msg}\n")


def insert_into_outlook(body_html: str, subject: str = "") -> tuple[bool, str]:
    try:
        import win32com.client
        try:
            outlook = win32com.client.GetActiveObject("Outlook.Application")
        except Exception:
            return False, "Outlook n'est pas ouvert."

        inspector = outlook.ActiveInspector()
        if inspector is None:
            return False, "Ouvrez ou répondez à un courriel dans Outlook d'abord."

        mail_item = inspector.CurrentItem
        if subject:
            mail_item.Subject = subject

        try:
            word_editor = inspector.WordEditor
            selection = word_editor.Application.Selection
            selection.TypeText("")
            # Insert HTML at cursor via clipboard approach
            existing = mail_item.HTMLBody
            # Find the body tag and insert after it
            import re
            body_match = re.search(r"<body[^>]*>", existing, re.IGNORECASE)
            if body_match:
                insert_pos = body_match.end()
                mail_item.HTMLBody = existing[:insert_pos] + body_html + existing[insert_pos:]
            else:
                mail_item.HTMLBody = body_html + existing
        except Exception:
            mail_item.HTMLBody = body_html + mail_item.HTMLBody

        return True, ""
    except Exception as e:
        msg = f"COM error: {e}"
        log.error(msg)
        _log_error(msg)
        return False, "Une erreur s'est produite. Consultez le journal d'erreurs."
