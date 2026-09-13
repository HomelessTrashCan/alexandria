# Produktions-Image fuer die Flask-App. Die MariaDB selbst laeuft in einem
# eigenen Container (siehe README/.env.example) - dieses Image enthaelt nur
# die Anwendung. SECRET_KEY/DATABASE_URL etc. werden bewusst NICHT hier
# gesetzt, sondern zur Laufzeit per --env-file/-e uebergeben, damit keine
# Zugangsdaten im Image landen (siehe .env.example fuer die noetigen Variablen).
FROM python:3.12-slim

# Kein .pyc-Muell im Image, und Logs landen sofort in stdout/stderr statt
# gepuffert zu werden (sonst sieht man Ausgaben bei "docker logs" verspaetet).
ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1

WORKDIR /app

# Erst nur requirements.txt kopieren: Docker cached diesen Layer, solange sich
# die Datei nicht aendert - Codeaenderungen erzwingen dann kein erneutes
# pip install bei jedem Build.
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

COPY . .

# Nicht als root laufen lassen (Least Privilege).
RUN chmod +x docker-entrypoint.sh \
    && useradd --create-home appuser \
    && chown -R appuser:appuser /app
USER appuser

EXPOSE 5000

# Wendet beim Containerstart automatisch ausstehende Migrationen an (flask db
# upgrade), bevor der eigentliche Prozess (gunicorn) startet - siehe
# docker-entrypoint.sh.
ENTRYPOINT ["./docker-entrypoint.sh"]
CMD ["gunicorn", "--bind", "0.0.0.0:5000", "--workers", "3", "wsgi:app"]
