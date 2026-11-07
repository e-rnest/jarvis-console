# Agent guide: jarvis-console

**Owns:** the dashboard, `/services` page and central ecosystem docs.

**Mandatory entry:** Before beginning work, read [AGENT_OPERATIONS.md](AGENT_OPERATIONS.md). Prefer GitHub SSH over port 443, distinguish Mac source from Synology deployment, preserve existing and untracked work, follow guarded hardware procedures, and do not repeat previously resolved diagnostics.

**Then read:** the [ecosystem guide](START_HERE.md) and [integration directory](INTEGRATIONS.md), then `jarvis_console/config.py`, `clients/`, `http.py`, `web/`.

**Safe checks:** `python3.12 -m unittest discover -s tests -v`.

**Depended on by:** Nothing depends on Console at runtime.

**Keep stable:** Health adapter schemas; the read-only Telegram history query; one-shot Morning Brief with no retries.

**Traps:** Do not turn a homepage into a health check to make a badge green. `web/services.html` is hand-maintained, so it drifts from the Markdown.

**Without authorization, do not:** deploy, restart or rebuild containers, change `.env` or secrets, trigger printing or alerts, clear state, or commit and push. `/volume1/docker` on the NAS and `/Volumes/docker` on the Mac are the same production files.

## Git Workflow Policy (Local-first)

- The local working source is authoritative for current development.
- Work directly on main by default.
- Do not create a branch for routine tasks, documentation, small fixes, or maintenance.
- Create a branch only for risky experiments, speculative features, or concurrent work requiring isolation.
- If operating in an existing isolated worktree, do not switch or modify another worktree's branch.
- Do not create branches merely because an AI agent starts a task.
- Preserve uncommitted work and never overwrite another agent's changes.
- Commit completed, intentional changes to main when authorized.
- Push completed commits to GitHub when authorized.
- Keep GitHub main aligned with the latest completed local source.
- Do not merge old agent branches automatically.
- Prefer fast-forward integration when possible.
- Never force-push, reset, rewrite history, or delete branches without explicit authorization.
- Do not run builds, tests, flashes, or deployments solely for Git housekeeping.
- Before finishing, report any uncommitted, unpushed, or unmerged work.
