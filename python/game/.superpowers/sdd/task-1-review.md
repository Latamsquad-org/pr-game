# Task 1 Review: Vendor tree + discover log paths + LATAM config

**Reviewer:** task-scoped gate (live filesystem; no git diff)  
**Date:** 2026-07-25  
**Sources:** task-1-brief.md, task-1-report.md, task-1-review-pkg.md, live reads under `C:/nginx/html/pr/logs/` and `C:/prbf2_N/admin/logs/`

---

## Spec Compliance

**PASS**

Task 1 deliverables match the brief and global constraints:

| Requirement | Evidence |
|---|---|
| Pinned upstream at `41ed8c1184c5877088d6496623607699aa873e32` | `C:/nginx/html/pr/logs/.git/HEAD` and `refs/heads/master` both resolve to that SHA; `FETCH_HEAD` records the same pin from `gerbesf/PR-LOG-Viewer` |
| Live tree at `C:/nginx/html/pr/logs/` | `public/index.php`, `config.php`, `app/Session.php`, vendor assets present |
| `public/logs/` exists (upstream empty `index.html`) | `C:/nginx/html/pr/logs/public/logs/index.html` readable (empty) |
| `VENDOR.md` content | Matches brief text (source URL, pin, maintainers, LATAM note) |
| `config.php` ASCII-only | No non-ASCII bytes (grep `[^\x00-\x7F]` empty); no comments with typographic chars |
| `require_login = false`, `hide_ips = true` | Lines 7-8 of live `config.php` |
| SV1-SV4 under `C:/prbf2_N/admin/logs/` pattern | All four `servers_list` entries use `C:/prbf2_{1..4}/admin/logs/...` |
| Discovery-driven whitelist/banlist | No real banlist/whitelist under searched candidates; config points at created `admin/logs/whitelist.txt` and `admin/logs/banlist.con` (not the brief's example `mods/pr/banlist.con`) |
| Placeholders when missing | Empty `whitelist.txt` and `banlist.con` exist for N=1..4 (verified via Read) |
| Optional missing logs keep expected paths | `ra_adminlog_main`, `cdhash`, `cdhash_main` paths present; files absent on disk (per brief) |
| `$GLOBALS['config']` assigned | Line 93 |
| `server_commands` match brief | Verbatim match to brief template |
| PHP lint | Controller/review-pkg report `No syntax errors`; live file is syntactically valid PHP |
| No game-repo commit for Task 1 | Report/commits: none; live-only under nginx html |

Environmental gaps (missing `cdhash*` / `*_main`, empty whitelist/banlist) are disclosed by the implementer and allowed by Step 2 rules. They do not fail Spec Compliance for this task.

---

## Strengths

1. **Pin is real, not just documented.** `.git/HEAD` is the required commit; `VENDOR.md` agrees.
2. **Config follows discovery, not the brief's example paths.** Banlist/whitelist correctly land under `admin/logs/` after all `mods/pr` / root candidates missed.
3. **Placeholders are in place** so `download.php` `file_get_contents` on banlist/whitelist does not immediately fatal on missing files.
4. **Global flags and ASCII constraint satisfied** without drifting from the brief's `server_commands` / date formats / `$GLOBALS` wiring.
5. **Honest DONE_WITH_CONCERNS report** — missing cdhash/`*_main` and empty downloads are called out for later smoke (Task 4), not papered over.

---

## Issues

### Critical

None.

### Important

None that violate Task 1 requirements.

**Environmental follow-up (out of Task 1 fix scope, but will bite smoke):**  
`public/download.php` calls bare `file_get_contents($server['cdhash'])` (no `@`). With `cdhash.txt` missing on all four servers, a full download action will fail/warn on hash save even though banlist/whitelist placeholders exist. Brief Step 2 only required placeholders for whitelist/banlist; optional hash paths were to remain as expected paths. Track for Task 4 smoke (empty `cdhash.txt` placeholders or tolerate failure).

### Minor

1. **`app_name` omitted from LATAM `config.php`**  
   - Files: `config.php` (absent key); used in `public/index.php:12,89` and `public/login.php:45,72`  
   - Brief template also omits it, so this is brief-aligned.  
   - Impact: empty title/heading and possible PHP notices when the UI loads.  
   - Optional polish later: add e.g. `$config['app_name'] = 'LATAM PR LOG Viewer';` if upstream sample had a title.

2. **Vendored `.git` left under docroot**  
   - Per brief copy steps; not a deviation.  
   - Note for ops: shallow clone metadata under `html/pr/logs/.git` is normal for this pin method; ensure it is not HTTP-exposed if that matters in later Nginx work.

---

## Assessment

**Task quality: Approved**

Implementation matches the Task 1 brief and binding constraints. Live pin, `VENDOR.md`, LATAM `config.php`, SV1-SV4 path pattern, discovery-adjusted whitelist/banlist with empty placeholders, and no game-repo commit are all verified. Remaining gaps are environmental (missing hash/main logs; empty ban/whitelist content) and already documented for later smoke — not Task 1 rework blockers.
