-- Wird vom offiziellen mariadb-Image automatisch beim ALLERERSTEN Start
-- ausgefuehrt (jedes Skript in /docker-entrypoint-initdb.d/, alphabetisch
-- sortiert - daher die Nummer im Dateinamen), aber NUR wenn das Datenvolume
-- noch leer ist. MARIADB_DATABASE/-USER/-PASSWORD (siehe docker-compose.yml)
-- legen bereits die Datenbank "cmdb" samt Benutzer an; dieses Skript ergaenzt
-- die zweite, fuer die pytest-Suite benoetigte Datenbank "cmdb_test" (siehe
-- backend/app/config.py, TestConfig) - ohne dieses Skript wuerde MariaDB
-- nur "cmdb" kennen und Tests haetten keine Datenbank zum Verbinden.
--
-- Der Benutzername ist hier bewusst fest "cmdb_user" (kein ${MARIADB_USER}-
-- Platzhalter moeglich, reines SQL wird nicht durch docker compose ersetzt) -
-- muss von Hand mitgepflegt werden, falls MARIADB_USER in .env jemals
-- geaendert wird.
CREATE DATABASE IF NOT EXISTS cmdb_test;
GRANT ALL PRIVILEGES ON cmdb_test.* TO 'cmdb_user'@'%';
FLUSH PRIVILEGES;
