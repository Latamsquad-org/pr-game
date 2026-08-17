<?php

declare(strict_types=1);

require_once dirname(__DIR__) . '/includes/discord_oauth.php';

/**
 * Inicia el flujo OAuth2 de Discord: guarda state en sesión y redirige.
 */
auth_start_session();

$cfg = auth_discord_config();
if ($cfg['client_id'] === '' || $cfg['redirect_uri'] === '') {
    http_response_code(503);
    header('Content-Type: text/plain; charset=utf-8');
    echo "Discord OAuth no está configurado. Copiá config.sample.php a config.php y completá la sección discord.\n";
    exit;
}

$state = bin2hex(random_bytes(16));
$_SESSION['oauth_state'] = $state;

$authorizeUrl = discord_authorize_url($state);
if ($authorizeUrl === '') {
    http_response_code(503);
    header('Content-Type: text/plain; charset=utf-8');
    echo "No se pudo construir la URL de autorización de Discord.\n";
    exit;
}

header('Location: ' . $authorizeUrl, true, 302);
exit;
