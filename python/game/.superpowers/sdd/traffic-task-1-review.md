# Traffic Task 1 Review: Settings library + CLI tests

**Reviewer role:** Task-scoped gate (spec + quality), not merge review
**Base:** `294e558bce1c54b30798b19999c8c6e8a37b6659`
**Head:** `b1866ecfc6a72a938b0885e669d64ada375678c2`
**Sources:** `traffic-task-1-brief.md`, `traffic-task-1-report.md`, `traffic-task-1-review-pkg.md`
**Live spot-check (read-only):** `C:/nginx/html/admin/lib/traffic_settings.php`

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
| Create live `C:/nginx/html/admin/lib/traffic_settings.php` | PASS | Present; SHA256 matches repo mirror. |
| Create `tools/traffic_settings_cli_test.php` | PASS | Matches brief Step 1 template (8 assertions + ALL PASS). |
| Mirror `docs/nginx-templates/admin/lib/traffic_settings.php` | PASS | Diff + live/mirror content identical. |
| CLI TDD (RED then GREEN) | PASS | Report documents missing-lib fatal then GREEN; re-run now: ALL PASS (exit 0). |
| Commit `b1866ec` | PASS | Message matches brief Step 5. |

### Interfaces

| Function | Result |
|----------|--------|
| `traffic_settings_defaults()` | PASS — enabled=true, conn=2, rate=8.0, rpm=60 |
| `traffic_settings_path()` | PASS — `dirname(__DIR__) . '/data/traffic-settings.json'` |
| `traffic_settings_load()` | PASS — merge defaults; missing/invalid JSON -> defaults; validate settings |
| `traffic_settings_validate()` | PASS — ok/errors/settings; ranges per brief |
| `traffic_settings_save()` | PASS — mkdir + atomic `.tmp` + rename |
| `traffic_generate_zones_conf()` | PASS — always emits conn + req zones (no enabled gate) |
| `traffic_generate_limits_conf()` | PASS — directives only when enabled; else comments-only |

### Global constraints

| Constraint | Result | Evidence |
|------------|--------|----------|
| ASCII PHP | PASS | 0 bytes >127 in mirrored lib; Spanish messages without accents |
| Defaults enabled=true, conn=2, rate=8, rpm=60 | PASS | `traffic_settings_defaults()` |
| Zones always | PASS | `traffic_generate_zones_conf` ignores `enabled` |
| Limits only when enabled | PASS | early return when `empty($settings['enabled'])`; CLI asserts no `limit_conn` when off |
| CLI TDD | PASS | test file + RED/GREEN flow documented; GREEN verified locally |

**Spec compliance: PASS.**

---

## Quality

### Strengths

- Implementation matches the brief template closely (validate ranges, atomic save, nginx `$` escaping).
- Live deploy and git mirror are byte-identical (same SHA256).
- CLI smoke covers reject path, coerce/accept path, float rate, zones, limits on/off.
- `php -l` clean on mirror; runtime CLI ALL PASS against live lib.

### Issues

#### Critical

None.

#### Important

None.

#### Minor

1. **`traffic_settings_save()` not exercised by CLI test** — Report already notes; acceptable for Task 1; Task 2+ should cover write/load round-trip.
2. **No CLI assert that zones still emit when `enabled=false`** — Implementation is correct (zones always); adding one assertion would lock the design constraint.

### Out of scope (not scored)

- Admin UI / save-load wiring (Task 2)
- Nginx conf deploy hook (Task 3)
- Live lib outside git (by design)

---

## Conclusion

Traffic Task 1 meets the brief and stated constraints. Defaults, zones-always / limits-when-enabled behavior, ASCII PHP, and CLI TDD are satisfied with live+mirror alignment.

**Ship Traffic Task 1 as-is for the next task.**
