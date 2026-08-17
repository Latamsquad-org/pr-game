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

Record FOUND paths. For missing optional files (`ra_adminlog_main`, `cdhash_main`), still put the expected path in config (upstream uses `@file_get_contents` / empty incremental). For `whitelist` / `banlist`, pick the FOUND path per server; if a server has no banlist/whitelist file, create an empty placeholder file next to that server's admin logs (e.g. `C:/prbf2_N/admin/logs/whitelist.txt` and empty `banlist.con`) so `download.php` does not fatally fail â€” only if no real file exists.

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

Overwrite `C:/nginx/html/pr/logs/config.php` with ASCII-only content. Adjust whitelist/banlist paths to match Step 2 FOUND results (examples below assume logs dir + `mods/pr/banlist.con` â€” replace if discovery differs):

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

