<?php
declare(strict_types=1);

require_once __DIR__ . '/lib.php';

auth_start_session();

/**
 * Respuesta de error en callback OAuth (texto plano).
 */
function auth_callback_fail(string $message, int $status = 400): void
{
    http_response_code($status);
    header('Content-Type: text/plain; charset=utf-8');
    echo $message . "\n";
    exit;
}

/**
 * Usuario no esta en el guild LATAMSQUAD (403).
 */
function auth_callback_guild_required(): void
{
    auth_render_notice_page(
        'Unite al Discord LATAMSQUAD',
        'Hace falta el Discord de LATAMSQUAD',
        'Para usar LATAMFILES tenes que estar en el servidor de Discord de la comunidad.',
        'Unite al Discord y volve a intentar el acceso de administradores.',
        [
            ['href' => 'https://discord.gg/latamsquad', 'label' => 'Unirse al Discord', 'primary' => true],
            ['href' => '/', 'label' => 'Volver al inicio'],
        ],
        403
    );
}

/**
 * Jugador sin rol staff: no se crea sesion en este sitio (403).
 */
function auth_callback_staff_required(): void
{
    auth_render_notice_page(
        'Acceso solo para administradores',
        'Acceso restringido',
        'LATAMFILES es solo para el staff de LATAMSQUAD. Tu cuenta de Discord no tiene permisos de administrador en este sitio.',
        'Si eres jugador, tus estadisticas y tu perfil estan en stats.latamsquad.org.',
        [
            ['href' => 'https://stats.latamsquad.org/', 'label' => 'Ir a stats.latamsquad.org', 'primary' => true],
            ['href' => '/', 'label' => 'Volver al inicio'],
        ],
        403
    );
}

$expectedState = $_SESSION['oauth_state'] ?? null;
$givenState = isset($_GET['state']) && is_string($_GET['state']) ? $_GET['state'] : '';

if (!is_string($expectedState) || $expectedState === '' || $givenState === ''
    || !hash_equals($expectedState, $givenState)) {
    auth_callback_fail('State OAuth invalido.', 400);
}

if (isset($_GET['error'])) {
    $err = is_string($_GET['error']) ? $_GET['error'] : 'error';
    auth_callback_fail('Discord rechazo el login: ' . $err . '.', 400);
}

$code = isset($_GET['code']) && is_string($_GET['code']) ? $_GET['code'] : '';
if ($code === '') {
    auth_callback_fail('Falta el codigo OAuth de Discord.', 400);
}

try {
    $cfg = auth_config();
    $tokens = discord_exchange_code($code);
    $accessToken = (string) ($tokens['access_token'] ?? '');
    if ($accessToken === '') {
        auth_callback_fail('No se pudo completar el login con Discord.', 502);
    }

    $user = discord_fetch_user($accessToken);
    $memberResult = discord_fetch_guild_member($accessToken, $cfg['guild_id']);
    $status = (int) ($memberResult['status'] ?? 0);

    if ($status === 404) {
        unset($_SESSION['oauth_state']);
        auth_callback_guild_required();
    }

    if ($status < 200 || $status >= 300) {
        auth_callback_fail('No se pudo verificar tu membresia en Discord. Intenta de nuevo mas tarde.', 502);
    }

    $member = $memberResult['body'] ?? null;
    $isStaff = discord_member_has_staff_role(is_array($member) ? $member : null, $cfg['staff_role_ids']);
    unset($_SESSION['oauth_state']);

    // Solo staff: jugadores no obtienen sesion en latamsquad.dev
    if (!$isStaff) {
        auth_logout();
        auth_callback_staff_required();
    }

    auth_login_user($user, true);
} catch (Throwable $e) {
    error_log('Discord OAuth callback failed: ' . $e->getMessage());
    auth_callback_fail('No se pudo completar el login con Discord. Intenta de nuevo mas tarde.', 502);
}

$return = '/';
if (isset($_SESSION['auth_return']) && is_string($_SESSION['auth_return'])) {
    $candidate = $_SESSION['auth_return'];
    unset($_SESSION['auth_return']);
    if ($candidate !== '' && $candidate[0] === '/' && !str_starts_with($candidate, '//')
        && !str_starts_with($candidate, '/auth/')) {
        $return = $candidate;
    }
}
header('Location: ' . $return, true, 302);
exit;