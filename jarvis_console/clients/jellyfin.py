"""Jellyfin public system-information adapter."""

from jarvis_console.config import ServiceConfig
from .common import StatusRequestError, fetch_json, result


def check(config: ServiceConfig, timeout: float) -> dict:
    try:
        http_status, payload = fetch_json(config.status_url, timeout)
        server_name = payload.get("ServerName")
        version = payload.get("Version")
        product_name = payload.get("ProductName")
        server_id = payload.get("Id")
        setup_complete = payload.get("StartupWizardCompleted")
        if (http_status != 200 or product_name != "Jellyfin"
                or not isinstance(server_name, str) or not server_name
                or not isinstance(version, str) or not version
                or not isinstance(server_id, str) or not server_id
                or type(setup_complete) is not bool):
            raise StatusRequestError(
                "Jellyfin system response did not match its accepted contract"
            )
        details = {"server_name": server_name, "version": version}
        if not setup_complete:
            return result(
                config.key, config.name, "failed", "Startup wizard is incomplete",
                config.launch_url, details,
            )
        return result(
            config.key, config.name, "healthy", "Media server API responding",
            config.launch_url, details,
        )
    except StatusRequestError as exc:
        return result(config.key, config.name, "unknown", str(exc), config.launch_url)
