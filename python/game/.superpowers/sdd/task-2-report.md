# Task 2 Report: Nginx locations for `/pr/logs/` + deny cache

**Date:** 2026-07-25  
**Status:** DONE (with noted app-level concern on PHP 500)

## Summary

Inserted the exact brief Nginx location blocks for the public PR LOG Viewer into the live `latamsquad-locations.conf`, reloaded Nginx successfully (from `C:/nginx` cwd), mirrored the conf into the game repo, and committed only that mirror file.

## Changes

### Live

- **File:** `C:/nginx/conf/latamsquad-locations.conf`
- **Placement:** Immediately before `# Tracker en /pr/tracker ...` (after `/pr/extras/`).
- **Blocks added (exact from brief):**
  - `location ^~ /pr/logs/public/logs/` → `deny all;` + `return 404;`
  - `location = /pr/logs` → `301 /pr/logs/`
  - `location /pr/logs/` → static `root html` + `try_files` to `/pr/logs/index.html`
  - `location ~ ^/pr/logs/(.+\.php)$` → FastCGI to `127.0.0.1:9000` with `SCRIPT_FILENAME $document_root/pr/logs/$1`
- **Constraints honored:**
  - No `auth_request` on `/pr/logs/`
  - `/pr/admins/logs/sv1/` left unchanged (still has `auth_request /auth/gate.php`)

### Mirror

- **File:** `docs/nginx-templates/latamsquad-locations.conf`
- Copied from live after edit so repo matches production include.
- Side effect of full live→mirror copy: existing `autoindex-enhance.js` cache-bust query aligned `v=20260725d` → `v=20260725g` (already present on live).

## Nginx test / reload

Commands run from `C:\nginx` (required; running `nginx.exe` from another cwd resolves a wrong relative `conf/nginx.conf`):

```text
nginx: the configuration file C:\nginx/conf/nginx.conf syntax is ok
nginx: configuration file C:\nginx/conf/nginx.conf test is successful
nginx.exe -s reload  (signal process started)
```

Pre-existing warnings only: duplicate MIME `text/html`, duplicate extension `prdemo`.

## Smoke results (Host: latamsquad.dev)

| URL | Result | Notes |
|-----|--------|-------|
| `GET -I https://127.0.0.1/pr/logs/` | **200** | Serves `index.html` redirect script to `public/index.php` |
| `GET -I https://127.0.0.1/pr/logs/public/index.php` | **500** | PHP reached (`X-Powered-By: PHP/8.3.32`); app error |
| `GET -I https://127.0.0.1/pr/logs/public/logs/` | **404** | Deny/`^~` block working |

### PHP 500 detail (out of Task 2 nginx scope)

From `C:\nginx\logs\php_errors.log`:

```text
PHP Fatal error: Uncaught Error: Class "App\Session" not found in C:\nginx\html\pr\logs\public\index.php:4
```

Nginx FastCGI location is correct; failure is missing autoload / App classes in the deployed viewer (Task 1 / app packaging). Brief expected HTTP 200 for `public/index.php`; routing to PHP is verified, application bootstrap is not.

## Commit

- **Repo:** `C:/prbf2_1/mods/pr/python/game`
- **SHA:** `2ae9d0c49e56add06fb982796fc902c04c59a43b`
- **Subject:** `nginx: add public /pr/logs locations and deny cache`
- **Files in commit:** only `docs/nginx-templates/latamsquad-locations.conf`

## Checklist

- [x] Step 1: Add locations (exact blocks, before tracker, `^~` deny)
- [x] Step 2: `nginx -t` + reload
- [x] Step 3: Smoke curls (UI 200; cache 404; PHP hit but 500 from app)
- [x] Step 4: Mirror conf into repo
- [x] Commit mirror only

## Concerns

1. **`/pr/logs/public/index.php` returns 500** — `App\Session` not found; needs Task 1 deploy/autoload fix, not further Nginx changes for this task.
2. **`nginx.exe -t` must be run from `C:\nginx`** (or with correct prefix); otherwise it looks for `conf/nginx.conf` under the current working directory.
3. Mirror commit also synced live autoindex JS version query (`20260725g`) that differed from the previous repo template.

## Evidence sources

- Brief: `.superpowers/sdd/task-2-brief.md`
- Live conf edit + `nginx -t` / reload output
- `curl.exe -skI` smoke responses
- `C:\nginx\logs\php_errors.log` for Class not found
- `git show 2ae9d0c`