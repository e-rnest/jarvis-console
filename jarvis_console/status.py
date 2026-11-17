"""Concurrent, failure-isolated downstream status aggregation."""

from __future__ import annotations

from concurrent.futures import ThreadPoolExecutor, as_completed
from datetime import datetime, timezone

from .clients import (
    blacktorrent, homeassistant, jellyfin, jeopardy, label, manifest, receipt,
    semavox, triviarom, wallboard,
)
from .clients.common import result
from .config import Config, ServiceConfig

ADAPTERS = {
    "homeassistant": homeassistant.check,
    "receipt": receipt.check,
    "label": label.check,
    "manifest": manifest.check,
    "jeopardy": jeopardy.check,
    "triviarom": triviarom.check,
    "wallboard": wallboard.check,
    "blacktorrent": blacktorrent.check,
    "semavox": semavox.check,
    "jellyfin": jellyfin.check,
}


def _unexpected(config: ServiceConfig) -> dict:
    return _with_secondary_links(config, result(
        config.key, config.name, "unknown",
        "Status check failed unexpectedly", config.launch_url,
    ))


def _with_secondary_links(config: ServiceConfig, service: dict) -> dict:
    if config.secondary_links:
        service["secondary_links"] = [
            {"label": label, "url": url}
            for label, url in config.secondary_links
        ]
    return service


def aggregate(config: Config) -> dict:
    services: dict[str, dict] = {}
    checked = [service for service in config.services if service.status_url is not None]
    receipt_checked = any(service.key == "receipt" for service in checked)
    printers_url = config.receipt_printers_url if receipt_checked else None
    with ThreadPoolExecutor(max_workers=len(checked) + 1,
                            thread_name_prefix="status") as executor:
        # One request per snapshot; Receipt caches the real printer check.
        printers = (executor.submit(receipt.printers, printers_url,
                                    config.timeout_seconds)
                    if printers_url else None)
        futures = {
            executor.submit(ADAPTERS[service.key], service, config.timeout_seconds): service
            for service in checked
        }
        for future in as_completed(futures):
            service = futures[future]
            try:
                services[service.key] = _with_secondary_links(service, future.result())
            except Exception:
                services[service.key] = _unexpected(service)

        if printers is not None:
            # Printer status is extra detail. It never changes Receipt's badge.
            try:
                services["receipt"]["printers"] = printers.result()
            except Exception:
                services["receipt"]["printers"] = None

    for service in config.services:
        if service.status_url is None:
            services[service.key] = _with_secondary_links(service, result(
                service.key, service.name, "unavailable",
                "Health status is not available", service.launch_url,
            ))
    ordered = [services[service.key] for service in config.services]
    return {
        "generated_at": datetime.now(timezone.utc).isoformat(),
        "services": ordered,
    }
