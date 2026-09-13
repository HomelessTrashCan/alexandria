from flask import current_app
from flask_mail import Message

from backend.app.extensions import mail


def send_email(to: str, subject: str, body: str) -> None:
    """Versendet eine E-Mail über SMTP, sofern MAIL_SERVER konfiguriert ist.

    Ohne SMTP-Konfiguration (lokale Entwicklung) wird der Inhalt stattdessen
    auf der Konsole ausgegeben, damit Bestätigungs-/Reset-Links trotzdem
    nutzbar sind. print() statt logging, damit die Ausgabe unabhaengig von
    der Logging-Konfiguration (Level, Handler) zuverlaessig sichtbar ist.
    """
    if not current_app.config.get("MAIL_SERVER"):
        print(f"\n----- E-MAIL (kein SMTP konfiguriert) -----\nAn: {to}\nBetreff: {subject}\n\n{body}\n---------------------------------------------\n", flush=True)
        return

    message = Message(subject=subject, recipients=[to], body=body)
    mail.send(message)
