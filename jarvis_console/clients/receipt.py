"""Receipt Service health adapter."""

from __future__ import annotations

from datetime import date, datetime
import re

from jarvis_console.config import ServiceConfig
from .common import StatusRequestError, fetch_json, result

TIME_PATTERN = re.compile(r"(?:[01][0-9]|2[0-3]):[0-5][0-9]\Z")
SCHEDULE_STATES = {"never", "claimed", "sent", "failed"}
PRINTER_NAMES = ("Pam", "Hedwig")
PAPER_STATES = {"ok", "near_end", "out", "unknown"}
PRINTER_ERRORS = {
    "cutter": "Cutter error",
    "unrecoverable": "Unrecoverable error",
    "auto_recoverable": "Auto-recoverable error",
    "no_response": "No status reply",
}
REACHABILITY_NOTE = "Reachability only. No paper status."


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


def _optional_bool(value: object) -> bool:
    return value is None or type(value) is bool


def printer_view(printer: object) -> dict:
    """Validate one Receipt printer entry and turn it into chip display data.

    ``state`` is one of ``ok``, ``warn``, ``bad`` or ``unknown``. The wording
    lives here, not in the browser, so it stays under test.
    """
    if not isinstance(printer, dict):
        raise StatusRequestError("Receipt printer status schema did not match")
    name, kind = printer.get("name"), printer.get("kind")
    reachable, checked_at = printer.get("reachable"), printer.get("checked_at")
    if (name not in PRINTER_NAMES or kind not in {"status", "reachability"}
            or not _optional_bool(reachable)
            or type(printer.get("busy")) is not bool
            or checked_at is not None and not isinstance(checked_at, str)
            or (reachable is None) != (checked_at is None)):
        raise StatusRequestError("Receipt printer status schema did not match")
    if checked_at is not None:
        try:
            datetime.fromisoformat(checked_at)
        except ValueError as exc:
            raise StatusRequestError("Receipt printer check time was invalid") from exc

    if kind == "status":
        online, cover_open = printer.get("online"), printer.get("cover_open")
        paper, error = printer.get("paper"), printer.get("error")
        if (not _optional_bool(online) or not _optional_bool(cover_open)
                or paper not in PAPER_STATES
                or error is not None and error not in PRINTER_ERRORS):
            raise StatusRequestError("Receipt printer status schema did not match")
        if reachable is None:
            state, text = "unknown", "Not checked yet"
        elif not reachable:
            state, text = "bad", "Unreachable"
        elif error == "no_response":
            state, text = "unknown", PRINTER_ERRORS[error]
        elif cover_open:
            state, text = "bad", "Cover open"
        elif paper == "out":
            state, text = "bad", "Paper out"
        elif error:
            state, text = "bad", PRINTER_ERRORS[error]
        elif online is False:
            state, text = "bad", "Offline"
        elif paper == "near_end":
            state, text = "warn", "Paper near end"
        elif online is True and paper == "ok":
            state, text = "ok", "Ready"
        else:
            state, text = "unknown", "Status unknown"
        note = None
    else:
        if reachable is None:
            state, text = "unknown", "Not checked yet"
        elif reachable:
            state, text = "ok", "Reachable"
        else:
            state, text = "bad", "Unreachable"
        note = REACHABILITY_NOTE
    return {"name": name, "kind": kind, "state": state, "text": text,
            "note": note, "busy": printer["busy"], "checked_at": checked_at}


def printers(url: str, timeout: float) -> list[dict] | None:
    """Read Hedwig and Pam status from Receipt Service.

    Console never contacts a printer itself. Any failure returns ``None`` so
    the Receipt card's own health badge is unaffected.
    """
    try:
        http_status, payload = fetch_json(url, timeout)
        entries = payload.get("printers")
        if (http_status != 200 or payload.get("service") != "morning-brief"
                or not isinstance(entries, list)):
            raise StatusRequestError("Receipt printer status schema did not match")
        views = [printer_view(entry) for entry in entries]
        if sorted(view["name"] for view in views) != sorted(PRINTER_NAMES):
            raise StatusRequestError("Receipt printer status schema did not match")
        return views
    except StatusRequestError:
        return None
