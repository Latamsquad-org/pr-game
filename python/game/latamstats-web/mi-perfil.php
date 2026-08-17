<?php

declare(strict_types=1);

require_once __DIR__ . '/includes/layout.php';
require_once __DIR__ . '/includes/db.php';
require_once __DIR__ . '/includes/player_links.php';
require_once __DIR__ . '/includes/player_profiles.php';

$configPath = __DIR__ . '/config.php';
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

$discordId = auth_require_login();

$flashOk = '';
$flashErr = '';
$link = null;
$profile = null;
$activeCode = null;
$activeExpires = null;

try {
    $pdo = createDatabaseConnection($config['db']);
    ensure_auth_schema($pdo);
    $serverId = current_server_id();

    // POST: generar código o guardar perfil (siempre con CSRF).
    if (($_SERVER['REQUEST_METHOD'] ?? 'GET') === 'POST') {
        $csrf = isset($_POST['csrf']) && is_string($_POST['csrf']) ? $_POST['csrf'] : '';
        if (!auth_csrf_validate($csrf)) {
            $flashErr = 'Token de seguridad inválido. Recargá la página e intentá de nuevo.';
        } else {
            $action = isset($_POST['action']) && is_string($_POST['action']) ? $_POST['action'] : '';

            if ($action === 'generate_code') {
                // Rate limit ~30s por discord_id (sesión) para generar códigos.
                if (auth_action_rate_limited('link_code_generate', $discordId)) {
                    $flashErr = 'Esperá unos segundos antes de generar otro código.';
                } else {
                    $code = link_code_generate($pdo, $discordId);
                    auth_action_rate_touch('link_code_generate', $discordId);
                    $flashOk = 'Código generado: ' . $code . '. Ponelo en tu nombre en el juego y jugá una ronda.';
                }
            } elseif ($action === 'save_profile') {
                // Mismo cooldown para guardar perfil / subir banner.
                if (auth_action_rate_limited('profile_save', $discordId)) {
                    $flashErr = 'Esperá unos segundos antes de guardar el perfil de nuevo.';
                } else {
                    $linkRow = player_link_for_discord($pdo, $discordId, $serverId);
                    if ($linkRow === null) {
                        $flashErr = 'Primero tenés que vincular tu cuenta de juego.';
                    } else {
                        $playerId = (string) $linkRow['player_id'];
                        $fields = [
                            'bio' => (string) ($_POST['bio'] ?? ''),
                            'show_discord' => isset($_POST['show_discord']) ? 1 : 0,
                            'socials' => [
                                'x' => (string) ($_POST['social_x'] ?? ''),
                                'youtube' => (string) ($_POST['social_youtube'] ?? ''),
                                'twitch' => (string) ($_POST['social_twitch'] ?? ''),
                                'instagram' => (string) ($_POST['social_instagram'] ?? ''),
                            ],
                        ];

                        // Banner opcional.
                        if (isset($_FILES['banner']) && is_array($_FILES['banner'])
                            && (int) ($_FILES['banner']['error'] ?? UPLOAD_ERR_NO_FILE) !== UPLOAD_ERR_NO_FILE) {
                            try {
                                $fields['banner_path'] = profile_store_banner($_FILES['banner']);
                            } catch (Throwable $bannerEx) {
                                $flashErr = $bannerEx->getMessage();
                            }
                        }

                        if ($flashErr === '') {
                            profile_save($pdo, $playerId, $serverId, $fields);
                            auth_action_rate_touch('profile_save', $discordId);
                            $flashOk = 'Perfil guardado.';
                        }
                    }
                }
            }
        }
    }

    $link = player_link_for_discord($pdo, $discordId, $serverId);

    if ($link === null) {
        // Código activo no vencido (si existe).
        $now = time();
        $codeStmt = $pdo->prepare(
            'SELECT code, expires_at FROM link_codes
             WHERE discord_id = ? AND expires_at >= ?
             ORDER BY created_at DESC
             LIMIT 1'
        );
        $codeStmt->execute([$discordId, $now]);
        $codeRow = $codeStmt->fetch(PDO::FETCH_ASSOC);
        if (is_array($codeRow)) {
            $activeCode = (string) $codeRow['code'];
            $activeExpires = (int) $codeRow['expires_at'];
        }
    } else {
        $profile = profile_get($pdo, (string) $link['player_id'], $serverId);
    }
} catch (Throwable $e) {
    $flashErr = $flashErr !== '' ? $flashErr : 'No se pudo cargar el perfil.';
}

$csrfToken = auth_csrf_token();
$avatarHash = is_string($_SESSION['discord_avatar'] ?? null) ? (string) $_SESSION['discord_avatar'] : '';
$avatarUrl = profile_discord_avatar_url($discordId, $avatarHash, 128);
$displayName = is_string($_SESSION['discord_global_name'] ?? null) && $_SESSION['discord_global_name'] !== ''
    ? (string) $_SESSION['discord_global_name']
    : (is_string($_SESSION['discord_username'] ?? null) ? (string) $_SESSION['discord_username'] : $discordId);

// Perfil puede ser null tras vincular (aún sin fila en player_profiles).
$profileData = $profile ?? [];
$socials = is_array($profileData['socials'] ?? null) ? $profileData['socials'] : [];
$bioValue = (string) ($profileData['bio'] ?? '');
$showDiscord = (int) ($profileData['show_discord'] ?? 1) === 1;
$bannerPath = (string) ($profileData['banner_path'] ?? '');

render_header('Mi perfil', [
    'stats_nav' => true,
    'hero_subtitle' => 'Vinculá Discord y personalizá tu ficha',
]);
?>
        <?php if ($flashOk !== ''): ?>
        <p class="profile-flash profile-flash--ok" role="status"><?= e($flashOk) ?></p>
        <?php endif; ?>
        <?php if ($flashErr !== ''): ?>
        <p class="profile-flash profile-flash--err" role="alert"><?= e($flashErr) ?></p>
        <?php endif; ?>

        <section class="profile-panel">
            <div class="profile-panel__identity">
                <img class="profile-panel__avatar" src="<?= e($avatarUrl) ?>" alt="" width="96" height="96">
                <div>
                    <p class="profile-panel__name"><?= e($displayName) ?></p>
                    <p class="text-muted">Discord · servidor <?= e(current_server_label()) ?></p>
                </div>
            </div>

            <?php if ($link === null): ?>
            <div class="profile-link-box">
                <h3 class="profile-section-title">Vincular cuenta de juego</h3>
                <ol class="profile-steps">
                    <li>Generá un código <code>LS-XXXX</code> (válido 45 minutos).</li>
                    <li>Agregalo a tu nombre en Project Reality (ej. <code>TuNick LS-A1B2</code>).</li>
                    <li>Jugá una ronda: el sync del servidor confirma el vínculo automáticamente.</li>
                </ol>

                <?php if ($activeCode !== null): ?>
                <p class="profile-code" aria-live="polite">
                    Tu código:
                    <strong><?= e($activeCode) ?></strong>
                    <?php if ($activeExpires !== null): ?>
                    <span class="text-muted">(vence <?= e(date('H:i', $activeExpires)) ?>)</span>
                    <?php endif; ?>
                </p>
                <?php else: ?>
                <p class="text-muted">Todavía no tenés un código activo.</p>
                <?php endif; ?>

                <form method="post" class="profile-form profile-form--inline" action="/mi-perfil.php">
                    <input type="hidden" name="csrf" value="<?= e($csrfToken) ?>">
                    <input type="hidden" name="action" value="generate_code">
                    <button type="submit" class="btn">
                        <?= $activeCode !== null ? 'Regenerar código' : 'Generar código' ?>
                    </button>
                </form>
            </div>
            <?php else: ?>
            <p class="profile-linked">
                Vinculado a jugador
                <a href="<?= e(stats_url('player.php', ['id' => (string) $link['player_id']])) ?>">
                    <?= e((string) $link['player_id']) ?>
                </a>
            </p>

            <form
                method="post"
                class="profile-form"
                action="/mi-perfil.php"
                enctype="multipart/form-data"
            >
                <input type="hidden" name="csrf" value="<?= e($csrfToken) ?>">
                <input type="hidden" name="action" value="save_profile">

                <label class="profile-form__label" for="bio">Bio (máx. 500)</label>
                <textarea
                    class="profile-form__textarea"
                    id="bio"
                    name="bio"
                    maxlength="500"
                    rows="4"
                ><?= e($bioValue) ?></textarea>

                <label class="profile-form__check">
                    <input type="checkbox" name="show_discord" value="1"<?= $showDiscord ? ' checked' : '' ?>>
                    Mostrar Discord en mi ficha pública
                </label>

                <fieldset class="profile-form__fieldset">
                    <legend>Redes (URLs https)</legend>
                    <label class="profile-form__label" for="social_x">X / Twitter</label>
                    <input class="profile-form__input" type="url" id="social_x" name="social_x"
                           value="<?= e((string) ($socials['x'] ?? '')) ?>" placeholder="https://">
                    <label class="profile-form__label" for="social_youtube">YouTube</label>
                    <input class="profile-form__input" type="url" id="social_youtube" name="social_youtube"
                           value="<?= e((string) ($socials['youtube'] ?? '')) ?>" placeholder="https://">
                    <label class="profile-form__label" for="social_twitch">Twitch</label>
                    <input class="profile-form__input" type="url" id="social_twitch" name="social_twitch"
                           value="<?= e((string) ($socials['twitch'] ?? '')) ?>" placeholder="https://">
                    <label class="profile-form__label" for="social_instagram">Instagram</label>
                    <input class="profile-form__input" type="url" id="social_instagram" name="social_instagram"
                           value="<?= e((string) ($socials['instagram'] ?? '')) ?>" placeholder="https://">
                </fieldset>

                <label class="profile-form__label" for="banner">Banner (JPEG/PNG/WebP, máx. 1.5 MB)</label>
                <?php if ($bannerPath !== ''): ?>
                <p class="profile-banner-preview">
                    <img src="<?= e(asset_url($bannerPath)) ?>" alt="Banner actual" width="480" height="120">
                </p>
                <?php endif; ?>
                <input class="profile-form__file" type="file" id="banner" name="banner"
                       accept="image/jpeg,image/png,image/webp">

                <button type="submit" class="btn">Guardar perfil</button>
            </form>
            <?php endif; ?>
        </section>
<?php
render_footer();
