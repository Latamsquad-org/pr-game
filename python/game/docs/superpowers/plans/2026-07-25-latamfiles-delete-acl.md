# Delete ACL Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (or executing-plans). Steps use checkbox (`- [ ]`) syntax.

**Goal:** Owner-only admin page to grant/revoke tracker delete permission; enforce in UI and `deleteRound.php`.

**Architecture:** JSON ACL under `admin/data/` + lib helpers; owner Discord ID constant; nav gated; tracker checks `delete_acl_can_delete()`.

**Tech Stack:** PHP 8, existing admin CSRF/bootstrap/layout, nginx html live + docs mirror.

---

### Task 1: Lib + JSON ACL

**Files:**
- Create: `C:/nginx/html/admin/lib/delete_acl.php`
- Create: `C:/nginx/html/admin/data/delete-acl.json` (empty list)
- Mirror: `docs/nginx-templates/admin/lib/delete_acl.php`

- [ ] Implement load/save/validate, `delete_acl_owner_id`, `delete_acl_is_owner`, `delete_acl_can_delete`, grant/revoke
- [ ] `php -l` on lib

### Task 2: Admin page + nav

**Files:**
- Create: `C:/nginx/html/admin/delete-acl.php`
- Modify: `C:/nginx/html/admin/_layout.php`
- Mirror both under `docs/nginx-templates/admin/`

- [ ] Page owner-only; add/remove with CSRF
- [ ] Nav item "Borrado" only if owner

### Task 3: Enforce on tracker

**Files:**
- Modify: `C:/nginx/html/pr/tracker/index.php`
- Modify: `C:/nginx/html/pr/tracker/deleteRound.php`

- [ ] Button only if `delete_acl_can_delete`
- [ ] POST rejects if not allowed (403)

### Task 4: Smoke

- [ ] Guest/no-acl staff: no × button
- [ ] Owner ID helper returns true for `357055203348054027`
- [ ] Non-owner hitting delete-acl.php gets 403 (simulate if possible)
