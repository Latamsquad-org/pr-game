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

