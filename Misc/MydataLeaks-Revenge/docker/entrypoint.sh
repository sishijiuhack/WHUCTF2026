#!/bin/sh
set -eu

cd /app/challenge

if [ -f /app/challenge/inject_flag.py ]; then
    python /app/challenge/inject_flag.py
fi

exec "$@"