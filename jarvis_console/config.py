"""Environment-backed configuration with explicit status/launch URL separation."""

from __future__ import annotations

import os
from dataclasses import dataclass
from urllib.parse import urlsplit


@dataclass(frozen=True)
class ServiceConfig:
    key: str
    name: str
    status_url: str | None
    launch_url: str | None


@dataclass(frozen=True)
class Config:
    host: str
    port: int
    timeout_seconds: float
    morning_brief_url: str
    morning_brief_timeout_seconds: float
    services: tuple[ServiceConfig, ...]


def _url(name: str, default: str) -> str:
    value = os.environ.get(name, default)
    parsed = urlsplit(value)
    if (parsed.scheme not in {"http", "https"} or not parsed.hostname
            or parsed.username or parsed.password or parsed.fragment):
        raise ValueError(f"{name} must be an HTTP(S) URL without credentials or a fragment")
    return value


def _status_url(name: str, default: str) -> str:
    value = _url(name, default)
    parsed = urlsplit(value)
    if parsed.query:
        raise ValueError(f"{name} must not contain a query string")
    return value


def load_config() -> Config:
    try:
        port = int(os.environ.get("HTTP_PORT", "8080"))
        timeout = float(os.environ.get("STATUS_TIMEOUT_SECONDS", "2"))
        morning_timeout = float(os.environ.get("MORNING_BRIEF_TIMEOUT_SECONDS", "300"))
    except ValueError as exc:
        raise ValueError("HTTP_PORT and timeout settings must be numeric") from exc
    if not 1 <= port <= 65535:
        raise ValueError("HTTP_PORT must be between 1 and 65535")
    if not 0.1 <= timeout <= 10:
        raise ValueError("STATUS_TIMEOUT_SECONDS must be between 0.1 and 10")
    if not 0.1 <= morning_timeout <= 600:
        raise ValueError("MORNING_BRIEF_TIMEOUT_SECONDS must be between 0.1 and 600")

    morning_brief_url = _status_url(
        "MORNING_BRIEF_URL", "http://receipt-service:8080/print/morning"
    )

    services = (
        ServiceConfig(
            "receipt", "Receipt",
            _status_url("RECEIPT_STATUS_URL", "http://receipt-service:8080/health"),
            None,
        ),
        ServiceConfig(
            "label", "Label",
            _status_url("LABEL_STATUS_URL", "http://jarvis.home:5050/health"),
            _url("LABEL_LAUNCH_URL", "http://label.jarvis.home/print"),
        ),
        ServiceConfig(
            "jeopardy", "Jeopardy",
            _status_url("JEOPARDY_STATUS_URL", "http://jeopardy-service:8080/health"),
            _url("JEOPARDY_LAUNCH_URL", "http://jeopardy.home/"),
        ),
        ServiceConfig(
            "triviarom", "TriviaROM",
            _status_url("TRIVIAROM_STATUS_URL", "http://triviarom-service:8080/health"),
            _url("TRIVIAROM_LAUNCH_URL", "http://jarvis.home:8790/"),
        ),
        ServiceConfig(
            "jellyfin", "Jellyfin", None,
            _url("JELLYFIN_LAUNCH_URL", "http://jellyfin.jarvis.home/"),
        ),
    )
    return Config(
        os.environ.get("HTTP_HOST", "0.0.0.0"), port, timeout,
        morning_brief_url, morning_timeout, services,
    )
