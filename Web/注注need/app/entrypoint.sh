#!/bin/sh
set -eu

MYSQL_HOST="${MYSQL_HOST:-127.0.0.1}"
MYSQL_PORT="${MYSQL_PORT:-3306}"
MYSQL_DATABASE="${MYSQL_DATABASE:-ctf_challenge}"
MYSQL_USER="${MYSQL_USER:-ctf_user}"
MYSQL_PASSWORD="${MYSQL_PASSWORD:-ctf_pass}"
MYSQL_DATA_DIR="${MYSQL_DATA_DIR:-/var/lib/mysql}"
MYSQL_SOCKET="${MYSQL_SOCKET:-/run/mysqld/mysqld.sock}"
MYSQL_PID_FILE="${MYSQL_PID_FILE:-/run/mysqld/mysqld.pid}"

mkdir -p /run/mysqld "$MYSQL_DATA_DIR"
chown -R mysql:mysql /run/mysqld "$MYSQL_DATA_DIR"

if [ ! -d "$MYSQL_DATA_DIR/mysql" ]; then
    mariadb-install-db --user=mysql --datadir="$MYSQL_DATA_DIR" >/dev/null
    mariadbd \
        --user=mysql \
        --datadir="$MYSQL_DATA_DIR" \
        --socket="$MYSQL_SOCKET" \
        --pid-file="$MYSQL_PID_FILE" \
        --skip-networking \
        --skip-grant-tables \
        --character-set-server=utf8mb4 \
        --collation-server=utf8mb4_unicode_ci &
    bootstrap_pid="$!"

    until mariadb-admin --protocol=socket --socket="$MYSQL_SOCKET" ping >/dev/null 2>&1; do
        sleep 1
    done

    mariadb --protocol=socket --socket="$MYSQL_SOCKET" <<SQL
CREATE DATABASE IF NOT EXISTS \`${MYSQL_DATABASE}\`
  CHARACTER SET utf8mb4
  COLLATE utf8mb4_unicode_ci;
SQL

    kill "$bootstrap_pid"
    wait "$bootstrap_pid"
fi

export MYSQL_HOST
export MYSQL_PORT
export MYSQL_DATABASE
export MYSQL_USER
export MYSQL_PASSWORD

echo -n "${GZCTF_FLAG:-whuctf{default}}" > /flag

mariadbd \
    --user=mysql \
    --datadir="$MYSQL_DATA_DIR" \
    --socket="$MYSQL_SOCKET" \
    --pid-file="$MYSQL_PID_FILE" \
    --bind-address="$MYSQL_HOST" \
    --port="$MYSQL_PORT" \
    --skip-grant-tables \
    --character-set-server=utf8mb4 \
    --collation-server=utf8mb4_unicode_ci &
mysql_pid="$!"

cleanup() {
    if [ "${mysql_pid:-}" ]; then
        kill "$mysql_pid" 2>/dev/null || true
        wait "$mysql_pid" 2>/dev/null || true
    fi
}

trap cleanup EXIT INT TERM

until mariadb-admin --host=127.0.0.1 --port="$MYSQL_PORT" ping >/dev/null 2>&1; do
    sleep 1
done

mariadb --host=127.0.0.1 --port="$MYSQL_PORT" <<SQL
CREATE DATABASE IF NOT EXISTS \`${MYSQL_DATABASE}\`
  CHARACTER SET utf8mb4
  COLLATE utf8mb4_unicode_ci;
SQL

exec python /app/app.py
