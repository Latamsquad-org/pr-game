# Traffic Task 3 Review: Wire Nginx includes + deny data + seed confs

**Reviewer role:** Task-scoped gate (spec + quality), not merge review
**Base:** `a4f62dc0d53f7601e8c9b1a1dae80347539f1316`
**Head:** `661e8acaa0a4dfa7a1677f7b28bc94eba1c3dc1d`
**Sources:** `traffic-task-3-brief.md`, `traffic-task-3-report.md`, `traffic-task-3-review-pkg.md`
**Live spot-check (read-only):** `C:/nginx/conf/nginx.conf`, `latamsquad-locations.conf`, `latam-traffic-zones.conf`, `latam-traffic-limits.conf`

---

## Verdict

| Gate | Result |
|------|--------|
| Spec compliance | **PASS** |
| Quality | **Approved** (0 Critical / 0 Important / 1 Minor) |

---

## Spec compliance

### Deliverables

| Requirement | Result | Notes |
|-------------|--------|-------|
| Step 1: `include latam-traffic-zones.conf;` in `http {}` after `types` | PASS | Live + mirror `nginx.conf` line 25; before `include latamsquad.conf`. |
| Step 2: Seed zones + limits via PHP defaults | PASS | Live confs match defaults: 60r/m, conn zone 10m, limit_conn 2, rate 8388608, burst 20 nodelay. |
| Step 3: `include latam-traffic-limits.conf;` in 8 demos locations | PASS | demos2d root+sv2-4, demos3d sv1-4; each after `autoindex on;`. |
| Step 4: Deny `location ^~ /admin/data/` | PASS | `deny all; return 404;` before admin block (live + mirror). |
| Step 5: `nginx -t` + reload | PASS | Report: syntax ok / test successful / reload OK; only pre-existing `prdemo` MIME warn. |
| Step 6: Mirror + commit | PASS | 4 files under `docs/nginx-templates/`; commit `661e8ac` message matches brief. |

### Live vs mirror alignment

| File | Result |
|------|--------|
| `nginx.conf` | PASS — live and template identical (zones include present). |
| `latamsquad-locations.conf` | PASS — 8 limits includes + deny `/admin/data/` at same positions. |
| `latam-traffic-zones.conf` | PASS — content matches live seed. |
| `latam-traffic-limits.conf` | PASS — content matches live seed. |

**Spec compliance: PASS.** Steps 1–6 satisfied for this task scope.

---

## Quality

### Strengths

- Wiring matches brief literally (placement after `autoindex on;`, zones in `http`, deny before admin).
- Limits scoped only to demos autoindex locations; extras/logs/admin/auth/tracker untouched.
- Generated conf headers (`do not edit by hand`) consistent with Task 1/2 generator output.
- Report accurately documents live-vs-git boundary and pre-existing MIME warn.

### Issues

#### Critical

None.

#### Important

None.

#### Minor

1. **`deny all;` + `return 404;` is redundant** — Matches brief template; either alone would block. Harmless; keep for brief fidelity.

### Out of scope (not scored)

- UI wiring of `traffic_nginx_apply()` (Task 4+)
- Functional load-test that limits actually throttle clients
- Fixing pre-existing duplicate `prdemo` MIME warn

---

## Conclusion

Traffic Task 3 meets the brief: zones/limits seeded and included, 8 demo locations limited, `/admin/data/` denied, nginx test/reload OK, templates mirrored and committed.

**Ship Traffic Task 3 as-is for the next task.**
