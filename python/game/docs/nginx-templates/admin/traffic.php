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
$lastBackup = '';

if ($_SERVER['REQUEST_METHOD'] === 'GET') {
    $lastBackup = isset($_SESSION['traffic_last_backup']) && is_string($_SESSION['traffic_last_backup'])
        ? $_SESSION['traffic_last_backup']
        : '';
    unset($_SESSION['traffic_last_backup']);
}

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
                if (!empty($result['backup']) && is_string($result['backup'])) {
                    $_SESSION['traffic_last_backup'] = $result['backup'];
                }
            }
        }
    }
}

admin_render_start('traffic', 'Trafico | Admin LATAMFILES', 'Trafico');

if ($flash !== '') {
    $flashClass = $flashErr
        ? 'latam-admin__flash latam-admin__flash--err'
        : 'latam-admin__flash latam-admin__flash--ok';
    echo '<p class="' . admin_h($flashClass) . '">' . admin_h($flash) . '</p>';
}

if ($lastBackup !== '') {
    echo '<p class="latam-admin__meta">Ultimo backup: ' . admin_h($lastBackup) . '</p>';
}

$csrf = admin_csrf_token();
?>
<form class="latam-admin-form" method="post" action="/admin/traffic.php">
  <input type="hidden" name="csrf" value="<?= admin_h($csrf) ?>">

  <label class="latam-admin-form__row latam-admin-form__row--check">
    <input type="checkbox" name="enabled" value="1"<?= $settings['enabled'] ? ' checked' : '' ?>>
    <span>Limites activos</span>
  </label>

  <label class="latam-admin-form__row">
    <span class="latam-admin-form__label">Conexiones demos por IP</span>
    <input class="latam-admin-form__input" type="number" name="demo_conn_per_ip" min="1" max="10" step="1"
      value="<?= admin_h((string) $settings['demo_conn_per_ip']) ?>" required>
  </label>

  <label class="latam-admin-form__row">
    <span class="latam-admin-form__label">Velocidad max MB/s</span>
    <input class="latam-admin-form__input" type="number" name="demo_rate_mbs" min="1" max="50" step="0.1"
      value="<?= admin_h((string) $settings['demo_rate_mbs']) ?>" required>
  </label>

  <label class="latam-admin-form__row">
    <span class="latam-admin-form__label">Peticiones listado por minuto</span>
    <input class="latam-admin-form__input" type="number" name="autoindex_req_per_min" min="10" max="300" step="1"
      value="<?= admin_h((string) $settings['autoindex_req_per_min']) ?>" required>
  </label>

  <?php if ($showConfirm): ?>
  <section class="latam-admin-form__confirm" aria-label="Confirmar cambios">
    <p class="latam-admin-form__confirm-text">Aplicar y recargar Nginx?</p>
    <input type="hidden" name="confirm" value="1">
    <div class="latam-admin__actions">
      <button type="submit" class="latam-admin__btn latam-admin__btn--primary">Si, aplicar y recargar</button>
      <a class="latam-admin__btn" href="/admin/traffic.php">Cancelar</a>
    </div>
  </section>
  <?php else: ?>
  <div class="latam-admin__actions">
    <button type="submit" class="latam-admin__btn latam-admin__btn--primary">Guardar</button>
  </div>
  <?php endif; ?>
</form>
<?php
admin_render_end();
