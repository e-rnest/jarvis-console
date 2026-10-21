# Jarvis Console

Jarvis Console is the small, read-only front door for the Jarvis home-service
ecosystem. It reports accepted service health contracts, provides useful
browser-reachable launch links, and exposes one deliberately guarded physical
action: printing a Morning Brief through Receipt Service.

## Access

On the trusted home LAN, open Jarvis Console at:

- Preferred: [http://console.jarvis.home/](http://console.jarvis.home/)
- Direct hostname and published port: [http://jarvis.home:8791/](http://jarvis.home:8791/)
- Direct IP and published port: [http://192.168.1.100:8791/](http://192.168.1.100:8791/)

The preferred URL is provided by local DNS and the Synology reverse proxy. This
repository packages the Console application but does not manage those external
DNS or reverse-proxy settings.

## Architecture

The application is a Python 3.12 standard-library HTTP server with static HTML,
CSS, and a small vanilla JavaScript client. `GET /api/status` checks Receipt,
Label, Jeopardy, TriviaROM, and BlackTorrent concurrently through strict
per-service adapters.
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
- `POST /api/actions/morning-brief` forwards exactly one non-retried request to
  Receipt Service while holding a process-local in-flight guard.
- `GET /`, `/assets/app.css`, and `/assets/app.js` serve the dashboard.
- `GET /services` serves the linked Jarvis Docker Services README. It records
  source-backed topology, contracts, operational boundaries, and possible safe
  navigation shortcuts without exposing service secrets.

The Morning Brief endpoint accepts no body. It reports success only when Receipt
returns its accepted response, reports known rejections as failures, and treats
timeouts, connection loss, and unrecognized post-dispatch responses as uncertain.
An uncertain result instructs the user to inspect the physical printer before
trying again. Console never retries the request automatically.

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
| `MORNING_BRIEF_URL` | `http://receipt-service:8080/print/morning` |
| `MORNING_BRIEF_TIMEOUT_SECONDS` | `300` |
| `RECEIPT_STATUS_URL` | `http://receipt-service:8080/health` |
| `RECEIPT_REPOSITORY_URL` | `https://github.com/e-rnest/receipt-service` |
| `LABEL_STATUS_URL` | `http://jarvis.home:5050/health` |
| `LABEL_LAUNCH_URL` | `http://label.jarvis.home/print` |
| `JEOPARDY_STATUS_URL` | `http://jeopardy-service:8080/health` |
| `JEOPARDY_LAUNCH_URL` | `http://jeopardy.home/` |
| `TRIVIAROM_STATUS_URL` | `http://triviarom-service:8080/health` |
| `TRIVIAROM_LAUNCH_URL` | `http://trivia.jarvis.home/` |
| `BLACKTORRENT_STATUS_URL` | `http://192.168.1.100:8080/` |
| `BLACKTORRENT_LAUNCH_URL` | `http://192.168.1.100:8080/` |
| `JELLYFIN_LAUNCH_URL` | `http://jellyfin.home` |
| `JELLYFIN_TV_GUIDE_URL` | `http://jellyfin.home/web/#/livetv?collectionType=livetv&tab=1` |

`STATUS_TIMEOUT_SECONDS` must be between 0.1 and 10 seconds, and the Morning
Brief timeout must be between 0.1 and 600 seconds. URLs must not contain
credentials. Backend status URLs additionally reject query strings and
fragments; browser launch links may use them for application deep links.

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

## Docker and deployment

`compose.yaml` packages Console as `jarvis-console`, joins the existing external
`jarvis-receipt-services` network, and has no cross-project `depends_on` links.
The published host port is configurable with `CONSOLE_HOST_PORT` and defaults to
8791. The deployed service is reachable directly through that port and through
the preferred `http://console.jarvis.home/` reverse-proxy URL.

The Compose configuration assumes `jarvis-receipt-services` already exists and
that `jarvis.home:5050` remains reachable from the container for Label status,
matching Receipt Service's accepted integration route.

This repository does not configure DNS or the reverse proxy and must not be
exposed outside the trusted home LAN.

## Known limitations

- Jellyfin status is unavailable until an accepted API contract is verified.
- Label health proves only that its HTTP process responds.
- Jeopardy health proves corpus readability; TriviaROM reports corpus counts.
- BlackTorrent health proves only that its unauthenticated qBittorrent WebUI is
  reachable. It does not inspect Docker, authenticate to qBittorrent, or prove
  VPN tunnel/interface/namespace state.
- Receipt health does not probe printers or upstream content services.
- Receipt provides configured scheduler time and durable prior-attempt state,
  but not a calculated next-run timestamp.
- The Morning Brief guard is intentionally process-local and does not claim
  persistent or cross-instance idempotency. Receipt Service remains the physical
  print authority, and an ambiguous transport result requires human inspection.
