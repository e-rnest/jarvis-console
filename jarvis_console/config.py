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
    secondary_links: tuple[tuple[str, str], ...] = ()
    status_bearer_token: str | None = None


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
            or parsed.username or parsed.password):
        raise ValueError(f"{name} must be an HTTP(S) URL without credentials")
    return value


def _status_url(name: str, default: str) -> str:
    value = _url(name, default)
    parsed = urlsplit(value)
    if parsed.query or parsed.fragment:
        raise ValueError(f"{name} must not contain a query string or fragment")
    return value


def _optional_token(name: str) -> str | None:
    value = os.environ.get(name, "").strip()
    if not value:
        return None
    if len(value) > 4096 or any(not 33 <= ord(character) <= 126 for character in value):
        raise ValueError(f"{name} must contain printable non-whitespace ASCII")
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

    home_assistant_token = _optional_token("HOME_ASSISTANT_TOKEN")
    services = (
        ServiceConfig(
            "homeassistant", "Home Assistant",
            _status_url("HOME_ASSISTANT_STATUS_URL", "http://192.168.1.100:8123/api/")
            if home_assistant_token else None,
            _url("HOME_ASSISTANT_LAUNCH_URL", "http://ha.jarvis.home/"),
            (
                ("Short alias", _url(
                    "HOME_ASSISTANT_SHORT_URL", "http://ha.home/",
                )),
                ("Direct", _url(
                    "HOME_ASSISTANT_DIRECT_URL", "http://192.168.1.100:8123/",
                )),
            ),
            home_assistant_token,
        ),
        ServiceConfig(
            "receipt", "Receipt Service",
            _status_url("RECEIPT_STATUS_URL", "http://receipt-service:8080/health"),
            None,
            (("GitHub", _url(
                "RECEIPT_REPOSITORY_URL",
                "https://github.com/e-rnest/receipt-service",
            )),),
        ),
        ServiceConfig(
            "label", "Label",
            _status_url("LABEL_STATUS_URL", "http://jarvis.home:5050/health"),
            _url("LABEL_LAUNCH_URL", "http://label.jarvis.home/print"),
            (
                ("Quick Labels", _url(
                    "LABEL_QUICK_LABELS_URL", "http://label.jarvis.home/labels",
                )),
                ("Fridge", _url(
                    "LABEL_FRIDGE_URL", "http://label.jarvis.home/inventory",
                )),
                ("Freezer", _url(
                    "LABEL_FREEZER_URL",
                    "http://label.jarvis.home/inventory/frozen",
                )),
            ),
        ),
        ServiceConfig(
            "manifest", "Manifest",
            _status_url("MANIFEST_STATUS_URL", "http://manifest.home/health"),
            _url("MANIFEST_LAUNCH_URL", "http://manifest.home/"),
        ),
        ServiceConfig(
            "jeopardy", "Jeopardy",
            _status_url("JEOPARDY_STATUS_URL", "http://jeopardy-service:8080/health"),
            _url("JEOPARDY_LAUNCH_URL", "http://jeopardy.home/"),
        ),
        ServiceConfig(
            "triviarom", "TriviaROM",
            _status_url("TRIVIAROM_STATUS_URL", "http://triviarom-service:8080/health"),
            _url("TRIVIAROM_LAUNCH_URL", "http://trivia.jarvis.home/"),
        ),
        ServiceConfig(
            "wallboard", "Wallboard",
            _status_url("WALLBOARD_STATUS_URL", "http://wallboard.home/health"),
            _url("WALLBOARD_LAUNCH_URL", "http://wallboard.home/"),
        ),
        ServiceConfig(
            "blacktorrent", "BlackTorrent",
            _status_url("BLACKTORRENT_STATUS_URL", "http://192.168.1.100:8080/"),
            _url("BLACKTORRENT_LAUNCH_URL", "http://blacktorrent.home/"),
            (("Backup", _url(
                "BLACKTORRENT_BACKUP_URL",
                "http://blacktorrent.jarvis.home/",
            )),),
        ),
        ServiceConfig(
            "jellyfin", "Jellyfin",
            _status_url(
                "JELLYFIN_STATUS_URL",
                "http://192.168.1.100:8096/System/Info/Public",
            ),
            _url("JELLYFIN_LAUNCH_URL", "http://jellyfin.home"),
            (("TV Guide", _url(
                "JELLYFIN_TV_GUIDE_URL",
                "http://jellyfin.home/web/#/livetv?collectionType=livetv&tab=1",
            )),),
        ),
        ServiceConfig(
            "semavox", "Semavox",
            _status_url("SEMAVOX_STATUS_URL", "http://semavox.home/api/status"),
            _url("SEMAVOX_LAUNCH_URL", "http://semavox.home"),
            (
                ("Fixed IP", _url(
                    "SEMAVOX_FALLBACK_URL", "http://192.168.1.80",
                )),
                ("GitHub", _url(
                    "SEMAVOX_REPOSITORY_URL",
                    "https://github.com/e-rnest/semavox",
                )),
            ),
        ),
    )
    return Config(
        os.environ.get("HTTP_HOST", "0.0.0.0"), port, timeout,
        morning_brief_url, morning_timeout, services,
    )
