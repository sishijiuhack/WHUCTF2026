#!/bin/sh
set -eu

MYSQL_HOST="${MYSQL_HOST:-127.0.0.1}"
MYSQL_PORT="${MYSQL_PORT:-3306}"
MYSQL_DATABASE="${MYSQL_DATABASE:-ctf_challenge}"
MYSQL_USER="${MYSQL_USER:-ctf_user}"
MYSQL_PASSWORD="${MYSQL_PASSWORD:-ctf_pass}"
MYSQL_SOCKET="/run/mysqld/mysqld.sock"
FLAG_VALUE="${GZCTF_FLAG:-whuctf{default}}"

mkdir -p /run/mysqld /var/lib/mysql
chown -R mysql:mysql /run/mysqld /var/lib/mysql

if [ ! -d /var/lib/mysql/mysql ]; then
    mariadb-install-db --user=mysql --datadir=/var/lib/mysql >/dev/null

    mariadbd \
        --user=mysql \
        --datadir=/var/lib/mysql \
        --socket="${MYSQL_SOCKET}" \
        --pid-file=/run/mysqld/mysqld.pid \
        --skip-networking \
        --skip-grant-tables \
        --character-set-server=utf8mb4 \
        --collation-server=utf8mb4_unicode_ci &
    bootstrap_pid="$!"

    until mariadb-admin --socket="${MYSQL_SOCKET}" ping >/dev/null 2>&1; do
        sleep 1
    done

    mariadb --socket="${MYSQL_SOCKET}" <<SQL
CREATE DATABASE IF NOT EXISTS \`${MYSQL_DATABASE}\` CHARACTER SET utf8mb4 COLLATE utf8mb4_unicode_ci;
SQL

    kill "${bootstrap_pid}"
    wait "${bootstrap_pid}"
fi

printf "%s" "${FLAG_VALUE}" > /flag
chmod 444 /flag

mariadbd \
    --user=mysql \
    --bind-address="${MYSQL_HOST}" \
    --port="${MYSQL_PORT}" \
    --datadir=/var/lib/mysql \
    --socket="${MYSQL_SOCKET}" \
    --pid-file=/run/mysqld/mysqld.pid \
    --skip-grant-tables \
    --character-set-server=utf8mb4 \
    --collation-server=utf8mb4_unicode_ci &
mysql_pid="$!"

cleanup() {
    kill "${mysql_pid}" >/dev/null 2>&1 || true
    wait "${mysql_pid}" >/dev/null 2>&1 || true
}

trap cleanup INT TERM EXIT

until mariadb-admin --host=127.0.0.1 --port="${MYSQL_PORT}" ping >/dev/null 2>&1; do
    sleep 1
done

mariadb --host=127.0.0.1 --port="${MYSQL_PORT}" <<SQL
CREATE DATABASE IF NOT EXISTS \`${MYSQL_DATABASE}\` CHARACTER SET utf8mb4 COLLATE utf8mb4_unicode_ci;
SQL

exec python /app/app.py
