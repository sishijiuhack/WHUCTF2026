FROM node:20-bullseye

ENV DEBIAN_FRONTEND=noninteractive
ENV NEXT_TELEMETRY_DISABLED=1

RUN apt-get update \
    && apt-get install -y --no-install-recommends \
        php-cli \
        php-curl \
        supervisor \
    && rm -rf /var/lib/apt/lists/*

WORKDIR /app

COPY next-app/package.json /app/next-app/package.json
RUN cd /app/next-app && npm install

COPY . /app
RUN mkdir -p /var/www/html \
    && cp -r /app/ssrf/. /var/www/html/ \
    && cd /app/next-app && npm run build \
    && chmod +x /app/docker/entrypoint.sh

EXPOSE 3000

ENTRYPOINT ["/app/docker/entrypoint.sh"]
