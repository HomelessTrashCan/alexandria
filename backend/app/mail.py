import logging

from flask import current_app
from flask_mail import Message

from backend.app.extensions import mail

logger = logging.getLogger(__name__)


def send_email(to: str, subject: str, body: str) -> None:
    """Versendet eine E-Mail über SMTP, sofern MAIL_SERVER konfiguriert ist.

    Ohne SMTP-Konfiguration (lokale Entwicklung) wird der Inhalt stattdessen
    geloggt, damit Bestätigungs-/Reset-Links trotzdem nutzbar sind.
    """
    if not current_app.config.get("MAIL_SERVER"):
        logger.info("MAIL_SERVER nicht konfiguriert - E-Mail wird nur geloggt.\nAn: %s\nBetreff: %s\n%s", to, subject, body)
        return

    message = Message(subject=subject, recipients=[to], body=body)
    mail.send(message)
