"""Semavox device-status adapter."""

from __future__ import annotations

import re

from jarvis_console.config import ServiceConfig
from .common import StatusRequestError, fetch_json, result

STATUS_PATTERN = re.compile(
    r"ONLINE \| IP: (?P<ip>[^ |]+) \| Uptime: (?P<uptime>[0-9]+) seconds\Z"
)


def check(config: ServiceConfig, timeout: float) -> dict:
    try:
        http_status, payload = fetch_json(config.status_url, timeout)
        message = payload.get("message")
        match = STATUS_PATTERN.fullmatch(message) if isinstance(message, str) else None
        volume = payload.get("volume")
        label = payload.get("label")
        if (http_status != 200 or match is None
                or type(payload.get("audio")) is not bool
                or type(volume) is not int or not 0 <= volume <= 100
                or type(payload.get("startupChime")) is not bool
                or not isinstance(label, str) or not 1 <= len(label) <= 32):
            raise StatusRequestError(
                "Semavox status response did not match its accepted contract"
            )
        details = {
            "uptime_seconds": int(match.group("uptime")),
            "audio_ready": payload["audio"],
            "volume_percent": volume,
            "startup_chime": payload["startupChime"],
            "label": label,
        }
        summary = (
            "Device API responding"
            if payload["audio"] else "Device API responding; audio unavailable"
        )
        return result(
            config.key, config.name, "healthy", summary, config.launch_url, details
        )
    except StatusRequestError as exc:
        return result(config.key, config.name, "unknown", str(exc), config.launch_url)
