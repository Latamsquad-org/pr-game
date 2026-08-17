# Traffic Task 4 Review: CSRF helpers + traffic.php UI

**Reviewer role:** Task-scoped gate (spec + quality), not merge review
**Base:** `661e8acaa0a4dfa7a1677f7b28bc94eba1c3dc1d`
**Head:** `c58ac12c3aeb2266ec483b16339b9211b6c476e1`
**Sources:** `traffic-task-4-brief.md`, `traffic-task-4-report.md`, `traffic-task-4-review-pkg.md`
**Live spot-check (read-only):** `C:/nginx/html/admin/_bootstrap.php`, `C:/nginx/html/admin/traffic.php`

---

## Verdict

| Gate | Result |
|------|--------|
| Spec compliance | **PASS** |
| Quality | **Approved** (0 Critical / 0 Important / 1 Minor) |

---

## Spec compliance

### Must-have checklist

| Requirement | Result | Notes |
|-------------|--------|-------|
| CSRF helpers in `_bootstrap.php` | PASS | `admin_csrf_token()` + `admin_csrf_validate()` match brief; `hash_equals`; live + mirror. |
| CSRF on POST | PASS | Invalid -> 403 + `CSRF invalido`; form posts hidden `csrf`. |
| Confirm step | PASS | POST without `confirm` -> panel "Aplicar y recargar Nginx?"; with `confirm=1` -> `traffic_nginx_apply()`. |
| No Proximamente placeholder | PASS | Placeholder removed from `traffic.php` (live + mirror). |
| ASCII labels | PASS | Limites activos / Conexiones demos por IP / Velocidad max MB/s / Peticiones listado por minuto; file is ASCII-only. |

### Deliverables

| Requirement | Result | Notes |
|-------------|--------|-------|
| Step 1: CSRF in `_bootstrap.php` | PASS | Helpers before `auth_start_session()`; session used at call time. |
| Step 2: Full `traffic.php` form | PASS | GET load + backup flash; validate; confirm; apply; escaped output via `admin_h()`. |
| Step 3: `php -l` | PASS | Report: no syntax errors (live + mirror). |
| Step 4: Mirror + commit | PASS | 3 files under `docs/nginx-templates/`; commit `c58ac12` message matches brief. |
| Form CSS | PASS | `.latam-admin-form*` + flash styles appended to `site.css`. |

**Spec compliance: PASS.** Must-haves and Steps 1-4 satisfied.

---

## Quality

### Strengths

- Flow matches brief sketch (CSRF gate -> validate -> confirm -> apply).
- XSS-safe rendering (`admin_h` on flash, values, CSRF, backup path).
- Cancel returns to GET; confirm is explicit before nginx reload.
- Live admin PHP aligns with mirrored templates for CSRF + form.

### Issues

#### Critical

None.

#### Important

None.

#### Minor

1. **Backup path only on next GET** — After successful apply, `traffic_last_backup` is set in session but `$lastBackup` is only filled on GET, so the apply POST response does not show the path until a later visit. Matches brief ("GET: ... last backup"); intentional one-shot flash.

### Out of scope (not scored)

- Browser smoke with staff Discord login (Task 5+)
- End-to-end `traffic_nginx_apply()` against live nginx from the UI

---

## Conclusion

Traffic Task 4 meets the brief: CSRF helpers, two-step confirm before nginx apply, full traffic form without Proximamente, ASCII labels, mirrored and committed.

**Ship Traffic Task 4 as-is for the next task.**
