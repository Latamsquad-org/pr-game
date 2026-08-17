# LATAMFILES Admin Traffic Limits Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Replace the Tráfico placeholder with a staff form that validates settings, generates Nginx zone/limit includes, backups, runs `nginx -t`, and reloads on success.

**Architecture:** JSON settings under `admin/data/` drive two generated conf files (`latam-traffic-zones.conf` in `http`, `latam-traffic-limits.conf` in demos locations). PHP libs handle validate/generate/apply; `traffic.php` owns UI + CSRF + confirm. Demo locations `include` the limits file; `nginx.conf` `include`s the zones file.

**Tech Stack:** PHP 8.x, existing `/admin/` bootstrap+layout, Nginx 1.26 on Windows (`C:/nginx/nginx.exe`), JSON file storage.

## Global Constraints

- ASCII only in PHP comments/strings (no fancy dashes/quotes).
- Staff-only via `_bootstrap.php`; CSRF on every POST.
- Defaults: enabled=true, demo_conn_per_ip=2, demo_rate_mbs=8, autoindex_req_per_min=60.
- Ranges: conn 1-10, rate 1-50 MB/s, autoindex 10-300 req/min; burst fixed at 20.
- Zones always written; location limits directives only when enabled=true (else comments-only).
- Apply: backup includes -> write -> `nginx -t` -> restore on fail / reload on OK.
- Limits only on `/pr/demos2d*` and `/pr/demos3d*` locations; not extras/admin/auth/tracker.
- Deny HTTP access to `/admin/data/`.
- Live root `C:/nginx/html/`, conf `C:/nginx/conf/`; mirror under `docs/nginx-templates/`.
- Branch: continue on `feature/latamfiles-admin-shell` (or current feature branch).

---

## File map

| Path | Responsibility |
|------|----------------|
| `C:/nginx/html/admin/lib/traffic_settings.php` | defaults, load, validate, save JSON, generate conf text |
| `C:/nginx/html/admin/lib/traffic_nginx.php` | backup, atomic write includes, nginx -t / reload |
| `C:/nginx/html/admin/traffic.php` | UI form, CSRF, confirm, flash |
| `C:/nginx/html/admin/data/traffic-settings.json` | persisted settings (created on first save or seed) |
| `C:/nginx/html/admin/data/.htaccess` or nginx deny | block web access (prefer nginx location) |
| `C:/nginx/conf/latam-traffic-zones.conf` | generated zones |
| `C:/nginx/conf/latam-traffic-limits.conf` | generated location limits |
| `C:/nginx/conf/nginx.conf` | `include latam-traffic-zones.conf;` inside `http` |
| `C:/nginx/conf/latamsquad-locations.conf` | `include latam-traffic-limits.conf;` in each demos location + deny `/admin/data/` |
| `docs/nginx-templates/**` | repo mirror |
| `tools/traffic_settings_cli_test.php` | CLI asserts for validate/generate (no PHPUnit) |

---

### Task 1: Settings library + CLI tests

**Files:**
- Create: `C:/nginx/html/admin/lib/traffic_settings.php`
- Create: `C:/prbf2_1/mods/pr/python/game/tools/traffic_settings_cli_test.php`
- Mirror lib: `docs/nginx-templates/admin/lib/traffic_settings.php`

**Interfaces:**
- Produces:
  - `traffic_settings_defaults(): array`
  - `traffic_settings_path(): string` -> `C:/nginx/html/admin/data/traffic-settings.json`
  - `traffic_settings_load(): array` (defaults merged)
  - `traffic_settings_validate(array $in): array` -> `['ok'=>bool,'errors'=>string[],'settings'=>array]`
  - `traffic_settings_save(array $settings): void` (atomic)
  - `traffic_generate_zones_conf(array $settings): string`
  - `traffic_generate_limits_conf(array $settings): string`

- [ ] **Step 1: Write CLI test file first (RED)**

Create `tools/traffic_settings_cli_test.php` that requires the lib and exits 1 on failure:

```php
<?php
declare(strict_types=1);
require_once 'C:/nginx/html/admin/lib/traffic_settings.php';

function assert_true($cond, $msg) {
    if (!$cond) { fwrite(STDERR, "FAIL: $msg\n"); exit(1); }
    echo "OK: $msg\n";
}

$bad = traffic_settings_validate(['enabled' => true, 'demo_conn_per_ip' => 0, 'demo_rate_mbs' => 8, 'autoindex_req_per_min' => 60]);
assert_true($bad['ok'] === false, 'conn 0 rejected');

$ok = traffic_settings_validate(['enabled' => '1', 'demo_conn_per_ip' => '2', 'demo_rate_mbs' => '8.5', 'autoindex_req_per_min' => '60']);
assert_true($ok['ok'] === true, 'valid settings accepted');
assert_true($ok['settings']['demo_rate_mbs'] === 8.5, 'rate float kept');

$zones = traffic_generate_zones_conf($ok['settings']);
assert_true(strpos($zones, 'limit_conn_zone') !== false, 'zones has conn zone');
assert_true(strpos($zones, 'rate=60r/m') !== false, 'zones has req rate');

$limOn = traffic_generate_limits_conf($ok['settings']);
assert_true(strpos($limOn, 'limit_conn') !== false, 'limits on has conn');
assert_true(strpos($limOn, 'limit_rate') !== false, 'limits on has rate');

$off = $ok['settings'];
$off['enabled'] = false;
$limOff = traffic_generate_limits_conf($off);
assert_true(strpos($limOff, 'limit_conn') === false, 'limits off has no limit_conn');

echo "ALL PASS\n";
```

- [ ] **Step 2: Run test — expect FAIL (missing lib)**

```powershell
php C:\prbf2_1\mods\pr\python\game\tools\traffic_settings_cli_test.php
```

Expected: fatal error / failed opening required file.

- [ ] **Step 3: Implement `traffic_settings.php`**

```php
<?php
declare(strict_types=1);

function traffic_settings_defaults(): array
{
    return [
        'enabled' => true,
        'demo_conn_per_ip' => 2,
        'demo_rate_mbs' => 8.0,
        'autoindex_req_per_min' => 60,
    ];
}

function traffic_settings_path(): string
{
    return dirname(__DIR__) . '/data/traffic-settings.json';
}

function traffic_settings_load(): array
{
    $defaults = traffic_settings_defaults();
    $path = traffic_settings_path();
    if (!is_file($path)) {
        return $defaults;
    }
    $raw = file_get_contents($path);
    $data = json_decode(is_string($raw) ? $raw : '', true);
    if (!is_array($data)) {
        return $defaults;
    }
    return traffic_settings_validate(array_merge($defaults, $data))['settings']
        ?? $defaults;
}

function traffic_settings_validate(array $in): array
{
    $errors = [];
    $enabled = !empty($in['enabled']) && $in['enabled'] !== '0' && $in['enabled'] !== false;

    $conn = filter_var($in['demo_conn_per_ip'] ?? null, FILTER_VALIDATE_INT);
    if ($conn === false || $conn < 1 || $conn > 10) {
        $errors[] = 'demo_conn_per_ip debe ser entero 1-10';
        $conn = 2;
    }

    $rate = filter_var($in['demo_rate_mbs'] ?? null, FILTER_VALIDATE_FLOAT);
    if ($rate === false || $rate < 1 || $rate > 50) {
        $errors[] = 'demo_rate_mbs debe ser numero 1-50';
        $rate = 8.0;
    }

    $rpm = filter_var($in['autoindex_req_per_min'] ?? null, FILTER_VALIDATE_INT);
    if ($rpm === false || $rpm < 10 || $rpm > 300) {
        $errors[] = 'autoindex_req_per_min debe ser entero 10-300';
        $rpm = 60;
    }

    $settings = [
        'enabled' => (bool) $enabled,
        'demo_conn_per_ip' => (int) $conn,
        'demo_rate_mbs' => round((float) $rate, 1),
        'autoindex_req_per_min' => (int) $rpm,
    ];

    return [
        'ok' => $errors === [],
        'errors' => $errors,
        'settings' => $settings,
    ];
}

function traffic_settings_save(array $settings): void
{
    $dir = dirname(traffic_settings_path());
    if (!is_dir($dir) && !mkdir($dir, 0755, true) && !is_dir($dir)) {
        throw new RuntimeException('No se pudo crear admin/data');
    }
    $json = json_encode($settings, JSON_PRETTY_PRINT | JSON_UNESCAPED_SLASHES);
    if ($json === false) {
        throw new RuntimeException('JSON encode failed');
    }
    $path = traffic_settings_path();
    $tmp = $path . '.tmp';
    if (file_put_contents($tmp, $json . "\n") === false) {
        throw new RuntimeException('No se pudo escribir settings tmp');
    }
    if (!rename($tmp, $path)) {
        @unlink($tmp);
        throw new RuntimeException('No se pudo renombrar settings');
    }
}

function traffic_generate_zones_conf(array $settings): string
{
    $rpm = (int) $settings['autoindex_req_per_min'];
    return "# Generated by LATAMFILES admin - do not edit by hand\n"
        . "limit_conn_zone \$binary_remote_addr zone=latam_demo_conn:10m;\n"
        . "limit_req_zone \$binary_remote_addr zone=latam_autoindex:10m rate={$rpm}r/m;\n";
}

function traffic_generate_limits_conf(array $settings): string
{
    $out = "# Generated by LATAMFILES admin - do not edit by hand\n";
    if (empty($settings['enabled'])) {
        $out .= "# limits disabled\n";
        return $out;
    }
    $conn = (int) $settings['demo_conn_per_ip'];
    $bytes = (int) round(((float) $settings['demo_rate_mbs']) * 1024 * 1024);
    $out .= "limit_conn latam_demo_conn {$conn};\n";
    $out .= "limit_rate {$bytes};\n";
    $out .= "limit_req zone=latam_autoindex burst=20 nodelay;\n";
    return $out;
}
```

Note: In the real file use `"limit_conn_zone $binary_remote_addr ..."` with a real `$` for nginx — in PHP double-quoted strings escape as `"limit_conn_zone \$binary_remote_addr zone=latam_demo_conn:10m;\n"` OR use single-quoted PHP strings: `'limit_conn_zone $binary_remote_addr zone=latam_demo_conn:10m;' . "\n"`.

- [ ] **Step 4: Run CLI test — expect PASS**

```powershell
php C:\prbf2_1\mods\pr\python\game\tools\traffic_settings_cli_test.php
```

Expected: `ALL PASS`

- [ ] **Step 5: Mirror + commit**

```powershell
New-Item -ItemType Directory -Force -Path C:\prbf2_1\mods\pr\python\game\docs\nginx-templates\admin\lib | Out-Null
Copy-Item -Force C:\nginx\html\admin\lib\traffic_settings.php C:\prbf2_1\mods\pr\python\game\docs\nginx-templates\admin\lib\traffic_settings.php
cd C:\prbf2_1\mods\pr\python\game
git add docs/nginx-templates/admin/lib/traffic_settings.php tools/traffic_settings_cli_test.php
git commit -m "Agrega libreria de settings de trafico y tests CLI."
```

---

### Task 2: Nginx apply library

**Files:**
- Create: `C:/nginx/html/admin/lib/traffic_nginx.php`
- Mirror: `docs/nginx-templates/admin/lib/traffic_nginx.php`

**Interfaces:**
- Consumes: `traffic_generate_zones_conf`, `traffic_generate_limits_conf`, `traffic_settings_save`
- Produces: `traffic_nginx_paths(): array`, `traffic_nginx_apply(array $settings): array` -> `['ok'=>bool,'message'=>string,'backup'=>?string,'nginx_log'=>string]`

- [ ] **Step 1: Implement apply helper**

```php
<?php
declare(strict_types=1);

require_once __DIR__ . '/traffic_settings.php';

function traffic_nginx_paths(): array
{
    return [
        'nginx_dir' => 'C:/nginx',
        'nginx_exe' => 'C:/nginx/nginx.exe',
        'zones' => 'C:/nginx/conf/latam-traffic-zones.conf',
        'limits' => 'C:/nginx/conf/latam-traffic-limits.conf',
        'backup_root' => 'C:/nginx/conf/backup',
    ];
}

function traffic_nginx_atomic_write(string $path, string $contents): void
{
    $tmp = $path . '.tmp';
    if (file_put_contents($tmp, $contents) === false) {
        throw new RuntimeException('write failed: ' . $path);
    }
    if (!rename($tmp, $path)) {
        @unlink($tmp);
        throw new RuntimeException('rename failed: ' . $path);
    }
}

function traffic_nginx_run(string $arg): array
{
    $p = traffic_nginx_paths();
    $cmd = escapeshellarg($p['nginx_exe']) . ' ' . $arg;
    $descriptors = [1 => ['pipe', 'w'], 2 => ['pipe', 'w']];
    $proc = proc_open($cmd, $descriptors, $pipes, $p['nginx_dir']);
    if (!is_resource($proc)) {
        return ['code' => 1, 'out' => '', 'err' => 'proc_open failed'];
    }
    $out = stream_get_contents($pipes[1]);
    $err = stream_get_contents($pipes[2]);
    fclose($pipes[1]);
    fclose($pipes[2]);
    $code = proc_close($proc);
    return ['code' => $code, 'out' => (string) $out, 'err' => (string) $err];
}

/**
 * Backup, write confs, nginx -t, restore or reload.
 */
function traffic_nginx_apply(array $settings): array
{
    $p = traffic_nginx_paths();
    $stamp = gmdate('Ymd-His');
    $backupDir = $p['backup_root'] . '/traffic-' . $stamp;
    if (!is_dir($p['backup_root']) && !mkdir($p['backup_root'], 0755, true) && !is_dir($p['backup_root'])) {
        return ['ok' => false, 'message' => 'No se pudo crear carpeta backup', 'backup' => null, 'nginx_log' => ''];
    }
    if (!mkdir($backupDir) && !is_dir($backupDir)) {
        return ['ok' => false, 'message' => 'No se pudo crear backup dir', 'backup' => null, 'nginx_log' => ''];
    }

    foreach (['zones', 'limits'] as $key) {
        $src = $p[$key];
        if (is_file($src)) {
            copy($src, $backupDir . '/' . basename($src));
        }
    }

    try {
        traffic_settings_save($settings);
        traffic_nginx_atomic_write($p['zones'], traffic_generate_zones_conf($settings));
        traffic_nginx_atomic_write($p['limits'], traffic_generate_limits_conf($settings));
    } catch (Throwable $e) {
        return ['ok' => false, 'message' => $e->getMessage(), 'backup' => $backupDir, 'nginx_log' => ''];
    }

    $test = traffic_nginx_run('-t');
    $log = trim($test['err'] . "\n" . $test['out']);
    if ($test['code'] !== 0) {
        foreach (['zones', 'limits'] as $key) {
            $bak = $backupDir . '/' . basename($p[$key]);
            if (is_file($bak)) {
                copy($bak, $p[$key]);
            }
        }
        return [
            'ok' => false,
            'message' => 'nginx -t fallo; se restauro el backup',
            'backup' => $backupDir,
            'nginx_log' => substr($log, 0, 2000),
        ];
    }

    $reload = traffic_nginx_run('-s reload');
    $log2 = trim($log . "\n" . $reload['err'] . "\n" . $reload['out']);
    if ($reload['code'] !== 0) {
        return [
            'ok' => false,
            'message' => 'nginx -t OK pero reload fallo',
            'backup' => $backupDir,
            'nginx_log' => substr($log2, 0, 2000),
        ];
    }

    return [
        'ok' => true,
        'message' => 'Limites aplicados y Nginx recargado',
        'backup' => $backupDir,
        'nginx_log' => substr($log2, 0, 2000),
    ];
}
```

- [ ] **Step 2: Smoke generate+write without reload (optional dry)**

```powershell
php -r "require 'C:/nginx/html/admin/lib/traffic_nginx.php'; echo traffic_generate_limits_conf(traffic_settings_defaults());"
```

Expected: prints limit_* lines.

- [ ] **Step 3: Mirror + commit**

```powershell
Copy-Item -Force C:\nginx\html\admin\lib\traffic_nginx.php C:\prbf2_1\mods\pr\python\game\docs\nginx-templates\admin\lib\traffic_nginx.php
cd C:\prbf2_1\mods\pr\python\game
git add docs/nginx-templates/admin/lib/traffic_nginx.php
git commit -m "Agrega aplicacion segura de limites Nginx desde el panel."
```

---

### Task 3: Wire Nginx includes + deny data + seed confs

**Files:**
- Modify: `C:/nginx/conf/nginx.conf`
- Modify: `C:/nginx/conf/latamsquad-locations.conf`
- Create initial: `C:/nginx/conf/latam-traffic-zones.conf`, `latam-traffic-limits.conf` (via PHP defaults apply or hand seed)
- Mirror conf templates

- [ ] **Step 1: Add zones include inside `http { }` in `nginx.conf`**

After the `types { ... }` block (before `include latamsquad.conf`):

```nginx
    include latam-traffic-zones.conf;
```

- [ ] **Step 2: Seed zone/limit files with defaults (enabled)**

Run once:

```powershell
php -r "require 'C:/nginx/html/admin/lib/traffic_settings.php'; file_put_contents('C:/nginx/conf/latam-traffic-zones.conf', traffic_generate_zones_conf(traffic_settings_defaults())); file_put_contents('C:/nginx/conf/latam-traffic-limits.conf', traffic_generate_limits_conf(traffic_settings_defaults()));"
```

- [ ] **Step 3: Add `include latam-traffic-limits.conf;` to each demos2d/demos3d location**

Inside every `location /pr/demos2d/...` and `/pr/demos3d/...` block, after `autoindex on;`:

```nginx
        include latam-traffic-limits.conf;
```

(8 locations: demos2d root+sv2-4, demos3d sv1-4)

- [ ] **Step 4: Deny `/admin/data/`**

Add near admin locations:

```nginx
    location ^~ /admin/data/ {
        deny all;
        return 404;
    }
```

- [ ] **Step 5: nginx -t && reload**

```powershell
cd C:\nginx; .\nginx.exe -t; if ($LASTEXITCODE -eq 0) { .\nginx.exe -s reload }
```

Expected: test successful.

- [ ] **Step 6: Mirror + commit**

Copy `nginx.conf`, `latamsquad-locations.conf`, both generated confs (as samples) into `docs/nginx-templates/`, commit:

```
git commit -m "Conecta includes de limites de trafico en Nginx."
```

---

### Task 4: CSRF helpers + traffic.php UI

**Files:**
- Modify: `C:/nginx/html/admin/_bootstrap.php` (add CSRF helpers) OR create `admin/lib/csrf.php` — prefer small helpers in `_bootstrap.php`:
  - `admin_csrf_token(): string`
  - `admin_csrf_validate(?string $token): bool`
- Replace: `C:/nginx/html/admin/traffic.php`
- Append minimal form CSS to `site.css` if needed (reuse `.latam-admin__*` + new `.latam-admin-form`)
- Mirror

- [ ] **Step 1: Add CSRF to `_bootstrap.php`**

```php
function admin_csrf_token(): string
{
    if (empty($_SESSION['admin_csrf']) || !is_string($_SESSION['admin_csrf'])) {
        $_SESSION['admin_csrf'] = bin2hex(random_bytes(16));
    }
    return $_SESSION['admin_csrf'];
}

function admin_csrf_validate(?string $token): bool
{
    $sess = $_SESSION['admin_csrf'] ?? '';
    return is_string($token) && is_string($sess) && $sess !== '' && hash_equals($sess, $token);
}
```

- [ ] **Step 2: Implement `traffic.php` form**

Behavior:
- GET: show current `traffic_settings_load()`, last backup path from session flash if any.
- POST without `confirm=1`: re-display form with posted values + confirm panel ("Aplicar y recargar Nginx?").
- POST with `confirm=1` + valid CSRF: validate -> `traffic_nginx_apply` -> flash result.
- Invalid CSRF: 403 message.

Use ASCII labels: "Limites activos", "Conexiones demos por IP", "Velocidad max MB/s", "Peticiones listado por minuto".

Sketch (structure):

```php
<?php
declare(strict_types=1);
require_once __DIR__ . '/_bootstrap.php';
require_once __DIR__ . '/_layout.php';
require_once __DIR__ . '/lib/traffic_settings.php';
require_once __DIR__ . '/lib/traffic_nginx.php';

$flash = '';
$flashErr = false;
$settings = traffic_settings_load();
$showConfirm = false;

if ($_SERVER['REQUEST_METHOD'] === 'POST') {
    if (!admin_csrf_validate($_POST['csrf'] ?? null)) {
        http_response_code(403);
        $flash = 'CSRF invalido';
        $flashErr = true;
    } else {
        $parsed = traffic_settings_validate($_POST);
        $settings = $parsed['settings'];
        if (!$parsed['ok']) {
            $flash = implode('; ', $parsed['errors']);
            $flashErr = true;
        } elseif (empty($_POST['confirm'])) {
            $showConfirm = true;
        } else {
            $result = traffic_nginx_apply($settings);
            $flash = $result['message'];
            $flashErr = !$result['ok'];
            if (!empty($result['nginx_log']) && $flashErr) {
                $flash .= ' | ' . $result['nginx_log'];
            }
            if ($result['ok']) {
                $settings = traffic_settings_load();
            }
        }
    }
}

admin_render_start('traffic', 'Trafico | Admin LATAMFILES', 'Trafico');
// echo flash, form with hidden csrf, checkbox enabled, number inputs,
// if $showConfirm: hidden fields + confirm=1 submit "Si, aplicar y recargar"
// else: submit "Guardar" (goes to confirm step)
admin_render_end();
```

Implement full HTML in the task (no placeholder Proximamente left).

- [ ] **Step 3: php -l traffic.php + bootstrap**

- [ ] **Step 4: Mirror + commit**

```
git commit -m "Activa el formulario de Trafico con CSRF y confirmacion."
```

---

### Task 5: End-to-end verification

**Files:** none (verification)

- [ ] **Step 1: CLI tests still pass**

```powershell
php C:\prbf2_1\mods\pr\python\game\tools\traffic_settings_cli_test.php
```

- [ ] **Step 2: Logged-out POST blocked**

`/admin/traffic.php` without session -> 302 Discord.

- [ ] **Step 3: Staff UI (manual)**
  - Open Tráfico, see defaults
  - Save without confirm -> confirm UI
  - Confirm -> success flash; `latam-traffic-limits.conf` contains limit_*; backup folder created
  - Toggle OFF, confirm -> limits file comments-only; nginx -t/reload OK
  - Toggle ON again

- [ ] **Step 4: Deny data**

```powershell
curl.exe -skI "https://127.0.0.1/admin/data/traffic-settings.json" -H "Host: latamsquad.dev"
```

Expected: 403 or 404.

- [ ] **Step 5: Write short report** `.superpowers/sdd/traffic-verify.md` with results; commit if any fixups needed.

---

## Spec coverage (self-review)

| Spec item | Task |
|-----------|------|
| Settings JSON + validation ranges | 1 |
| Generate zones/limits text | 1 |
| Backup + nginx -t + restore/reload | 2 |
| Wire http + demos locations | 3 |
| Deny /admin/data | 3 |
| UI + confirm + CSRF | 4 |
| Success criteria spot-check | 5 |

No TBD placeholders. Function names consistent across tasks.
