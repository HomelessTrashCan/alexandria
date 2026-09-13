from flask import current_app
from flask_mail import Message

from backend.app.extensions import mail


def send_email(to: str, subject: str, body: str) -> None:
    """Versendet eine E-Mail über SMTP, sofern MAIL_SERVER konfiguriert ist - sonst landet der Inhalt auf der Konsole (lokale Entwicklung ohne Mailserver)."""
    if not current_app.config.get("MAIL_SERVER"):
        print(f"\n----- E-MAIL (kein SMTP konfiguriert) -----\nAn: {to}\nBetreff: {subject}\n\n{body}\n---------------------------------------------\n", flush=True)
        return

    message = Message(subject=subject, recipients=[to], body=body)
    mail.send(message)
