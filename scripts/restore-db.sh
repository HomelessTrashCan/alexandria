#!/bin/sh
# Spielt ein mit backup-db.sh erstelltes Backup zurück in die laufende MariaDB.
#
# Nutzung: ./scripts/restore-db.sh backups/cmdb-20260101-020000.sql.gz
set -eu

FILE="${1:-}"
if [ -z "$FILE" ] || [ ! -f "$FILE" ]; then
    echo "Nutzung: $0 <backup-datei.sql.gz>" >&2
    exit 1
fi

PROJECT_DIR="$(cd "$(dirname "$0")/.." && pwd)"

set -a
# shellcheck disable=SC1091
. "$PROJECT_DIR/.env"
set +a

echo "Stelle $FILE in Datenbank '$MARIADB_DATABASE' wieder her..."
gunzip -c "$FILE" | docker compose -f "$PROJECT_DIR/docker-compose.yml" exec -T db \
  mariadb -u"$MARIADB_USER" -p"$MARIADB_PASSWORD" "$MARIADB_DATABASE"

echo "Wiederhergestellt aus: $FILE"
