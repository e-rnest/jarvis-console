"""Receipt Service health adapter."""

from __future__ import annotations

from datetime import date
import re

from jarvis_console.config import ServiceConfig
from .common import StatusRequestError, fetch_json, result

TIME_PATTERN = re.compile(r"(?:[01][0-9]|2[0-3]):[0-5][0-9]\Z")
SCHEDULE_STATES = {"never", "claimed", "sent", "failed"}


def _details(payload: dict) -> dict:
    required = {
        "status", "service", "timezone", "printing", "schedule_enabled",
        "morning_time", "schedule", "scheduler_error",
    }
    if not required <= payload.keys() or payload["service"] != "morning-brief":
        raise StatusRequestError("Receipt health schema did not match")
    if (payload["status"] not in {"ok", "degraded"}
            or not isinstance(payload["timezone"], str) or not payload["timezone"]
            or type(payload["printing"]) is not bool
            or type(payload["schedule_enabled"]) is not bool
            or not isinstance(payload["morning_time"], str)
            or not TIME_PATTERN.fullmatch(payload["morning_time"])
            or not isinstance(payload["schedule"], dict)
            or payload["scheduler_error"] is not None
            and not isinstance(payload["scheduler_error"], str)):
        raise StatusRequestError("Receipt health schema did not match")
    schedule = payload["schedule"]
    if set(schedule) != {"last_date", "status"} or schedule["status"] not in SCHEDULE_STATES:
        raise StatusRequestError("Receipt schedule schema did not match")
    last_date = schedule["last_date"]
    if last_date is not None:
        if not isinstance(last_date, str):
            raise StatusRequestError("Receipt schedule date was invalid")
        try:
            if date.fromisoformat(last_date).isoformat() != last_date:
                raise ValueError
        except ValueError as exc:
            raise StatusRequestError("Receipt schedule date was invalid") from exc
    return {
        "schedule_enabled": payload["schedule_enabled"],
        "morning_time": payload["morning_time"],
        "timezone": payload["timezone"],
        "last_date": last_date,
        "schedule_status": schedule["status"],
        "scheduler_error": payload["scheduler_error"],
        "printing": payload["printing"],
    }


def check(config: ServiceConfig, timeout: float) -> dict:
    try:
        http_status, payload = fetch_json(config.status_url, timeout)
        details = _details(payload)
        if payload["status"] == "degraded":
            if http_status != 503:
                raise StatusRequestError("Receipt HTTP and health states disagreed")
            return result(config.key, config.name, "failed",
                          "Scheduler reported degraded service", config.launch_url, details)
        if http_status != 200:
            raise StatusRequestError("Receipt returned an unexpected HTTP status")
        summary = (
            "Thermal printing, morning briefs, Jeopardy, and encrypted IPPS telegrams"
        )
        return result(config.key, config.name, "healthy", summary,
                      config.launch_url, details)
    except StatusRequestError as exc:
        return result(config.key, config.name, "unknown", str(exc), config.launch_url)
