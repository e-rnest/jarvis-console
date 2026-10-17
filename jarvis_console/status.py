"""Concurrent, failure-isolated downstream status aggregation."""

from __future__ import annotations

from concurrent.futures import ThreadPoolExecutor, as_completed
from datetime import datetime, timezone

from .clients import blacktorrent, jeopardy, label, receipt, triviarom
from .clients.common import result
from .config import Config, ServiceConfig

ADAPTERS = {
    "receipt": receipt.check,
    "label": label.check,
    "jeopardy": jeopardy.check,
    "triviarom": triviarom.check,
    "blacktorrent": blacktorrent.check,
}


def _unexpected(config: ServiceConfig) -> dict:
    return result(config.key, config.name, "unknown",
                  "Status check failed unexpectedly", config.launch_url)


def aggregate(config: Config) -> dict:
    services: dict[str, dict] = {}
    checked = [service for service in config.services if service.status_url is not None]
    with ThreadPoolExecutor(max_workers=len(checked), thread_name_prefix="status") as executor:
        futures = {
            executor.submit(ADAPTERS[service.key], service, config.timeout_seconds): service
            for service in checked
        }
        for future in as_completed(futures):
            service = futures[future]
            try:
                services[service.key] = future.result()
            except Exception:
                services[service.key] = _unexpected(service)

    for service in config.services:
        if service.status_url is None:
            services[service.key] = result(
                service.key, service.name, "unavailable",
                "Health status is not available", service.launch_url,
            )
    ordered = [services[service.key] for service in config.services]
    return {
        "generated_at": datetime.now(timezone.utc).isoformat(),
        "services": ordered,
    }
