# LATAMFILES Admin Traffic Limits — Design

**Date:** 2026-07-24  
**Status:** Approved for implementation (pending user review of this written spec)  
**Depends on:** Admin shell at `/admin/` (staff Discord gate)  
**Scope:** Editable Nginx traffic limits via `/admin/traffic.php` with safe apply + reload.

## Problem

Staff need to tune download and listing pressure (demos bandwidth, autoindex scraping) without hand-editing Nginx. The admin shell already has a Tráfico placeholder.

## Goals

- Staff can enable/disable limits and edit: concurrent demo connections per IP, max download rate per connection, autoindex requests per minute per IP.
- Saving applies real Nginx limits: generate an include file, backup previous, `nginx -t`, restore on failure, else `nginx -s reload`.
- UI requires explicit confirmation before apply/reload.
- Only staff (existing `/admin/` bootstrap) can use this page.

## Non-goals (v1)

- IP allowlists / denylists
- Daily quotas or bandwidth accounting dashboards
- Free-text Nginx editing
- Limits for tracker PHP, auth, or unrelated paths beyond demos autoindex + demo file downloads
- Changing `worker_processes` or global `worker_connections`

## Settings model

Stored as JSON (source of truth for the form), e.g. `C:/nginx/html/admin/data/traffic-settings.json` (directory not web-served as listing; file not linked publicly).

| Key | Type | Default | Notes |
|-----|------|---------|-------|
| `enabled` | bool | `true` | Global ON/OFF |
| `demo_conn_per_ip` | int | `2` | Concurrent connections per IP to demo file locations |
| `demo_rate_mbs` | number | `8` | Max MB/s per connection (`limit_rate`) |
| `autoindex_req_per_min` | int | `60` | `limit_req` rate for autoindex HTML listings |

**Validation (reject save if invalid):**

- `demo_conn_per_ip`: integer 1–10
- `demo_rate_mbs`: number 1–50 (one decimal allowed, e.g. 8 or 8.5)
- `autoindex_req_per_min`: integer 10–300
- Unknown keys ignored; missing keys filled from defaults on load

## Nginx application

### Zones (http context)

Generated include for zones, e.g. `C:/nginx/conf/latam-traffic-zones.conf`, included once from `http { }` in `nginx.conf` or `latamsquad.conf`:

When `enabled` is true, define something equivalent to:

```nginx
limit_conn_zone $binary_remote_addr zone=latam_demo_conn:10m;
limit_req_zone $binary_remote_addr zone=latam_autoindex:10m rate=<N>r/m;
```

When `enabled` is false, the zones file may still define zones with a high rate / unused, **or** emit empty/comment-only content and location include omits directives — prefer: zones always present with configured rate; location directives only applied when enabled (simpler reload). Chosen approach:

- **Zones file always written** with current numeric values (rate from settings).
- **Location limits file** contains `limit_conn` / `limit_rate` / `limit_req` only when `enabled` is true; when false, file is empty or comments-only so no limits apply.

### Location directives

Generated include e.g. `C:/nginx/conf/latam-traffic-limits.conf`, pulled into each demos2d / demos3d autoindex (and download) location via `include latam-traffic-limits.conf;` (or a shared snippet).

When enabled:

```nginx
limit_conn latam_demo_conn <demo_conn_per_ip>;
limit_rate <bytes_per_sec>;  # demo_rate_mbs * 1024 * 1024
limit_req zone=latam_autoindex burst=20 nodelay;
```

Notes:

- `limit_rate` applies to the response body (demo files and large HTML listings). Acceptable for v1.
- Autoindex locations already use `sub_filter`; adding limit_* is compatible.
- Exact burst value fixed in generator (e.g. 20), not exposed in UI v1.

### Wiring

- `http` block: `include latam-traffic-zones.conf;`
- Each `/pr/demos2d/` and `/pr/demos3d/` location (and svN variants already listed): `include latam-traffic-limits.conf;`
- Do not attach these limits to `/admin/`, `/auth/`, `/pr/tracker/`, or `/pr/extras/` in v1 unless extras is treated as demos — **exclude extras**.

## Apply pipeline (on confirmed save)

1. Validate POST fields.
2. Write JSON settings (atomic write: temp + rename).
3. Copy current zones + limits includes to timestamped backup dir, e.g. `C:/nginx/conf/backup/traffic-YYYYMMDD-HHMMSS/`.
4. Generate new zones + limits files (atomic write).
5. Run `C:/nginx/nginx.exe -t` with cwd `C:/nginx`.
6. If test fails: restore backups over the includes, surface stderr to staff, do not reload.
7. If test OK: `C:/nginx/nginx.exe -s reload`, show success (and optional `-t` OK message).

**Process execution:** PHP must be allowed to run `nginx.exe` (same machine). Use absolute paths. No shell metacharacters from user input in the command line (fixed argv).

**Permissions:** document that the PHP / FastCGI identity needs execute on `nginx.exe` and write on `C:/nginx/conf/` for the include + backup paths.

## UI (`/admin/traffic.php`)

- Reuse admin layout; nav key `traffic` active.
- Form fields matching settings model with labels in Spanish (ASCII-safe in PHP source: "Trafico", "limites", etc.).
- Toggle "Limites activos" (enabled).
- Number inputs for the three numeric settings with min/max hints.
- Primary button opens confirm step (second submit or JS `confirm` / inline confirm panel): copy like "Aplicar y recargar Nginx?"
- Flash messages: success / validation error / nginx -t failure (show truncated log).
- Read-only line: path of last backup or "sin backup aun" after first successful apply.
- No fake controls beyond these fields.

## Security

- Staff-only via `_bootstrap.php`.
- CSRF token on POST (session-bound).
- `noindex` already from bootstrap.
- Never echo full nginx.conf secrets; only `-t` error text.
- Do not allow path traversal in backup names (server-generated timestamps only).

## Files (expected)

| Path | Role |
|------|------|
| `html/admin/traffic.php` | Form + apply orchestration |
| `html/admin/lib/traffic_settings.php` | Load/validate/save JSON + generate conf text |
| `html/admin/lib/traffic_nginx.php` | Backup, write includes, nginx -t / reload |
| `html/admin/data/traffic-settings.json` | Persisted settings |
| `nginx/conf/latam-traffic-zones.conf` | Generated zones |
| `nginx/conf/latam-traffic-limits.conf` | Generated location limits |
| `nginx/conf/nginx.conf` or `latamsquad.conf` | include zones |
| `nginx/conf/latamsquad-locations.conf` | include limits in demo locations |
| Repo mirrors under `docs/nginx-templates/` | As elsewhere |

## Success criteria

- Staff can open Tráfico, change values, confirm, and see success when Nginx reloads.
- Failed `nginx -t` restores previous includes and does not reload.
- With limits ON, concurrent demo connections and rate behave per settings (spot-check with two downloads / throttle observation).
- With limits OFF, generated location include applies no limit_* directives; listings/downloads unrestricted by these zones.
- Non-staff cannot POST settings.
- CSRF rejects forged POST without token.

## Follow-ups (later)

- Expose burst in UI
- Apply similar limits to `/pr/extras/`
- Audit log of who changed settings and when
