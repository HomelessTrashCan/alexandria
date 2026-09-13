#!/bin/sh
# Wird als ENTRYPOINT ausgefuehrt, bevor CMD (gunicorn) startet.
#
# "flask db upgrade" wendet beim Containerstart automatisch alle noch
# ausstehenden Alembic-Migrationen an, damit ein Deploy nicht zusaetzlich
# einen manuellen Migrationsschritt braucht. Bei genau einer laufenden Instanz
# (wie in diesem Projekt) unproblematisch; bei mehreren gleichzeitig
# startenden Instanzen koennten zwei "upgrade"-Laeufe theoretisch
# kollidieren - fuer den Umfang dieser Praxisarbeit (Einzelinstanz) ist das
# kein relevantes Szenario.
set -e

# Wiederholt "flask db upgrade" ein paar Mal, statt bei einem einzigen
# fehlgeschlagenen Versuch sofort aufzugeben: der Compose-Healthcheck der DB
# bestaetigt zwar, dass MariaDB innerhalb ihres eigenen Containers auf einen
# lokalen Ping antwortet, aber das Docker-Netzwerk zwischen den Containern
# kann im allerersten Moment nach dem Start noch minimal hinterherhinken
# (insbesondere unter Docker Desktop auf Windows) - ohne diese Wiederholung
# wuerde der Container abstuerzen und sich nur durch die "restart:
# unless-stopped"-Policy in docker-compose.yml zufaellig selbst heilen.
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
