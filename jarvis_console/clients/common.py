"""Bounded JSON HTTP client shared by downstream adapters."""

from __future__ import annotations

import json
from urllib.error import HTTPError
from urllib.request import Request, urlopen

MAX_RESPONSE_BYTES = 64 * 1024


class StatusRequestError(Exception):
    """The downstream response could not establish trustworthy status."""


def fetch_json(url: str, timeout: float) -> tuple[int, dict]:
    request = Request(url, headers={
        "Accept": "application/json",
        "User-Agent": "jarvis-console/1.0",
    })
    try:
        response = urlopen(request, timeout=timeout)
    except HTTPError as exc:
        response = exc
    except OSError as exc:
        raise StatusRequestError("Health check could not connect") from exc

    try:
        with response:
            status = response.status
            body = response.read(MAX_RESPONSE_BYTES + 1)
    except OSError as exc:
        raise StatusRequestError("Health response could not be read") from exc
    if len(body) > MAX_RESPONSE_BYTES:
        raise StatusRequestError("Health response was too large")
    try:
        payload = json.loads(body)
    except (UnicodeDecodeError, json.JSONDecodeError) as exc:
        raise StatusRequestError("Health response was not valid JSON") from exc
    if not isinstance(payload, dict):
        raise StatusRequestError("Health response was not a JSON object")
    return status, payload


def result(key: str, name: str, status: str, summary: str,
           launch_url: str | None, details: dict | None = None) -> dict:
    document = {
        "key": key,
        "name": name,
        "status": status,
        "summary": summary,
        "launch_url": launch_url,
    }
    if details is not None:
        document["details"] = details
    return document
