FROM python:3.11-slim

WORKDIR /app

ENV PASSWORD_PEPPER="kaffuchinokawayi"
ENV SECRET_KEY="great_chino"

RUN apt-get update \
    && DEBIAN_FRONTEND=noninteractive apt-get install -y --no-install-recommends \
        mariadb-server \
        unzip \
        zip \
    && rm -rf /var/lib/apt/lists/*

COPY requirements.txt /app/requirements.txt
RUN pip install --no-cache-dir -r /app/requirements.txt

COPY . /app

RUN chmod +x /app/entrypoint.sh \
    && mkdir -p /app/static/avatars /app/static/images /app/static/uploads /run/mysqld \
    && chown -R mysql:mysql /run/mysqld /var/lib/mysql

EXPOSE 5000

ENTRYPOINT ["/app/entrypoint.sh"]
