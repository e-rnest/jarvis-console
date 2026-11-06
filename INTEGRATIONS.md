# Jarvis integration directory

Source-verified on 2026-11-05 by static reading, unless a row says otherwise. Nothing here was
exercised live. Authentication is **none** for all LAN routes. "Owner" is the side that should
change first and notify the other.

## Event and data integrations

| Source → destination | Trigger | Protocol and endpoint | Data | Configuration | Failure behavior | Source files | Safe verification |
| --- | --- | --- | --- | --- | --- | --- | --- |
| Wallboard → Semavox (owner: Wallboard) | New NFL event for enabled types | `POST /api/alert`, JSON | `theme: nfl`; kickoff, touchdown, field goal, halftime, final | `WALLBOARD_SEMAVOX_URL` overrides `nfl.semavox_url` | One attempt, 1s connect and 2s read. Queue of 8; overflow is dropped and logged. In-memory dedupe of 100 IDs. **No retry, including on 429.** | `wallboard/semavox_alerts.py`, `nfl_events.py`, `nfl_service.py` | `GET wallboard:8787/nfl/events`; Wallboard has no test suite in this directory; Semavox `tools/alert_test/run.sh` on host |
| ESPN → Wallboard | Poller thread: 30s live, 300s idle, slower when quiet | HTTPS JSON | Scores and scoring plays | `nfl` in `config.json`, `config.local.json` | Backoff up to 5 min; dashboard serves last snapshot | `wallboard/nfl_provider.py`, `nfl_service.py` | `GET /nfl` |
| Receipt → Semavox (owner: Receipt) | After a Telegram receipt prints successfully | `POST /api/alert`, JSON | `telegram.received`, `theme: scanning_eyes`. **No text or sender leaves Receipt.** | `SEMA_VOX_URL`, `SEMA_VOX_NOTIFICATIONS_ENABLED` | Best effort; printing is unaffected. 200 duplicate and 202 count as success; 409 and 429 are logged | `receipt_service/integrations/sema_vox.py`, `features/friend_printing/listener.py` | Unit tests. `play-semavox` makes sound, so it needs approval |
| Browser IPPS page → ntfy → Receipt | Sender submits form | HTTPS, outbound subscription by Receipt | RSA-OAEP and AES-GCM envelope | `TELEGRAM_TOPIC` (secret, blank disables), `IPPS_PRIVATE_KEY_FILE` | Durable ledger; see Receipt README | `receipt_service/telegram_listener.py`, `features/friend_printing/` | Unit tests only. Publishing prints paper |
| Receipt → Epson and EOM printers | Manual jobs go to Epson; scheduled brief goes to EOM | Raw TCP 9100, ESC/POS | Receipt bytes | `RECEIPT_PRINTER_*`, `SCHEDULED_MORNING_PRINTER_*` | Shared lock; no physical completion signal | `receipt_service/printer/` | Unit tests; `/print` menu is read-only to open |
| Receipt → Label | Morning Brief or inventory receipt | `GET /api/inventory/items` | Active fridge items | `LABEL_SERVICE_BASE_URL` | Bounded timeout (`INVENTORY_TIMEOUT_SECONDS`) | `features/inventory/client.py` | `GET` the route |
| Receipt → Jeopardy | Jeopardy receipt | `GET /api/jeopardy/...` via Docker alias | Clue | `JEOPARDY_SERVICE_BASE_URL` | Bounded timeout | `features/jeopardy/client.py` | `GET /api/jeopardy/random` |
| Receipt → TriviaROM | Morning Brief | `GET /api/trivia/...` via Docker alias | Question | `TRIVIAROM_SERVICE_BASE_URL` | Bounded timeout | `features/morning_brief/triviarom_client.py` | `GET /api/trivia/random` |
| Jeopardy → Receipt | User prints a clue | `POST /print/jeopardy?id=` to `morning-brief:8080` | Clue ID | `RECEIPT_SERVICE_BASE_URL` | Error surfaced to caller | `jeopardy/http.py` | Unit tests. A live call prints |
| Home Assistant → Receipt | Aircraft automation | `POST 192.168.1.100:8788/print/aircraft`, JSON | Flight fields | `rest_command.print_aircraft_receipt` | Set by HA | `homeassistant/config/configuration.yaml`, `automations.yaml` | Read config. A live call prints |
| Home Assistant → Matter Server | Runtime | `ws://127.0.0.1:5580/ws` | Matter nodes | HA integration | Set by HA | `matterjs-server/compose.yaml`, READMEs | Inspect HA integration page |
| Zebra → Manifest Scanner | Barcode scan | evdev | Keystrokes | Device name match, `/dev/input` mount | Durable SQLite FIFO | `manifest-scanner/scanner.py` | Tests in `tests/` |
| Manifest Scanner → Manifest | Queue drain | `POST /api/v1/scans` | Event with stable ID | `MANIFEST_URL` | Retries the same event ID; Manifest dedupes | `scanner.py`, `barcode_service/scanner/routes.py` | Isolated tests per `ISOLATED_SCANNER_TESTS.md` |
| Manifest → Label | User prints a location or container label | `POST /print/location`, `POST /print/text` | Barcode or text | `MANIFEST_LABEL_SERVICE_URL` | 15s timeout; rejection becomes HTTP 502 | `barcode_service/labels/routes.py`, `label-service/app.py` | Unit tests. A live call prints |
| Label → Brother QL-710W | Print route | Raw TCP 9100, `brother_ql` raster | Label image | `BROTHER_PRINTER_HOST` | Audit log is best effort | `label-service/brother.py`, `print_audit.py` | `GET /print/history` |

## Console integrations

| Target | Route | Accepted contract | File |
| --- | --- | --- | --- |
| Receipt | `receipt-service:8080/health` | Receipt adapter | `clients/receipt.py` |
| Label | `jarvis.home:5050/health` | `status: ok` | `clients/label.py` |
| Manifest | `manifest.home/health` | `status: ok` | `clients/manifest.py` |
| Jeopardy | `jeopardy-service:8080/health` | Corpus-aware | `clients/jeopardy.py` |
| TriviaROM | `triviarom-service:8080/health` | Corpus counts | `clients/triviarom.py` |
| Wallboard | `wallboard.home/health` | `status: ok`. **Wallboard returns `{"ok": true}`, so see the mismatch below.** | `clients/wallboard.py` |
| BlackTorrent | `192.168.1.100:8080/` | Any 2xx; proves only WebUI reachability | `clients/blacktorrent.py` |
| Receipt print | `POST receipt-service:8080/print/morning` | One guarded request, never retried | `actions.py` |
| Telegram history | `/receipt-data/telegram_history.sqlite3`, read-only | Receipt's schema | `http.py` |

Home Assistant, Jellyfin and Semavox are launch links only.

## Known contract problems

1. **Wallboard health mismatch.** `wallboard/server.py:1271` returns `{"ok": true}`, while
   `clients/wallboard.py` requires `status == "ok"`. From source, the Console card should read
   `unknown`. The Console test stub uses `{"status": "ok"}`, so tests do not catch this. Not fixed: it is application behavior.
2. **Semavox 429 handling.** Semavox documents 429 as "retry with the same ID". Neither sender retries, so an alert during a full queue is lost. This may be intended best-effort behavior.
3. **Wallboard dedupe after restart.** The notifier's seen-ID set is in memory, but the event tracker's per-game state is persisted, and `nfl_service.py` saves it before calling `submit`. A restart therefore should not resubmit a saved event. If that save fails, an event could be derived again, and Semavox's own 15-minute dedupe limits the effect. Traced from source only.

## Semavox surfaces

The contract is `API.md` in the firmware repository. The historical
`alert-typography-e` integration entered `main` through PR #9 at
`8a4a2394191c85a2c50bd0032b5e36d81a1913ca`; a later README correction was committed at
`07097ea024a2b60e3de3362fcb58d959d2e71039` (reported; this SHA was not in the local checkout's refs on 2026-11-05, while `8a4a239` was the local `origin/main`). These are milestones, not current branch-head
claims. New work should verify refs and start from current `origin/main`. Routes
confirmed in `src/main.cpp` include `/api/status`, `/api/brightness`, `/api/mode`,
`/api/spectrum/settings`, `/api/eyes`, `/api/audio`, `/api/speak`, `/api/sound`, `/api/stop`,
`/api/volume`, `/api/settings`, `/api/startup`, `/api/label`, `/api/nanoheart` and `/api/gains`.

- **Modes:** `eyes`, `synthwave`, `rain`, `lightcycle`, `chaos`, `litebrite`, `fire`, `outrun`, `splitflap`, `spectrum`.
- **Microphone:** the `spectrum` mode reads the ES7210 when it is showing, with fallback to speaker audio. Subsequent physical testing historically verified live room capture, Scope, Bars, and runtime switching. That successful test does not prove the device's current runtime state, and host tests alone remain insufficient hardware evidence.
- **Runtime settings:** brightness and spectrum settings are not persisted and reset on reboot.
- **Flashed version:** unknown. Do not assume the checkout's features are on the device.
