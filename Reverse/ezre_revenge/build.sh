#!/usr/bin/env bash
set -euo pipefail

cd "$(dirname "$0")"

mkdir -p bin

gcc -Wall -Wextra -std=c11 -O2 -static -s \
    -o bin/ezre_revenge_unpacked \
    src/main.c src/vm.c src/aes128.c \
    -Wl,--whole-archive \
    /usr/lib/x86_64-linux-gnu/libcrypto.a \
    /usr/lib/x86_64-linux-gnu/libssl.a \
    /usr/lib/x86_64-linux-gnu/libz.a \
    -Wl,--no-whole-archive \
    -ldl -pthread

./upx bin/ezre_revenge_unpacked -o bin/ezre_revenge

rm bin/ezre_revenge_unpacked

perl -0pi -e 's/UPX!/VVM!/g' bin/ezre_revenge
