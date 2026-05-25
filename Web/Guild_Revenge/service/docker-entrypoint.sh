#!/bin/sh

# 在无debug参数下启动flask
cd /app && gosu nobody "python" "main.py"
