# Operations

Source-audited 2026-11-06. Run deployment-changing commands only with explicit
authorization. On Synology the path is `/volume1/docker/jarvis-console`; the same
production files appear on the Mac at `/Volumes/docker/jarvis-console`. Editing the SMB
mount changes production files but not the image-based running container.

## Deployment model and prerequisites

The Dockerfile uses `python:3.12-slim`, copies `jarvis_console/` and `web/`, creates UID
10001, and runs `python -m jarvis_console` as non-root. Compose uses `restart:
unless-stopped`, an init process, a process-only healthcheck, and rotating JSON logs
(5 MiB, three files).

Before deployment verify:

1. The intended source/Compose file and unrelated tracked or untracked work.
2. External network `jarvis-receipt-services` exists.
3. External volume `morning-brief_schedule-data` exists and is Receipt-owned.
4. `${LAN_BIND_IP:-192.168.1.100}:${CONSOLE_HOST_PORT:-8791}` is intended.
5. DNS and Synology reverse-proxy rules are configured separately.

Console requires no secrets. Do not open `.env` or secret files for routine work.

## Authorized rollout

From `/volume1/docker/jarvis-console` on the NAS:

```sh
sudo docker compose build jarvis-console
sudo docker compose up -d jarvis-console
sudo docker compose ps jarvis-console
sudo docker compose logs --tail=100 jarvis-console
```

A rebuild/recreate is required after Python, web assets, Dockerfile, Compose environment,
or `/services` changes. Markdown under `docs/` is not copied into the image. Do not add
downstream `depends_on`; Console is designed to tolerate missing peers.

## Verification

Safe pre-deployment checks:

```sh
python3.12 -m unittest discover -s tests -v
python3.12 -m compileall -q jarvis_console tests
git diff --check
```

After an authorized deployment, bounded read-only checks include:

```sh
curl --fail --silent http://127.0.0.1:8791/health
curl --fail --silent http://127.0.0.1:8791/api/status
sudo docker compose ps jarvis-console
sudo docker compose logs --tail=100 jarvis-console
```

Use the published address if loopback is not bound. Never call the Morning Brief POST as
a health check—it can print paper.

## Logs and health

Logs go to stdout/stderr and include access entries, startup, disconnects, missing assets,
and history-query exceptions. Adapter connection/schema errors are returned in status
summaries but are not separately logged.

The healthcheck calls `http://127.0.0.1:8080/health` every 30 seconds with a 5-second
timeout, 10-second start period, and three retries. It proves Console only;
`/api/status` may contain failures while the container is healthy.

## Backups and persistent data

Console owns no persistent state. Back up source and deployment configuration normally.
Do not copy, repair, prune, or restore the mounted Receipt volume as Console data.

Receipt owns `morning-brief_schedule-data`, including scheduler state and private history.
Its backup/restore must follow Receipt procedures and use a SQLite-safe or quiesced
method. Preserve both the Compose `:ro` mount and SQLite `mode=ro`. DNS and reverse-proxy
configuration are external and need separate backup.

## Troubleshooting

### Container will not start

- Read the startup exception for invalid numeric or URL configuration.
- Confirm port/address availability and external network/volume names.
- Confirm UID 10001 can read copied assets and the mounted database.
- Distinguish Mac, NAS, and container checks; Docker aliases resolve only on the shared
  network.

### A card is `unknown`

- Read the card's schema/transport summary.
- If authorized, make one bounded read-only request from inside the container.
- Check shared-network membership for Receipt, Jeopardy, TriviaROM; check LAN DNS/routing
  for Home Assistant, Label, Manifest, Wallboard, BlackTorrent, Jellyfin, and Semavox.
- Account for Wallboard's known `{"ok":true}` versus `{"status":"ok"}` mismatch.
- Do not weaken an adapter or use a homepage merely to make a badge green.

### A card is `unavailable`

Intentional for Home Assistant only when `HOME_ASSISTANT_TOKEN` is empty: navigation-only,
not confirmed downtime.

### Telegram history returns 503

- Confirm the volume is mounted at `/receipt-data` read-only.
- Confirm Receipt still owns the expected file, table, and selected columns.
- Inspect logs for `ipps_history_unavailable` without printing message contents.
- Do not mutate or repair the database through Console.

### Morning Brief is busy, failed, or uncertain

- `busy`: another request is in flight in this process.
- `failed`: Receipt returned a definite rejection; inspect Receipt and printer conditions.
- `uncertain`: inspect the physical printer before retrying; the job may have been accepted.

The lock is process-local. Multiple Console instances require checking Receipt's own lock
and logs.

### Friendly URL fails but direct URL works

Check external local DNS and Synology reverse proxy. Do not change internal health targets
to compensate for browser routing.

## Rollback

Before an authorized rollout, record the running image ID and preserve the previous
source revision/build artifact. If the new container fails:

1. Capture bounded logs and `/health`.
2. Restore prior source or retag the recorded image without deleting shared resources.
3. Recreate only `jarvis-console` and verify `/health` and the read-only dashboard.
4. Do not invoke the Morning Brief action during verification.

There is no Console database migration to reverse. Never use `docker compose down -v`;
the external volume belongs to Receipt and contains durable private state. Do not clear
queues, histories, images, or unrelated containers during rollback.
