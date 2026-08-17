<?php

declare(strict_types=1);

require_once dirname(__DIR__) . '/includes/layout.php';
require_once dirname(__DIR__) . '/includes/db.php';
require_once dirname(__DIR__) . '/includes/auth_schema.php';
require_once dirname(__DIR__) . '/includes/clan_permissions.php';

$configPath = dirname(__DIR__) . '/config.php';
if (!is_file($configPath)) {
    http_response_code(500);
    echo 'Configuración no disponible.';
    exit;
}

$config = require $configPath;
if (!is_array($config) || !isset($config['db']) || !is_array($config['db'])) {
    http_response_code(500);
    echo 'Configuración de base de datos inválida.';
    exit;
}

$flashOk = '';
$flashErr = '';
$clanNames = [];
$editors = [];
$selectedClan = '';
$discordId = '';
$serverId = '';

try {
    $pdo = createDatabaseConnection($config['db']);
    ensure_multi_server_schema($pdo);
    ensure_auth_schema($pdo);

    // Staff obligatorio con revalidación de rol Discord.
    $discordId = auth_require_staff($pdo);
    $serverId = current_server_id();

    // POST: grant / revoke con CSRF.
    if (($_SERVER['REQUEST_METHOD'] ?? 'GET') === 'POST') {
        $csrf = isset($_POST['csrf']) && is_string($_POST['csrf']) ? $_POST['csrf'] : '';
        if (!auth_csrf_validate($csrf)) {
            $flashErr = 'Token de seguridad inválido. Recargá la página e intentá de nuevo.';
        } else {
            $action = isset($_POST['action']) && is_string($_POST['action']) ? $_POST['action'] : '';
            $clanPost = isset($_POST['clan']) && is_string($_POST['clan'])
                ? clan_display_name($_POST['clan'])
                : '';
            $targetId = isset($_POST['discord_id']) && is_string($_POST['discord_id'])
                ? trim($_POST['discord_id'])
                : '';

            if ($clanPost === '' || clan_is_empty($clanPost)) {
                $flashErr = 'Clan inválido.';
            } elseif ($action === 'grant') {
                if ($targetId === '' || !preg_match('/^\d{5,32}$/', $targetId)) {
                    $flashErr = 'Discord ID inválido (solo dígitos).';
                } else {
                    clan_editor_grant($pdo, $clanPost, $serverId, $targetId, $discordId);
                    $flashOk = 'Editor asignado.';
                    $selectedClan = $clanPost;
                }
            } elseif ($action === 'revoke') {
                if ($targetId === '') {
                    $flashErr = 'Discord ID inválido.';
                } else {
                    clan_editor_revoke($pdo, $clanPost, $serverId, $targetId);
                    $flashOk = 'Editor revocado.';
                    $selectedClan = $clanPost;
                }
            } else {
                $flashErr = 'Acción desconocida.';
            }
        }
    }

    // Clanes del server: DISTINCT player_clan + claves de clans_info.
    $names = [];
    $stmt = $pdo->prepare(
        'SELECT DISTINCT player_clan FROM players
         WHERE ' . server_sql_where() . '
           AND TRIM(COALESCE(player_clan, \'\')) <> \'\'
           AND TRIM(player_clan) <> \'=+=\'
         ORDER BY player_clan ASC'
    );
    server_sql_bind($stmt);
    $stmt->execute();
    while ($row = $stmt->fetch(PDO::FETCH_ASSOC)) {
        if (!is_array($row)) {
            continue;
        }
        $raw = (string) ($row['player_clan'] ?? '');
        if (clan_is_empty($raw)) {
            continue;
        }
        $names[clan_display_name($raw)] = true;
    }
    foreach (array_keys(clans_info()) as $infoKey) {
        $display = clan_display_name((string) $infoKey);
        if (!clan_is_empty($display)) {
            $names[$display] = true;
        }
    }
    $clanNames = array_keys($names);
    natcasesort($clanNames);
    $clanNames = array_values($clanNames);

    if ($selectedClan === '') {
        $selectedClan = isset($_GET['clan']) && is_string($_GET['clan'])
            ? clan_display_name($_GET['clan'])
            : '';
    }
    if ($selectedClan !== '' && !in_array($selectedClan, $clanNames, true)) {
        // Permitir clan elegido aunque no esté en la lista unificada (p. ej. recién vaciado).
        $clanNames[] = $selectedClan;
        natcasesort($clanNames);
        $clanNames = array_values($clanNames);
    }

    if ($selectedClan !== '') {
        $editors = clan_editors_list($pdo, $selectedClan, $serverId);
    }
} catch (Throwable $e) {
    error_log('Admin clanes failed: ' . $e->getMessage());
    if ($discordId === '') {
        // auth_require_staff ya pudo haber respondido; si falló DB antes, 500.
        http_response_code(500);
        echo 'No se pudo cargar el panel de clanes.';
        exit;
    }
    $flashErr = $flashErr !== '' ? $flashErr : 'No se pudo cargar el panel de clanes.';
}

$csrfToken = auth_csrf_token();
$serverQuery = isset($_GET['s']) && is_string($_GET['s']) && $_GET['s'] !== ''
    ? '?s=' . rawurlencode($_GET['s'])
    : '';

render_header('Admin · Clanes', [
    'stats_nav' => true,
    'hero_subtitle' => 'Editores de clan · ' . current_server_label(),
]);
?>
        <p class="text-muted"><a href="/admin/<?= e($serverQuery) ?>">← Volver al admin</a></p>

        <?php if ($flashOk !== ''): ?>
        <p class="profile-flash profile-flash--ok" role="status"><?= e($flashOk) ?></p>
        <?php endif; ?>
        <?php if ($flashErr !== ''): ?>
        <p class="profile-flash profile-flash--err" role="alert"><?= e($flashErr) ?></p>
        <?php endif; ?>

        <section class="profile-panel">
            <h3 class="profile-section-title">Clanes del servidor</h3>
            <?php if ($clanNames === []): ?>
            <p class="text-muted">No hay clanes para listar en este servidor.</p>
            <?php else: ?>
            <ul class="admin-clan-list">
                <?php foreach ($clanNames as $name): ?>
                <li>
                    <?php
                    $clanHref = '/admin/clanes.php' . ($serverQuery !== '' ? $serverQuery . '&' : '?')
                        . 'clan=' . rawurlencode($name);
                    $isActive = $selectedClan === $name;
                    ?>
                    <a class="admin-clan-list__link<?= $isActive ? ' is-active' : '' ?>" href="<?= e($clanHref) ?>">
                        <?= e($name) ?>
                    </a>
                </li>
                <?php endforeach; ?>
            </ul>
            <?php endif; ?>
        </section>

        <?php if ($selectedClan !== ''): ?>
        <section class="profile-panel">
            <h3 class="profile-section-title">Editores · <?= e($selectedClan) ?></h3>

            <?php if ($editors === []): ?>
            <p class="text-muted">Ningún editor asignado todavía.</p>
            <?php else: ?>
            <table class="data-table">
                <thead>
                    <tr>
                        <th>Discord ID</th>
                        <th>Otorgado por</th>
                        <th>Fecha</th>
                        <th></th>
                    </tr>
                </thead>
                <tbody>
                    <?php foreach ($editors as $row): ?>
                    <?php
                    $edId = (string) ($row['discord_id'] ?? '');
                    $grantedBy = (string) ($row['granted_by'] ?? '');
                    $grantedAt = (string) ($row['granted_at'] ?? '');
                    ?>
                    <tr>
                        <td><code><?= e($edId) ?></code></td>
                        <td><code><?= e($grantedBy) ?></code></td>
                        <td><?= e($grantedAt) ?></td>
                        <td>
                            <form method="post" class="profile-form profile-form--inline" action="/admin/clanes.php<?= e($serverQuery) ?>">
                                <input type="hidden" name="csrf" value="<?= e($csrfToken) ?>">
                                <input type="hidden" name="action" value="revoke">
                                <input type="hidden" name="clan" value="<?= e($selectedClan) ?>">
                                <input type="hidden" name="discord_id" value="<?= e($edId) ?>">
                                <button type="submit" class="btn">Revocar</button>
                            </form>
                        </td>
                    </tr>
                    <?php endforeach; ?>
                </tbody>
            </table>
            <?php endif; ?>

            <form method="post" class="profile-form" action="/admin/clanes.php<?= e($serverQuery) ?>">
                <input type="hidden" name="csrf" value="<?= e($csrfToken) ?>">
                <input type="hidden" name="action" value="grant">
                <input type="hidden" name="clan" value="<?= e($selectedClan) ?>">

                <label class="profile-form__label" for="discord_id">Agregar editor (Discord ID)</label>
                <input
                    class="profile-form__input"
                    type="text"
                    id="discord_id"
                    name="discord_id"
                    inputmode="numeric"
                    pattern="\d{5,32}"
                    required
                    autocomplete="off"
                    placeholder="Ej. 123456789012345678"
                >
                <button type="submit" class="btn">Asignar</button>
            </form>
        </section>
        <?php endif; ?>
<?php
render_footer();
