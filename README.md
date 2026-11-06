# Jarvis Console

Jarvis Console is the read-oriented front door for the household services on
the Jarvis Docker host. It presents normalized service status, trusted-LAN
launch links, a read-only Telegram history viewer, and one deliberately guarded
physical action: printing a Morning Brief through Receipt Service.

Start with the [complete service catalog](SERVICE_CATALOG.md) for the table of
every service, LAN IP/port, household alias, Docker alias, network, health
contract, persistence boundary, and local README. The same catalog is rendered
on the appliance at [http://console.jarvis.home/services](http://console.jarvis.home/services).

## Access

- Preferred: [http://console.jarvis.home/](http://console.jarvis.home/)
- Direct hostname and port: [http://jarvis.home:8791/](http://jarvis.home:8791/)
- Direct IP and port: [http://192.168.1.100:8791/](http://192.168.1.100:8791/)

The friendly URL depends on local DNS and Synology Reverse Proxy. This project
does not manage either external system. Console is intentionally a trusted-LAN
application and must not be exposed to the public Internet.

## What appears on the dashboard

| Card | Status source | Primary action | Secondary actions |
| --- | --- | --- | --- |
| Home Assistant | none; launch-only | Home Assistant | short alias and direct `:8123` route |
| Receipt Service | accepted `/health` JSON | confirmed Morning Brief print | project repository |
| Thermal Telegram | Receipt status; history is read-only | view the most recent stored Telegram messages | none |
| Label | accepted `/health` JSON | Print UI | Quick Labels, Fridge, Freezer |
| Manifest | accepted `/health` JSON | inventory application | none |
| Jeopardy | corpus-aware `/health` | clue browser | none |
| TriviaROM | corpus-count `/health` | trivia browser | none |
| Wallboard | accepted `/health` JSON | household wallboard | none |
| BlackTorrent | qBittorrent WebUI reachability | preferred WebUI alias | backup alias |
| Jellyfin | none; launch-only | media application | TV Guide |
| Semavox | none; launch-only | device control interface | fixed IP and project repository |

Infrastructure without a useful, verified browser target stays in the service
catalog instead of becoming a misleading card. This currently includes Matter
Server, Manifest Scanner, the standalone Jarvis Scanner, and Scrypted. Scrypted
can gain a card after its canonical household URL is recorded; a status badge
still requires a truthful accepted health contract.

## Architecture and boundaries

The application is a Python 3.12 standard-library `ThreadingHTTPServer` with
static HTML, CSS, and vanilla JavaScript. No build system, JavaScript runtime,
framework, external CDN, database, or authentication provider is required by
Console itself.

`GET /api/status` checks supported downstreams concurrently. Each adapter has a
bounded timeout and strict response validation. One slow, malformed, or failed
service cannot suppress healthy peers. Backend Docker/LAN targets never appear
in the browser payload; browser links are configured separately.

Console is an orchestrator/client, not an owner of downstream behavior:

- it does not start, stop, restart, update, or inspect Docker containers;
- it does not duplicate Receipt scheduling, printing, or retry policy;
- it does not interpret Manifest scanner events or inspect the scanner queue;
- it does not infer device/printer/VPN/media health from a homepage;
- it does not expose credentials, private keys, tokens, or service databases;
- downstream services continue to operate when Console is unavailable.

See [SERVICE_CATALOG.md](SERVICE_CATALOG.md#integration-ownership) for the full
cross-service ownership map.

## HTTP surface

| Method and path | Purpose |
| --- | --- |
| `GET /` | dashboard |
| `GET /health` | Console process health only |
| `GET /api/status` | timestamped normalized downstream snapshot |
| `GET /api/ipps/history` | newest 50 stored Telegram entries from Receipt's read-only history database |
| `POST /api/actions/morning-brief` | exactly one guarded Receipt print request |
| `GET /services` | HTML service catalog |
| `GET /assets/app.css` | local stylesheet |
| `GET /assets/app.js` | local dashboard client |

Unknown routes return JSON 404. Static files and JSON use `Cache-Control:
no-store`, `X-Content-Type-Options: nosniff`, and a no-referrer policy.

### Morning Brief safety contract

The endpoint accepts no request body. The browser asks for confirmation before
dispatch. Console sends one request and never retries it automatically. A
process-local in-flight guard rejects overlap.

- An accepted Receipt response becomes `success`.
- A recognized downstream rejection becomes `failed`.
- Timeout, connection loss, or an unrecognized post-dispatch response becomes
  `uncertain` and tells the operator to inspect the physical printer before
  trying again.

The guard is intentionally process-local, not durable or cross-instance
idempotency. Receipt remains the physical print authority.

### Telegram history boundary

Console mounts Receipt's external schedule/history volume read-only and opens
`telegram_history.sqlite3` in SQLite read-only URI mode. The endpoint returns at
most 50 newest entries. It does not mutate, acknowledge, delete, or retry
messages. The history can contain household-private message and network
metadata, so Console must remain limited to the trusted LAN.

## Status semantics

- `healthy`: an accepted service contract returned a valid healthy response.
- `failed`: an accepted contract explicitly returned a supported degraded or
  failed state. Receipt scheduler degradation and Jeopardy corpus failure are
  current examples.
- `unknown`: timeout, connection error, malformed data, schema mismatch, or
  another condition prevented Console from establishing trustworthy state.
- `unavailable`: no accepted health contract is configured; the card is
  navigation-only.

No card claims physical printer readiness. Receipt exposes service/scheduler
and print-lock state only. BlackTorrent proves WebUI reachability only, not VPN
tunnel or namespace safety. The exact contract matrix is in the
[service catalog](SERVICE_CATALOG.md#health-contracts).

## Configuration

Internal status targets and browser launch URLs are deliberately separate.
Every URL must be HTTP(S), contain a hostname, and omit embedded credentials.
Status URLs also reject query strings and fragments; launch URLs may contain
them for application deep links.

### Server and actions

| Variable | Default |
| --- | --- |
| `HTTP_HOST` | `0.0.0.0` |
| `HTTP_PORT` | `8080` |
| `STATUS_TIMEOUT_SECONDS` | `2` |
| `MORNING_BRIEF_URL` | `http://receipt-service:8080/print/morning` |
| `MORNING_BRIEF_TIMEOUT_SECONDS` | `300` |

`STATUS_TIMEOUT_SECONDS` must be 0.1–10 seconds. The Morning Brief timeout must
be 0.1–600 seconds.

### Launch-only services

| Variable | Default |
| --- | --- |
| `HOME_ASSISTANT_LAUNCH_URL` | `http://ha.jarvis.home/` |
| `HOME_ASSISTANT_SHORT_URL` | `http://ha.home/` |
| `HOME_ASSISTANT_DIRECT_URL` | `http://192.168.1.100:8123/` |
| `JELLYFIN_LAUNCH_URL` | `http://jellyfin.home` |
| `JELLYFIN_TV_GUIDE_URL` | `http://jellyfin.home/web/#/livetv?collectionType=livetv&tab=1` |
| `SEMAVOX_LAUNCH_URL` | `http://semavox.home` |
| `SEMAVOX_FALLBACK_URL` | `http://192.168.1.80` |
| `SEMAVOX_REPOSITORY_URL` | `https://github.com/e-rnest/semavox` |

### Checked services and browser links

| Variable | Default |
| --- | --- |
| `RECEIPT_STATUS_URL` | `http://receipt-service:8080/health` |
| `RECEIPT_REPOSITORY_URL` | `https://github.com/e-rnest/receipt-service` |
| `LABEL_STATUS_URL` | `http://jarvis.home:5050/health` |
| `LABEL_LAUNCH_URL` | `http://label.jarvis.home/print` |
| `LABEL_QUICK_LABELS_URL` | `http://label.jarvis.home/labels` |
| `LABEL_FRIDGE_URL` | `http://label.jarvis.home/inventory` |
| `LABEL_FREEZER_URL` | `http://label.jarvis.home/inventory/frozen` |
| `MANIFEST_STATUS_URL` | `http://manifest.home/health` |
| `MANIFEST_LAUNCH_URL` | `http://manifest.home/` |
| `JEOPARDY_STATUS_URL` | `http://jeopardy-service:8080/health` |
| `JEOPARDY_LAUNCH_URL` | `http://jeopardy.home/` |
| `TRIVIAROM_STATUS_URL` | `http://triviarom-service:8080/health` |
| `TRIVIAROM_LAUNCH_URL` | `http://trivia.jarvis.home/` |
| `WALLBOARD_STATUS_URL` | `http://wallboard.home/health` |
| `WALLBOARD_LAUNCH_URL` | `http://wallboard.home/` |
| `BLACKTORRENT_STATUS_URL` | `http://192.168.1.100:8080/` |
| `BLACKTORRENT_LAUNCH_URL` | `http://blacktorrent.home/` |
| `BLACKTORRENT_BACKUP_URL` | `http://blacktorrent.jarvis.home/` |

## Docker deployment

`compose.yaml` builds `jarvis-console`, publishes host port 8791 to container
port 8080 by default, and joins both its project network and the existing
external `jarvis-receipt-services` network. It intentionally has no cross-project
`depends_on`; Console tolerates absent downstreams.

The external `morning-brief_schedule-data` volume is mounted at `/receipt-data`
read-only for Telegram history. The volume belongs to Receipt Service and must
already exist. Console's healthcheck calls its own `/health`. JSON logs rotate
at 5 MiB with three retained files.

Deployment prerequisites:

1. Docker Compose can build the local image.
2. `jarvis-receipt-services` exists.
3. `morning-brief_schedule-data` exists and contains Receipt's expected history
   database when the viewer is used.
4. `192.168.1.100` is the intended trusted-LAN bind address, or `LAN_BIND_IP` is
   set explicitly.
5. Local DNS and reverse proxy routes are configured outside this repository.

Typical deployment from `/volume1/docker/jarvis-console`:

```sh
sudo docker compose build jarvis-console
sudo docker compose up -d jarvis-console
sudo docker compose ps jarvis-console
sudo docker compose logs --tail=100 jarvis-console
```

Rebuild/recreate the container after changing Python, static assets, Compose
environment, or documentation served by `/services`.

## Development and verification

Run locally:

```sh
python3.12 -m jarvis_console
```

Run the dependency-free checks:

```sh
python3.12 -m unittest discover -s tests -v
python3.12 -m compileall -q jarvis_console tests
git diff --check
```

Tests use disposable local fake HTTP servers and do not call live household
services or printers. A passing unit suite does not validate DNS, reverse proxy,
the external Docker network/volume, a real printer, scanner hardware, VPN
containment, or physical output.

## Troubleshooting

### A card says `unknown`

Check the service-specific summary first, then test the configured status URL
from inside the Console container. Verify Docker-network membership for Receipt,
Jeopardy, and TriviaROM; verify LAN routing/DNS for Label, Manifest, and
BlackTorrent. Do not change an adapter to accept a generic homepage merely to
turn the badge green.

### A launch-only card says `unavailable`

That is intentional: the browser link is useful, but Console has no accepted
health contract. It does not mean the application is down.

### Telegram history is unavailable

Verify the external volume exists, is mounted read-only at `/receipt-data`, and
contains `telegram_history.sqlite3` with the expected `telegram_history` table.
Do not copy or repair the live database through Console.

### Morning Brief result is uncertain

Inspect the printer before retrying. A timeout can occur after Receipt accepted
the physical job, so an automatic or immediate manual retry can duplicate paper
output.

### Friendly URL fails but the direct port works

Console does not manage local DNS or Synology Reverse Proxy. Verify those rules
against the address table in [SERVICE_CATALOG.md](SERVICE_CATALOG.md).

## Known limitations

- Docker runtime state is not integrated; cards represent application
  contracts, not container state.
- Jellyfin and Home Assistant are launch-only. Matter Server, scanners, and
  Scrypted are catalog-only.
- Label health does not reach the printer; Receipt health does not reach its
  printer or content providers.
- Manifest health does not include scanner attachment or persistent queue depth.
- BlackTorrent health does not prove VPN/tunnel/namespace state.
- The Telegram viewer assumes Receipt's current SQLite schema and is private-LAN
  functionality, not a public API.
- Reverse proxy and DNS remain external configuration and must be maintained
  alongside the source-backed catalog.


## Related projects

Cross-service contracts are in the [integration directory](INTEGRATIONS.md), and the full map is in the [ecosystem guide](ECOSYSTEM.md). Coding agents must read the [operations playbook](AGENT_OPERATIONS.md) and [AGENTS.md](AGENTS.md).
