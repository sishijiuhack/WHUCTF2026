#!/bin/sh
set -eu

FLAG_VALUE="${GZCTF_FLAG:-WHUCTF{default}}"
printf '%s' "$FLAG_VALUE" > /flag
chmod 444 /flag

exec "$@"
