#!/bin/sh
# 写入 flag
FLAG="flag{phi11sh1n9_4tt@ck_i5_l3thal}"
echo "$FLAG" > /flag
chmod 644 /flag

# 将敏感配置写入运行时目录，app.py 从此处读取
mkdir -p /run/secrets
printf '%s' "$FLAG"                  > /run/secrets/flag
printf '%s' "gabe_newell"            > /run/secrets/sys_username
printf '%s' "gabefkingnewell@gmail.com" > /run/secrets/sys_email
printf '%s' "V3x!Q9m#L2t@R7p\$K4n"  > /run/secrets/sys_password
chown appuser:appuser /run/secrets/*
chmod 400 /run/secrets/*

# 创建必要的目录
mkdir -p /app/articles /app/data /app/writable /app/replies /app/plugins /app/static
touch /app/plugins/__init__.py

# 注入 API Key
export IFLOW_API_KEY="sk-f7eb6c920b9d473e86d510f75c5742de"

# 启动应用（以非特权用户运行，无法读取 root-only 文件）
exec gunicorn -w 2 --bind 0.0.0.0:5000 --timeout 120 --user appuser --group appuser app:app
