"""Authenticated Home Assistant API status adapter."""

from jarvis_console.config import ServiceConfig
from .common import StatusRequestError, fetch_json, result


def check(config: ServiceConfig, timeout: float) -> dict:
    try:
        if not config.status_bearer_token:
            raise StatusRequestError("Home Assistant status token is not configured")
        http_status, payload = fetch_json(
            config.status_url,
            timeout,
            {"Authorization": f"Bearer {config.status_bearer_token}"},
        )
        if http_status != 200 or payload != {"message": "API running."}:
            raise StatusRequestError(
                "Home Assistant API response did not match its accepted contract"
            )
        return result(
            config.key, config.name, "healthy", "Authenticated API responding",
            config.launch_url,
        )
    except StatusRequestError as exc:
        return result(config.key, config.name, "unknown", str(exc), config.launch_url)
