# Agent guide: jarvis-console

**Owns:** the dashboard, `/services` page and central ecosystem docs.

**Mandatory entry:** Before beginning work, read [AGENT_OPERATIONS.md](AGENT_OPERATIONS.md). Prefer GitHub SSH over port 443, distinguish Mac source from Synology deployment, preserve existing and untracked work, follow guarded hardware procedures, and do not repeat previously resolved diagnostics.

**Then read:** the [ecosystem guide](START_HERE.md) and [integration directory](INTEGRATIONS.md), then `jarvis_console/config.py`, `clients/`, `http.py`, `web/`.

**Safe checks:** `python3.12 -m unittest discover -s tests -v`.

**Depended on by:** Nothing depends on Console at runtime.

**Keep stable:** Health adapter schemas; the read-only Telegram history query; one-shot Morning Brief with no retries.

**Traps:** Do not turn a homepage into a health check to make a badge green. `web/services.html` is hand-maintained, so it drifts from the Markdown.

**Without authorization, do not:** deploy, restart or rebuild containers, change `.env` or secrets, trigger printing or alerts, clear state, or commit and push. `/volume1/docker` on the NAS and `/Volumes/docker` on the Mac are the same production files.
