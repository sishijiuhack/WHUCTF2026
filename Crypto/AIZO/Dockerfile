FROM python:3.11-slim-bookworm

ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1

RUN set -eux; \
    if [ -f /etc/apt/sources.list ]; then \
      sed -i 's|deb.debian.org|mirrors.tuna.tsinghua.edu.cn|g; s|security.debian.org|mirrors.tuna.tsinghua.edu.cn/debian-security|g' /etc/apt/sources.list; \
    fi; \
    if [ -f /etc/apt/sources.list.d/debian.sources ]; then \
      sed -i 's|http://deb.debian.org/debian|https://mirrors.tuna.tsinghua.edu.cn/debian|g; s|http://security.debian.org/debian-security|https://mirrors.tuna.tsinghua.edu.cn/debian-security|g' /etc/apt/sources.list.d/debian.sources; \
    fi; \
    apt-get update -o Acquire::Retries=5 \
    && apt-get install -y --no-install-recommends socat \
    && rm -rf /var/lib/apt/lists/*

WORKDIR /app

COPY chall.py secret.py /app/

RUN pip install --no-cache-dir -i https://pypi.tuna.tsinghua.edu.cn/simple pycryptodome sympy

RUN useradd -m -u 1000 ctf
USER ctf

EXPOSE 9999

CMD ["socat", "TCP-LISTEN:9999,reuseaddr,fork", "EXEC:'timeout 180 python3 -u /app/chall.py',pty,stderr,setsid,sigint,sane"]
