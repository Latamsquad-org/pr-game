# LATAMFILES Admin Demos Settings Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Replace `/admin/demos.php` placeholder with a CSRF-protected form that saves public `demos-settings.json`, and teach `autoindex-enhance.js` to fetch and apply those settings (servers, sort, labels).

**Architecture:** PHP lib validates/saves JSON under `html/assets/demos-settings.json`. Admin form mirrors traffic module patterns (without Nginx reload). Autoindex JS loads settings with `fetch(..., { cache: 'no-store' })` before building nav/sort; defaults if fetch fails.

**Tech Stack:** PHP 8.x admin shell, existing CSRF helpers, vanilla JS autoindex enhance, Nginx (cache-bust JS query only).

## Global Constraints

- ASCII only in PHP comments/strings.
- Staff-only `_bootstrap.php`; CSRF on POST; no Nginx reload for demos save.
- Defaults: servers `[1,2,3,4]`, sort `newest`, tab_2d `PRdemos 2D`, tab_3d `BF2demos 3D`, server_label `Servidor`.
- servers_visible: subset of 1..4, unique, sorted, at least one; tab strings max 40; label max 24.
- Public JSON at `C:/nginx/html/assets/demos-settings.json` — no secrets.
- JS fetch no-store; fallback to in-JS defaults on failure.
- If current server hidden, redirect to first visible for current kind.
- Live `C:/nginx/html/`; mirror `docs/nginx-templates/`; branch `feature/latamfiles-admin-shell`.

---

## File map

| Path | Role |
|------|------|
| `C:/nginx/html/admin/lib/demos_settings.php` | defaults/load/validate/save |
| `C:/nginx/html/admin/demos.php` | UI form |
| `C:/nginx/html/assets/demos-settings.json` | seeded public settings |
| `C:/nginx/html/assets/autoindex-enhance.js` | fetch + apply |
| `C:/nginx/conf/latamsquad-locations.conf` | bump `?v=` on JS |
| `tools/demos_settings_cli_test.php` | CLI asserts |
| `docs/nginx-templates/**` | mirrors |

---

### Task 1: demos_settings.php + CLI tests

**Files:**
- Create: `C:/nginx/html/admin/lib/demos_settings.php`
- Create: `tools/demos_settings_cli_test.php`
- Mirror lib under `docs/nginx-templates/admin/lib/`

**Interfaces:**
- `demos_settings_defaults(): array`
- `demos_settings_path(): string` -> `dirname(__DIR__, 2)` wait: file is in `admin/lib`, assets is `html/assets` -> `dirname(__DIR__, 2)` is wrong. From `admin/lib`, `dirname(__DIR__)` is `admin`, parent of admin is html: `dirname(dirname(__DIR__)) . '/assets/demos-settings.json'` OR `dirname(__DIR__) . '/../assets/demos-settings.json'`.
- Use: `return dirname(__DIR__, 2) . '/assets/demos-settings.json'` only if PHP 7+ dirname levels — `__DIR__` = `.../admin/lib`, `dirname(__DIR__)` = `.../admin`, `dirname(__DIR__, 2)` = `.../html`. Correct: `dirname(__DIR__, 2) . '/assets/demos-settings.json'`.
- `demos_settings_load(): array`
- `demos_settings_validate(array $in): array` -> ok/errors/settings
- `demos_settings_save(array $settings): void` atomic

POST shape for servers: checkboxes `servers_visible[]` = 1..4.

- [ ] **Step 1: Write CLI test (RED)**

`tools/demos_settings_cli_test.php` requires live lib; assert reject empty servers; accept `[1,3]`; reject sort `foo`; accept name sort; trim tab length; print ALL PASS.

- [ ] **Step 2: Run — expect fail missing lib**

- [ ] **Step 3: Implement lib** (defaults, load merge, validate, atomic save)

- [ ] **Step 4: Run — ALL PASS**

- [ ] **Step 5: Mirror + commit** `Agrega libreria de settings de demos y tests CLI.`

---

### Task 2: Seed JSON + admin demos.php form

**Files:**
- Create: `C:/nginx/html/assets/demos-settings.json` (defaults)
- Replace: `C:/nginx/html/admin/demos.php`
- Optional CSS reuse from traffic form classes
- Mirror

- [ ] **Step 1: Seed JSON** with defaults pretty-printed.

- [ ] **Step 2: Implement demos.php**

Pattern like traffic without confirm:

```php
require bootstrap, layout, demos_settings;
POST: csrf -> validate -> save -> flash;
GET: load settings;
Form: checkboxes 1-4, select sort, inputs tab_2d/tab_3d/server_label, csrf, Guardar.
```

Remove Proximamente entirely.

- [ ] **Step 3: php -l demos.php + lib**

- [ ] **Step 4: Mirror + commit** `Activa el formulario de settings de demos.`

---

### Task 3: autoindex-enhance.js consumes settings

**Files:**
- Modify: `C:/nginx/html/assets/autoindex-enhance.js`
- Modify: `latamsquad-locations.conf` bump `autoindex-enhance.js?v=` (e.g. `20260725d`)
- Mirror + nginx reload after conf bump

**Behavior changes:**

1. Add `DEMOS_DEFAULTS` object matching PHP defaults.
2. Add `normalizeDemosSettings(raw)` client-side (same rules, defensive).
3. Add `fetchDemosSettings(cb)` using `fetch('/assets/demos-settings.json', { cache: 'no-store' })` then `cb(settings)`; on error `cb(DEMOS_DEFAULTS)`.
4. Change `build()` flow for demos context:
   - If `getDemoContext()` non-null: fetch settings then continue build with settings.
   - Else: build with null settings (no nav change for extras).
5. `injectServerNav(settings)` uses tab titles, visible servers, server_label + ` i`.
6. Before inject: if `servers_visible.indexOf(ctx.srv) < 0`, `location.replace(demoServerHref(ctx.kind, settings.servers_visible[0])); return;`
7. Sort: if `settings.sort === 'name'` sort by name; else `sortRowsNewestFirst`.

Keep IE-ish style (var/function) already used in file; `fetch` is OK for modern browsers staff use — if fetch missing, use defaults synchronously.

- [ ] **Step 1: Implement JS changes**

- [ ] **Step 2: Bump cache query in all demos (and other) autoindex sub_filter lines; nginx -t; reload**

- [ ] **Step 3: Smoke**

```powershell
curl.exe -sk "https://127.0.0.1/assets/demos-settings.json" -H "Host: latamsquad.dev"
# expect JSON defaults
curl.exe -sk "https://127.0.0.1/assets/autoindex-enhance.js?v=20260725d" -H "Host: latamsquad.dev" | Select-String "fetchDemosSettings|DEMOS_DEFAULTS"
```

- [ ] **Step 4: Mirror + commit** `El listado de demos lee settings desde JSON.`

---

### Task 4: Verification

- [ ] CLI tests pass
- [ ] Logged-out `/admin/demos.php` -> 302 Discord
- [ ] Staff manual: uncheck server 4, change tab text, sort name, save, refresh listing
- [ ] Write `.superpowers/sdd/demos-verify.md`
- [ ] Commit verify doc only if needed; otherwise leave untracked OK

---

## Spec coverage

| Spec | Task |
|------|------|
| Lib + validation | 1 |
| Admin form + JSON save | 2 |
| Autoindex fetch/apply | 3 |
| Success criteria checks | 4 |

No TBD left. Names: `demos_settings_*` consistent.
