# Start here: Jarvis ecosystem guide for agents

Read this first when you are given a change somewhere in the Jarvis ecosystem.
Mandatory operations guidance: [AGENT_OPERATIONS.md](AGENT_OPERATIONS.md). Reference
pages: [ECOSYSTEM.md](ECOSYSTEM.md) (catalog, architecture, operations) and
[INTEGRATIONS.md](INTEGRATIONS.md) (cross-service contracts and known contradictions).

## Paths

The same share has three names. `/volume1/docker` is the path on the Jarvis NAS, and
Compose files and deployment commands use it. `/Volumes/docker` is the SMB mount on the
Mac. There is no `/docker`. Editing a file through the mount changes the production
directory, but a running container does not pick it up until someone rebuilds it.

## 1. Find the correct repository

Use the catalog in [ECOSYSTEM.md](ECOSYSTEM.md#service-catalog). Common traps:

- **Scanner:** `manifest-scanner` delivers scans. `jarvis-scanner` only logs them.
- **Food inventory:** Label Service and Manifest each hold separate inventory data.
- **Telegram:** this is a feature of Receipt Service, reached through IPPS and ntfy. It does not use the Telegram app or API.
- **Semavox:** the firmware repository is outside this share, in the user's iCloud Arduino folder.
- **Wallboard:** not a git repository. Its secrets and state are in `wallboard-private`.

## 2. Find the contract

Look up the service in [INTEGRATIONS.md](INTEGRATIONS.md), then read the listed source
files. Source beats documentation. Check both sides of a contract before changing either one.

## 3. Trace a cross-service event

Start at the producer, follow the integration row to the consumer's route, and read that
service's logs. Example, an NFL touchdown: ESPN → `wallboard/nfl_provider.py` →
`nfl_events.py` → `nfl_service.py` → `semavox_alerts.py` → `POST semavox.home/api/alert` →
Semavox `src/alert_core.h` and `src/alert_display.h`.

## 4. Avoid the wrong deployment

- Check `git status` first. Preserve any work you did not make.
- Backup, baseline and `.before-*` copies are not live code. Neither are `backups/`, `baseline-*`, `*backup*` or `archive`.
- `manifest-service` has extra worktrees under `~/.codex/worktrees`, both detached at `2fc1556`.
- A Semavox checkout is not proof of what is flashed. The checkout is on a feature branch.
- Docker aliases such as `morning-brief` work only inside `jarvis-receipt-services`.

## 5. Verify safely

Use `GET` routes and each repository's tests. Do not call these without explicit approval,
because they have physical or production effects:

- `POST /print/*` on Receipt or Label, and `POST /api/actions/morning-brief` on Console (paper output)
- `POST /api/alert`, `/api/speak`, `/api/audio` or `/api/mode` on Semavox (sound or display)
- `docker compose up`, `down`, `restart` or `build` (production restart)
- Publishing to the ntfy topic (prints a Telegram receipt)
- Flashing firmware, or enabling Semavox microphone modes
- Clearing any queue, or opening `.env`, `secrets/`, `wallboard-private/*.json` or Telegram history

## 6. Update documentation

When you add or change an integration, update in the same change:

1. The owning service's README.
2. The row in [INTEGRATIONS.md](INTEGRATIONS.md).
3. [ECOSYSTEM.md](ECOSYSTEM.md) if a name, port, alias, network or status changed.
4. `SERVICE_CATALOG.md` and `web/services.html`, which feed the live `/services` page.

Label each claim as source-verified or observed at runtime, with a date.
