# LATAMFILES Admin Shell (`/admin/`) — Design

**Date:** 2026-07-24  
**Status:** Approved for implementation (pending user review of this spec)  
**Scope:** Panel shell only (navigation + auth gate). No editable settings yet.

## Problem

LATAMFILES will need admin-editable settings (Nginx traffic limits, demos UI, auth/messages). There is Discord staff login today (`/auth/`) but no staff home or menu to hang future modules on.

## Goals

- Staff-only area at `/admin/`
- Reuse existing Discord OAuth + `is_staff` session
- Home + sidebar with placeholders for future modules
- Header **ADMINS** link points to `/admin/`
- Match LATAMFILES visual language (`site.css`)

## Non-goals (v1)

- Saving any settings
- Regenerating or reloading Nginx config
- Editing demos list behavior, auth roles, or copy beyond static “Próximamente” pages
- Public (non-staff) access to any `/admin/` URL

## Access control

1. Every PHP page under `/admin/` includes a shared bootstrap that:
   - Starts session via `auth_start_session()`
   - Sends `noindex`
   - If no Discord session → redirect `302` to `/auth/discord.php` (with return path if easy; otherwise plain Discord login)
   - If session but not staff → HTTP 403 using existing notice-page style (or reuse `auth_callback_staff_required` pattern)
2. Nginx serves `/admin/*.php` through FastCGI (same pattern as `/auth/`).
3. Optional defense in depth: `auth_request` to `/auth/gate.php` for `/admin/` — nice-to-have, not required if PHP bootstrap is solid.

## Information architecture

| Path | Purpose |
|------|---------|
| `/admin/` or `/admin/index.php` | Home: welcome + Discord user card + logout |
| `/admin/traffic.php` | Placeholder “Tráfico — Próximamente” |
| `/admin/demos.php` | Placeholder “Demos — Próximamente” |
| `/admin/auth-settings.php` | Placeholder “Auth — Próximamente” |
| `/auth/logout.php` | Existing logout (link from admin) |

Sidebar (all admin pages):

- Inicio → `/admin/`
- Tráfico → `/admin/traffic.php` (disabled look OK, but linkable placeholder)
- Demos → `/admin/demos.php`
- Auth → `/admin/auth-settings.php`

Active item highlighted.

## Home content

- Title: something like “Panel de administración”
- Short line: settings modules will appear here as they are built
- Card: display name (`auth_current_display_name` or equivalent), Discord ID, staff badge
- Actions: “Cerrar sesión” → `/auth/logout.php`; “Volver al sitio” → `/` or `/pr.php`

## UI

- Reuse `/assets/css/site.css` and LATAMFILES header/logo
- Admin layout: sticky header + sidebar + main
- Mobile: sidebar stacks above main or collapses to a simple top nav of the same links
- No fake forms, toggles, or sample values that imply settings already work

## Header site-wide

- Autoindex JS and public pages: **ADMINS** → `/admin/` (instead of `/auth/discord.php` when we want one entry; unauthenticated users hitting `/admin/` are redirected to Discord)
- `pr.php` / public header: same target if present

## Files (expected)

| File | Role |
|------|------|
| `html/admin/_bootstrap.php` | Session + staff gate + shared helpers |
| `html/admin/_layout.php` | Header, sidebar, footer wrapper |
| `html/admin/index.php` | Home |
| `html/admin/traffic.php` | Placeholder |
| `html/admin/demos.php` | Placeholder |
| `html/admin/auth-settings.php` | Placeholder |
| `assets/css/site.css` | Admin layout styles (`.latam-admin-*`) |
| `latamsquad-locations.conf` | `location` for `/admin/` PHP |
| `assets/autoindex-enhance.js` | ADMINS href → `/admin/` |

Templates/backups may live under `docs/nginx-templates/` as the repo mirror of live Nginx HTML.

## Security notes

- Do not expose `client_secret` or auth config in the panel
- All admin responses `noindex, nofollow`
- Validate staff on every request (no trust of client-only flags)

## Success criteria

- Staff Discord user can open `/admin/` and see home + sidebar
- Non-logged user is sent to Discord login
- Non-staff Discord user gets 403 / access-restricted page
- Placeholder pages load with “Próximamente”
- ADMINS in public header reaches `/admin/`
- No settings are persisted in v1

## Follow-ups (later specs)

1. Tráfico Nginx (limits + safe reload)
2. Demos settings
3. Auth / message settings
