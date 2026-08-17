<?php
declare(strict_types=1);
require_once __DIR__ . '/_bootstrap.php';
require_once __DIR__ . '/_layout.php';

$name = auth_display_name() ?? 'Staff';
$id = (string) auth_current_discord_id();

admin_render_start('home', 'Panel de administracion | LATAMFILES', 'Panel de administracion');
?>
<p class="latam-admin__lead">Aqui van a aparecer los modulos de configuracion (trafico, demos, auth) a medida que los activemos.</p>
<section class="latam-admin__card" aria-label="Sesion actual">
  <p class="latam-admin__card-label">Staff</p>
  <p class="latam-admin__card-name"><?= admin_h($name) ?></p>
  <p class="latam-admin__card-meta">Discord ID: <?= admin_h($id) ?></p>
  <div class="latam-admin__actions">
    <a class="latam-admin__btn latam-admin__btn--primary" href="/pr.php">Volver al sitio</a>
    <a class="latam-admin__btn" href="/auth/logout.php">Cerrar sesion</a>
  </div>
</section>
<?php
admin_render_end();
