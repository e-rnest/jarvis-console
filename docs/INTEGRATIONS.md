# Integrations

Source-audited 2026-11-06. This page covers Console's direct boundaries. Use the
[central integration directory](../INTEGRATIONS.md) for connections among other Jarvis
projects.

All Console routes and downstreams are unauthenticated and intended only for the trusted
LAN. Status checks originate in the container; launch links open in the user's browser,
so those paths can have different DNS and network reachability.

## Inbound clients

| Source | Interface | Effect and change risk |
| --- | --- | --- |
| Household browser | `GET /`, `/services`, assets, `/api/status`, `/api/ipps/history` | Reads dashboard, status, docs, and private history. Route/response changes require coordinated `web/app.js` changes. |
| Household browser | `POST /api/actions/morning-brief` | Can consume paper. Must remain empty-body, confirmed in UI, one-shot, and non-retrying. |
| Docker healthcheck/operator | `GET /health` | Checks Console only. Adding downstream checks would incorrectly couple container health to optional peers. |
| Synology reverse proxy/local DNS | Browser-facing aliases | Rules live outside this repository; alias changes must be coordinated externally. |

## Outbound status connections

| Target | Default endpoint | Accepted contract and change impact |
| --- | --- | --- |
| Receipt | `http://receipt-service:8080/health` | Identity `morning-brief`; strict scheduler/printing schema; HTTP 200 `ok` or HTTP 503 `degraded`. Schema/identity/alias changes produce `unknown`; supported degradation becomes `failed`. |
| Label | `http://jarvis.home:5050/health` | HTTP 200 JSON `status: ok`. Does not prove printer health. |
| Manifest | `http://manifest.home/health` | HTTP 200 JSON `status: ok`. Does not cover scanner or queue health. |
| Jeopardy | `http://jeopardy-service:8080/health` | HTTP 200 `status: ok`; HTTP 503 `error: corpus unavailable` is known `failed`. Other shape changes produce `unknown`. |
| TriviaROM | `http://triviarom-service:8080/health` | Identity `TriviaROM`, loaded corpus, non-negative integer counts, playable ≤ total. |
| Wallboard | `http://wallboard.home/health` | Console expects HTTP 200 `status: ok`. **Open mismatch:** Wallboard source returns `{"ok": true}`, so the card should be `unknown`. Coordinate an application contract change; do not weaken checks just for a green badge. |
| BlackTorrent/qBittorrent | `http://192.168.1.100:8080/` | Any HTTP 2xx. Proves WebUI reachability only—not Gluetun, `tun0`, VPN egress, leak safety, or job state. |
| Home Assistant | `http://192.168.1.100:8123/api/` when `HOME_ASSISTANT_TOKEN` is configured | Bearer-authenticated HTTP 200 exact `{"message":"API running."}`. Token remains server-side. Does not inspect integrations, entities, automations, or devices. |
| Jellyfin | `http://192.168.1.100:8096/System/Info/Public` | Public HTTP 200 Jellyfin identity, version, ID, and completed startup wizard. Does not prove libraries, playback, transcoding, plugins, or Live TV. |
| Semavox | `http://semavox.home/api/status` | HTTP 200 plus the documented online/uptime/audio/volume/startup-chime/label schema. Proves the device API answered, not physical hardware behavior or flashed feature parity. |

Receipt, Jeopardy, and TriviaROM share external Docker network
`jarvis-receipt-services` with Console. Home Assistant, Label, Manifest, Wallboard,
BlackTorrent, Jellyfin, and Semavox are reached through LAN/DNS routes. Missing targets
produce `unknown`; there is no
cross-project startup dependency.

## Receipt action and shared data

| Connection | Contract | Ownership and risk |
| --- | --- | --- |
| Console → Receipt | One empty `POST http://receipt-service:8080/print/morning`; expected success has `status: sent`, integer `bytes`, and string `delivery`. | Receipt owns content, upstream calls, printer selection/locking, and delivery. A timeout may follow acceptance; retrying can duplicate paper. |
| Receipt volume → Console | External `morning-brief_schedule-data`, mounted read-only; `/receipt-data/telegram_history.sqlite3`; table `telegram_history`. | Receipt owns schema and writes. Renaming the volume, file, table, or selected columns makes history return 503. Never treat it as Console-owned data. |

History responses include message text, sender, public IP, derived location, receive
timestamp, and print status. This is sensitive household data even though the mount is
read-only.

## Browser launch connections

Console emits configurable links for Home Assistant, Receipt's repository, Label and its
subpages, Manifest, Jeopardy, TriviaROM, Wallboard, BlackTorrent, Jellyfin, Semavox, and
the Semavox repository. Home Assistant is navigation-only without its token; Home
Assistant, Jellyfin, and Semavox otherwise have bounded read-only status requests. Their
launch and secondary links remain navigation only.

Semavox is an ESP32-S3 LAN device, not a container. Receipt and Wallboard have separate
direct Semavox alert integrations documented in the central directory; Console does not
call or proxy those actions. Console only reads `/api/status`.

## External dependencies

- Python 3.12 standard library is the only runtime software dependency.
- Docker/Compose, the external shared network, and Receipt volume are deployment
  prerequisites.
- Local DNS, Synology reverse proxy, LAN routing, and the fixed NAS address are external.
- The base image `python:3.12-slim` is not digest-pinned, so rebuilds can change it.
- Console needs no secrets. Configuration rejects credentials embedded in URLs.

## Cross-project change checklist

Before changing a health payload, Receipt schema/volume, Docker alias/network, service
URL, or browser alias:

1. Update the owner first and inspect both sides of the contract.
2. Update the adapter/configuration and contract tests.
3. Update this page, top-level `INTEGRATIONS.md`, `ECOSYSTEM.md`, `SERVICE_CATALOG.md`,
   and hand-maintained `web/services.html` when applicable.
4. Preserve the read-only history boundary and non-retrying action behavior.
5. Treat tests as static evidence; deployment and hardware need separate authorization.
