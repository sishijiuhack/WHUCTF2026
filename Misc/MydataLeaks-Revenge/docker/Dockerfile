FROM python:3.11-slim

ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1

WORKDIR /app

COPY challenge /app/challenge
COPY docker /app/docker
COPY writeup_internal /app/writeup_internal

EXPOSE 8000
ENTRYPOINT ["python", "/app/docker/entrypoint.py"]
