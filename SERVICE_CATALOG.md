# Jarvis service catalog

This is the source-backed inventory for the Docker services mounted under
`/volume1/docker` on the Jarvis host. It was reconciled against the service
Compose files, application configuration, and READMEs on 2026-10-22. The same
inventory is available on the LAN as the Console's
[HTML service catalog](http://console.jarvis.home/services).

Secrets, credentials, tokens, private databases, media history, camera/device
state, and downloaded content are intentionally excluded. Docker was not
available in the documentation environment, so this records deployment intent
from files rather than claiming current container uptime. Container IPs are
intentionally absent: Docker assigns them dynamically, and callers must use a
service/network alias or the fixed Jarvis LAN address instead.

## Addressing conventions

- **Jarvis LAN IP:** `192.168.1.100`.
- **Canonical household names:** use the documented friendly name when one
  exists. The `*.jarvis.home` namespace is preferred for Jarvis services;
  shorter `.home` names are retained where they are already established.
- **Published port:** a host port reachable on the trusted LAN. `host network`
  means the container shares Jarvis's network namespace and Compose publishes
  no separate port.
- **Docker alias:** usable only by containers attached to that Docker network.
  It is not a browser URL and must never be emitted by Console's API.
- **No listener:** the component initiates outbound traffic or reads a local
  device but does not expose a browser/API port.

## Complete service and address table

| Project / component | Container or Compose service | Household entry points and aliases | Host bind / service port | Docker network and aliases | Console representation |
| --- | --- | --- | --- | --- | --- |
| Jarvis Console | `jarvis-console` | `console.jarvis.home`; direct `jarvis.home:8791`; `192.168.1.100:8791` | `192.168.1.100:8791` → `8080` | project default + `jarvis-receipt-services`; hostname `jarvis-console` | Own process health and service dashboard |
| Home Assistant | `homeassistant` | `ha.jarvis.home`; `ha.home`; direct `192.168.1.100:8123` | host network, application `8123` | host network | Launch-only card; no accepted Console health contract |
| Matter Server | `matterjs-server` | Infrastructure only; Home Assistant uses `ws://127.0.0.1:5580/ws` | host network, service `5580` | host network | Catalog only; no general UI or accepted health contract |
| Receipt Service | `receipt-service` | API at `jarvis.home:8788` / `192.168.1.100:8788`; printer DNS `receipt.home` is a dependency, not the service | `192.168.1.100:8788` → `8080`; printer `9100` | project default + `jarvis-receipt-services`; aliases `receipt-service`, `morning-brief` | Health, scheduler detail, Morning Brief action, read-only Telegram history, repository link |
| Label Service | `label-service` | `label.jarvis.home`; direct/integration route `jarvis.home:5050`; older docs also reference `go.home:5050`; printer DNS `labeler.home` is a dependency | `0.0.0.0:5050` → `5050`; printer `9100` | project default; service name `label-service` | Health, Print, Quick Labels, Fridge, and Freezer links |
| Manifest | Compose service `manifest` in project `manifest-service` | `manifest.home`; direct `192.168.1.100:8000` | active `.env`: `192.168.1.100:8000` → `8000`; safe Compose default is loopback | project default; service name `manifest` | Health and launch card |
| Manifest Scanner | `manifest-scanner` (Compose service `scanner`) | No listener; delivers to `192.168.1.100:8000/api/v1/scans` by default | no listener | project default bridge; outbound HTTP only | Catalog only; no accepted health endpoint |
| Jarvis Scanner | `jarvis-scanner` (Compose service `scanner`) | No listener; observation-only barcode logging | no listener | `network_mode: none` | Catalog only; legacy standalone scanner, not a Manifest delivery path |
| Jeopardy Service | `jeopardy-service` | `jeopardy.home`; direct `192.168.1.100:8789` when bound to the Jarvis LAN address | `${LAN_BIND_IP:-0.0.0.0}:8789` → `8080` | project default + `jarvis-receipt-services`; hostname/service alias `jeopardy-service` | Corpus-aware health and launch card |
| TriviaROM | `triviarom-service` | `trivia.jarvis.home`; direct `192.168.1.100:8790` | `192.168.1.100:8790` → `8080` | project default + `jarvis-receipt-services`; hostname/service alias `triviarom-service` | Corpus counts and launch card |
| Wallboard | deployment details not present in the mounted sources | `wallboard.home` | not established from mounted sources | not established from mounted sources | JSON health and launch card |
| BlackTorrent / Gluetun | `gluetun` | `blacktorrent.home`; `blacktorrent.jarvis.home`; direct `192.168.1.100:8080` | `192.168.1.100:8080` → shared namespace port `8080` | project default; owns the qBittorrent network namespace and published port | WebUI reachability and two launch links |
| BlackTorrent / qBittorrent | `qbittorrent` | Same browser aliases as Gluetun's published WebUI | no independent published port | `network_mode: service:gluetun` | Represented by the BlackTorrent card; no independent control |
| Jellyfin | deployment definition not present in the mounted directory; configured server name `jellyfin` | `jellyfin.home`; known direct route `192.168.1.100:8096` | configured HTTP `8096`; exact container mapping is not source-backed here | unknown from mounted sources | Launch and TV Guide links; no accepted health contract |
| Semavox | ESP32-S3 firmware (not a container) | `semavox.home`; fixed IP fallback `192.168.1.80`; HTTP API preserves `/api/speak`, `/api/audio`, and `/api/status` | device HTTP port `80` | trusted LAN device; no Docker network | Launch-only card, fixed-IP fallback, and repository link; `/api/status` is not treated as a stable health contract |
| Scrypted | `scrypted` | Canonical household URL not established in mounted sources | host network; UI port not asserted here | host network | Catalog only until a verified LAN URL and health contract exist |

## Health contracts

| Component | Contract | What it proves | What it does not prove |
| --- | --- | --- | --- |
| Console | `GET /health` → HTTP 200 JSON with `status: ok` | Console process and HTTP handler respond | Any downstream service |
| Receipt | `GET /health` accepted by the Receipt adapter | Service, scheduler state, and print-lock state | Printer reachability, paper output, or upstream content providers |
| Label | `GET /health` → HTTP 200 JSON with `status: ok` | Flask process responds | Brother printer reachability or physical output |
| Manifest | `GET /health` → HTTP 200 JSON with `status: ok` | Inventory application responds | Scanner process, scanner device, or queue depth |
| Jeopardy | `GET /health` with accepted healthy response | HTTP process and readable clue corpus | Receipt printer availability |
| TriviaROM | `GET /health` with valid corpus counts | Loaded and validated trivia corpus | Content suitability or Receipt availability |
| Wallboard | `GET /health` → HTTP 200 JSON with `status: ok` | Wallboard application responds | Display device, kiosk browser, or screen state |
| BlackTorrent | unauthenticated `GET /` returns 2xx | qBittorrent WebUI is reachable through the published Gluetun namespace | VPN tunnel, `tun0`, leak safety, or container state |
| Home Assistant, Matter Server, Manifest Scanner, Jarvis Scanner, Jellyfin, Semavox, Scrypted | no accepted Console contract | Nothing is probed | Console must not infer health from a homepage, evolving status API, or deployment presence |

Console status words are strict: **healthy** is a validated contract,
**failed** is an explicit supported failure, **unknown** means the check could
not establish truth, and **unavailable** means no accepted check is configured.

## Persistence and backup scope

| Project | Durable or generated state | Backup / restore rule |
| --- | --- | --- |
| Console | no application database; read-only Receipt history mount | Rebuild from source; do not treat the read-only mount as Console-owned |
| Home Assistant | complete `config/` tree | Back up the whole directory, including `.storage`, before migration or integration work |
| Matter Server | complete `data/` tree | Treat as opaque fabric state; back up before upgrade, reset, or recommissioning |
| Receipt | external `morning-brief_schedule-data` volume; read-only config and private key input | Preserve the external volume and deployment secrets separately |
| Label | application files and its local inventory/audit data in the bind-mounted project | Back up data/audit files according to its README; never infer successful paper output from an HTTP response |
| Manifest | `data/`, `backups/`, and read-only generated `catalog/` | Use Manifest's integrity-checked backup/isolated-restore workflow; catalog can be regenerated |
| Manifest Scanner | `state/queue.db` and SQLite sidecars | Back up only while quiesced or with a SQLite-safe method; never delete a queue to clear an incident |
| Jarvis Scanner | none | Logs are transient; there is no delivery queue |
| Jeopardy | generated `data/jeopardy.sqlite` mounted read-only | Preserve the source TSV separately or back up the generated corpus |
| TriviaROM | immutable corpus in the image; in-memory recent-ID ring | Rebuild from source; restart intentionally clears recent history |
| BlackTorrent | Gluetun state, qBittorrent config, watch directory, and downloads | Back up configuration/state separately; downloaded content policy is operator-defined |
| Jellyfin | mounted `config/`, metadata, plugins, databases, logs, and `cache/` | Back up configuration/databases; cache and transcodes are replaceable; never publish embedded tokens |
| Semavox | firmware source, local Wi-Fi secrets, and persistent device configuration | Rebuild firmware from source; keep Wi-Fi credentials out of version control and preserve any required PicoTTS model files |
| Scrypted | mounted `volume/` including its database and plugin state | Back up the complete volume before upgrades or migration; treat device/plugin state as private |

## Integration ownership

- Home Assistant owns automation policy and calls Receipt for selected aircraft
  events. Receipt owns validation, layout, printer locking, and delivery.
- Home Assistant consumes Matter Server over same-host WebSocket. Matter Server
  owns fabric and commissioned-node persistence.
- Manifest Scanner captures Zebra events, commits each event to a durable FIFO,
  and retries the same event ID. Manifest owns idempotency and inventory meaning.
- Console calls Receipt, Jeopardy, and TriviaROM over
  `jarvis-receipt-services`; it reaches Label and Manifest through their accepted
  LAN routes.
- Jeopardy delegates clue printing to Receipt. Receipt consumes TriviaROM and
  Jeopardy content and may call Label through the LAN route.
- qBittorrent has no independent network path; it shares Gluetun's namespace.
  Never add a separate qBittorrent network or published port without revalidating
  the VPN fail-safe.
- Jellyfin and Scrypted are operationally independent of the shared Jarvis
  application network.
- Semavox is a trusted-LAN embedded device. Console only links to its browser
  interface; speech requests and Home Assistant automation remain external.

## Source directories and local documentation

| Project | Host directory | README |
| --- | --- | --- |
| Console | `/volume1/docker/jarvis-console` | [Jarvis Console](README.md) |
| Receipt | `/volume1/docker/receipt-service` | [Receipt Service](../receipt-service/README.md) |
| Label | `/volume1/docker/label-service` | [Label Service](../label-service/README.md) |
| Manifest | `/volume1/docker/manifest-service` | [Manifest](../manifest-service/README.md) |
| Manifest Scanner | `/volume1/docker/manifest-scanner` | [Manifest Scanner](../manifest-scanner/README.md) |
| Jarvis Scanner | `/volume1/docker/jarvis-scanner` | [Jarvis Scanner](../jarvis-scanner/README.md) |
| Jeopardy | `/volume1/docker/jeopardy-service` | [Jeopardy Service](../jeopardy-service/README.md) |
| TriviaROM | `/volume1/docker/triviaROM-service` | [TriviaROM](../triviaROM-service/README.md) |
| BlackTorrent | `/volume1/docker/blacktorrent` | [BlackTorrent](../blacktorrent/README.md) |
| Home Assistant | `/volume1/docker/homeassistant` | [Home Assistant](../homeassistant/README.md) |
| Matter Server | `/volume1/docker/matterjs-server` | [Matter Server](../matterjs-server/README.md) |
| Jellyfin | `/volume1/docker/jellyfin` | [Jellyfin](../jellyfin/README.md) |
| Scrypted | `/volume1/docker/scrypted` | [Scrypted](../scrypted/README.md) |

## Documentation maintenance rule

Update this catalog whenever a service is added, removed, renamed, given a new
published port, moved between networks, assigned a new household alias, or
given a new health contract. Update the service-local README in the same change.
Runtime observations should be dated and labeled as observations; Compose and
application behavior remain the source for durable claims.
