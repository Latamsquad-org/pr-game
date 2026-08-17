<?php

declare(strict_types=1);

require_once __DIR__ . '/helpers.php';
require_once __DIR__ . '/servers.php';
require_once __DIR__ . '/ranks.php';
require_once __DIR__ . '/auth.php';
require_once __DIR__ . '/player_profiles.php';

/** URL pública del sitio LATAMSQUAD. */
const LATAMSQUAD_WEB_URL = 'https://latamsquad.org';

/** URL pública de LATAMTORNEOS. */
const LATAMTORNEOS_WEB_URL = 'https://latamtorneos.org';

/** Invitación al servidor de Discord LATAMSQUAD. */
const LATAMSQUAD_DISCORD_URL = 'https://discord.gg/latamsquad';

/** Si el layout muestra Ranking / Rangos / Clanes (páginas de un juego). */
$GLOBALS['layout_stats_nav'] = true;

/**
 * Imprime la cabecera HTML, navegación y bloque hero de marca.
 *
 * @param array{
 *   stats_nav?: bool,
 *   hero_subtitle?: string,
 *   default_title?: string,
 *   meta_description?: string
 * } $options
 */
function render_header(string $title = '', array $options = []): void
{
    maybe_redirect_persisted_server();

    $showStatsNav = array_key_exists('stats_nav', $options)
        ? (bool) $options['stats_nav']
        : true;
    $GLOBALS['layout_stats_nav'] = $showStatsNav;

    $showServerTabs = array_key_exists('server_tabs', $options)
        ? (bool) $options['server_tabs']
        : $showStatsNav;
    $toolbarTitle = trim((string) ($options['toolbar_title'] ?? ''));

    $heroSubtitle = (string) ($options['hero_subtitle'] ?? 'Project Reality Stats');
    $defaultTitle = (string) ($options['default_title'] ?? 'LATAMSQUAD · Project Reality Stats');
    $metaDescription = (string) ($options['meta_description']
        ?? 'Estadísticas de Project Reality del servidor LATAMSQUAD.');

    $pageTitle = $title !== ''
        ? e($title) . ' · LATAMSQUAD Stats'
        : e($defaultTitle);

    $cssHref = asset_url('assets/css/main.css') . '?v=20260725toolbar';
    $homeScript = stats_home_script();
    $homeActive = $showStatsNav
        ? is_current_page($homeScript)
        : is_current_page('index.php');
    $homeHref = $showStatsNav ? stats_url($homeScript) : home_url();
    $gamesHubHref = home_url();

    // Enlaces de cuenta segun sesion Discord (Entrar / chip avatar+nombre / Admin / Salir).
    $navDiscordId = auth_current_discord_id();
    $navIsStaff = $navDiscordId !== null
        && session_status() === PHP_SESSION_ACTIVE
        && !empty($_SESSION['is_staff']);
    $navAdminActive = str_contains((string) ($_SERVER['SCRIPT_NAME'] ?? ''), '/admin/');
    $navDisplayName = '';
    $navAvatarUrl = '';
    if ($navDiscordId !== null) {
        $global = is_string($_SESSION['discord_global_name'] ?? null)
            ? trim((string) $_SESSION['discord_global_name'])
            : '';
        $user = is_string($_SESSION['discord_username'] ?? null)
            ? trim((string) $_SESSION['discord_username'])
            : '';
        $navDisplayName = $global !== '' ? $global : ($user !== '' ? $user : 'Usuario');
        $avatarHash = is_string($_SESSION['discord_avatar'] ?? null)
            ? (string) $_SESSION['discord_avatar']
            : '';
        $navAvatarUrl = profile_discord_avatar_url($navDiscordId, $avatarHash, 64);
    }
    ?>
<!DOCTYPE html>
<html lang="es">
<head>
    <meta charset="utf-8">
    <meta name="viewport" content="width=device-width, initial-scale=1">
    <title><?= $pageTitle ?></title>
    <meta name="description" content="<?= e($metaDescription) ?>">
    <meta name="theme-color" content="#ff8000">
    <link rel="icon" href="<?= e(asset_url('favicon.ico')) ?>" sizes="any">
    <link rel="icon" href="<?= e(asset_url('assets/img/favicon-32.png')) ?>" type="image/png" sizes="32x32">
    <link rel="apple-touch-icon" href="<?= e(asset_url('assets/img/favicon.png')) ?>">
    <link rel="preconnect" href="https://fonts.googleapis.com">
    <link rel="preconnect" href="https://fonts.gstatic.com" crossorigin>
    <link href="https://fonts.googleapis.com/css2?family=Rajdhani:wght@400;500;600;700&display=swap" rel="stylesheet">
    <link rel="stylesheet" href="<?= e($cssHref) ?>">
</head>
<body>
    <header class="site-header">
        <div class="site-header__inner">
            <div class="site-header__left">
                <a class="site-brand" href="<?= e($gamesHubHref) ?>" aria-label="LATAMSTATS — Elegir juego">
                    <img
                        class="site-brand__logo"
                        src="<?= e(asset_url('assets/img/latamstats-logo.png')) ?>?v=1"
                        alt="LATAMSTATS"
                        width="610"
                        height="91"
                    >
                </a>
                <nav class="site-nav site-nav--primary" aria-label="Principal">
                    <a class="site-nav__link<?= is_current_page('index.php') ? ' is-active' : '' ?>" href="<?= e($gamesHubHref) ?>">Juegos</a>
                    <?php if ($showStatsNav): ?>
                    <a class="site-nav__link<?= $homeActive ? ' is-active' : '' ?>" href="<?= e($homeHref) ?>">Inicio</a>
                    <a class="site-nav__link<?= is_current_page('ranking.php') ? ' is-active' : '' ?>" href="<?= e(stats_url('ranking.php')) ?>">Ranking</a>
                    <a class="site-nav__link<?= is_current_page('rangos.php') ? ' is-active' : '' ?>" href="<?= e(stats_url('rangos.php')) ?>">Rangos</a>
                    <a class="site-nav__link<?= is_current_page('clans.php') ? ' is-active' : '' ?>" href="<?= e(stats_url('clans.php')) ?>">Clanes</a>
                    <?php endif; ?>
                </nav>
            </div>

            <nav class="site-nav site-nav--meta" aria-label="Cuenta y enlaces">
                <a class="site-nav__link site-nav__link--external site-nav__link--latamsquad" href="<?= e(LATAMSQUAD_WEB_URL) ?>" target="_blank" rel="noopener noreferrer"><span class="site-nav__latamsquad-latam">LATAM</span><span class="site-nav__latamsquad-squad">SQUAD</span></a>
                <a class="site-nav__link site-nav__link--external site-nav__link--latamtorneos" href="<?= e(LATAMTORNEOS_WEB_URL) ?>" target="_blank" rel="noopener noreferrer"><span class="site-nav__latamtorneos-latam">LATAM</span><span class="site-nav__latamtorneos-torneos">TORNEOS</span></a>
                <a class="site-nav__link site-nav__link--external site-nav__link--discord" href="<?= e(LATAMSQUAD_DISCORD_URL) ?>" target="_blank" rel="noopener noreferrer">Discord</a>
                <?php if ($navDiscordId === null): ?>
                <a class="site-nav__link<?= is_current_page('discord.php') ? ' is-active' : '' ?>" href="<?= e(AUTH_LOGIN_PATH) ?>">Entrar</a>
                <?php else: ?>
                <a
                    class="site-nav__user<?= is_current_page('mi-perfil.php') ? ' is-active' : '' ?>"
                    href="/mi-perfil.php"
                    title="Mi perfil"
                >
                    <img
                        class="site-nav__avatar"
                        src="<?= e($navAvatarUrl) ?>"
                        alt=""
                        width="28"
                        height="28"
                        decoding="async"
                        referrerpolicy="no-referrer"
                    >
                    <span class="site-nav__user-name"><?= e($navDisplayName) ?></span>
                </a>
                <?php if ($navIsStaff): ?>
                <a class="site-nav__link<?= $navAdminActive ? ' is-active' : '' ?>" href="/admin/">Admin</a>
                <?php endif; ?>
                <a class="site-nav__link" href="/auth/logout.php">Salir</a>
                <?php endif; ?>
            </nav>
        </div>
    </header>

    <main class="site-main">
        <?php if ($showServerTabs || $toolbarTitle !== ''): ?>
        <div class="content-toolbar">
            <?php if ($toolbarTitle !== ''): ?>
            <h2 class="content-toolbar__title"><?= e($toolbarTitle) ?></h2>
            <?php else: ?>
            <span class="content-toolbar__spacer" aria-hidden="true"></span>
            <?php endif; ?>
            <?php if ($showServerTabs): ?>
            <?php render_server_tabs(); ?>
            <?php endif; ?>
        </div>
        <?php endif; ?>
    <?php
}

/**
 * Cierra el contenido principal y muestra el pie de página.
 */
function render_footer(): void
{
    $year = (int) date('Y');
    $showStatsNav = !empty($GLOBALS['layout_stats_nav']);
    $homeHref = $showStatsNav ? stats_url(stats_home_script()) : home_url();
    $gamesHubHref = home_url();
    ?>
    </main>

    <footer class="site-footer">
        <div class="site-footer__inner">
            <p class="site-footer__copy">
                &copy; 2021 - <?= $year ?>
                <a href="<?= e(LATAMSQUAD_WEB_URL) ?>" target="_blank" rel="noopener noreferrer">LATAMSQUAD</a>
            </p>
            <p class="site-footer__links">
                <a href="<?= e($gamesHubHref) ?>">Juegos</a>
                <?php if ($showStatsNav): ?>
                <span aria-hidden="true">·</span>
                <a href="<?= e($homeHref) ?>">Inicio</a>
                <span aria-hidden="true">·</span>
                <a href="<?= e(stats_url('ranking.php')) ?>">Ranking</a>
                <span aria-hidden="true">·</span>
                <a href="<?= e(stats_url('rangos.php')) ?>">Rangos</a>
                <span aria-hidden="true">·</span>
                <a href="<?= e(stats_url('clans.php')) ?>">Clanes</a>
                <?php endif; ?>
                <span aria-hidden="true">·</span>
                <a href="<?= e(LATAMSQUAD_DISCORD_URL) ?>" target="_blank" rel="noopener noreferrer">Discord</a>
            </p>
        </div>
    </footer>
    <?php if ($showStatsNav): ?>
    <script src="<?= e(asset_url('assets/js/server-tabs.js')) ?>?v=20260716servertabpulse" defer></script>
    <?php endif; ?>
</body>
</html>
    <?php
}
