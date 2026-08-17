# LATAMFILES Admin Nav Shortcuts — Design

**Date:** 2026-07-25  
**Status:** Approved for implementation (pending user review of this written spec)  
**Depends on:** Admin shell (`/admin/`, `_layout.php`, `_bootstrap.php`)  
**Scope:** Expand admin sidebar with a second group of same-tab shortcuts to site tools. No new admin pages.

## Problem

Staff use `/admin/` for Trafico/Demos/Auth settings but still jump manually to logs viewer, raw logs, tracker, and demos listings. The sidebar only lists config modules.

## Goals

- Add an **Atajos** section in the admin sidebar with five same-tab links.
- Keep existing **Config** items unchanged (Inicio, Trafico, Demos settings, Auth placeholder).
- Visual grouping so "Demos" (settings) is not confused with Demos 2D/3D listings.
- Mirror live changes under `docs/nginx-templates/`.

## Non-goals (v1)

- Implementing Auth settings (still Proximamente)
- New `/admin/*.php` pages for shortcuts
- `target="_blank"`
- Renaming the Demos settings nav label
- Changing URLs of Trafico/Demos/Auth modules
- Mobile redesign beyond existing admin breakpoints

## Decisions (locked)

| Topic | Choice |
|-------|--------|
| Integration | Sidebar sections in `_layout.php` (approach 1) |
| Behavior | Same-tab links |
| Grouping | Config + Atajos headings |
| Demos listings | Two items: Demos 2D, Demos 3D |
| Settings label | Keep **Demos** for `/admin/demos.php` |

## Information architecture

### Config (active nav keys unchanged)

| Label | Href | Active key |
|-------|------|------------|
| Inicio | `/admin/` | `home` |
| Trafico | `/admin/traffic.php` | `traffic` |
| Demos | `/admin/demos.php` | `demos` |
| Auth | `/admin/auth-settings.php` | `auth` |

### Atajos (never `is-active` / `aria-current`)

| Label | Href |
|-------|------|
| Visor de logs | `/pr/logs/` |
| Logs crudos | `/pr/admins/logs/sv1/` |
| Tracker | `/pr/tracker/?srv=1` |
| Demos 2D | `/pr/demos2d/` |
| Demos 3D | `/pr/demos3d/sv1/` |

Section titles **Config** and **Atajos** are non-interactive labels (e.g. `<p>` or `<h2 class="...">` inside the aside nav).

## UI / CSS

Add minimal styles in `site.css`:

- `.latam-admin__nav-section` — group wrapper (spacing between Config and Atajos)
- `.latam-admin__nav-label` — small uppercase/muted section title matching admin look (use existing CSS variables / accent; ASCII-safe)

Reuse existing `.latam-admin__nav-link` for all links. Atajo links use the same class without `.is-active`.

## Access control

Unchanged: every `/admin/*.php` still goes through `_bootstrap.php` (Discord staff).  
Shortcuts navigate away from `/admin/`; destination auth is whatever those paths already use (e.g. Logs crudos keeps Discord gate; Visor de logs remains public).

## Files

| Path | Role |
|------|------|
| `C:/nginx/html/admin/_layout.php` | Render two nav sections |
| `C:/nginx/html/assets/css/site.css` | Section label/spacing |
| `docs/nginx-templates/admin/_layout.php` | Mirror |
| `docs/nginx-templates/assets/css/site.css` | Mirror |

## Testing (smoke)

1. Logged-in staff: `GET /admin/` HTML contains `Config`, `Atajos`, and all five shortcut hrefs.
2. Config active states still work on Trafico/Demos/Auth/Inicio.
3. Click/check URLs: logs, admins logs, tracker, demos2d, demos3d paths as table above.
4. Narrow viewport: sidebar still usable with existing media queries (no overflow regression beyond pre-existing behavior).

## Success criteria

- Sidebar shows Config + Atajos with the locked labels and hrefs.
- Demos settings item remains labeled **Demos**.
- No new admin PHP pages.
- Live and repo mirror stay in sync for `_layout.php` and `site.css`.
