# Architecture

Source-audited 2026-11-06. This describes the checked-in implementation, not a live
deployment observation.

## System boundary

Jarvis Console is a stateless Python 3.12 web application on the trusted household LAN.
Its only durable-data access is read-only access to a SQLite file owned by Receipt
Service. It has no package dependencies, frontend toolchain, application database,
authentication layer, job queue, scheduler, or container-control socket.

```text
Browser
  ├─ static dashboard and /services ───────────────┐
  ├─ GET /api/status                              │
  ├─ GET /api/ipps/history                        ▼
  └─ POST /api/actions/morning-brief      Jarvis Console
                                                ├─ concurrent HTTP status checks
                                                ├─ one-shot POST to Receipt
                                                └─ read-only SQLite query
```

## Components

| Component | Responsibility |
| --- | --- |
| `jarvis_console/__main__.py` | Loads configuration, initializes logging, and runs the server. |
| `jarvis_console/config.py` | Validates settings and separates internal targets from browser launch URLs. |
| `jarvis_console/http.py` | Allowlisted static files, JSON routing, headers, history query, and action dispatch. |
| `jarvis_console/status.py` | Concurrent aggregation, result ordering, launch-only entries, and exception isolation. |
| `jarvis_console/clients/` | Service-specific health adapters and bounded JSON HTTP client. |
| `jarvis_console/actions.py` | Process-local Morning Brief lock and non-retrying Receipt proxy. |
| `web/` | Hand-authored dashboard, client-side rendering, and separately maintained `/services` page. |
| `tests/` | Fake-server tests for configuration, routes, adapters, concurrency, and action safety. |

`ThreadingHTTPServer` handles requests concurrently using daemon request threads. The
status aggregator creates a fresh `ThreadPoolExecutor` per snapshot with one worker per
checked service (up to ten; Home Assistant is conditional on its token). Results are
returned in configuration order.

## Status workflow

1. The browser fetches `GET /api/status` with caching disabled.
2. `aggregate()` separates checked services from launch-only services.
3. Each checked service runs through its named adapter in parallel using the common
   configured timeout.
4. The common JSON client caps response bodies at 64 KiB and requires a JSON object.
5. Each adapter validates its own HTTP/schema contract. Contract failures become
   `unknown`; explicitly supported degraded states may become `failed`.
6. Unexpected adapter exceptions are isolated and normalized to `unknown`.
7. Launch-only services become `unavailable`; secondary links are appended; output is
   restored to configured order with a UTC `generated_at` value.

Internal status URLs never appear in the result. Launch URLs do because the browser
needs them. See [Integrations](INTEGRATIONS.md) for exact adapter contracts.

## Morning Brief workflow

1. The dashboard requires confirmation and sends an empty POST to Console.
2. Console rejects bodies, transfer encoding, query strings, and wrong routes.
3. A non-blocking process-local lock admits only one request in this process.
4. Console performs one empty POST to Receipt's `/print/morning`. It never retries.
5. Only HTTP 200 with expected `status: sent`, non-negative integer `bytes`, and string
   `delivery` is `success`. Receipt HTTP errors are `failed`; ambiguous transport or
   response failures are `uncertain`.
6. The lock is released in all cases.

The lock is neither durable nor distributed. Multiple Console instances could submit
concurrently, and a restart forgets in-flight state. Receipt owns its own printer lock
and remains the print authority. TCP acceptance does not prove paper output.

## Telegram history workflow

Receipt writes `/data/telegram_history.sqlite3` in its external schedule-data volume.
Compose mounts that volume at `/receipt-data:ro`. Console opens the database with SQLite
URI `mode=ro`, selects the newest 50 rows, and maps stored fields into the response. It
does not expose the ntfy ID, user agent, error details, or claim/completion timestamps.

The query depends directly on Receipt's table and column names; there is no versioned
database contract. A schema change can make this endpoint return 503 without affecting
the rest of Console.

## HTTP, deployment, and failure boundaries

Only an explicit static-file allowlist is served. Responses include `Cache-Control:
no-store`, `X-Content-Type-Options: nosniff`, and `Referrer-Policy: no-referrer`. The
frontend is plain HTML/CSS/JavaScript with no external CDN. `/services` is hand-maintained
and can drift from Markdown.

- The image copies only `jarvis_console/` and `web/`, then runs as UID 10001.
- Console joins its private network and the external Receipt network.
- There is deliberately no cross-project `depends_on`; unavailable peers degrade cards.
- Container health proves only Console responds, not that any downstream is healthy.
- JSON-file logs rotate at 5 MiB with three retained files.
- Loss of Console does not interrupt downstream applications, schedules, or devices.

DNS, proxy rules, running image versions, physical device state, and the production
history schema were not live-verified. No notification hub, control plane, durable action
ledger, or automatic retry layer exists.
