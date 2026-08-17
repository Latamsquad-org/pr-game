<?php

declare(strict_types=1);

require_once dirname(__DIR__) . '/includes/discord_oauth.php';
require_once dirname(__DIR__) . '/includes/db.php';

/**
 * Callback OAuth2: valida state, intercambia code, upsert usuario y crea sesión.
 */
auth_start_session();

/**
 * Respuesta de error genérica para el callback (sin filtrar detalles internos).
 */
function auth_callback_fail(string $message, int $status = 400): void
{
    http_response_code($status);
    header('Content-Type: text/plain; charset=utf-8');
    echo $message . "\n";
    exit;
}

$expectedState = $_SESSION['oauth_state'] ?? null;
$givenState = isset($_GET['state']) && is_string($_GET['state']) ? $_GET['state'] : '';
unset($_SESSION['oauth_state']);

if (!is_string($expectedState) || $expectedState === '' || $givenState === ''
    || !hash_equals($expectedState, $givenState)) {
    auth_callback_fail('State OAuth inválido. Volvé a intentar el login.', 403);
}

if (isset($_GET['error'])) {
    auth_callback_fail('Discord rechazó el login. Volvé a intentar.', 403);
}

$code = isset($_GET['code']) && is_string($_GET['code']) ? $_GET['code'] : '';
if ($code === '') {
    auth_callback_fail('Falta el código OAuth de Discord.');
}

try {
    $tokens = discord_exchange_code($code);
    $accessToken = (string) ($tokens['access_token'] ?? '');
    if ($accessToken === '') {
        auth_callback_fail('No se pudo completar el login con Discord.', 502);
    }

    $user = discord_fetch_user($accessToken);
    $cfg = auth_discord_config();

    $configPath = is_file(dirname(__DIR__) . '/config.php')
        ? dirname(__DIR__) . '/config.php'
        : dirname(__DIR__) . '/config.sample.php';
    if (!is_file($configPath)) {
        auth_callback_fail('El sitio no está configurado correctamente.', 503);
    }
    $config = require $configPath;
    if (!is_array($config) || !isset($config['db']) || !is_array($config['db'])) {
        auth_callback_fail('El sitio no está configurado correctamente.', 503);
    }

    $pdo = createDatabaseConnection($config['db']);
    ensure_auth_schema($pdo);

    $discordId = (string) ($user['id'] ?? '');
    $previousStaff = $discordId !== '' && auth_user_is_staff_from_db($pdo, $discordId);

    // Staff: 404 demote; 2xx por roles; 5xx/429/red conserva flag previo (no escribe 0).
    $fetched = discord_fetch_guild_member($accessToken, $cfg['guild_id']);
    $resolved = discord_resolve_staff_flag(
        (int) $fetched['status'],
        $fetched['member'],
        $cfg['staff_role_ids'],
        $previousStaff
    );

    $staffForUpsert = $resolved['write'] ? $resolved['is_staff'] : null;
    discord_upsert_user($pdo, $user, $tokens, $staffForUpsert);
    auth_login_user($user, $resolved['is_staff']);
} catch (Throwable $e) {
    error_log('Discord OAuth callback failed: ' . $e->getMessage());
    auth_callback_fail('No se pudo completar el login con Discord. Intentá de nuevo más tarde.', 502);
}

header('Location: /mi-perfil.php', true, 302);
exit;
