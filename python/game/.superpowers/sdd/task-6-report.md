# Task 6 — Manual verification report

Date: 2026-07-24

## Automated checks (controller)

| Check | Result |
|-------|--------|
| GET /admin/ without session | 302 Location: /auth/discord.php ; X-Robots-Tag: noindex, nofollow |
| GET /admin/traffic.php without session | 302 (auth) |
| pr.php ADMINS href | `/admin/` |
| autoindex-enhance.js ADMINS | `/admin/` |
| Admin PHP files present | index, traffic, demos, auth-settings, _bootstrap, _layout |
| Fake settings forms | none |
| Placeholder copy Proximamente | traffic, demos, auth-settings |

## Manual checks requiring Discord (user)

| Check | Result |
|-------|--------|
| Staff Discord lands on /admin/ with sidebar + card | PENDING user |
| Non-staff Discord gets 403 notice | PENDING user |
| Cerrar sesion works | PENDING user |
| ADMINS from demos list to /admin/ | PENDING user (JS href verified) |

## Verdict

Automated gate for Task 6: PASS for logged-out paths and link wiring.
Staff/non-staff OAuth paths need one live click from a staff account.
