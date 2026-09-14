#!/bin/sh
# Sichert die MariaDB-Datenbank aus dem laufenden docker-compose-Container.
#
# mariadb-dump statt eigener Dump-Logik: das Standardwerkzeug für MariaDB-
# Backups, erzeugt ein direkt wiederherstellbares SQL-Abbild. "-T" deaktiviert
# die Pseudo-TTY-Allokation, die die Ausgabe sonst verfälschen würde.
#
# Nutzung: ./scripts/backup-db.sh
# Regelmässig via Cron, z. B. täglich um 02:00 Uhr:
#   0 2 * * * cd /pfad/zum/projekt && ./scripts/backup-db.sh >> /var/log/alexandria-backup.log 2>&1
set -eu

PROJECT_DIR="$(cd "$(dirname "$0")/.." && pwd)"
BACKUP_DIR="$PROJECT_DIR/backups"
RETENTION_DAYS=14

# Zugangsdaten stammen aus derselben .env, die auch docker-compose.yml nutzt.
set -a
# shellcheck disable=SC1091
. "$PROJECT_DIR/.env"
set +a

mkdir -p "$BACKUP_DIR"
TIMESTAMP="$(date +%Y%m%d-%H%M%S)"
TARGET="$BACKUP_DIR/${MARIADB_DATABASE}-$TIMESTAMP.sql.gz"

docker compose -f "$PROJECT_DIR/docker-compose.yml" exec -T db \
  mariadb-dump -u"$MARIADB_USER" -p"$MARIADB_PASSWORD" --single-transaction "$MARIADB_DATABASE" \
  | gzip > "$TARGET"

echo "Backup gespeichert: $TARGET"

# Alte Backups aufräumen, damit der Datenträger nicht unbegrenzt wächst.
find "$BACKUP_DIR" -name "${MARIADB_DATABASE}-*.sql.gz" -mtime "+$RETENTION_DAYS" -delete
