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

/**
 * Formatea timestamps ISO o MySQL para mostrar en la ficha.
 */
function format_player_timestamp(?string $value): string
{
    if ($value === null || trim($value) === '') {
        return '—';
    }

    $parsed = strtotime($value);

    if ($parsed === false) {
        return e($value);
    }

    return date('d/m/Y H:i', $parsed);
}

/** Etiquetas legibles para redes del perfil público. */
function player_profile_social_label(string $key): string
{
    $labels = [
        'x' => 'X',
        'youtube' => 'YouTube',
        'twitch' => 'Twitch',
        'instagram' => 'Instagram',
    ];

    return $labels[$key] ?? $key;
}

$playerId = trim((string) ($_GET['id'] ?? ''));
$player = null;
$loadError = false;
$profile = null;
$playerLink = null;
$discordUser = null;

if ($playerId !== '') {
    try {
        $pdo = createDatabaseConnection($config['db']);
        $statement = $pdo->prepare(
            'SELECT player_id, player_name, player_clan, score, kills, deaths, rounds, treasures, created, seen
             FROM players
             WHERE player_id = :player_id
             LIMIT 1'
        );
        $statement->bindValue(':player_id', $playerId, PDO::PARAM_STR);
        $statement->execute();
        $row = $statement->fetch();

        if (is_array($row)) {
            $player = $row;

            // Perfil / Discord: fallo aislado para no tumbar la ficha de stats.
            try {
                $serverId = current_server_id();
                $playerLink = player_link_for_player($pdo, $playerId, $serverId);
                $profile = profile_get($pdo, $playerId, $serverId);

                if ($playerLink !== null) {
                    $discordStmt = $pdo->prepare(
                        'SELECT username, global_name, avatar_hash
                         FROM discord_users
                         WHERE discord_id = ?
                         LIMIT 1'
                    );
                    $discordStmt->execute([(string) $playerLink['discord_id']]);
                    $discordRow = $discordStmt->fetch(PDO::FETCH_ASSOC);
                    if (is_array($discordRow)) {
                        $discordUser = $discordRow;
                    }
                }
            } catch (Throwable $profileException) {
                $profile = null;
                $playerLink = null;
                $discordUser = null;
            }
        }
    } catch (Throwable $exception) {
        $loadError = true;
    }
}

if ($loadError) {
    render_header('Error');
    ?>
        <p class="text-muted">No se pudo cargar la ficha del jugador.</p>
        <p><a class="btn" href="ranking.php">Volver al ranking</a></p>
    <?php
    render_footer();
    exit;
}

if ($player === null) {
    http_response_code(404);
    render_header('Jugador no encontrado');
    ?>
        <p class="text-muted">
            No existe ningún jugador con el identificador
            <?= $playerId !== '' ? '«' . e($playerId) . '»' : 'solicitado' ?>.
        </p>
        <p><a class="btn" href="ranking.php">Volver al ranking</a></p>
    <?php
    render_footer();
    exit;
}

$playerName = (string) ($player['player_name'] ?? '');
$playerClan = (string) ($player['player_clan'] ?? '');
$displayName = $playerName !== '' ? $playerName : $playerId;
$kd = kd_ratio($player['kills'] ?? 0, $player['deaths'] ?? 0);
$rankInfo = player_rank($player);
$maxRank = rank_by_id((int) $rankInfo['max_rank_id']);
$nextUnlockDays = rank_next_age_unlock_days((int) $rankInfo['days']);
$progressPct = (int) round(((float) $rankInfo['progress']) * 100);

// Datos públicos del perfil personalizado (banner / Discord / bio / redes).
$profileData = is_array($profile) ? $profile : [];
$bannerPath = (string) ($profileData['banner_path'] ?? '');
$bioText = trim((string) ($profileData['bio'] ?? ''));
$showDiscord = (int) ($profileData['show_discord'] ?? 1) === 1;
$socials = is_array($profileData['socials'] ?? null) ? $profileData['socials'] : [];
$avatarUrl = null;
if ($playerLink !== null) {
    $avatarUrl = profile_discord_avatar_url(
        (string) $playerLink['discord_id'],
        is_array($discordUser) ? (string) ($discordUser['avatar_hash'] ?? '') : '',
        96
    );
}
$discordDisplay = '';
if ($showDiscord && is_array($discordUser)) {
    $globalName = trim((string) ($discordUser['global_name'] ?? ''));
    $username = trim((string) ($discordUser['username'] ?? ''));
    $discordDisplay = $globalName !== '' ? $globalName : $username;
}
$activeSocials = [];
foreach (PROFILE_SOCIAL_KEYS as $socialKey) {
    $socialUrl = trim((string) ($socials[$socialKey] ?? ''));
    if ($socialUrl !== '') {
        $activeSocials[$socialKey] = $socialUrl;
    }
}
$hasPublicProfile = $bannerPath !== ''
    || $avatarUrl !== null
    || $bioText !== ''
    || $discordDisplay !== ''
    || $activeSocials !== [];

render_header($displayName);
?>
        <p class="text-muted">
            Clan: <strong><?= render_clan_link($playerClan) ?></strong>
            · ID: <?= e($playerId) ?>
        </p>

        <?php if ($hasPublicProfile): ?>
        <section class="player-profile" aria-label="Perfil del jugador">
            <?php if ($bannerPath !== ''): ?>
            <div class="player-profile__banner">
                <img src="<?= e(asset_url($bannerPath)) ?>" alt="" width="960" height="180">
            </div>
            <?php endif; ?>

            <?php if ($avatarUrl !== null || $discordDisplay !== ''): ?>
            <div class="player-profile__identity">
                <?php if ($avatarUrl !== null): ?>
                <img class="player-profile__avatar" src="<?= e($avatarUrl) ?>" alt="" width="72" height="72">
                <?php endif; ?>
                <?php if ($discordDisplay !== ''): ?>
                <p class="player-profile__discord">
                    <span class="player-profile__discord-label">Discord</span>
                    <?= e($discordDisplay) ?>
                </p>
                <?php endif; ?>
            </div>
            <?php endif; ?>

            <?php if ($bioText !== ''): ?>
            <p class="player-profile__bio"><?= e($bioText) ?></p>
            <?php endif; ?>

            <?php if ($activeSocials !== []): ?>
            <ul class="player-profile__socials">
                <?php foreach ($activeSocials as $socialKey => $socialUrl): ?>
                <li>
                    <a class="player-profile__social player-profile__social--<?= e($socialKey) ?>"
                       href="<?= e($socialUrl) ?>"
                       target="_blank"
                       rel="noopener noreferrer">
                        <?= e(player_profile_social_label($socialKey)) ?>
                    </a>
                </li>
                <?php endforeach; ?>
            </ul>
            <?php endif; ?>
        </section>
        <?php endif; ?>

        <section class="rank-panel" aria-label="Rango militar">
            <div class="rank-panel__heading">
                <?= render_rank_icon($rankInfo['rank'], 'rank-panel__icon', 48) ?>
                <h3 class="rank-panel__title">
                    <?= e((string) $rankInfo['rank']['name']) ?>
                    <span class="text-muted">(<?= e((string) $rankInfo['rank']['abbr']) ?>)</span>
                </h3>
            </div>
            <p class="rank-panel__meta">
                XP <?= number_format((int) $rankInfo['xp'], 0, ',', '.') ?>
                · Antigüedad <?= e(format_account_age((int) $rankInfo['days'])) ?>
                <span class="text-muted">(<?= (int) $rankInfo['days'] ?> día<?= ((int) $rankInfo['days'] === 1) ? '' : 's' ?>)</span>
                <?php if (is_array($rankInfo['next'])): ?>
                · Siguiente: <?= e((string) $rankInfo['next']['name']) ?>
                  (<?= number_format((int) $rankInfo['next']['xp_min'], 0, ',', '.') ?> XP)
                <?php endif; ?>
            </p>
            <div class="rank-panel__bar" role="progressbar"
                 aria-valuemin="0" aria-valuemax="100" aria-valuenow="<?= $progressPct ?>">
                <div class="rank-panel__bar-fill" style="width: <?= $progressPct ?>%;"></div>
            </div>
            <?php if (!empty($rankInfo['capped_by_age']) && is_array($maxRank)): ?>
            <p class="rank-panel__hint">
                Antigüedad: <?= e(format_account_age((int) $rankInfo['days'])) ?>
                · Tope actual: <?= e((string) $maxRank['name']) ?>.
                <?php if ($nextUnlockDays !== null): ?>
                Seguí sumando XP; el siguiente tramo se desbloquea a los <?= (int) $nextUnlockDays ?> días.
                <?php endif; ?>
            </p>
            <?php endif; ?>
        </section>

        <section class="metrics" aria-label="Estadísticas del jugador">
            <article class="metric">
                <p class="metric__label">Score</p>
                <p class="metric__value"><?= number_format((int) ($player['score'] ?? 0), 0, ',', '.') ?></p>
            </article>
            <article class="metric">
                <p class="metric__label">Kills</p>
                <p class="metric__value"><?= number_format((int) ($player['kills'] ?? 0), 0, ',', '.') ?></p>
            </article>
            <article class="metric">
                <p class="metric__label">Deaths</p>
                <p class="metric__value"><?= number_format((int) ($player['deaths'] ?? 0), 0, ',', '.') ?></p>
            </article>
            <article class="metric">
                <p class="metric__label">K/D</p>
                <p class="metric__value"><?= number_format($kd, 2, ',', '.') ?></p>
            </article>
            <article class="metric">
                <p class="metric__label">Rounds</p>
                <p class="metric__value"><?= number_format((int) ($player['rounds'] ?? 0), 0, ',', '.') ?></p>
            </article>
            <article class="metric">
                <p class="metric__label">Tesoros encontrados</p>
                <p class="metric__value"><?= number_format((int) ($player['treasures'] ?? 0), 0, ',', '.') ?></p>
            </article>
            <article class="metric">
                <p class="metric__label">Primera vez</p>
                <p class="metric__value"><?= format_player_timestamp(isset($player['created']) ? (string) $player['created'] : null) ?></p>
            </article>
            <article class="metric">
                <p class="metric__label">Última vez</p>
                <p class="metric__value"><?= format_player_timestamp(isset($player['seen']) ? (string) $player['seen'] : null) ?></p>
            </article>
        </section>

        <p><a class="btn" href="ranking.php">Volver al ranking</a></p>
<?php
render_footer();
