# JARVIS Agent Operations Playbook

This is the durable operating guide for coding agents working anywhere in the JARVIS
ecosystem. Read it before running diagnostics, changing source, or proposing a deployment.
Use [START_HERE.md](START_HERE.md) for orientation, [ECOSYSTEM.md](ECOSYSTEM.md) for the
service catalog, and [INTEGRATIONS.md](INTEGRATIONS.md) for cross-service contracts.

## Evidence labels

- **Source-verified (2026-11-05):** confirmed by static inspection of a checkout,
  configuration, Compose file, or tool. This does not prove what is currently running.
- **Historically observed:** reported from a successful or failed real operation. Treat it
  as useful operational evidence, not a guarantee that the environment has not changed.
- **Unverified:** plausible or previously reported, but still needs a bounded check before
  it becomes an operational fact.

This audit did not query live containers, DNS, reverse-proxy configuration, or the device.
It did not deploy, restart, flash, scan the network, commit, or push.

## New-agent quick start

1. Read this page, the local `AGENTS.md`, [START_HERE.md](START_HERE.md), and the relevant
   row in [INTEGRATIONS.md](INTEGRATIONS.md).
2. Identify the execution environment: Mac checkout, `/Volumes/docker` SMB mount, NAS
   shell, container, or hardware. A result from one is not automatically valid in another.
3. Run `git status --short --branch` where Git exists. Preserve all work you did not make,
   including untracked files. If there is no `.git`, stop treating the directory as a
   checkout.
4. Locate the live source, Compose/Dockerfile, persistent volumes, and both sides of any
   integration before changing anything. Ignore backup, baseline, `.before-*`, and archive
   copies unless the task explicitly concerns them.
5. Prefer static inspection and focused host tests. Use one bounded live check only when
   the task needs it and the current environment is permitted to reach the target.
6. Keep local source, deployed containers, and physical hardware state separate in every
   report. A build is not a flash; a flash is not a boot; a host preview is not a panel test.
7. Do not repeat an already successful check unless relevant code, inputs, environment, or
   acceptance criteria changed. Stop after the requested outcome.

## Environment map

### Mac development environment

**Source-verified:** the Mac is the source-development environment accessible during this
audit. It mounts the NAS share at `/Volumes/docker` and has the Semavox checkout at:

```text
$HOME/Library/Mobile Documents/com~apple~CloudDocs/¶ PROJECTS/¶ CODE/Arduino/semavox
```

That path contains spaces and the Unicode paragraph character `¶`; quote the entire path.
Git, PlatformIO, firmware tools, and host previews can run on the Mac. The PlatformIO
virtual environment currently exists at `$HOME/.venvs/platformio`.

**Historically observed:** a separate Terminal session running `caffeinate -dimsu` has
kept the Mac awake during approved unattended work. Start it only when needed, keep its
process identifiable, and stop it afterward. An agent shell can have different LAN or
network permissions from Terminal.app.

**Source-verified (2026-11-06):** Wallboard's canonical Git checkout and Docker build context are
the same directory: `/volume1/docker/wallboard` on the NAS and `/Volumes/docker/wallboard` on the
Mac. The former `$HOME/dev/wallboard` checkout was archived, pushed, and removed during
consolidation. Git operations run from the Mac-mounted checkout; Docker operations run on the NAS.

### Synology deployment environment

**Source-verified:** JARVIS Docker deployment definitions and production-mounted files are
under `/volume1/docker` on the NAS and visible from the Mac at `/Volumes/docker`. The known
NAS LAN address in Compose and Console configuration is `192.168.1.100`.

The NAS directory is a deployment environment, not the default place to develop. Some
service directories contain Git metadata, but others do not. On 2026-11-05,
`/Volumes/docker/wallboard`, `homeassistant`, `jarvis-scanner`, `jellyfin`, and `scrypted`
were not Git checkouts. Do not infer that every `/volume1/docker/<service>` is a repository.

**Historically observed:** Git is not installed in the established Synology workflow.
Do not keep retrying Git commands in a NAS shell. Develop in the appropriate Mac checkout,
then use the project's documented deployment mechanism only after authorization.

Editing the SMB-mounted production directory changes files on disk. It does not imply that
an image-based running container reloads them. Conversely, Label Service bind-mounts its
checkout at `/app`, so an edit can reach the running container sooner than expected. Read
the service's `compose.yaml` before making either assumption.

**Critical rule:** never assume a Mac development checkout and a deployed Synology
container are the same thing. Containers can have different networks, mounts, persistence,
and image versions. Do not deploy, rebuild, restart, or alter production to verify docs.

### Semavox hardware

**Source-verified:** Semavox targets an ESP32-S3 with a 64x32 HUB75 panel. Its API docs and
JARVIS configuration use `semavox.home` and the fixed-IP fallback `192.168.1.80`.

**Historically observed, after the initial audit:** physical-device testing successfully
verified live ES7210 room-audio capture; green-phosphor Scope and FFT Bars; runtime
Scope/Bars switching; Heart-nano and chime playback; the responsive iPhone web console;
web-console scene switching; Digital Rain 2.0 Classic and Abstract visuals; expanded Rain
settings; and improved slider interaction. Earlier tests also verified alerts and physical
Telegram-notification behavior. These are successful historical hardware tests, not proof
of the device's current firmware or runtime state. Host tests alone still cannot establish
microphone, panel, speaker, mobile-browser, boot, or LAN behavior. Production firmware is
not a disposable test target.

## Source, deployment, and persistence map

The authoritative full catalog is [ECOSYSTEM.md](ECOSYSTEM.md#service-catalog). The table
below records how source reaches production; it does not claim that a container is running.

| Project | Production definition | Update mechanism from source | Persistent/runtime boundary |
| --- | --- | --- | --- |
| Console | `jarvis-console/compose.yaml`, `Dockerfile` | Local image build from `/volume1/docker/jarvis-console`; recreate required for Python, static assets, Compose, or served-doc changes | External Receipt history volume mounted read-only |
| Wallboard | `wallboard/compose.yaml`, `Dockerfile` | Canonical Git checkout and local image build at `/volume1/docker/wallboard` | `wallboard-private` bind mounts credentials, token, local config, caches, histories, and NFL state |
| Receipt | `receipt-service/compose.yaml`, `Dockerfile` | Local image build from the deployment directory | External `morning-brief_schedule-data`; private key is a Compose secret |
| Label | `label-service/compose.yaml`, `Dockerfile` | Local image plus `.:/app` bind mount; source edits may be visible without an image rebuild, but reload behavior still depends on the process | Inventory/runtime files live in the mounted project tree; printer is external hardware |
| Manifest | `manifest-service/compose.yaml`, `Dockerfile` | Local tagged image built from `MANIFEST_BUILD_CONTEXT` | `data/` writable database, `catalog/` read-only, `backups/` mounted; container root is read-only |
| Manifest Scanner | `manifest-scanner/compose.yaml`, `Dockerfile` | Local image build | `state/queue.db`; `/dev/input` and `/sys/class/input` are device mounts |
| Jarvis Scanner | `jarvis-scanner/compose.yaml`, `Dockerfile` | Local image build in a non-Git deployment directory | Scanner device mounts; no network; legacy log-only role |
| Jeopardy | `jeopardy-service/compose.yaml`, `Dockerfile` | Local image build | Clue SQLite database mounted read-only; shared Receipt network |
| TriviaROM | `triviaROM-service/compose.yaml`, `Dockerfile` | Local image build | Corpus copied into image; shared Receipt network |
| Home Assistant | `homeassistant/compose.yaml` | Pulls the configured upstream image | `config/` bind mount; host networking and host integrations |
| Matter Server | `matterjs-server/compose.yaml` | Pulls the configured upstream image | `data/` bind mount; host networking |
| BlackTorrent | `blacktorrent/compose.yaml` | Pulls Gluetun and qBittorrent images | `gluetun/`, `qbittorrent/`, `inbox/`, and `downloads/`; qBittorrent shares Gluetun's network namespace |
| Scrypted | `scrypted/compose.yaml` | Pulls the configured upstream image | `scrypted/volume`; host networking |
| Jellyfin | No Compose file found in this share | **Unverified** | Existing README documents paths, but the container definition remains to be located |
| Semavox | Mac iCloud Git checkout, `platformio.ini` | PlatformIO build, then guarded application-only uploader with explicit authorization | Firmware and device partitions; no Docker deployment |

Never run `docker compose build`, `up`, `down`, `restart`, or container replacement merely
to learn how deployment works. Static configuration is the first source of truth.

## Git and GitHub workflow

### Before any Git operation

```sh
git status --short --branch
git remote -v
git branch --show-current
```

Protect tracked, untracked, and ignored local work. Do not move, delete, stash, reset, or
overwrite work merely to obtain a clean status. Use an isolated worktree for substantial
independent work, and keep documentation audits separate from feature branches.

### GitHub SSH over port 443

**Historically observed:** GitHub SSH on port 22 has hung or timed out in this environment.
Use GitHub's SSH endpoint on port 443 by default for a required SSH fetch or approved push:

```sh
GIT_SSH_COMMAND='ssh -o HostName=ssh.github.com -p 443 -o ConnectTimeout=8 -o BatchMode=yes' git fetch origin
GIT_SSH_COMMAND='ssh -o HostName=ssh.github.com -p 443 -o ConnectTimeout=8 -o BatchMode=yes' git push origin <branch>
```

Make one bounded attempt over port 443. If it fails, report the error and stop. Do not wait
minutes on port 22, repeat identical attempts, edit global SSH/Git configuration, rewrite
remotes, or force-push to compensate for connectivity. Never launch competing Git
operations.

### Semavox branch history

**Historically observed milestones:** the `alert-typography-e` integration entered `main` through PR
#9 at merge commit `8a4a2394191c85a2c50bd0032b5e36d81a1913ca`. A subsequent README
correction was committed directly to `main` at
`07097ea024a2b60e3de3362fcb58d959d2e71039`. These SHAs establish history; neither is a
promise about the current head of `main`.

For new work, verify current remote refs and start from the current `origin/main`, preferably
in an isolated worktree. Do not continue development on `alert-typography-e`, and do not
merge, reset, rebase, clean, or otherwise modify that old checkout merely to begin new work.

Generated previews, firmware images, logs, backups, and runtime data stay out of commits
unless a task explicitly requires them. Never merge a PR, commit, or push without approval.

## Semavox firmware workflow

Keep each proof separate and perform the least expensive proof first:

1. Inspect relevant source, API contracts, and existing tests.
2. Make one focused change.
3. Run focused host tests once.
4. After the change is complete, run one PlatformIO firmware compilation.
5. For graphics, generate a host preview where practical and obtain visual approval.
6. With explicit flashing authorization, use the guarded application-only uploader once.
7. Obtain physical confirmation of boot and the changed behavior.
8. Commit and push only the approved files, and only when authorized.

Build command:

```sh
PATH="$HOME/.venvs/platformio/bin:$PATH" pio run -e semavox
```

Authorized application-only upload command:

```sh
PATH="$HOME/.venvs/platformio/bin:$PATH" python3 tools/flash_semavox.py upload
```

The upload command is not a routine validation step. It requires explicit authorization.

### Deployment-ready builds from isolated worktrees

**Historically observed during Digital Rain 2.0:** an isolated Semavox worktree compiled
successfully while using `BUILD_ONLY` Wi-Fi placeholders because ignored local files do not
follow a Git worktree. In particular, a new worktree may not contain
`src/wifi_secrets.h`, even when the existing source checkout does.

A placeholder build can be valid for host tests or compilation checks. It is not safe to
flash: the board could lose LAN connectivity and make the mobile console unreachable.
Only when preparing an image for actual deployment:

1. Confirm that the isolated build has the intended local Wi-Fi configuration and contains
   no `BUILD_ONLY` placeholders.
2. Use a securely handled temporary copy of the existing credential header, or an already
   established equivalent build mechanism. Do not change the source credential file.
3. Never print, log, expose, commit, upload, or weaken `.gitignore` for credentials.
4. Build the intended configuration and use the standard guarded uploader.
5. Remove only the temporary credential material created for that specific build, and only
   after it is no longer needed.

Successful compilation alone does not make an image deployment-ready. Conversely, do not
require production credentials for host-test or build-only firmware checks.

### Flash safety facts

**Source-verified in `picoTTS.csv`, `RECOVERY.md`, and `tools/flash_semavox.py`:** the
factory application starts at `0x10000` and has size `0x600000` (6 MiB). `upload` identifies
the registered ESP32-S3 by MAC, builds, performs a small `0xC00` partition-table comparison
at `0x8000`, checks that the image fits the allowed factory region, and writes only the
application. It does not erase the chip or write the bootloader, partition table, NVS, or
PicoTTS dictionaries.

The partition-table read is a safety comparison, not a full backup. Do not require a full
flash readback; earlier readbacks took many minutes. Do not use generic PlatformIO uploads,
whole-flash writes, `erase_flash`, `recover`, or `provision-picotts` as shortcuts. Recovery
and dictionary provisioning are separate exceptional operations and require their own
explicit authorization.

An esptool write/hash verification proves that bytes were written. It does not prove that
the board booted, joined the LAN, displayed correctly, captured microphone audio, or passed
feature tests. Likewise, an auxiliary `esp-idf-size --ng` warning does not negate a final
PlatformIO `[SUCCESS]`; use the build's final result as the compilation verdict.

### Embedded Safari caching after firmware updates

**Historically observed during Digital Rain 2.0:** after a correct firmware flash, an
iPhone web console can still show old slider limits, JavaScript behavior, flickering, HTML,
CSS, or styling because Safari reused cached `/app.js`, `/styles.css`, or page assets.

Use a bounded response:

1. Make one read-only request to verify the firmware API's current values or accepted range.
2. Inspect the embedded asset delivery and cache behavior.
3. If needed, try a private-browsing session or equivalent cache-isolation check.
4. Separate stale browser assets from incorrect firmware before changing UI code.

Appropriate cache headers or deterministic asset versioning are the long-term prevention,
but are recommendations until the web-serving implementation proves they are present.
Do not rewrite working UI code or claim caching is fixed merely because a stale page appears
after a firmware update.

## Network and API access

**Historically observed:** normal Mac Terminal has reached
`http://192.168.1.80/api/ping`, while restricted agent shells have failed to reach the same
device. NAS containers have separately resolved and reached Semavox. These observations
describe different network namespaces and permission boundaries.

When a request fails:

1. Record exactly which environment made it: agent shell, Terminal.app, NAS shell, or a
   named container.
2. Decide whether live access is necessary. Continue with source and host validation when
   it is not.
3. Make at most one bounded attempt from a known-restricted environment. Do not diagnose
   the household LAN in a loop.
4. If physical verification is required, ask the operator for one read-only check from
   normal Terminal, for example:

   ```sh
   curl --fail --show-error --max-time 5 http://192.168.1.80/api/ping
   ```

5. Report the result as evidence about that environment only.

An agent-network failure is never evidence that a healthy device or production service
should be restarted.

## Cross-project integration rules

The contract table and source paths live in [INTEGRATIONS.md](INTEGRATIONS.md). Trace both
producer and consumer before changing a payload or endpoint.

- Wallboard creates NFL events and sends best-effort `POST /api/alert` requests to
  Semavox. Document by reading `nfl_provider.py`, `nfl_events.py`, `nfl_service.py`, and
  `semavox_alerts.py`; do not synthesize an NFL alert.
- Receipt sends a Semavox alert only after a Telegram receipt prints. The paper and device
  actions are real side effects; unit tests and source inspection are the safe checks.
- Semavox implements `/api/alert` and `/api/alert/status`; the firmware `API.md` is the
  consumer contract. A live alert, sound, speech, audio, or mode call needs approval.
- Console mounts Receipt's Telegram history volume read-only and sends exactly one guarded
  Morning Brief request. A timeout is uncertain because paper may already have printed.
- Local DNS and Synology reverse proxy rules are external to these repositories. Container
  aliases work only on their configured Docker networks.
- There is no source-verified notification hub. Wallboard and Receipt call Semavox
  directly. Proposed hub/refactor code is not production merely because it exists in a
  development checkout or conversation.

Do not restart Wallboard, send test alerts, print receipts, publish to ntfy, or alter
container networking to document these contracts.

## Known Agent Traps and Their Resolutions

| Trap and symptom | Root cause and known successful resolution | Do not repeat | Evidence | Escalate only when |
| --- | --- | --- | --- | --- |
| GitHub SSH port 22 hangs | Port 22 is unreliable here. Use the per-command `ssh.github.com:443` `GIT_SSH_COMMAND` above with an 8-second connect timeout. | Long waits, identical retries, global config edits, remote rewrites, force-push | Historical operations; command recorded above | The single port-443 attempt fails and remote access is essential |
| Agent shell cannot reach a LAN device | Execution environments have different LAN permissions. Identify the caller, use source validation, or ask for one normal-Terminal `curl --max-time 5`. | Declaring the device offline, scanning, restarting, or looping | Semavox `API.md` runtime notes; historical agent/Terminal observations | The task truly requires live or physical proof |
| Full firmware readback is proposed before every flash | The guarded uploader needs only its small partition-table comparison; a full readback is slow and not the normal safety gate. | Multi-minute full-flash backups by default | Semavox `tools/flash_semavox.py`, `RECOVERY.md` | An exceptional recovery task explicitly requires a backup |
| Firmware is rebuilt repeatedly after a successful compile | Build success is already established; repeated builds add time without new evidence. Run focused tests, then one final compile after edits settle. | Rebuilding after every comment or unrelated check | Semavox `platformio.ini`; workflow above | Source or build inputs changed after the successful compile |
| Isolated worktree produces a `BUILD_ONLY` Wi-Fi image | Ignored `src/wifi_secrets.h` does not follow a new worktree. Before an actual deployment build, securely provide the established local configuration and verify placeholders are absent. | Flashing a compile-only image; printing, logging, committing, uploading, modifying, or weakening ignore rules for credentials | Historical Digital Rain 2.0 build; deployment-ready workflow above | A secure established credential mechanism cannot be used |
| An auxiliary size-tool error is reported as compilation failure | `esp-idf-size --ng` has warned while PlatformIO still completed successfully. Use the final `[SUCCESS]`/`[FAILED]`. | Treating an auxiliary warning as the verdict or rebuilding blindly | Semavox `RECOVERY.md` | PlatformIO ends in failure or no firmware image is produced |
| Git commands fail in a Synology deployment directory | Some deployment directories have no `.git`, and the established NAS workflow has no Git. Locate the Mac checkout or document the non-Git deployment path. | Repeated `git` attempts or initializing a repository in production | [ECOSYSTEM.md](ECOSYSTEM.md); `.git` inventory from 2026-11-05 | No authoritative source checkout can be located |
| New work continues on a long-lived Semavox feature branch | The approved integration was merged through PR #9. Verify refs and branch/worktree from current `origin/main`. | Mixing another sprint into, or resetting/rebasing/cleaning, `alert-typography-e` | Historical merge `8a4a2394191c85a2c50bd0032b5e36d81a1913ca`; later README correction `07097ea024a2b60e3de3362fcb58d959d2e71039` | Current remote refs cannot be established |
| Untracked files are removed to make status clean | Untracked previews, experiments, docs, or another agent's work can be valuable. Preserve them; work around them or use an isolated worktree. | `git clean`, destructive reset, bulk moves, or overwrites | Current dirty Semavox and service statuses; local `AGENTS.md` rules | A specific conflicting file blocks the task and its owner must decide |
| Concurrent documentation edits disappear | Multiple agents can edit the same docs. Read current status and diff immediately before patching; make surgical additions and re-check afterward. | Replacing whole files or assuming an earlier snapshot is current | Uncommitted ecosystem audit present on 2026-11-05 | The same lines are actively changing and cannot be merged safely |
| Host-generated audio or fixtures are treated as microphone proof | Host tests validate algorithms and fallback paths, not the ES7210, room capture, or board wiring. Require physical confirmation for new hardware acceptance. | Claiming current microphone success from WAV/host tests or treating a historical hardware test as current runtime proof | Subsequent physical testing historically verified ES7210 Scope/Bars operation | The requested acceptance criterion is current physical microphone operation |
| Successful flash is treated as successful firmware | Hash verification proves the write only. Confirm serial boot or operator-observed boot, then the specific real-device behavior. | Reporting boot, Wi-Fi, panel, audio, or API success from esptool alone | Semavox `RECOVERY.md`, `API.md` | Boot or feature confirmation is required and unavailable |
| iPhone console looks unchanged after a correct flash | Safari may reuse cached embedded JavaScript, CSS, or HTML. Verify one firmware-side value, inspect caching, then use a private session or equivalent bounded isolation test. | Rewriting working UI code because stale assets show old limits, flicker, behavior, or styling | Historical Digital Rain 2.0 mobile-console verification | Firmware/API evidence also appears stale or incorrect |
| A development notification refactor is described as production | No hub exists in source-verified production. Follow live Compose and producer-to-consumer calls. | Documenting proposals, experiments, or dirty checkout code as deployed | [ECOSYSTEM.md](ECOSYSTEM.md#operational-map), [INTEGRATIONS.md](INTEGRATIONS.md) | Deployment/source provenance cannot be determined |
| Diagnostics become an open-ended loop | The environment limitation or narrow blocker has already been established. Bound commands and report the exact missing proof. | Repeated curl/serial/SSH/build retries with unchanged inputs | Decision rules below | A new observation changes the hypothesis or the user authorizes broader diagnostics |
| Routine steps trigger repeated permission questions | Read-only inspection, status checks, and focused host tests are already within ordinary documentation/development scope. Continue independently inside the authorized task. | Asking again for each bounded non-mutating command | This playbook and local `AGENTS.md` files | A step adds real side effects: deploy, restart, print, alert, flash, secrets, commit, push, merge, or destructive cleanup |
| A backup or baseline file is edited as if live | Dated `backups/`, `baseline-*`, `.before-*`, and archive files are historical copies. Start from the active Compose/source paths. | Updating or deploying an archival copy | [START_HERE.md](START_HERE.md), directory inventory | The task explicitly asks to restore or compare a backup |
| Console reports Wallboard `unknown` although `/health` responds | Wallboard returns `{"ok": true}` while Console expects `status == "ok"`. This is a source-verified contract mismatch, not proof that Wallboard is down. | Restarting Wallboard or weakening a health adapter to make a badge green | [INTEGRATIONS.md](INTEGRATIONS.md#known-contract-problems) | The user authorizes a contract fix and both sides are reviewed |

## No repeated tests or diagnostics

**Do not repeat a successful test, compile, flash verification, network probe, or diagnostic
command unless relevant code, inputs, environment, or acceptance criteria have changed.**
When repetition is justified, record what changed and why the previous result no longer
answers the question.

- A README-only edit does not require another firmware build.
- Prefer focused tests for a small web UI change; do not rerun the full host suite when they
  provide adequate coverage.
- Do not repeat a successful flash verification.
- Do not probe the same restricted network path repeatedly.
- Do not create another full-device backup when the guarded partition check is sufficient.
- Do not rerun suites already completed successfully before a documentation-only handoff.

## Decision rules

### Prefer

- One focused check before exploratory troubleshooting; use timeouts and explicit targets.
- Existing proven scripts, especially guarded hardware tools.
- Static inspection before any live diagnostic.
- Focused tests and one final build.
- Source-backed claims with evidence labels and dates.
- Independent progress inside authorized scope.
- Narrow blocker reports that name the missing environment or proof.
- Small reviewable patches and isolated worktrees.
- Separate statements for local source, deployment definition, observed runtime, and hardware.

### Avoid

- Infinite or unchanged retries.
- Guessing production topology, container reachability, or DNS.
- Unrequested backups or full-device readbacks.
- Long-running exploratory loops.
- Rebuilding a service or all firmware for a documentation or UI-only check.
- Moving, cleaning, stashing, or deleting someone else's files as housekeeping.
- Repeated permission questions for already-authorized read-only work.
- Touching unrelated repositories or mixing feature and documentation changes.
- Treating future architecture, dirty checkout code, or a deployment definition as live state.
- Competing Git operations or parallel commands that mutate the same checkout.

If a command hangs, inspect its state once, cancel it cleanly, and use at most one known-good
alternative. A tool's permission restriction is not evidence that the target device is down.
An auxiliary size-reporting warning is not a build failure when PlatformIO reports success.
Stop once the requested result is achieved.
If the task cannot proceed without exceeding scope, record the blocker and continue every
independent permitted part.

## Safe command patterns

These commands are read-only or local verification when run from the intended checkout:

```sh
git status --short --branch
git diff --check
git diff -- <documentation-file>
git remote -v
python3.12 -m unittest discover -s tests -v   # Console
```

Before using a project-specific test command, read its local `AGENTS.md`; some commands
create containers or touch hardware and therefore need approval. Add timeouts to network
checks. Never put credentials, `.env` content, private keys, private databases, or
`wallboard-private` data into logs or documentation.

## Documentation maintenance

When a service, route, network, deployment path, or integration changes:

1. Update the owning service README and local `AGENTS.md` when operational guidance changes.
2. Update [INTEGRATIONS.md](INTEGRATIONS.md) for producer/consumer contracts.
3. Update [ECOSYSTEM.md](ECOSYSTEM.md) for names, paths, ports, networks, ownership, or
   deployment mechanisms.
4. Update `SERVICE_CATALOG.md` and `web/services.html` together when the Console service
   catalog changes.
5. Date runtime observations and label them separately from source-verified facts.
6. Check every relative link and run `git diff --check` before handoff.

Do not duplicate this playbook across repositories. Link to it from local agent entry
points. Preserve concurrent changes: inspect current content immediately before editing,
patch only the necessary lines, and review the final diff.

## Environment details still needing verification

- Whether Git is presently unavailable in the actual Synology shell; this is a historical
  workflow fact, not a live shell check from this audit.
- Which commits/images are currently running in every container. Static Compose files do
  not answer this.
- The current Semavox flashed revision and whether all previously tested hardware features
  remain operational on that revision.
- Current DNS and Synology reverse-proxy records, which live outside these repositories.
- The active Jellyfin container definition and its update mechanism.
- Whether an agent-instruction entry point should be added to the Semavox repository. It
  currently has no `AGENTS.md` or `CLAUDE.md`, is outside this workspace's writable roots,
  and contains concurrent Digital Rain/other work; add only in a separately authorized
  Semavox documentation change.
- Which Semavox host-test and preview commands are the canonical minimal set for each
  graphics/audio subsystem; use the scripts nearest the changed subsystem until documented.

