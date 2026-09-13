#!/bin/sh
# Wendet vor dem Start (CMD, meist gunicorn) automatisch ausstehende Migrationen an.
set -e

# Wiederholt "flask db upgrade" statt beim ersten Fehlschlag aufzugeben: der
# DB-Healthcheck bestätigt nur, dass MariaDB innerhalb ihres eigenen Containers
# antwortet, das Docker-Netzwerk zwischen den Containern kann kurz danach noch
# hinterherhinken.
attempt=1
max_attempts=10
until flask db upgrade; do
    if [ "$attempt" -ge "$max_attempts" ]; then
        echo "Datenbank nach $max_attempts Versuchen weiterhin nicht erreichbar - breche ab." >&2
        exit 1
    fi
    echo "Datenbank noch nicht bereit (Versuch $attempt/$max_attempts) - warte 2s..."
    attempt=$((attempt + 1))
    sleep 2
done

exec "$@"
