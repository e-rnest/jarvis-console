"""TriviaROM health adapter."""

from jarvis_console.config import ServiceConfig
from .common import StatusRequestError, fetch_json, result


def check(config: ServiceConfig, timeout: float) -> dict:
    try:
        http_status, payload = fetch_json(config.status_url, timeout)
        required = {"status", "service", "corpus_loaded", "dataset_count",
                    "record_count", "playable_record_count"}
        counts = (payload.get("dataset_count"), payload.get("record_count"),
                  payload.get("playable_record_count"))
        if (http_status != 200 or not required <= payload.keys()
                or payload["status"] != "ok" or payload["service"] != "TriviaROM"
                or payload["corpus_loaded"] is not True
                or any(type(value) is not int or value < 0 for value in counts)
                or counts[2] > counts[1]):
            raise StatusRequestError("TriviaROM health schema did not match")
        details = {
            "dataset_count": counts[0],
            "record_count": counts[1],
            "playable_record_count": counts[2],
        }
        return result(config.key, config.name, "healthy",
                      f"{counts[2]:,} playable questions", config.launch_url, details)
    except StatusRequestError as exc:
        return result(config.key, config.name, "unknown", str(exc), config.launch_url)
