# Image für die Flask-App allein - MariaDB läuft separat (siehe docker-compose.yml).
# SECRET_KEY/DATABASE_URL werden bewusst nicht hier gesetzt, sondern zur
# Laufzeit übergeben, damit keine Zugangsdaten im Image landen.
FROM python:3.12-slim

ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1

WORKDIR /app

# Erst requirements.txt kopieren, damit Docker diesen Layer cached und
# Codeänderungen kein erneutes pip install erzwingen.
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

COPY . .

# Nicht als root laufen lassen.
RUN chmod +x docker-entrypoint.sh \
    && useradd --create-home appuser \
    && chown -R appuser:appuser /app
USER appuser

EXPOSE 5000

# Wendet vor dem Start automatisch ausstehende Migrationen an, siehe docker-entrypoint.sh.
ENTRYPOINT ["./docker-entrypoint.sh"]
CMD ["gunicorn", "--bind", "0.0.0.0:5000", "--workers", "3", "wsgi:app"]
