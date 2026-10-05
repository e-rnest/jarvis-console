FROM python:3.12-slim

ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1

WORKDIR /app
COPY jarvis_console /app/jarvis_console
COPY web /app/web

RUN useradd --create-home --uid 10001 console
USER console

EXPOSE 8080
CMD ["python", "-m", "jarvis_console"]
