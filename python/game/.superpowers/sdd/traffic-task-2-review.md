# Traffic Task 2 Review: Nginx apply library

**Reviewer role:** Task-scoped gate (spec + quality), not merge review
**Base:** `b1866ecfc6a72a938b0885e669d64ada375678c2`
**Head:** `a4f62dc0d53f7601e8c9b1a1dae80347539f1316`
**Sources:** `traffic-task-2-brief.md`, `traffic-task-2-report.md`, `traffic-task-2-review-pkg.md`
**Live spot-check (read-only):** `C:/nginx/html/admin/lib/traffic_nginx.php`

---

## Verdict

| Gate | Result |
|------|--------|
| Spec compliance | **PASS** |
| Quality | **Approved** (2 Minor) |

---

## Spec compliance

### Deliverables

| Requirement | Result | Notes |
|-------------|--------|-------|
| Create live `C:/nginx/html/admin/lib/traffic_nginx.php` | PASS | Present; SHA256 `87463DBF...C118DA` matches repo mirror. |
| Mirror `docs/nginx-templates/admin/lib/traffic_nginx.php` | PASS | New file +110 lines in `a4f62dc`; content matches brief template. |
| Dry smoke (generate limits, no apply/reload) | PASS | Re-run emits `limit_conn` / `limit_rate` / `limit_req` lines; report correctly notes `traffic_nginx_apply()` not invoked. |
| Commit `a4f62dc` | PASS | Message matches brief Step 3: `Agrega aplicacion segura de limites Nginx desde el panel.` |
| `php -l` | PASS | No syntax errors on live and mirror. |

### Interfaces

| Function | Result |
|----------|--------|
| `traffic_nginx_paths(): array` | PASS — nginx_dir, nginx_exe, zones, limits, backup_root |
| `traffic_nginx_atomic_write(string, string): void` | PASS — `.tmp` + rename; unlink tmp on rename fail |
| `traffic_nginx_run(string): array` | PASS — proc_open with cwd nginx_dir; returns code/out/err |
| `traffic_nginx_apply(array): array` | PASS — ok/message/backup/nginx_log; backup, save, write, `-t`, restore-on-fail, reload |

Consumes: `traffic_settings_save`, `traffic_generate_zones_conf`, `traffic_generate_limits_conf` via `require_once traffic_settings.php` — PASS.

### Global / design constraints (task scope)

| Constraint | Result | Evidence |
|------------|--------|----------|
| ASCII PHP | PASS | 0 bytes >127 in mirror (3750 bytes) |
| Backup then write then `nginx -t` then restore or reload | PASS | Matches brief + design apply pipeline for this lib |
| Truncate nginx_log to 2000 | PASS | `substr(..., 0, 2000)` on failure/success paths |
| Server-generated backup stamp only | PASS | `gmdate('Ymd-His')` under `C:/nginx/conf/backup/traffic-{stamp}/` |

**Spec compliance: PASS.** Steps 1–3 satisfied for this task scope.

### Review package note

`traffic-task-2-review-pkg.md` had empty Commits/Stat/Diff sections. Verified instead via `git show`/`git diff` Base..Head and live/mirror hashes (not scored against implementation).

---

## Quality

### Strengths

- Implementation matches the brief template line-for-line (paths, atomic write, proc_open, apply flow).
- Live deploy and git mirror are byte-identical (same SHA256).
- Dry smoke re-verified against live lib; `php -l` clean.
- Report accurately scopes risk: apply not called; full apply needs Task 3 includes + UI confirm (Task 4+).

### Issues

#### Critical

None.

#### Important

None.

#### Minor

1. **On write/`settings_save` exception, confs are not restored from the just-created backup** — Matches brief template; settings JSON may already be saved. Acceptable for Task 2; UI/ops path (Task 4+) should treat catch as partial apply.
2. **Reload failure does not roll back conf files** — Matches brief (`nginx -t OK pero reload fallo`). Files on disk may diverge from running config until next successful reload; document in UI messaging later.

### Out of scope (not scored)

- `nginx.conf` / locations `include` wiring (Task 3)
- Admin UI confirm + call to `traffic_nginx_apply()` (Task 4+)
- Invoking live `nginx -t` / `-s reload` in this task (brief Step 2 is dry generate only)
- Live lib outside git (by design)

---

## Conclusion

Traffic Task 2 meets the brief: apply library with backup / atomic write / `-t` restore / reload, live+mirror aligned, ASCII PHP, dry smoke OK.

**Ship Traffic Task 2 as-is for the next task.**
