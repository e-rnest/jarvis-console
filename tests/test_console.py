from __future__ import annotations

from contextlib import contextmanager
import json
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from pathlib import Path
import socket
import threading
import time
import unittest
from urllib.error import HTTPError
from urllib.request import urlopen

from jarvis_console.config import Config, ServiceConfig
from jarvis_console.http import make_server
from jarvis_console.status import aggregate


ROOT = Path(__file__).resolve().parent.parent


RECEIPT_OK = {
    "status": "ok",
    "service": "morning-brief",
    "timezone": "America/Los_Angeles",
    "printing": False,
    "schedule_enabled": True,
    "morning_time": "07:00",
    "schedule": {"last_date": "2026-10-04", "status": "sent"},
    "scheduler_error": None,
}
TRIVIA_OK = {
    "status": "ok",
    "service": "TriviaROM",
    "corpus_loaded": True,
    "dataset_count": 68,
    "record_count": 145600,
    "playable_record_count": 137173,
}
RECEIPT_PRINT_OK = {
    "status": "sent",
    "bytes": 1234,
    "notices": [],
    "delivery": "TCP accepted; physical output is not confirmed",
}
DROP_CONNECTION = object()


class FakeHandler(BaseHTTPRequestHandler):
    def do_GET(self):
        response = self.server.responses.get(self.path)
        if response is None:
            status, body, delay = 404, {"error": "missing"}, 0
        else:
            status, body, delay = response
        if delay:
            time.sleep(delay)
        payload = body if isinstance(body, bytes) else json.dumps(body).encode()
        self.send_response(status)
        self.send_header("Content-Type", "application/json")
        self.send_header("Content-Length", str(len(payload)))
        self.end_headers()
        try:
            self.wfile.write(payload)
        except (BrokenPipeError, ConnectionResetError):
            pass

    def do_POST(self):
        with self.server.request_lock:
            self.server.post_paths.append(self.path)
        response = self.server.responses.get(self.path)
        if response is None:
            status, body, delay = 404, {"error": "missing"}, 0
        else:
            status, body, delay = response
        if delay:
            time.sleep(delay)
        if body is DROP_CONNECTION:
            self.connection.shutdown(socket.SHUT_RDWR)
            self.connection.close()
            return
        payload = body if isinstance(body, bytes) else json.dumps(body).encode()
        self.send_response(status)
        self.send_header("Content-Type", "application/json")
        self.send_header("Content-Length", str(len(payload)))
        self.end_headers()
        try:
            self.wfile.write(payload)
        except (BrokenPipeError, ConnectionResetError):
            pass

    def log_message(self, format, *args):
        pass


@contextmanager
def fake_downstreams(responses):
    server = ThreadingHTTPServer(("127.0.0.1", 0), FakeHandler)
    server.daemon_threads = True
    server.responses = responses
    server.post_paths = []
    server.request_lock = threading.Lock()
    thread = threading.Thread(target=server.serve_forever, daemon=True)
    thread.start()
    try:
        yield f"http://127.0.0.1:{server.server_port}", server
    finally:
        server.shutdown()
        server.server_close()
        thread.join()


def configuration(base_url: str, timeout: float = 0.25,
                  action_timeout: float = 0.25) -> Config:
    return Config("127.0.0.1", 0, timeout,
                  f"{base_url}/print/morning", action_timeout, (
        ServiceConfig("receipt", "Receipt", f"{base_url}/receipt", None),
        ServiceConfig("label", "Label", f"{base_url}/label", "http://launch/label"),
        ServiceConfig("jeopardy", "Jeopardy", f"{base_url}/jeopardy", "http://launch/jeopardy"),
        ServiceConfig("triviarom", "TriviaROM", f"{base_url}/trivia", "http://launch/trivia"),
        ServiceConfig("jellyfin", "Jellyfin", None, "http://launch/jellyfin"),
    ))


def healthy_responses():
    return {
        "/receipt": (200, RECEIPT_OK, 0),
        "/label": (200, {"status": "ok"}, 0),
        "/jeopardy": (200, {"status": "ok"}, 0),
        "/trivia": (200, TRIVIA_OK, 0),
    }


def by_key(snapshot):
    return {service["key"]: service for service in snapshot["services"]}


class AggregationTests(unittest.TestCase):
    def test_all_supported_services_healthy_and_jellyfin_unavailable(self):
        with fake_downstreams(healthy_responses()) as (base, _):
            statuses = by_key(aggregate(configuration(base)))
        self.assertEqual(
            {key: value["status"] for key, value in statuses.items()},
            {"receipt": "healthy", "label": "healthy", "jeopardy": "healthy",
             "triviarom": "healthy", "jellyfin": "unavailable"},
        )
        self.assertIsNone(statuses["receipt"]["launch_url"])

    def test_receipt_identity_and_scheduler_details_are_normalized(self):
        with fake_downstreams(healthy_responses()) as (base, _):
            receipt = by_key(aggregate(configuration(base)))["receipt"]
        self.assertEqual(receipt["details"], {
            "schedule_enabled": True,
            "morning_time": "07:00",
            "timezone": "America/Los_Angeles",
            "last_date": "2026-10-04",
            "schedule_status": "sent",
            "scheduler_error": None,
            "printing": False,
        })

    def test_receipt_rejects_non_compatibility_identity(self):
        responses = healthy_responses()
        responses["/receipt"] = (200, {**RECEIPT_OK, "service": "receipt-service"}, 0)
        with fake_downstreams(responses) as (base, _):
            receipt = by_key(aggregate(configuration(base)))["receipt"]
        self.assertEqual(receipt["status"], "unknown")

    def test_receipt_explicit_degraded_state_is_failed(self):
        responses = healthy_responses()
        responses["/receipt"] = (503, {
            **RECEIPT_OK, "status": "degraded", "scheduler_error": "RuntimeError",
        }, 0)
        with fake_downstreams(responses) as (base, _):
            receipt = by_key(aggregate(configuration(base)))["receipt"]
        self.assertEqual(receipt["status"], "failed")
        self.assertEqual(receipt["details"]["scheduler_error"], "RuntimeError")

    def test_label_minimal_health_is_accepted(self):
        with fake_downstreams(healthy_responses()) as (base, _):
            label = by_key(aggregate(configuration(base)))["label"]
        self.assertEqual(label["summary"], "Service responding")
        self.assertNotIn("details", label)

    def test_jeopardy_corpus_failure_is_failed(self):
        responses = healthy_responses()
        responses["/jeopardy"] = (503, {"error": "corpus unavailable"}, 0)
        with fake_downstreams(responses) as (base, _):
            jeopardy = by_key(aggregate(configuration(base)))["jeopardy"]
        self.assertEqual(jeopardy["status"], "failed")

    def test_triviarom_corpus_counts_are_normalized(self):
        with fake_downstreams(healthy_responses()) as (base, _):
            trivia = by_key(aggregate(configuration(base)))["triviarom"]
        self.assertEqual(trivia["details"], {
            "dataset_count": 68,
            "record_count": 145600,
            "playable_record_count": 137173,
        })

    def test_malformed_json_is_unknown_without_suppressing_peers(self):
        responses = healthy_responses()
        responses["/label"] = (200, b"not-json", 0)
        with fake_downstreams(responses) as (base, _):
            statuses = by_key(aggregate(configuration(base)))
        self.assertEqual(statuses["label"]["status"], "unknown")
        self.assertEqual(statuses["receipt"]["status"], "healthy")
        self.assertEqual(statuses["jeopardy"]["status"], "healthy")

    def test_schema_mismatch_is_unknown(self):
        responses = healthy_responses()
        responses["/trivia"] = (200, {**TRIVIA_OK, "playable_record_count": "many"}, 0)
        with fake_downstreams(responses) as (base, _):
            trivia = by_key(aggregate(configuration(base)))["triviarom"]
        self.assertEqual(trivia["status"], "unknown")

    def test_connection_failure_is_unknown(self):
        with socket.socket() as probe:
            probe.bind(("127.0.0.1", 0))
            unused_port = probe.getsockname()[1]
        config = configuration(f"http://127.0.0.1:{unused_port}", timeout=0.1)
        statuses = by_key(aggregate(config))
        self.assertTrue(all(statuses[key]["status"] == "unknown"
                            for key in ("receipt", "label", "jeopardy", "triviarom")))

    def test_timeout_is_unknown(self):
        responses = healthy_responses()
        responses["/label"] = (200, {"status": "ok"}, 0.3)
        with fake_downstreams(responses) as (base, _):
            label = by_key(aggregate(configuration(base, timeout=0.05)))["label"]
        self.assertEqual(label["status"], "unknown")

    def test_checks_run_concurrently_with_bounded_timeouts(self):
        responses = {
            path: (status, body, 0.3)
            for path, (status, body, _) in healthy_responses().items()
        }
        with fake_downstreams(responses) as (base, _):
            started = time.monotonic()
            statuses = by_key(aggregate(configuration(base, timeout=0.1)))
            elapsed = time.monotonic() - started
        self.assertLess(elapsed, 0.28)
        self.assertTrue(all(statuses[key]["status"] == "unknown"
                            for key in ("receipt", "label", "jeopardy", "triviarom")))

    def test_jellyfin_makes_no_health_request(self):
        responses = healthy_responses()
        with fake_downstreams(responses) as (base, downstream):
            statuses = by_key(aggregate(configuration(base)))
        self.assertEqual(statuses["jellyfin"]["status"], "unavailable")
        self.assertEqual(set(responses), {"/receipt", "/label", "/jeopardy", "/trivia"})
        self.assertEqual(downstream.post_paths, [])


class ConsoleHTTPTests(unittest.TestCase):
    @contextmanager
    def console(self, config):
        server = make_server(config, host="127.0.0.1", port=0)
        thread = threading.Thread(target=server.serve_forever, daemon=True)
        thread.start()
        try:
            yield f"http://127.0.0.1:{server.server_port}"
        finally:
            server.shutdown()
            server.server_close()
            thread.join()

    def test_console_health_is_independent_of_downstreams(self):
        config = configuration("http://127.0.0.1:1", timeout=0.1)
        with self.console(config) as base:
            with urlopen(base + "/health", timeout=1) as response:
                payload = json.load(response)
        self.assertEqual(response.status, 200)
        self.assertEqual(payload["status"], "ok")
        self.assertEqual(payload["service"], "jarvis-console")

    def test_status_api_does_not_leak_internal_targets(self):
        with fake_downstreams(healthy_responses()) as (base, _):
            config = configuration(base)
            with self.console(config) as console:
                with urlopen(console + "/api/status", timeout=2) as response:
                    body = response.read().decode()
        self.assertNotIn(base, body)
        self.assertNotIn("receipt-service", body)
        self.assertNotIn("triviarom-service", body)
        self.assertIn("http://launch/trivia", body)

    def test_static_page_has_required_structure_and_no_internal_hostnames(self):
        html = (ROOT / "web/index.html").read_text()
        script = (ROOT / "web/app.js").read_text()
        styles = (ROOT / "web/app.css").read_text()
        combined = html + script + styles
        self.assertIn('id="refresh"', html)
        self.assertIn('id="services"', html)
        self.assertIn('fetch("/api/status"', script)
        self.assertIn('fetch("/api/actions/morning-brief"', script)
        self.assertIn("Print Morning Brief", script)
        self.assertIn("produce physical paper output", script)
        self.assertIn("button.disabled = true", script)
        self.assertIn("button.disabled = false", script)
        self.assertIn('addDetail(details, "Datasets"', script)
        self.assertNotIn('addDetail(details, "Packs"', script)
        self.assertIn('if (service.key === "receipt")', script)
        self.assertIn("@media (max-width: 620px)", styles)
        for hostname in ("receipt-service", "jeopardy-service", "triviarom-service"):
            self.assertNotIn(hostname, combined)

    def test_unknown_routes_and_posts_do_not_add_actions(self):
        config = configuration("http://127.0.0.1:1", timeout=0.1)
        with self.console(config) as base:
            with self.assertRaises(HTTPError) as get_error:
                urlopen(base + "/missing", timeout=1)
            with self.assertRaises(HTTPError) as post_error:
                from urllib.request import Request
                urlopen(Request(base + "/api/action", method="POST"), timeout=1)
        self.assertEqual(get_error.exception.code, 404)
        self.assertEqual(post_error.exception.code, 404)

    @staticmethod
    def action_request(base):
        from urllib.request import Request
        request = Request(base + "/api/actions/morning-brief", data=b"", method="POST")
        try:
            response = urlopen(request, timeout=2)
        except HTTPError as exc:
            response = exc
        with response:
            return response.status, json.load(response)

    def test_successful_action_forwards_exactly_one_request(self):
        responses = healthy_responses() | {
            "/print/morning": (200, RECEIPT_PRINT_OK, 0),
        }
        with fake_downstreams(responses) as (base, downstream):
            with self.console(configuration(base)) as console:
                status, result = self.action_request(console)
        self.assertEqual(status, 200)
        self.assertEqual(result["outcome"], "success")
        self.assertIn("not confirmed", result["message"])
        self.assertEqual(downstream.post_paths, ["/print/morning"])

    def test_definite_downstream_rejection_is_failure_without_retry(self):
        responses = healthy_responses() | {
            "/print/morning": (409, {"error": "A print job is already running"}, 0),
        }
        with fake_downstreams(responses) as (base, downstream):
            with self.console(configuration(base)) as console:
                status, result = self.action_request(console)
                responses["/print/morning"] = (200, RECEIPT_PRINT_OK, 0)
                next_status, next_result = self.action_request(console)
        self.assertEqual(status, 502)
        self.assertEqual(result["outcome"], "failed")
        self.assertEqual(result["downstream_status"], 409)
        self.assertEqual((next_status, next_result["outcome"]), (200, "success"))
        self.assertEqual(downstream.post_paths, ["/print/morning", "/print/morning"])

    def test_timeout_is_uncertain_without_retry_and_guard_releases(self):
        responses = healthy_responses() | {
            "/print/morning": (200, RECEIPT_PRINT_OK, 0.2),
        }
        with fake_downstreams(responses) as (base, downstream):
            with self.console(configuration(base, action_timeout=0.05)) as console:
                first_status, first = self.action_request(console)
                second_status, second = self.action_request(console)
        self.assertEqual((first_status, first["outcome"]), (502, "uncertain"))
        self.assertEqual((second_status, second["outcome"]), (502, "uncertain"))
        self.assertIn("physical printer", first["message"])
        self.assertEqual(downstream.post_paths, ["/print/morning", "/print/morning"])

    def test_connection_loss_is_uncertain_without_retry(self):
        responses = healthy_responses() | {
            "/print/morning": (200, DROP_CONNECTION, 0),
        }
        with fake_downstreams(responses) as (base, downstream):
            with self.console(configuration(base)) as console:
                status, result = self.action_request(console)
        self.assertEqual((status, result["outcome"]), (502, "uncertain"))
        self.assertEqual(downstream.post_paths, ["/print/morning"])

    def test_unrecognized_success_response_is_uncertain_without_retry(self):
        responses = healthy_responses() | {
            "/print/morning": (200, {"status": "unexpected"}, 0),
        }
        with fake_downstreams(responses) as (base, downstream):
            with self.console(configuration(base)) as console:
                status, result = self.action_request(console)
        self.assertEqual((status, result["outcome"]), (502, "uncertain"))
        self.assertEqual(downstream.post_paths, ["/print/morning"])

    def test_second_concurrent_action_is_not_forwarded_and_guard_releases(self):
        responses = healthy_responses() | {
            "/print/morning": (200, RECEIPT_PRINT_OK, 0.3),
        }
        with fake_downstreams(responses) as (base, downstream):
            with self.console(configuration(base, action_timeout=1)) as console:
                first_result = []
                thread = threading.Thread(
                    target=lambda: first_result.append(self.action_request(console))
                )
                thread.start()
                deadline = time.monotonic() + 1
                while not downstream.post_paths and time.monotonic() < deadline:
                    time.sleep(0.005)
                busy_status, busy = self.action_request(console)
                thread.join()
                final_status, final = self.action_request(console)
        self.assertEqual((busy_status, busy["outcome"]), (409, "busy"))
        self.assertEqual((first_result[0][0], first_result[0][1]["outcome"]),
                         (200, "success"))
        self.assertEqual((final_status, final["outcome"]), (200, "success"))
        self.assertEqual(downstream.post_paths,
                         ["/print/morning", "/print/morning"])

    def test_status_and_health_never_invoke_print_action(self):
        responses = healthy_responses() | {
            "/print/morning": (200, RECEIPT_PRINT_OK, 0),
        }
        with fake_downstreams(responses) as (base, downstream):
            with self.console(configuration(base)) as console:
                with urlopen(console + "/health", timeout=2) as response:
                    self.assertEqual(response.status, 200)
                with urlopen(console + "/api/status", timeout=2) as response:
                    self.assertEqual(response.status, 200)
        self.assertEqual(downstream.post_paths, [])


if __name__ == "__main__":
    unittest.main()
