<?php
declare(strict_types=1);
require_once __DIR__ . '/_bootstrap.php';
require_once __DIR__ . '/_layout.php';
require_once __DIR__ . '/lib/demos_settings.php';

$flash = '';
$flashErr = false;
$settings = demos_settings_load();

if ($_SERVER['REQUEST_METHOD'] === 'POST') {
    if (!admin_csrf_validate($_POST['csrf'] ?? null)) {
        http_response_code(403);
        $flash = 'CSRF invalido';
        $flashErr = true;
    } else {
        $parsed = demos_settings_validate($_POST);
        $settings = $parsed['settings'];
        if (!$parsed['ok']) {
            $flash = implode('; ', $parsed['errors']);
            $flashErr = true;
        } else {
            try {
                demos_settings_save($settings);
                $settings = demos_settings_load();
                $flash = 'Settings de demos guardados';
            } catch (Throwable $e) {
                $flash = 'No se pudo guardar: ' . $e->getMessage();
                $flashErr = true;
            }
        }
    }
}

admin_render_start('demos', 'Demos | Admin LATAMFILES', 'Demos');

if ($flash !== '') {
    $flashClass = $flashErr
        ? 'latam-admin__flash latam-admin__flash--err'
        : 'latam-admin__flash latam-admin__flash--ok';
    echo '<p class="' . admin_h($flashClass) . '">' . admin_h($flash) . '</p>';
}

$csrf = admin_csrf_token();
$visible = $settings['servers_visible'];
?>
<p class="latam-admin__lead">Opciones del listado PRdemos / BF2demos. Se aplican al recargar el listado (sin recargar Nginx).</p>
<form class="latam-admin-form" method="post" action="/admin/demos.php">
  <input type="hidden" name="csrf" value="<?= admin_h($csrf) ?>">

  <fieldset class="latam-admin-form__row">
    <legend class="latam-admin-form__label">Servidores visibles</legend>
    <?php for ($i = 1; $i <= 4; $i++): ?>
    <label class="latam-admin-form__row--check" style="display:inline-flex;margin-right:1rem;">
      <input type="checkbox" name="servers_visible[]" value="<?= $i ?>"<?= in_array($i, $visible, true) ? ' checked' : '' ?>>
      <span><?= $i ?></span>
    </label>
    <?php endfor; ?>
  </fieldset>

  <label class="latam-admin-form__row">
    <span class="latam-admin-form__label">Orden del listado</span>
    <select class="latam-admin-form__input" name="sort">
      <option value="newest"<?= $settings['sort'] === 'newest' ? ' selected' : '' ?>>Mas nuevos primero</option>
      <option value="name"<?= $settings['sort'] === 'name' ? ' selected' : '' ?>>Nombre A-Z</option>
    </select>
  </label>

  <label class="latam-admin-form__row">
    <span class="latam-admin-form__label">Texto pestana 2D</span>
    <input class="latam-admin-form__input" type="text" name="tab_2d" maxlength="40" required
      value="<?= admin_h($settings['tab_2d']) ?>">
  </label>

  <label class="latam-admin-form__row">
    <span class="latam-admin-form__label">Texto pestana 3D</span>
    <input class="latam-admin-form__input" type="text" name="tab_3d" maxlength="40" required
      value="<?= admin_h($settings['tab_3d']) ?>">
  </label>

  <fieldset class="latam-admin-form__row">
    <legend class="latam-admin-form__label">Nombres de servidores (hint del listado)</legend>
    <?php
    $names = $settings['server_names'] ?? [];
    for ($i = 1; $i <= 4; $i++):
        $nameVal = isset($names[$i]) ? (string) $names[$i] : '';
    ?>
    <label class="latam-admin-form__row" style="margin-top:.5rem;">
      <span class="latam-admin-form__label">Servidor <?= $i ?></span>
      <input class="latam-admin-form__input" type="text" name="server_names[<?= $i ?>]" maxlength="80" required
        value="<?= admin_h($nameVal) ?>">
    </label>
    <?php endfor; ?>
  </fieldset>
  <input type="hidden" name="server_label" value="<?= admin_h($settings['server_label'] ?? 'Servidor') ?>">

  <div class="latam-admin__actions">
    <button type="submit" class="latam-admin__btn latam-admin__btn--primary">Guardar</button>
  </div>
</form>
<?php
admin_render_end();
