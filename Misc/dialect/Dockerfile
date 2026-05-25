FROM python:3.11-slim

WORKDIR /app

COPY . /app

RUN useradd -m -u 10001 ctf \
    && chown -R ctf:ctf /app \
    && chmod +x /app/start.sh

USER ctf

EXPOSE 9999

ENV PYTHONUNBUFFERED=1

CMD ["/app/start.sh"]
