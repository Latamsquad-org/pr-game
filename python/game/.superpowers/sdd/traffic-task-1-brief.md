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

