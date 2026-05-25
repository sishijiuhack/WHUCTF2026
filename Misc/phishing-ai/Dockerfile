FROM python:3.10-slim

WORKDIR /app

# 安装依赖
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt -i https://mirrors.aliyun.com/pypi/simple/

# 复制应用代码
COPY . .

# 创建必要目录，收紧 app.py 权限（仅 root 可读），创建非特权用户
RUN mkdir -p /app/articles /app/data /app/writable /app/replies /app/plugins /app/static \
    && touch /app/plugins/__init__.py \
    && adduser --disabled-password --gecos "" appuser \
    && chown -R appuser:appuser /app/data /app/writable /app/replies /app/articles

# 设置启动脚本
COPY flag.sh /flag.sh
RUN chmod +x /flag.sh

# 运行时通过环境变量注入 IFLOW_API_KEY

EXPOSE 5000

CMD ["/flag.sh"]