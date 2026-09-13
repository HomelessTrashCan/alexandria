-- Läuft nur beim allerersten Start (leeres Datenvolume), wie alles unter
-- /docker-entrypoint-initdb.d/. MARIADB_DATABASE legt nur "cmdb" an, dieses
-- Skript ergänzt "cmdb_test" für die pytest-Suite.
--
-- Benutzername bewusst fest "cmdb_user" (kein ${MARIADB_USER}-Platzhalter
-- möglich, reines SQL wird nicht durch docker compose ersetzt) - von Hand
-- anpassen, falls MARIADB_USER in .env je geändert wird.
CREATE DATABASE IF NOT EXISTS cmdb_test;
GRANT ALL PRIVILEGES ON cmdb_test.* TO 'cmdb_user'@'%';
FLUSH PRIVILEGES;
