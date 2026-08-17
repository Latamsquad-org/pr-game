# Task 3 Review: Hub link on `/pr.php`

**Reviewer:** task-scoped gate (read-only)  
**Date:** 2026-07-25  
**Base:** `2ae9d0c49e56add06fb982796fc902c04c59a43b`  
**Head:** `226de34fc682820cae64f702b003c63a59336fd2`  
**Sources:** `task-3-brief.md`, `task-3-report.md`, `task-3-review-pkg.md`, live `C:/nginx/html/pr.php`, mirror `docs/nginx-templates/pr.php`, smoke curls

---

## Spec Compliance

**PASS**

Task 3 hub-link deliverables match the brief and global constraints:

| Requirement | Evidence |
|---|---|
| Add list item in `.pr-links` | Live line 98 and mirror line 93: `<li><a href="/pr/logs/">Visor de logs</a></li>` |
| ASCII label `Visor de logs` | Label is plain ASCII; no accented or unicode punctuation in the new line |
| href `/pr/logs/` | Exact path per brief and global plan |
| Order after tracker/demos, before Extras | Both live and mirror: tracker -> demos2d -> demos3d -> **logs** -> extras |
| Hub HTML smoke (Step 2) | Reviewer curl: `GET https://127.0.0.1/pr.php` (Host: latamsquad.dev) -> body contains `href="/pr/logs/"` and `Visor de logs` |
| Mirror `docs/nginx-templates/pr.php` (Step 3) | Commit `226de34` subject `hub: link Visor de logs to /pr/logs/`; single file `docs/nginx-templates/pr.php` (+1 list item) |
| Consumes working `/pr/logs/` from Task 2 | Reviewer smoke: `GET /pr/logs/` -> **200**; `GET /pr/logs/public/index.php` -> **200** |
| Live `pr.php` serves without BOM regression | Reviewer: live file starts `<?php` (no UTF-8 BOM); `GET /pr.php` -> **200** (`PHP/8.3.32`) |

**Spec compliance: PASS.** Steps 1-3 satisfied for this task scope.

---

## Strengths

1. **Minimal, correct hub entry** — one list item, exact label and path from the brief; no scope creep into viewer or Nginx config.
2. **Consistent placement** — `Visor de logs` sits after demos and before Extras in both live and mirror `.pr-links` blocks (identical markup for the five links).
3. **End-to-end discoverability verified** — hub page returns the link; target `/pr/logs/` and its PHP entry point respond 200.
4. **Honest report** — documents the live UTF-8 BOM incident (HTTP 500) and in-place fix; mirror amended without BOM.
5. **Focused git commit** — repo change is a single-file hub link addition with a clear subject line.

---

## Issues

### Critical

None.

### Important

None that violate Task 3 hub-link requirements.

**Resolved outside repo (note only):**  
Initial live edit wrote a UTF-8 BOM before `<?php`, breaking `declare(strict_types=1)`. Report states this was fixed on live `C:/nginx/html/pr.php`. Reviewer confirms no BOM and HTTP 200 on live hub.

### Minor

1. **Incidental encoding churn in mirror commit**  
   - File: `docs/nginx-templates/pr.php`  
   - Diff also touches unrelated middle-dot and back-arrow bytes on auth/back links (display as mojibake in the review package). The new hub line is unaffected. Prefer future edits to avoid re-saving unrelated UTF-8 sequences when adding ASCII-only list items.

2. **Live vs mirror full-file drift (pre-existing)**  
   - Live header includes `latam-ext-nav` community links; mirror template does not.  
   - Out of scope for Task 3 (`.pr-links` only), but full `pr.php` is not byte-identical between live and mirror.

3. **Live deploy not in game git**  
   - Expected for this workflow: only the mirror is versioned; live change relies on manual sync. Documented in report.

---

## Assessment

**Approved**

The hub link `Visor de logs` -> `/pr/logs/` is present, ASCII-labeled, consistently ordered, mirrored in the repo, and verified live. Task 2 dependency responds 200. Minor encoding noise and pre-existing header drift do not block this task. Ready to proceed.
