"""Conservative, non-retrying proxies for deliberate physical actions."""

from __future__ import annotations

import json
import threading
from urllib.error import HTTPError
from urllib.request import Request, urlopen

MAX_RESPONSE_BYTES = 64 * 1024


class MorningBriefAction:
    """Allow at most one process-local Morning Brief request at a time."""

    def __init__(self, url: str, timeout: float):
        self.url = url
        self.timeout = timeout
        self._in_flight = threading.Lock()

    def perform(self) -> tuple[int, dict]:
        if not self._in_flight.acquire(blocking=False):
            return 409, {
                "outcome": "busy",
                "message": "A Morning Brief print request is already in progress.",
            }
        try:
            return self._perform_once()
        finally:
            self._in_flight.release()

    def _perform_once(self) -> tuple[int, dict]:
        request = Request(
            self.url,
            data=b"",
            method="POST",
            headers={
                "Accept": "application/json",
                "Content-Length": "0",
                "User-Agent": "jarvis-console/1.0",
            },
        )
        try:
            response = urlopen(request, timeout=self.timeout)
        except HTTPError as exc:
            return self._known_rejection(exc)
        except OSError:
            return 502, {
                "outcome": "uncertain",
                "message": (
                    "The connection ended without a trustworthy result. "
                    "Check the physical printer before trying again."
                ),
            }

        try:
            with response:
                status = response.status
                body = response.read(MAX_RESPONSE_BYTES + 1)
        except OSError:
            return 502, {
                "outcome": "uncertain",
                "message": (
                    "The print request may have reached Receipt Service, but its result "
                    "was lost. Check the physical printer before trying again."
                ),
            }
        if status != 200:
            return 502, {
                "outcome": "failed",
                "message": f"Receipt Service rejected the request with HTTP {status}.",
                "downstream_status": status,
            }
        if len(body) > MAX_RESPONSE_BYTES:
            return self._uncertain_response()
        try:
            payload = json.loads(body)
        except (UnicodeDecodeError, json.JSONDecodeError):
            return self._uncertain_response()
        if (not isinstance(payload, dict) or payload.get("status") != "sent"
                or type(payload.get("bytes")) is not int or payload["bytes"] < 0
                or not isinstance(payload.get("delivery"), str)):
            return self._uncertain_response()
        return 200, {
            "outcome": "success",
            "message": (
                "Receipt Service accepted the print request. "
                "Physical paper output is not confirmed."
            ),
            "bytes": payload["bytes"],
        }

    @staticmethod
    def _uncertain_response() -> tuple[int, dict]:
        return 502, {
            "outcome": "uncertain",
            "message": (
                "Receipt Service returned an unrecognized result after the request was sent. "
                "Check the physical printer before trying again."
            ),
        }

    @staticmethod
    def _known_rejection(response: HTTPError) -> tuple[int, dict]:
        try:
            with response:
                body = response.read(MAX_RESPONSE_BYTES + 1)
            payload = json.loads(body) if len(body) <= MAX_RESPONSE_BYTES else None
            detail = payload.get("error") if isinstance(payload, dict) else None
        except (OSError, UnicodeDecodeError, json.JSONDecodeError):
            detail = None
        message = f"Receipt Service rejected the request with HTTP {response.code}."
        if isinstance(detail, str) and detail.strip():
            message = f"Receipt Service rejected the request: {detail.strip()}"
        return 502, {
            "outcome": "failed",
            "message": message,
            "downstream_status": response.code,
        }
