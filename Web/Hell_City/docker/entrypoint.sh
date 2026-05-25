#!/bin/sh
set -eu

printf '%s\n' "${GZCTF_FLAG}" > /flag
exec /usr/bin/supervisord -c /app/docker/supervisord.conf
