# Jarvis documentation audit report

Audit date: 2026-11-05. Method: static reading of source and configuration. No service,
container, DNS record, proxy rule, printer or device was contacted. Nothing was committed or pushed.

## Scope

Top-level entries under `/Volumes/docker`: 9 Git repositories, 5 deployment directories
without Git (`wallboard`, `homeassistant`, `jellyfin`, `scrypted`, `jarvis-scanner`) and 4
supporting directories (`wallboard-private`, `backups`, `manifest-acceptance-runs`,
`manifest-food-database-raw`). Semavox is outside the share and was read but not changed.

Depth varied. Central contracts were traced in source. Label, Manifest and Jeopardy were
checked by routes and contracts, not line by line. The upstream-image projects (Home
Assistant, Matter Server, Scrypted, Jellyfin) were checked by configuration and README only.

## Contradictions

| # | Finding | Evidence | Status |
| --- | --- | --- | --- |
| 1 | Wallboard `/health` returns `{"ok": true}`; Console requires `status == "ok"`, so the card should read `unknown` | `wallboard/server.py:1271`, `jarvis_console/clients/wallboard.py` | **Open:** application fix needs authorization |
| 2 | `SERVICE_CATALOG.md` line 61 says Wallboard returns `status: ok` | Same as #1 | **Open:** file outside approved edit list |
| 3 | `SERVICE_CATALOG.md` and `web/services.html` say Wallboard deployment is not established | `wallboard/compose.yaml` | **Open:** same restriction; `services.html` is an application asset |
| 4 | `Jarvis Service URL and API Inventory.md` is dated 2026-10-01 and predates current Receipt routes and printers | `receipt_service/app/http.py` | **Open:** same restriction |
| 5 | Semavox documents 429 as retry; neither sender retries | `semavox_alerts.py`, `integrations/sema_vox.py` | **Open:** may be intended best effort |
| 6 | Receipt README omitted `GET /print`, to-do list and capabilities routes | `receipt_service/app/http.py` | Fixed |
| 7 | Label README had no route index and omitted history, Quick Label and location routes | `label-service/app.py` | Fixed |
| 8 | Wallboard restart dedupe was marked untraced | `nfl_service.py`, `nfl_events.py` | Fixed in `INTEGRATIONS.md` |

## Unverified claims

- Every "Production" label in `ECOSYSTEM.md`. It is a judgment from configuration.
- All friendly hostnames; DNS and DSM proxy rules are outside these repositories.
- Which image or commit each container runs, and which firmware Semavox runs.
- The Jellyfin container definition, which is not on this share.
- Which container owns the scanner: both `manifest-scanner` and `jarvis-scanner` mount input devices.
- The "historically observed" statements in `AGENT_OPERATIONS.md`, including physical ES7210
  tests. They are reports, not findings of this audit.
- Semavox commit `07097ea`, which is absent from the local checkout's refs.

## Remaining gaps

- `/services` does not expose these documents. Doing so means editing `web/services.html`,
  and `Dockerfile` copies only `jarvis_console` and `web`, so the Markdown is not in the image.
- Semavox has no `AGENTS.md` or `CLAUDE.md`; it needs separate authorization.
- `$HOME/dev/wallboard` and `/volume1/docker/wallboard` have no documented reconciliation path.
- `wallboard` has no test suite in its deployment directory.
- `manifest-acceptance-runs` and `manifest-food-database-raw` have no README.
