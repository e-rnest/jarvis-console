# HTTP API

Source-audited 2026-11-06. Console has no authentication, TLS, CORS policy, or versioned
API prefix. Keep it on the trusted LAN.

Responses include `Cache-Control: no-store`, `X-Content-Type-Options: nosniff`, and
`Referrer-Policy: no-referrer`. JSON is UTF-8. Unknown paths, disallowed query strings,
and unsupported POST paths return `404 {"error":"Not found"}`. Other HTTP methods are
not implemented by the handler.

## `GET /health`

Process health only; it does not query downstreams.

```json
{"status":"ok","service":"jarvis-console","version":"1.1.0","build":"2026.11.06.1"}
```

## `GET /api/status`

Checks up to ten targets concurrently; Home Assistant is launch-only until its token is
configured. The endpoint
returns HTTP 200 even when individual services are failed, unknown, or unavailable.

```json
{
  "generated_at": "2026-11-06T20:00:00+00:00",
  "console": {"version":"1.1.0","build":"2026.11.06.1"},
  "services": [{
    "key": "label",
    "name": "Label",
    "status": "healthy",
    "summary": "Service responding",
    "launch_url": "http://label.jarvis.home/print",
    "secondary_links": [{"label":"Quick Labels","url":"http://label.jarvis.home/labels"}]
  }]
}
```

Every service has `key`, `name`, `status`, `summary`, and nullable `launch_url`.
`secondary_links` and `details` are optional. Receipt details expose schedule/printing
state; TriviaROM details expose corpus counts; Jellyfin details expose server name and
version; Semavox details expose uptime, audio readiness, volume, startup-chime state,
and label. Status values are `healthy`, `failed`,
`unknown`, and `unavailable`. Internal check URLs are never returned.

## `GET /api/ipps/history`

Returns at most 50 newest Receipt Telegram-history records:

```json
{"messages":[{
  "timestamp":"2026-11-06T19:00:00+00:00",
  "sender":"Example",
  "message":"Example message",
  "ip":"192.0.2.1",
  "location":"City, Region, Country",
  "status":"sent"
}]}
```

`ip` and `location` may be null. This is private household data. If the file, table,
selected columns, or query is unavailable, Console returns HTTP 503:

```json
{"error":"Message history unavailable"}
```

No pagination, filtering, mutation, or acknowledgement interface exists.

## `POST /api/actions/morning-brief`

Requests one Receipt Morning Brief. It must have no query, transfer encoding, or body;
`Content-Length` must be absent or exactly `0`.

HTTP 200 success:

```json
{
  "outcome":"success",
  "message":"Receipt Service accepted the print request. Physical paper output is not confirmed.",
  "bytes":1234
}
```

| HTTP | Outcome | Meaning |
| --- | --- | --- |
| 400 | `failed` | Caller supplied a body or transfer encoding; nothing is forwarded. |
| 409 | `busy` | Another action is in progress in this process; nothing is forwarded. |
| 502 | `failed` | Receipt returned a definite HTTP rejection; `downstream_status` is included. |
| 502 | `uncertain` | Connection/result was lost or the post-dispatch success response was unrecognized; it may have printed. |

Console never retries. After `uncertain`, inspect the printer before trying again.

## Static routes

| Route | Content |
| --- | --- |
| `GET /` | Dashboard HTML |
| `GET /services` or `/services/` | Hand-maintained ecosystem catalog HTML |
| `GET /assets/app.css` | Stylesheet |
| `GET /assets/app.js` | Dashboard client |

Only allowlisted files are served. Markdown is not included in the container image or
exposed over HTTP.
