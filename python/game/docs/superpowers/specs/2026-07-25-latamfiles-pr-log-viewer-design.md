# LATAMFILES PR LOG Viewer (`/pr/logs`) — Design

**Date:** 2026-07-25  
**Status:** Approved for implementation (pending user review of this written spec)  
**Upstream:** [gerbesf/PR-LOG-Viewer](https://github.com/gerbesf/PR-LOG-Viewer) (PHP app, branch `master`, v1.4)  
**Scope:** Vendor the viewer on latamsquad.dev at public `/pr/logs/`, local SV1-SV4 logs, IPs masked, no raw log HTTP exposure. Link from `/pr.php`. Keep staff autoindex as-is.

## Problem

Staff and community currently rely on a Discord-gated autoindex at `/pr/admins/logs/sv1/` for raw admin log files. There is no public, searchable UI for admin/player logs across all four PR servers. Upstream PR-LOG-Viewer already provides that UI (filter by command, player history, hash/IP views) but is not deployed on LATAMFILES.

## Goals

- Public access at `https://latamsquad.dev/pr/logs/` (no Discord, no viewer MD5 login).
- Vendor PR-LOG-Viewer with LATAM `config.php` for SV1-SV4 local paths.
- Mask IPs in viewer output (`hide_ips = true`).
- Do not serve raw cached `.txt` / `.con` over HTTP under `/pr/logs/`.
- Discoverability: link from `/pr.php` hub.
- Keep `/pr/admins/logs/sv1/` unchanged (staff Discord + autoindex for raw files).

## Non-goals (v1)

- LATAMFILES visual restyle of the viewer UI.
- Git submodule / auto-sync from upstream.
- Public raw file download or public autoindex of log directories.
- Expanding staff autoindex to SV2-SV4 (viewer covers multi-server; staff raw remains SV1 only unless done later).
- Integrating the viewer into `/admin/` panel shell.
- Changing Reality Admin logging paths inside the game Python.

## Decisions (locked)

| Topic | Choice |
|-------|--------|
| Integration style | Vendor copy into docroot (approach 1) |
| URL | `/pr/logs/` public |
| Auth | None on `/pr/logs/` |
| IP privacy | `hide_ips = true` |
| Servers | SV1-SV4 |
| Log roots | `C:/prbf2_N/admin/logs/` for N=1..4 |
| Raw downloads under `/pr/logs` | Not public; always deny HTTP to cache dir. `download.php` may stay as JSON-only refresh if UI requires it; never stream raw log bodies |
| Staff raw logs | Keep `/pr/admins/logs/sv1/` |
| Hub | Link on `/pr.php` |

## Architecture

```
Browser  -->  GET /pr/logs/  -->  Nginx FastCGI  -->  public/index.php (UI)
Browser  -->  GET/POST APIs  -->  get_log.php / get_player.php / ...
                                      |
                                      v
                         file_get_contents(C:/prbf2_N/...)
                                      |
                                      v
                         hide_ips + JSON response

Browser  -->  /pr/logs/public/logs/*  -->  Nginx deny/404
Browser  -->  /pr/admins/logs/sv1/    -->  auth_request Discord (unchanged)
```

**On-disk layout**

| Path | Role |
|------|------|
| `C:/nginx/html/pr/logs/` | Vendor tree: `config.php`, `app/`, `public/`, root redirect to `public/index.php` |
| `C:/nginx/html/pr/logs/config.php` | LATAM servers_list + flags (not Divsul sample URLs) |
| `C:/nginx/html/pr/logs/public/logs/` | Upstream cache dir; writable by PHP; **not** HTTP-readable |
| `docs/nginx-templates/pr/logs/` | Repo mirror of vendor + LATAM config/patches |
| `docs/nginx-templates/latamsquad-locations.conf` | New `/pr/logs/` locations + denies |
| `docs/nginx-templates/pr.php` | Hub link |

## Config model

`require_login = false`  
`hide_ips = true`  
`with_md5` / `auth` unused while login is off (do not ship meaningful default passwords in deployed config).

Each `servers_list[]` entry (ids 1..4):

| Field | SV1 example (pattern for SV2-4) |
|-------|----------------------------------|
| `name` | e.g. `LATAM SV1` (final label ASCII; confirm at implement) |
| `ra_adminlog` | `C:/prbf2_1/admin/logs/ra_adminlog.txt` |
| `ra_adminlog_main` | `C:/prbf2_1/admin/logs/ra_adminlog_main.txt` |
| `cdhash` | `C:/prbf2_1/admin/logs/cdhash.txt` |
| `cdhash_main` | `C:/prbf2_1/admin/logs/cdhash_main.txt` |
| `whitelist` | Path under that install (confirm exact file at implement) |
| `banlist` | Path under that install (confirm exact file at implement) |
| `local_name` | e.g. `latam_sv1.txt` |

If a file is missing for a server, APIs return empty/partial data without fatal HTML errors (upstream-tolerant behavior). Paths verified during smoke against real installs.

## Nginx

Mirror patterns used for `/pr/tracker/`:

1. `location /pr/logs/` — try_files / index into viewer; PHP via FastCGI for `*.php`.
2. Prefer document root under `html/pr/logs/` so `public/` is the app front (or alias carefully so relative JS/CSS keep working).
3. `location ^~ /pr/logs/public/logs/` — `deny all;` (or `return 404;`).
4. `download.php`: keep callable only if upstream UI refresh depends on it; response must be JSON status only (no raw file body). Always deny HTTP listing/GETs under `public/logs/`. If refresh can be done without that endpoint, return 404 for it.
5. No `auth_request` on `/pr/logs/`.
6. Do not change `/pr/admins/logs/sv1/`.

## Hub (`pr.php`)

Add one list item under `.pr-links` with label **Visor de logs** pointing to `/pr/logs/`. ASCII-safe PHP source. No Discord gate on the link.

## Security

- Public surface: UI + JSON APIs only.
- IPs masked in API/UI output via upstream `hide_ips`.
- Cache directory and raw aliases under `/pr/logs` not web-accessible.
- Staff raw access remains Discord-gated at existing admins path.
- Attribution: keep upstream credit in footer/README note (Ferreira, Danesh_italiano, initializers per upstream README); do not claim authorship of vendor code.
- No secrets in public JSON; config stays server-side PHP.

## Error handling

| Case | Behavior |
|------|----------|
| Missing log file | Empty result / soft fail for that server |
| Wrong path in config | Smoke fails; fix config |
| PHP cannot read path | Empty/error JSON; no stack trace to client |
| Cache write fails | Log server-side; UI may show stale/empty until fixed |

## Testing (smoke)

1. `GET https://latamsquad.dev/pr/logs/` (Host header / local curl) → 200, UI loads.
2. Call log API for SV1 (and spot-check SV2-SV4) → JSON; sample IP fields masked (last octets zeroed per upstream).
3. `GET /pr/logs/public/logs/` and a known cache filename if present → 403/404.
4. `GET /pr/logs/public/download.php` → if kept for refresh: JSON only, no raw body; if unused: 404. Cache dir still 403/404.
5. `GET /pr.php` contains href `/pr/logs/`.
6. `GET /pr/admins/logs/sv1/` still redirects unauthenticated users to Discord login.

## Success criteria

- Public can open `/pr/logs/` and query SV1-SV4 without login.
- IPs appear masked in viewer output.
- Raw log bytes are not downloadable via `/pr/logs/` URLs.
- Hub links to the viewer.
- Staff autoindex path unchanged and still protected.

## Implementation notes

- Prefer copying a pinned upstream commit/tag into `html/pr/logs/` and recording source URL + commit in a short `VENDOR.md` (or comment in config) under the vendor tree.
- Confirm whitelist/banlist absolute paths per install during implement (may live next to `admin/logs` or elsewhere on each `prbf2_N`).
- Domain in copy/canonicals: `latamsquad.dev` (existing LATAMFILES origin in `pr.php`).
