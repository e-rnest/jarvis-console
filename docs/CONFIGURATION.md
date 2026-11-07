# Configuration

Source-audited 2026-11-06. Environment variables are read once at startup. Console does
not load `.env` itself; Compose may perform its normal interpolation.
`HOME_ASSISTANT_TOKEN` is a secret and must never be committed, logged, or exposed to the
browser. Other variables on this page are non-secret routing/configuration values.

## Server and action settings

| Variable | Default | Validation / purpose |
| --- | --- | --- |
| `HTTP_HOST` | `0.0.0.0` | Listener address; not otherwise validated. Compose does not pass it. |
| `HTTP_PORT` | `8080` | Integer 1–65535; Compose fixes the container value at 8080. |
| `STATUS_TIMEOUT_SECONDS` | `2` | Float 0.1–10, applied independently to each downstream request. |
| `MORNING_BRIEF_URL` | `http://receipt-service:8080/print/morning` | HTTP(S), host required, no credentials/query/fragment. |
| `MORNING_BRIEF_TIMEOUT_SECONDS` | `300` | Float 0.1–600. A timeout is ambiguous and never retried. |

## Checked services and launch links

| Service | Status variable and default | Browser link variables and defaults |
| --- | --- | --- |
| Receipt | `RECEIPT_STATUS_URL=http://receipt-service:8080/health` | `RECEIPT_REPOSITORY_URL=https://github.com/e-rnest/receipt-service` |
| Label | `LABEL_STATUS_URL=http://jarvis.home:5050/health` | `LABEL_LAUNCH_URL=http://label.jarvis.home/print`; `LABEL_QUICK_LABELS_URL=http://label.jarvis.home/labels`; `LABEL_FRIDGE_URL=http://label.jarvis.home/inventory`; `LABEL_FREEZER_URL=http://label.jarvis.home/inventory/frozen` |
| Manifest | `MANIFEST_STATUS_URL=http://manifest.home/health` | `MANIFEST_LAUNCH_URL=http://manifest.home/` |
| Jeopardy | `JEOPARDY_STATUS_URL=http://jeopardy-service:8080/health` | `JEOPARDY_LAUNCH_URL=http://jeopardy.home/` |
| TriviaROM | `TRIVIAROM_STATUS_URL=http://triviarom-service:8080/health` | `TRIVIAROM_LAUNCH_URL=http://trivia.jarvis.home/` |
| Wallboard | `WALLBOARD_STATUS_URL=http://wallboard.home/health` | `WALLBOARD_LAUNCH_URL=http://wallboard.home/` |
| BlackTorrent | `BLACKTORRENT_STATUS_URL=http://192.168.1.100:8080/` | `BLACKTORRENT_LAUNCH_URL=http://blacktorrent.home/`; `BLACKTORRENT_BACKUP_URL=http://blacktorrent.jarvis.home/` |
| Home Assistant | Conditional: `HOME_ASSISTANT_STATUS_URL=http://192.168.1.100:8123/api/`; enabled only when `HOME_ASSISTANT_TOKEN` is non-empty | `HOME_ASSISTANT_LAUNCH_URL=http://ha.jarvis.home/`; `HOME_ASSISTANT_SHORT_URL=http://ha.home/`; `HOME_ASSISTANT_DIRECT_URL=http://192.168.1.100:8123/` |
| Jellyfin | `JELLYFIN_STATUS_URL=http://192.168.1.100:8096/System/Info/Public` | `JELLYFIN_LAUNCH_URL=http://jellyfin.home`; `JELLYFIN_TV_GUIDE_URL=http://jellyfin.home/web/#/livetv?collectionType=livetv&tab=1` |
| Semavox | `SEMAVOX_STATUS_URL=http://semavox.home/api/status` | `SEMAVOX_LAUNCH_URL=http://semavox.home`; `SEMAVOX_FALLBACK_URL=http://192.168.1.80`; `SEMAVOX_REPOSITORY_URL=https://github.com/e-rnest/semavox` |

Status URLs must use HTTP(S), have a hostname, and contain no credentials, query, or
fragment. Launch/repository URLs use the same scheme/host/credential checks but may
contain queries and fragments for deep links.

## Launch-only services

| Service | Variables and defaults |
| --- | --- |
| Home Assistant | Launch-only only when `HOME_ASSISTANT_TOKEN` is empty |

Create a dedicated non-admin Home Assistant user, create a long-lived access token from
that user's profile, and place it in the deployment `.env` as `HOME_ASSISTANT_TOKEN`.
Console sends it only as an Authorization bearer header to the configured API root.

## Compose-only interpolation and resources

| Variable | Default | Purpose |
| --- | --- | --- |
| `LAN_BIND_IP` | `192.168.1.100` | Host address for the published port. |
| `CONSOLE_HOST_PORT` | `8791` | Host port mapped to container port 8080. |

Compose requires external network `jarvis-receipt-services` and external volume
`morning-brief_schedule-data`, mounted under the local name `ipps-history` at
`/receipt-data:ro`. The container also gets a private project-default network. It has no
`depends_on`, secrets, writable application volume, or Docker socket.

Invalid numeric values, ranges, or URLs raise `ValueError` during startup. Validation
does not resolve DNS or test connectivity. Keep internal targets separate from browser
links: Docker aliases may resolve only in the container, while friendly names may resolve
only for LAN browsers.
