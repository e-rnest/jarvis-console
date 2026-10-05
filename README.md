# Jarvis Console

Jarvis Console is the small, read-only front door for the Jarvis home-service
ecosystem. Milestone 1 reports accepted service health contracts and provides
browser-reachable launch links. It does not administer Docker, mutate service
state, or print anything.

## Architecture

The application is a Python 3.12 standard-library HTTP server with static HTML,
CSS, and a small vanilla JavaScript client. `GET /api/status` checks Receipt,
Label, Jeopardy, and TriviaROM concurrently through strict per-service adapters.
Each request has a bounded timeout, and each result is isolated so a slow or
invalid service cannot suppress healthy peers. Jellyfin is launch-only because
no accepted health contract has been inventoried.

The browser receives normalized status and LAN-reachable launch URLs. Docker
hostnames are used only by the backend and are never included in browser assets
or API output.

## HTTP API

- `GET /health` reports only the Console process. Downstream failures do not
  make this endpoint unhealthy.
- `GET /api/status` returns a timestamped list of normalized service results.
- `GET /`, `/assets/app.css`, and `/assets/app.js` serve the dashboard.

There are no action endpoints in Milestone 1.

## Status semantics

- `healthy`: an accepted health contract returned a valid healthy response.
- `failed`: an accepted contract explicitly reported a supported degraded or
  failed state. Receipt scheduler degradation and Jeopardy corpus failure are
  currently the supported cases.
- `unknown`: a configured check timed out, failed to connect, returned malformed
  JSON, violated its schema, or otherwise could not establish trustworthy state.
- `unavailable`: no accepted health contract is configured. Jellyfin always uses
  this state in Milestone 1 and is never probed.

No card claims physical printer readiness. Receipt health only exposes the
service's current print-lock state.

## Configuration

Internal status targets and browser launch URLs are separate settings:

| Variable | Default |
|---|---|
| `HTTP_HOST` | `0.0.0.0` |
| `HTTP_PORT` | `8080` |
| `STATUS_TIMEOUT_SECONDS` | `2` |
| `RECEIPT_STATUS_URL` | `http://receipt-service:8080/health` |
| `RECEIPT_LAUNCH_URL` | `http://receipt.jarvis.home/` |
| `LABEL_STATUS_URL` | `http://jarvis.home:5050/health` |
| `LABEL_LAUNCH_URL` | `http://label.jarvis.home/print` |
| `JEOPARDY_STATUS_URL` | `http://jeopardy-service:8080/health` |
| `JEOPARDY_LAUNCH_URL` | `http://jeopardy.home/` |
| `TRIVIAROM_STATUS_URL` | `http://triviarom-service:8080/health` |
| `TRIVIAROM_LAUNCH_URL` | `http://jarvis.home:8790/` |
| `JELLYFIN_LAUNCH_URL` | `http://jellyfin.jarvis.home/` |

`STATUS_TIMEOUT_SECONDS` must be between 0.1 and 10 seconds. Status URLs must
not contain credentials, fragments, or query strings.

## Development and tests

Run locally with:

```sh
python3.12 -m jarvis_console
```

Run the dependency-free test suite and syntax validation with:

```sh
python3.12 -m unittest discover -s tests -v
python3.12 -m compileall -q jarvis_console tests
git diff --check
```

Tests use local fake HTTP servers and never contact live Jarvis services.

## Docker and eventual deployment

`compose.yaml` packages Console as `jarvis-console`, joins the existing external
`jarvis-receipt-services` network, and has no cross-project `depends_on` links.
The candidate host port is configurable with `CONSOLE_HOST_PORT` and defaults to
8791. Port availability must be verified on Jarvis before any deployment.

The Compose configuration assumes `jarvis-receipt-services` already exists and
that `jarvis.home:5050` remains reachable from the container for Label status,
matching Receipt Service's accepted integration route. A later, separately
approved task may configure `http://jarvis.home/` through Synology's reverse
proxy and local DNS.

This repository does not configure DNS or the reverse proxy and must not be
exposed outside the trusted home LAN. No deployment is part of Milestone 1.

## Known limitations

- Jellyfin status is unavailable until an accepted API contract is verified.
- Label health proves only that its HTTP process responds.
- Jeopardy health proves corpus readability; TriviaROM reports corpus counts.
- Receipt health does not probe printers or upstream content services.
- Receipt provides configured scheduler time and durable prior-attempt state,
  but not a calculated next-run timestamp.
- There are no print or other mutation controls. A deliberate, no-retry Morning
  Brief action is reserved for a later milestone.
