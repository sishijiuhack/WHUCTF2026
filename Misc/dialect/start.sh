#!/bin/sh
set -eu

cd /app
FLAG_FILE="${FLAG_FILE:-/app/flag}"
printf '%s\n' "${GZCTF_FLAG:-flag_test_flag}" > "$FLAG_FILE"
chmod 400 "$FLAG_FILE" 2>/dev/null || true

# Drop flag env after materializing file so players must pivot to file path.
unset GZCTF_FLAG || true

exec python /app/server.py