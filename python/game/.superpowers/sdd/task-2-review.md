# Task 2 Review: Nginx locations for `/pr/logs/` + deny cache

**Reviewer:** task-scoped gate (read-only)  
**Date:** 2026-07-25  
**Base:** `bb4f38587b153105d66e9275258a28ab58e7e2bf`  
**Head:** `2ae9d0c49e56add06fb982796fc902c04c59a43b`  
**Sources:** `task-2-brief.md`, `task-2-report.md`, `task-2-review-pkg.md`, live `C:/nginx/conf/latamsquad-locations.conf`, mirror `docs/nginx-templates/latamsquad-locations.conf`, smoke curls

---

## Spec Compliance

**PASS**

Task 2 Nginx deliverables match the brief and global constraints:

| Requirement | Evidence |
|---|---|
| Exact location blocks from brief | Live + mirror lines 179-201: `^~ /pr/logs/public/logs/` deny+404; `= /pr/logs` 301; prefix `/pr/logs/`; PHP regex FastCGI to `127.0.0.1:9000` with `SCRIPT_FILENAME $document_root/pr/logs/$1` |
| Placement before tracker block | Immediately after `/pr/extras/`, before `# Tracker en /pr/tracker` |
| Deny uses `^~` | `location ^~ /pr/logs/public/logs/` present |
| No `auth_request` on `/pr/logs/` | Grep: `auth_request` only on `/pr/admins/logs/sv1/` and `/pr/admins/bans1.sqlite3`; none under `/pr/logs` blocks |
| Do not modify `/pr/admins/logs/sv1/` semantics | Still `auth_request /auth/gate.php`, same `alias C:/prbf2_1/admin/logs/`, autoindex + sub_filter intact |
| Deny HTTP to cache dir (403/404) | Smoke: `GET /pr/logs/public/logs/` and `/pr/logs/public/logs/index.html` → **404** |
| Public UI without auth | Smoke: `GET /pr/logs/` → **200**; `GET /pr/logs/public/index.php` → **200** (`X-Powered-By: PHP/8.3.32`); no Discord redirect |
| Mirror repo template to live | SHA256 live == mirror (`84d2d15c...ad4fc1d0`) |
| Commit mirror only | Commit `2ae9d0c` subject `nginx: add public /pr/logs locations and deny cache`; single file `docs/nginx-templates/latamsquad-locations.conf` |

Controller follow-up (not in this git diff): Session autoload fixed in live `config.php`; reviewer re-smoke confirms PHP **200** and cache **404**. Implementer-time PHP **500** (`App\Session` not found) was app packaging, not an Nginx location defect.

**Spec compliance: PASS.** Steps 1-4 satisfied for this task scope.

---

## Strengths

1. **Blocks match the brief verbatim** — deny/`^~`, slash redirect, static prefix, and PHP FastCGI location are as specified; placement before tracker avoids location-order surprises.
2. **Constraints honored** — no `auth_request` on the public viewer; `/pr/admins/logs/sv1/` keeps its gate; cache path returns 404 including nested files.
3. **Live and mirror are identical** — full-file hash match; repo template is a true production mirror.
4. **Honest report** — documented PHP 500 and the `C:\nginx` cwd requirement for `nginx -t` instead of claiming a clean brief smoke.
5. **Routing verified end-to-end** — static 200, PHP hits FastCGI, bare `/pr/logs` → 301 `/pr/logs/`.

---

## Issues

### Critical

None.

### Important

None that violate Task 2 Nginx requirements.

**Resolved outside this commit (note only):**  
At implementer smoke, `/pr/logs/public/index.php` returned 500 (`Class "App\Session" not found`). Controller later fixed Session autoload in live `config.php`. Current live smoke is 200. No further Nginx change needed for Task 2.

### Minor

1. **Incidental autoindex cache-bust sync (`v=20260725d` → `v=20260725g`)**  
   - Files: multiple `sub_filter` lines in `docs/nginx-templates/latamsquad-locations.conf` (demos2d/3d, extras, and the `sub_filter` line under `/pr/admins/logs/sv1/`)  
   - Cause: full live→mirror copy, not intentional admins-logs redesign.  
   - Auth/alias semantics of `/pr/admins/logs/sv1/` unchanged; query bump only.  
   - Prefer future mirrors to avoid unrelated noise in the Task 2 diff, or document the sync as intentional.

---

## Assessment

**Task quality: Approved**

Nginx locations for the public PR LOG Viewer are correctly inserted, constrained, mirrored, and verified live. Cache deny works; public routes have no auth; admins logs gate is preserved. The implementer-time PHP 500 was outside Nginx scope and is already cleared by the controller follow-up. Ready to proceed to the next task.
