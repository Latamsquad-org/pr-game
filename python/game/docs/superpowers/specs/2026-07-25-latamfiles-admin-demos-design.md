# LATAMFILES Admin Demos Settings — Design

**Date:** 2026-07-25  
**Status:** Approved for implementation (pending user review of this written spec)  
**Depends on:** Admin shell at `/admin/`; autoindex enhance JS on demos2d/demos3d  
**Scope:** Staff-editable demos listing options via `/admin/demos.php`, consumed as public JSON by autoindex JS.

## Problem

Demo listing UX (tabs, server buttons, sort, labels) is hard-coded in `autoindex-enhance.js`. Staff need to change visibility, sort, and labels without editing JS by hand. `/admin/demos.php` is still a "Proximamente" placeholder.

## Goals

- Staff can edit: visible servers 1-4 (shared for 2D and 3D), sort mode, tab titles, server-row label.
- Settings persist in a public JSON file the list JS fetches.
- Save uses CSRF; no Nginx reload required.
- Fallbacks: if JSON missing/invalid, keep current hard-coded defaults behavior.

## Non-goals (v1)

- Separate server visibility for 2D vs 3D
- Hiding an entire tab type (2D or 3D)
- Changing disk paths or Nginx locations
- Traffic limits (already a different module)
- Auth/message settings
- Regenerating `autoindex-enhance.js` on save

## Settings model

**Public file:** `C:/nginx/html/assets/demos-settings.json`  
**URL:** `/assets/demos-settings.json` (readable by browsers; no secrets)

| Key | Type | Default | Notes |
|-----|------|---------|-------|
| `servers_visible` | int[] | `[1,2,3,4]` | Subset of 1..4, unique, sorted ascending; at least one |
| `sort` | string | `"newest"` | `"newest"` or `"name"` |
| `tab_2d` | string | `"PRdemos 2D"` | Non-empty, max 40 chars after trim |
| `tab_3d` | string | `"BF2demos 3D"` | Non-empty, max 40 chars after trim |
| `server_label` | string | `"Servidor"` | Non-empty, max 24 chars after trim |

**Validation:** reject save if invalid; unknown keys ignored on load; missing keys filled from defaults.

**Canonical store for the form:** same JSON path (no private duplicate required). Optional private mirror under `admin/data/` is YAGNI for v1.

## Apply model

1. Staff POST validated fields + CSRF.
2. Atomic write of `demos-settings.json` (temp + rename).
3. Flash success. No `nginx -t` / reload.
4. Autoindex pages pick up changes on next load (browser may cache JSON — use short cache or cache-bust query in JS, e.g. `demos-settings.json?v=` + filemtime from a tiny inline stamp, or `Cache-Control: no-cache` via Nginx location for that file). **Chosen:** JS fetch with `cache: 'no-store'` (or cache-bust timestamp from `Date.now()` only on admin save is impossible client-side; prefer `fetch(url, { cache: 'no-store' })`).

## Autoindex JS behavior

On demos2d/demos3d pages, before/during `injectServerNav` / sort:

1. Fetch `/assets/demos-settings.json` with no-store.
2. Merge with defaults if partial/invalid.
3. Tabs use `tab_2d` / `tab_3d`.
4. Server buttons: only `servers_visible`; label prefix from `server_label` (e.g. `Servidor` + number, or if label empty forbidden — always non-empty).
5. Sort: `newest` -> existing date sort; `name` -> localeCompare on name (parent `../` already filtered out).
6. If current server number is not in `servers_visible`, redirect to first visible server href for current kind (2d/3d).

If fetch fails: use in-JS defaults matching the table above (same as today).

## UI (`/admin/demos.php`)

- Admin layout; nav `demos` active.
- Checkboxes servers 1-4.
- Select sort: "Mas nuevos primero" / "Nombre A-Z".
- Text inputs for tab_2d, tab_3d, server_label.
- CSRF + single save button (no Nginx confirm dialog).
- Flash success/validation errors.
- ASCII-safe PHP source strings.

## Security

- Staff-only via `_bootstrap.php`.
- CSRF on POST.
- JSON contains only public UX strings/ints — no secrets.
- Sanitize display lengths; escape HTML in admin form values via `admin_h`.
- Autoindex must not `eval` JSON beyond parsing object fields.

## Files (expected)

| Path | Role |
|------|------|
| `html/admin/demos.php` | Form + save |
| `html/admin/lib/demos_settings.php` | defaults, load, validate, save, optional generate helpers |
| `html/assets/demos-settings.json` | Public settings (seeded with defaults) |
| `html/assets/autoindex-enhance.js` | Fetch settings; apply to nav + sort |
| `latamsquad-locations.conf` | Bump JS `?v=` cache bust after JS change |
| Repo mirrors under `docs/nginx-templates/` | As elsewhere |

## Success criteria

- Staff can save demos settings and see success without Nginx reload.
- Listing reflects visible servers, sort, and labels after refresh.
- Invalid POST rejected; CSRF forged POST rejected.
- Missing JSON -> defaults still work on listing.
- Hidden current server redirects to first visible.
- Non-staff cannot access save.

## Follow-ups (later)

- Per-type server visibility
- Hide 2D or 3D tab entirely
- Preview pane in admin
