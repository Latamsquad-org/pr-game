<?php
declare(strict_types=1);

require_once dirname(__DIR__) . '/auth/lib.php';

/**
 * Escape HTML.
 */
function admin_h(string $s): string
{
    return htmlspecialchars($s, ENT_QUOTES, 'UTF-8');
}

/**
 * Safe internal return path only (same-site path).
 */
function admin_safe_return_path(?string $path): string
{
    if ($path === null || $path === '') {
        return '/admin/';
    }
    if ($path[0] !== '/' || str_starts_with($path, '//')) {
        return '/admin/';
    }
    if (str_starts_with($path, '/auth/')) {
        return '/admin/';
    }
    return $path;
}

/**
 * Session CSRF token for admin forms.
 */
function admin_csrf_token(): string
{
    if (empty($_SESSION['admin_csrf']) || !is_string($_SESSION['admin_csrf'])) {
        $_SESSION['admin_csrf'] = bin2hex(random_bytes(16));
    }
    return $_SESSION['admin_csrf'];
}

/**
 * Validate posted CSRF token against session.
 */
function admin_csrf_validate(?string $token): bool
{
    $sess = $_SESSION['admin_csrf'] ?? '';
    return is_string($token) && is_string($sess) && $sess !== '' && hash_equals($sess, $token);
}

auth_start_session();
auth_send_noindex();

$discordId = auth_current_discord_id();
if ($discordId === null) {
    $_SESSION['auth_return'] = admin_safe_return_path(
        isset($_SERVER['REQUEST_URI']) ? (string) $_SERVER['REQUEST_URI'] : '/admin/'
    );
    header('Location: /auth/discord.php', true, 302);
    exit;
}

if (!auth_is_staff()) {
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
