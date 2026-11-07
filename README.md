# Jarvis Console

Jarvis Console is the trusted-LAN front door for the Jarvis household services. It
provides a browser dashboard, strict and failure-isolated downstream status checks,
launch links, a read-only view of Receipt Service's encrypted-IPPS/“Thermal Telegram”
history, and one guarded physical action: requesting a Morning Brief print.

Console is an observer and client, not a service manager. It does not inspect or
control Docker, own downstream data, schedule prints, verify printer or device
hardware, or retry physical actions. Every downstream continues to operate if Console
is unavailable.

This documentation was source-audited on **2026-11-06** against the Python code,
tests, Dockerfile, Compose definition, web assets, and relevant neighboring service
contracts. It does not claim that a container, DNS record, reverse-proxy rule, printer,
or device was live at audit time.

## Capabilities

- Normalizes status for Receipt, Label, Manifest, Jeopardy, TriviaROM, Wallboard,
  BlackTorrent, and Semavox without exposing internal check URLs to the browser.
- Runs checks concurrently with bounded timeouts; one bad service does not hide peers.
- Uses Home Assistant's authenticated API root, Jellyfin's public system-info API,
  and Semavox's structured `/api/status` for bounded service identity/readiness
  without claiming physical-device or media-playback behavior. Home Assistant remains
  launch-only until its dedicated token is configured.
- Reads up to 50 newest Telegram-history rows from Receipt's SQLite database through
  a read-only Docker mount and SQLite `mode=ro` connection.
- Proxies exactly one Morning Brief request at a time, with no automatic retry and
  explicit `success`, `failed`, `busy`, and `uncertain` outcomes.
- Serves the hand-maintained `/services` ecosystem catalog alongside the dashboard.
- Displays backend version `1.1.0` and build `2026.11.06.1` in the dashboard footer.
- Uses only Python 3.12's standard library plus static HTML, CSS, and JavaScript.

## Access

- Preferred: `http://console.jarvis.home/`
- Direct host: `http://jarvis.home:8791/`
- Direct IP: `http://192.168.1.100:8791/`

The friendly URLs depend on local DNS and Synology reverse-proxy configuration, both
managed outside this repository. There is no authentication or TLS in Console; do not
expose it to the public Internet. The history endpoint contains household-private
message and network metadata, and the action endpoint can consume paper.

## Quick start

```sh
python3.12 -m jarvis_console
python3.12 -m unittest discover -s tests -v
python3.12 -m compileall -q jarvis_console tests
git diff --check
```

The default listener is `0.0.0.0:8080`. Most checks will be unavailable unless the host
can resolve and reach the configured Docker/LAN targets. Tests use disposable fake
servers and do not contact household services, printers, or devices.

## Docker deployment summary

`compose.yaml` builds the local image, publishes `${CONSOLE_HOST_PORT:-8791}` on
`${LAN_BIND_IP:-192.168.1.100}`, mounts the external Receipt volume
`morning-brief_schedule-data` read-only at `/receipt-data`, and joins the external
`jarvis-receipt-services` network. Those external resources must exist before startup.

Production changes require an image rebuild and container recreation because source,
web assets, and served HTML are copied into the image. Do not deploy merely to verify
documentation; see [Operations](docs/OPERATIONS.md) for the authorized procedure,
backup boundary, health checks, troubleshooting, and rollback.

## Documentation

- [Architecture](docs/ARCHITECTURE.md) — components, concurrency, data flows, and
  implementation boundaries.
- [Integrations](docs/INTEGRATIONS.md) — every inbound/outbound connection, contracts,
  ownership, and change risks.
- [Operations](docs/OPERATIONS.md) — Docker deployment, logs, maintenance, backups,
  troubleshooting, and rollback.
- [API](docs/API.md) — Console's HTTP endpoints and response contracts.
- [Configuration](docs/CONFIGURATION.md) — all environment variables, validation,
  Docker resources, and external infrastructure.
- [Service catalog](SERVICE_CATALOG.md) — ecosystem-wide ports, aliases, networks,
  health contracts, and persistence.
- [Ecosystem map](ECOSYSTEM.md) and [central integration directory](INTEGRATIONS.md) —
  cross-project orientation beyond Console's direct connections.
- [Agent operations](AGENT_OPERATIONS.md) — mandatory production-safety guidance.

## Status model

| State | Meaning |
| --- | --- |
| `healthy` | A service-specific accepted contract returned a valid healthy response. |
| `failed` | A supported contract explicitly reported a known failure/degraded state. |
| `unknown` | Timeout, transport failure, malformed data, schema mismatch, or an unexpected adapter failure prevented a truthful conclusion. |
| `unavailable` | The card is navigation-only; no status request is made. |

Status is intentionally conservative. BlackTorrent's check proves only that the
qBittorrent WebUI returned 2xx, not that the VPN is safe. No check proves physical
paper output, scanner operation, display state, or device firmware state.

## Important known gap

Source inspection shows Wallboard currently returns `{"ok": true}` from `/health`,
while Console accepts only `{"status": "ok"}`. The Wallboard card should therefore be
`unknown` until one side's application contract changes. This documentation records
the mismatch; it does not weaken the adapter to make the badge green.

There are no documented planned Console features in this repository. Ideas such as a
notification hub, container controls, or inferred physical-device health are not implemented.
