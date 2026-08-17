<?php
declare(strict_types=1);

require_once __DIR__ . '/_bootstrap.php';
require_once __DIR__ . '/_layout.php';
require_once __DIR__ . '/lib/delete_acl.php';

$me = (string) auth_current_discord_id();
if (!delete_acl_is_owner($me)) {
    http_response_code(403);
    auth_render_notice_page(
        'Solo el owner',
        'Acceso restringido',
        'Este menu de permisos de borrado solo lo puede usar el owner del sitio.',
        'Si necesitas borrar partidas, pedile permiso a Chaziz.',
        [
            ['href' => '/admin/', 'label' => 'Volver al panel', 'primary' => true],
            ['href' => '/pr/tracker/?srv=1', 'label' => 'Ir al tracker'],
        ],
        403
    );
    exit;
}

$flash = '';
$flashErr = false;
$settings = delete_acl_load();

if ($_SERVER['REQUEST_METHOD'] === 'POST') {
    if (!admin_csrf_validate($_POST['csrf'] ?? null)) {
        http_response_code(403);
        $flash = 'CSRF invalido';
        $flashErr = true;
    } else {
        $action = (string) ($_POST['action'] ?? '');
        if ($action === 'grant') {
            $res = delete_acl_grant(
                (string) ($_POST['discord_id'] ?? ''),
                (string) ($_POST['label'] ?? '')
            );
            $settings = $res['settings'];
            if ($res['ok']) {
                $flash = 'Permiso de borrado concedido';
            } else {
                $flash = $res['error'];
                $flashErr = true;
            }
        } elseif ($action === 'revoke') {
            $res = delete_acl_revoke((string) ($_POST['discord_id'] ?? ''));
            $settings = $res['settings'];
            if ($res['ok']) {
                $flash = 'Permiso de borrado revocado';
            } else {
                $flash = $res['error'];
                $flashErr = true;
            }
        } else {
            $flash = 'Accion desconocida';
            $flashErr = true;
        }
    }
}

admin_render_start('delete_acl', 'Borrado | Admin LATAMFILES', 'Permisos de borrado');

if ($flash !== '') {
    $flashClass = $flashErr
        ? 'latam-admin__flash latam-admin__flash--err'
        : 'latam-admin__flash latam-admin__flash--ok';
    echo '<p class="' . admin_h($flashClass) . '">' . admin_h($flash) . '</p>';
}

$csrf = admin_csrf_token();
?>
<p class="latam-admin__lead">
  Solo vos (owner) podes borrar partidas del tracker por defecto.
  Acá das o quitas ese poder a otros usuarios staff (por Discord ID).
</p>

<section class="latam-admin__card" aria-label="Owner">
  <p class="latam-admin__card-label">Owner (siempre puede borrar)</p>
  <p class="latam-admin__card-meta">Discord ID: <?= admin_h(delete_acl_owner_id()) ?></p>
</section>

<section class="latam-admin__card" style="margin-top:1rem;" aria-label="Staff con permiso">
  <p class="latam-admin__card-label">Staff con permiso de borrar</p>
  <?php if ($settings['can_delete'] === []): ?>
    <p class="latam-admin__card-meta">Nadie mas tiene permiso todavia.</p>
  <?php else: ?>
    <ul class="latam-admin-list" style="list-style:none;padding:0;margin:.75rem 0 0;">
      <?php foreach ($settings['can_delete'] as $row): ?>
        <li style="display:flex;align-items:center;gap:.75rem;margin-bottom:.5rem;flex-wrap:wrap;">
          <code><?= admin_h($row['id']) ?></code>
          <?php if ($row['label'] !== ''): ?>
            <span><?= admin_h($row['label']) ?></span>
          <?php endif; ?>
          <form method="post" action="/admin/delete-acl.php" style="display:inline;margin:0;"
            onsubmit="return confirm('Quitar permiso de borrado a este usuario?');">
            <input type="hidden" name="csrf" value="<?= admin_h($csrf) ?>">
            <input type="hidden" name="action" value="revoke">
            <input type="hidden" name="discord_id" value="<?= admin_h($row['id']) ?>">
            <button type="submit" class="latam-admin__btn">Quitar</button>
          </form>
        </li>
      <?php endforeach; ?>
    </ul>
  <?php endif; ?>
</section>

<form class="latam-admin-form" method="post" action="/admin/delete-acl.php" style="margin-top:1.25rem;">
  <input type="hidden" name="csrf" value="<?= admin_h($csrf) ?>">
  <input type="hidden" name="action" value="grant">
  <p class="latam-admin__card-label">Dar permiso</p>
  <label class="latam-admin-form__row">
    <span class="latam-admin-form__label">Discord ID</span>
    <input class="latam-admin-form__input" type="text" name="discord_id" required
      pattern="[0-9]{5,32}" maxlength="32" placeholder="Ej: 123456789012345678"
      autocomplete="off">
  </label>
  <label class="latam-admin-form__row">
    <span class="latam-admin-form__label">Nombre (opcional)</span>
    <input class="latam-admin-form__input" type="text" name="label" maxlength="64"
      placeholder="Ej: Admin Juan">
  </label>
  <div class="latam-admin__actions">
    <button type="submit" class="latam-admin__btn latam-admin__btn--primary">Dar permiso de borrado</button>
  </div>
</form>
<?php
admin_render_end();
