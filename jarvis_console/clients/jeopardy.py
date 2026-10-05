"""Jeopardy Service health adapter."""

from jarvis_console.config import ServiceConfig
from .common import StatusRequestError, fetch_json, result


def check(config: ServiceConfig, timeout: float) -> dict:
    try:
        http_status, payload = fetch_json(config.status_url, timeout)
        if http_status == 503 and payload.get("error") == "corpus unavailable":
            return result(config.key, config.name, "failed",
                          "Clue corpus unavailable", config.launch_url)
        if http_status != 200 or payload.get("status") != "ok":
            raise StatusRequestError("Jeopardy health response did not match its accepted contract")
        return result(config.key, config.name, "healthy",
                      "Clue corpus responding", config.launch_url)
    except StatusRequestError as exc:
        return result(config.key, config.name, "unknown", str(exc), config.launch_url)
