"""BlackTorrent qBittorrent WebUI reachability adapter."""

from urllib.error import HTTPError
from urllib.request import Request, urlopen

from jarvis_console.config import ServiceConfig
from .common import result


def check(config: ServiceConfig, timeout: float) -> dict:
    request = Request(config.status_url, headers={
        "Accept": "text/html,application/xhtml+xml",
        "User-Agent": "jarvis-console/1.0",
    })
    try:
        with urlopen(request, timeout=timeout) as response:
            status = response.status
    except HTTPError as exc:
        return result(
            config.key, config.name, "unknown",
            f"qBittorrent WebUI returned HTTP {exc.code}", config.launch_url,
        )
    except OSError:
        return result(
            config.key, config.name, "unknown",
            "qBittorrent WebUI could not be reached", config.launch_url,
        )
    if not 200 <= status < 300:
        return result(
            config.key, config.name, "unknown",
            f"qBittorrent WebUI returned HTTP {status}", config.launch_url,
        )
    return result(
        config.key, config.name, "healthy",
        "qBittorrent WebUI reachable", config.launch_url,
    )
