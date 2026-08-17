# LATAMFILES PR LOG Viewer Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Deploy a vendored [gerbesf/PR-LOG-Viewer](https://github.com/gerbesf/PR-LOG-Viewer) at public `https://latamsquad.dev/pr/logs/` reading local SV1-SV4 logs with IPs masked, without exposing raw cache files over HTTP, and link it from `/pr.php`.

**Architecture:** Copy upstream PHP app into `C:/nginx/html/pr/logs/`. LATAM `config.php` points at `C:/prbf2_N/admin/logs/` (N=1..4). Upstream flow is refresh-via-`download.php` (copies sources into `public/logs/`) then APIs read that cache; Nginx denies HTTP to `public/logs/` while allowing JSON refresh. Hub gets one link. Staff autoindex `/pr/admins/logs/sv1/` unchanged.

**Tech Stack:** PHP (existing FastCGI 127.0.0.1:9000), Nginx on Windows (`C:/nginx`), AngularJS UI from upstream, PowerShell/curl smoke checks.

**Spec:** `docs/superpowers/specs/2026-07-25-latamfiles-pr-log-viewer-design.md`

## Global Constraints

- ASCII only in new/edited PHP comments and strings (no fancy dashes/quotes).
- Public `/pr/logs/` — no Discord `auth_request`, no viewer MD5 login (`require_login = false`).
- `hide_ips = true` in config.
- Never serve raw cache or source logs under `/pr/logs/` HTTP (deny `public/logs/`).
- Keep `download.php` callable as JSON-only refresh if UI depends on it (it does: `ApplicationController.downloadLog`).
- Do not change `/pr/admins/logs/sv1/`.
- Live: `C:/nginx/html/`, `C:/nginx/conf/`; mirror under `docs/nginx-templates/`.
- Domain/origin: `latamsquad.dev`.
- Pin upstream commit `41ed8c1184c5877088d6496623607699aa873e32` (master as of design).
- Hub link label: `Visor de logs` -> `/pr/logs/`.

---

## File map

| Path | Responsibility |
|------|----------------|
| `C:/nginx/html/pr/logs/**` | Vendored upstream tree + LATAM `config.php` + `VENDOR.md` |
| `C:/nginx/html/pr/logs/config.php` | SV1-SV4 paths, `require_login`, `hide_ips` |
| `C:/nginx/html/pr/logs/public/logs/` | Writable cache (PHP only; HTTP denied) |
| `C:/nginx/html/pr.php` | Hub link |
| `C:/nginx/conf/latamsquad-locations.conf` | `/pr/logs/` PHP + deny cache |
| `docs/nginx-templates/pr/logs/**` | Repo mirror of vendor + config |
| `docs/nginx-templates/pr.php` | Mirror hub |
| `docs/nginx-templates/latamsquad-locations.conf` | Mirror nginx |

---

### Task 1: Vendor tree + discover log paths + LATAM config

**Files:**
- Create: `C:/nginx/html/pr/logs/` (full upstream tree)
- Create: `C:/nginx/html/pr/logs/VENDOR.md`
- Create/overwrite: `C:/nginx/html/pr/logs/config.php`
- Ensure: `C:/nginx/html/pr/logs/public/logs/` exists and is writable (keep empty `index.html` if upstream has it)
- Mirror later in Task 4 (or sync after config frozen)

**Interfaces:**
- Produces: working vendor at `html/pr/logs` with `config.php` exposing `$GLOBALS['config']` including `servers_list` ids 1..4 and flags below.
- Consumes: disk layout `C:/prbf2_N/...` for N=1..4.

- [ ] **Step 1: Clone pinned upstream into a temp folder, then copy into docroot**

```powershell
$pin = "41ed8c1184c5877088d6496623607699aa873e32"
$tmp = "C:/nginx/html/_tmp_pr_log_viewer"
if (Test-Path $tmp) { Remove-Item -Recurse -Force $tmp }
git clone --depth 1 https://github.com/gerbesf/PR-LOG-Viewer.git $tmp
Set-Location $tmp
git fetch --depth 1 origin $pin
git checkout $pin
$dest = "C:/nginx/html/pr/logs"
New-Item -ItemType Directory -Force -Path "C:/nginx/html/pr" | Out-Null
if (Test-Path $dest) { Remove-Item -Recurse -Force $dest }
Copy-Item -Recurse $tmp $dest
Remove-Item -Recurse -Force $tmp
# Ensure cache dir exists
New-Item -ItemType Directory -Force -Path "$dest/public/logs" | Out-Null
```

Expected: `C:/nginx/html/pr/logs/public/index.php` and `config.php` exist.

- [ ] **Step 2: Discover real file paths on this machine**

```powershell
1..4 | ForEach-Object {
  $n = $_
  $root = "C:/prbf2_$n"
  Write-Host "=== SV$n $root ==="
  @(
    "admin/logs/ra_adminlog.txt",
    "admin/logs/ra_adminlog_main.txt",
    "admin/logs/cdhash.txt",
    "admin/logs/cdhash_main.txt",
    "admin/logs/whitelist.txt",
    "mods/pr/banlist.con",
    "mods/pr/python/banlist.con",
    "admin/banlist.con",
    "banlist.con"
  ) | ForEach-Object {
    $p = Join-Path $root $_
    if (Test-Path $p) { "FOUND $p" } else { "miss  $p" }
  }
  Get-ChildItem -ErrorAction SilentlyContinue "C:/prbf2_$n/admin/logs" | Select-Object -ExpandProperty Name
}
```

Record FOUND paths. For missing optional files (`ra_adminlog_main`, `cdhash_main`), still put the expected path in config (upstream uses `@file_get_contents` / empty incremental). For `whitelist` / `banlist`, pick the FOUND path per server; if a server has no banlist/whitelist file, create an empty placeholder file next to that server's admin logs (e.g. `C:/prbf2_N/admin/logs/whitelist.txt` and empty `banlist.con`) so `download.php` does not fatally fail — only if no real file exists.

- [ ] **Step 3: Write `VENDOR.md`**

Create `C:/nginx/html/pr/logs/VENDOR.md`:

```markdown
# Vendored: gerbesf/PR-LOG-Viewer

- Source: https://github.com/gerbesf/PR-LOG-Viewer
- Pinned commit: 41ed8c1184c5877088d6496623607699aa873e32
- Upstream maintainers: Ferreira, Danesh_italiano (see upstream README)
- LATAM changes: config.php paths/flags only; Nginx denies public/logs HTTP
```

- [ ] **Step 4: Write LATAM `config.php`**

Overwrite `C:/nginx/html/pr/logs/config.php` with ASCII-only content. Adjust whitelist/banlist paths to match Step 2 FOUND results (examples below assume logs dir + `mods/pr/banlist.con` — replace if discovery differs):

```php
<?php
$config = [];

$config['date_format'] = 'Y-m-d';
$config['hour_format'] = 'H:i:s';
$config['expiration_time'] = '30 minutes';
$config['require_login'] = false;
$config['hide_ips'] = true;
$config['with_md5'] = false;
$config['auth'] = [];

$config['servers_list'] = [];

$config['servers_list'][] = [
    'id' => 1,
    'name' => 'LATAM SV1',
    'ra_adminlog' => 'C:/prbf2_1/admin/logs/ra_adminlog.txt',
    'ra_adminlog_main' => 'C:/prbf2_1/admin/logs/ra_adminlog_main.txt',
    'cdhash' => 'C:/prbf2_1/admin/logs/cdhash.txt',
    'cdhash_main' => 'C:/prbf2_1/admin/logs/cdhash_main.txt',
    'whitelist' => 'C:/prbf2_1/admin/logs/whitelist.txt',
    'banlist' => 'C:/prbf2_1/mods/pr/banlist.con',
    'local_name' => 'latam_sv1.txt',
];

$config['servers_list'][] = [
    'id' => 2,
    'name' => 'LATAM SV2',
    'ra_adminlog' => 'C:/prbf2_2/admin/logs/ra_adminlog.txt',
    'ra_adminlog_main' => 'C:/prbf2_2/admin/logs/ra_adminlog_main.txt',
    'cdhash' => 'C:/prbf2_2/admin/logs/cdhash.txt',
    'cdhash_main' => 'C:/prbf2_2/admin/logs/cdhash_main.txt',
    'whitelist' => 'C:/prbf2_2/admin/logs/whitelist.txt',
    'banlist' => 'C:/prbf2_2/mods/pr/banlist.con',
    'local_name' => 'latam_sv2.txt',
];

$config['servers_list'][] = [
    'id' => 3,
    'name' => 'LATAM SV3',
    'ra_adminlog' => 'C:/prbf2_3/admin/logs/ra_adminlog.txt',
    'ra_adminlog_main' => 'C:/prbf2_3/admin/logs/ra_adminlog_main.txt',
    'cdhash' => 'C:/prbf2_3/admin/logs/cdhash.txt',
    'cdhash_main' => 'C:/prbf2_3/admin/logs/cdhash_main.txt',
    'whitelist' => 'C:/prbf2_3/admin/logs/whitelist.txt',
    'banlist' => 'C:/prbf2_3/mods/pr/banlist.con',
    'local_name' => 'latam_sv3.txt',
];

$config['servers_list'][] = [
    'id' => 4,
    'name' => 'LATAM SV4',
    'ra_adminlog' => 'C:/prbf2_4/admin/logs/ra_adminlog.txt',
    'ra_adminlog_main' => 'C:/prbf2_4/admin/logs/ra_adminlog_main.txt',
    'cdhash' => 'C:/prbf2_4/admin/logs/cdhash.txt',
    'cdhash_main' => 'C:/prbf2_4/admin/logs/cdhash_main.txt',
    'whitelist' => 'C:/prbf2_4/admin/logs/whitelist.txt',
    'banlist' => 'C:/prbf2_4/mods/pr/banlist.con',
    'local_name' => 'latam_sv4.txt',
];

$config['server_commands'] = [
    ['name' => 'SETNEXT', 'color' => 'success', 'value' => ['SETNEXT']],
    ['name' => 'RUNNEXT', 'color' => 'danger', 'value' => ['RUNNEXT']],
    ['name' => 'MAPVOTE', 'color' => 'success', 'value' => ['MAPVOTE']],
    ['name' => 'REPORT', 'color' => 'danger', 'value' => ['REPORT']],
    ['name' => 'REPORT PLAYER', 'color' => 'danger', 'value' => ['REPORTP']],
    ['name' => 'WARNING', 'color' => 'warning', 'value' => ['WARN']],
    ['name' => 'KICK', 'color' => 'danger', 'value' => ['KICK']],
    ['name' => 'TEMP BAN', 'color' => 'danger', 'value' => ['TEMPBAN']],
    ['name' => 'PERM BAN', 'color' => 'danger', 'value' => ['BAN']],
    ['name' => 'RESIGN', 'color' => 'danger', 'value' => ['RESIGN']],
    ['name' => 'HISTORY', 'color' => 'success', 'value' => ['HISTORY']],
    ['name' => 'SCRAMBLE', 'color' => 'danger', 'value' => ['SCRAMBLE']],
    ['name' => 'SAY / SAYTEAM', 'color' => 'success', 'value' => ['SAY', 'SAYTEAM']],
    ['name' => 'SWITCH', 'color' => 'success', 'value' => ['SWITCH']],
    ['name' => 'SWAPTEAMS', 'color' => 'success', 'value' => 'SWAPTEAMS'],
    ['name' => 'FLY', 'color' => 'success', 'value' => ['FLY']],
    ['name' => 'UNBAN', 'color' => 'danger', 'value' => ['UNBAN']],
    ['name' => 'INIT', 'color' => 'success', 'value' => 'INIT'],
    ['name' => 'RELOAD', 'color' => 'success', 'value' => 'RELOAD'],
    ['name' => 'TICKETS', 'color' => 'warning', 'value' => 'TICKETS'],
    ['name' => 'TIMEBAN', 'color' => 'danger', 'value' => 'TIMEBAN'],
    ['name' => 'STOPSERVER', 'color' => 'danger', 'value' => 'STOPSERVER'],
    ['name' => 'MESSAGE', 'color' => 'success', 'value' => 'MESSAGE'],
    ['name' => 'KILL', 'color' => 'danger', 'value' => 'KILL'],
    ['name' => 'RESIGNALL', 'color' => 'danger', 'value' => 'RESIGNALL'],
];

$config['full_width'] = false;
$config['modal_height'] = '700px';

$GLOBALS['config'] = $config;
```

Keep the rest of upstream `server_commands` behavior identical; the list above matches upstream README/config intent.

- [ ] **Step 5: PHP lint config**

Run: `php -l C:/nginx/html/pr/logs/config.php`  
Expected: `No syntax errors detected`

- [ ] **Step 6: Commit (repo mirror comes in Task 4; commit live-only notes only if mirroring same turn)**

If only live html changed so far, skip git commit until Task 4 mirrors into the game repo. Optional local note is fine.

---

### Task 2: Nginx locations for `/pr/logs/` + deny cache

**Files:**
- Modify: `C:/nginx/conf/latamsquad-locations.conf` (insert before tracker block or after extras)
- Mirror: `docs/nginx-templates/latamsquad-locations.conf`

**Interfaces:**
- Consumes: files from Task 1 at `html/pr/logs/`
- Produces: public PHP app at `/pr/logs/`; HTTP 403/404 for `/pr/logs/public/logs/`

- [ ] **Step 1: Add locations (place BEFORE the generic tracker PHP regex is fine; deny must use `^~`)**

Insert into `latamsquad-locations.conf`:

```nginx
    # PR LOG Viewer (public UI; cache dir not web-readable)
    location ^~ /pr/logs/public/logs/ {
        deny all;
        return 404;
    }

    location = /pr/logs {
        return 301 /pr/logs/;
    }

    location /pr/logs/ {
        root html;
        index index.html index.php;
        try_files $uri $uri/ /pr/logs/index.html;
    }

    location ~ ^/pr/logs/(.+\.php)$ {
        root html;
        include fastcgi_params;
        fastcgi_param SCRIPT_FILENAME $document_root/pr/logs/$1;
        fastcgi_param HTTPS $https if_not_empty;
        fastcgi_pass 127.0.0.1:9000;
    }
```

Do **not** add `auth_request` here. Do **not** modify `/pr/admins/logs/sv1/`.

- [ ] **Step 2: Test and reload Nginx**

```powershell
C:/nginx/nginx.exe -t
# Expected: syntax is ok
C:/nginx/nginx.exe -s reload
```

- [ ] **Step 3: Smoke URL routing (no auth)**

```powershell
curl.exe -skI "https://127.0.0.1/pr/logs/" -H "Host: latamsquad.dev"
# Expect: 200 (or 302 to public/index.php then 200 on follow)
curl.exe -skI "https://127.0.0.1/pr/logs/public/index.php" -H "Host: latamsquad.dev"
# Expect: 200
curl.exe -skI "https://127.0.0.1/pr/logs/public/logs/" -H "Host: latamsquad.dev"
# Expect: 403 or 404
```

- [ ] **Step 4: Mirror conf into repo**

Copy updated `latamsquad-locations.conf` to `docs/nginx-templates/latamsquad-locations.conf`.

---

### Task 3: Hub link on `/pr.php`

**Files:**
- Modify: `C:/nginx/html/pr.php` (`.pr-links` list)
- Mirror: `docs/nginx-templates/pr.php`

**Interfaces:**
- Consumes: working `/pr/logs/` from Task 2
- Produces: discoverable hub entry

- [ ] **Step 1: Add list item**

In the `<ul class="pr-links">` block, add:

```html
      <li><a href="/pr/logs/">Visor de logs</a></li>
```

Keep ASCII (`Visor de logs`). Suggested order: after Extras or before Extras — either is fine; prefer after tracker/demos, before or after Extras consistently in live + mirror.

- [ ] **Step 2: Verify hub HTML**

```powershell
curl.exe -sk "https://127.0.0.1/pr.php" -H "Host: latamsquad.dev" | findstr /C:"/pr/logs/"
# Expect: href="/pr/logs/"
```

- [ ] **Step 3: Mirror `pr.php` to `docs/nginx-templates/pr.php`**

---

### Task 4: Repo mirror of vendor + end-to-end smoke

**Files:**
- Create: `docs/nginx-templates/pr/logs/**` (mirror of live vendor + LATAM config + VENDOR.md; may omit bulky identical upstream blobs if policy prefers — **default: full mirror of tree used in production**, exclude `public/logs/*` cache contents except empty `index.html`)
- Ensure `.gitignore` does not need to ignore cache: add `docs/nginx-templates/pr/logs/public/logs/*` keep `!docs/nginx-templates/pr/logs/public/logs/index.html` if committing cache empties; live cache stays on server only.

**Interfaces:**
- Consumes: Tasks 1-3 live state
- Produces: reproducible mirror + smoke evidence

- [ ] **Step 1: Sync vendor mirror**

```powershell
$src = "C:/nginx/html/pr/logs"
$dst = "C:/prbf2_1/mods/pr/python/game/docs/nginx-templates/pr/logs"
New-Item -ItemType Directory -Force -Path (Split-Path $dst) | Out-Null
if (Test-Path $dst) { Remove-Item -Recurse -Force $dst }
robocopy $src $dst /E /XD logs
# Recreate empty logs placeholder
New-Item -ItemType Directory -Force -Path "$dst/public/logs" | Out-Null
if (Test-Path "$src/public/logs/index.html") {
  Copy-Item "$src/public/logs/index.html" "$dst/public/logs/index.html"
}
```

(`/XD logs` skips nested `public/logs` content during robocopy from `pr/logs` — if robocopy excludes wrong `logs`, copy manually excluding only `public/logs/*.txt` cache files.)

- [ ] **Step 2: Refresh cache via download.php (SV1) then query API**

```powershell
curl.exe -sk "https://127.0.0.1/pr/logs/public/download.php?server_id=1" -H "Host: latamsquad.dev"
# Expect JSON with success true (or clear error if source missing)
curl.exe -sk "https://127.0.0.1/pr/logs/public/get_timestamp.php?server_id=1" -H "Host: latamsquad.dev"
curl.exe -sk "https://127.0.0.1/pr/logs/public/get_log.php?server_id=1,&command=ALL" -H "Host: latamsquad.dev" -o "$env:TEMP/prlog_sv1.json"
# Spot SV2-SV4 download + timestamp similarly
```

- [ ] **Step 3: Prove cache is not HTTP-readable after refresh**

```powershell
# After a successful download, latam_sv1.txt should exist on disk:
Test-Path "C:/nginx/html/pr/logs/public/logs/latam_sv1.txt"
curl.exe -skI "https://127.0.0.1/pr/logs/public/logs/latam_sv1.txt" -H "Host: latamsquad.dev"
# Expect: 403 or 404 (NOT 200)
```

- [ ] **Step 4: Verify hide_ips on player API (if cdhash data exists)**

```powershell
curl.exe -sk "https://127.0.0.1/pr/logs/public/download.php?server_id=1" -H "Host: latamsquad.dev"
curl.exe -sk "https://127.0.0.1/pr/logs/public/get_player.php?server_id=1,&search=&group_by=nick&hide=" -H "Host: latamsquad.dev" -o "$env:TEMP/prlog_players.json"
# Inspect: IP fields should look like a.b.0.0 / masked per upstream, not full client IPs
```

If upstream leaves full IPs inside admin log `content`/`mess` strings, document as known limitation in smoke notes; only patch if trivial (YAGNI unless smoke shows clear unmasked IP columns in player view with `hide_ips` true — then fix get_player path).

- [ ] **Step 5: Session endpoint must not bounce public users**

```powershell
curl.exe -sk "https://127.0.0.1/pr/logs/public/get_session.php" -H "Host: latamsquad.dev"
# Expect JSON status true when require_login is false
```

- [ ] **Step 6: Staff autoindex still gated**

```powershell
curl.exe -skI "https://127.0.0.1/pr/admins/logs/sv1/" -H "Host: latamsquad.dev"
# Expect: 302 to Discord login (or 401 handled by error_page), not a public 200 listing
```

- [ ] **Step 7: Commit mirrors + spec already present**

```bash
git add docs/nginx-templates/pr/logs docs/nginx-templates/pr.php docs/nginx-templates/latamsquad-locations.conf docs/superpowers/specs/2026-07-25-latamfiles-pr-log-viewer-design.md docs/superpowers/plans/2026-07-25-latamfiles-pr-log-viewer.md
git commit -m "$(cat <<'EOF'
Add public PR LOG Viewer at /pr/logs for LATAMFILES.

Vendor gerbesf/PR-LOG-Viewer with local SV1-SV4 paths, hide IPs, deny cache HTTP, and hub link.
EOF
)"
```

(On Windows PowerShell without HEREDOC, use an equivalent `git commit -m` multi-line message.)

---

## Spec coverage checklist

| Spec requirement | Task |
|------------------|------|
| Vendor at `/pr/logs/` | 1, 2 |
| Public, no Discord/login | 1 (`require_login`), 2 (no auth_request) |
| `hide_ips` | 1, 4 smoke |
| SV1-SV4 local `prbf2_N` | 1 |
| Deny raw cache HTTP | 2, 4 |
| `download.php` JSON refresh allowed | 4 (keep endpoint) |
| Hub link Visor de logs | 3 |
| Staff autoindex unchanged | 2 (no edit), 4 smoke |
| Repo mirror + VENDOR pin | 1, 4 |
| Smoke criteria | 2, 3, 4 |

## Placeholder / consistency self-review

- No TBD left for paths: discovery Step 2 freezes concrete whitelist/banlist before config write.
- `download.php` kept (UI hard-depends); cache HTTP denied — matches locked design.
- Hub label fixed to `Visor de logs`.
- Upstream pin recorded: `41ed8c1184c5877088d6496623607699aa873e32`.
