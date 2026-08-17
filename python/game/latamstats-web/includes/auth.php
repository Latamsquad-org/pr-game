<?php

declare(strict_types=1);

require_once __DIR__ . '/auth_schema.php';

/** URL relativa de inicio de sesión Discord (Task 3 crea auth/discord.php). */
const AUTH_LOGIN_PATH = '/auth/discord.php';

/** Cooldown mínimo (segundos) entre acciones sensibles por discord_id (sesión). */
const AUTH_ACTION_COOLDOWN_SECONDS = 30;

/**
 * Inicia sesión PHP con cookie HttpOnly, Secure (si HTTPS) y SameSite=Lax.
 */
function auth_start_session(): void
{
    if (session_status() === PHP_SESSION_ACTIVE) {
        return;
    }
    // En CLI (smoke tests) los headers ya pueden estar enviados; omitir params de cookie.
    if (!headers_sent()) {
        session_set_cookie_params([
            'lifetime' => 0,
            'path' => '/',
            'secure' => (!empty($_SERVER['HTTPS']) && $_SERVER['HTTPS'] !== 'off'),
            'httponly' => true,
            'samesite' => 'Lax',
        ]);
        session_start();
        return;
    }
    if (session_status() !== PHP_SESSION_ACTIVE) {
        // Tras session_destroy() en CLI no se puede reabrir sesión si ya hubo output.
        return;
    }
}

/**
 * Devuelve (y crea si falta) el token CSRF de la sesión actual.
 */
function auth_csrf_token(): string
{
    auth_start_session();
    if (empty($_SESSION['csrf']) || !is_string($_SESSION['csrf'])) {
        $_SESSION['csrf'] = bin2hex(random_bytes(32));
    }
    return $_SESSION['csrf'];
}

/**
 * Valida un token CSRF contra el almacenado en sesión (comparación timing-safe).
 */
function auth_csrf_validate(?string $token): bool
{
    auth_start_session();
    $expected = $_SESSION['csrf'] ?? '';
    return is_string($token) && is_string($expected) && $expected !== ''
        && hash_equals($expected, $token);
}

/**
 * Discord ID del usuario logueado, o null si no hay sesión activa.
 */
function auth_current_discord_id(): ?string
{
    auth_start_session();
    if (session_status() !== PHP_SESSION_ACTIVE) {
        return null;
    }
    $id = $_SESSION['discord_id'] ?? null;
    return is_string($id) && $id !== '' ? $id : null;
}

/**
 * Exige login: devuelve discord_id o redirige a la página de OAuth Discord.
 */
function auth_require_login(): string
{
    $discordId = auth_current_discord_id();
    if ($discordId !== null) {
        return $discordId;
    }

    if (!headers_sent()) {
        header('Location: ' . AUTH_LOGIN_PATH, true, 302);
    }
    exit;
}

/**
 * Exige login + staff (revalida rol Discord en el guild).
 * Devuelve discord_id o responde 403 Forbidden.
 */
function auth_require_staff(PDO $pdo): string
{
    $discordId = auth_require_login();
    if (!auth_user_is_staff($pdo, $discordId, true)) {
        http_response_code(403);
        if (!headers_sent()) {
            header('Content-Type: text/plain; charset=utf-8');
        }
        echo 'Forbidden';
        exit;
    }

    return $discordId;
}

/**
 * Indica si un usuario Discord es staff (rol en guild).
 *
 * Con $revalidate=true consulta el miembro del guild vía Discord OAuth helpers
 * y actualiza discord_users.is_staff + sesión. Sin revalidate usa sesión/DB.
 */
function auth_user_is_staff(PDO $pdo, string $discordId, bool $revalidate = false): bool
{
    auth_start_session();
    ensure_auth_schema($pdo);

    if ($revalidate) {
        // Carga diferida: discord_oauth.php requiere auth.php (ciclo). Documentado a propósito.
        require_once __DIR__ . '/discord_oauth.php';
        $isStaff = discord_revalidate_staff($pdo, $discordId);
        auth_sync_staff_session($discordId, $isStaff);
        return $isStaff;
    }

    $currentId = auth_current_discord_id();
    if ($currentId === $discordId && isset($_SESSION['is_staff'])) {
        return (int) $_SESSION['is_staff'] === 1;
    }

    return auth_user_is_staff_from_db($pdo, $discordId);
}

/**
 * Establece la sesión tras login OAuth (regenera ID de sesión).
 *
 * @param array<string, mixed> $discordUser
 */
function auth_login_user(array $discordUser, bool $isStaff): void
{
    auth_start_session();
    if (!headers_sent()) {
        session_regenerate_id(true);
    }
    $_SESSION['discord_id'] = (string) ($discordUser['id'] ?? '');
    $_SESSION['discord_username'] = (string) ($discordUser['username'] ?? '');
    $_SESSION['discord_global_name'] = (string) ($discordUser['global_name'] ?? '');
    $_SESSION['discord_avatar'] = (string) ($discordUser['avatar'] ?? '');
    $_SESSION['is_staff'] = $isStaff ? 1 : 0;
}

/** Cierra sesión y elimina la cookie de sesión (SameSite=Lax). */
function auth_logout(): void
{
    auth_start_session();
    $_SESSION = [];
    if (!headers_sent() && ini_get('session.use_cookies')) {
        $p = session_get_cookie_params();
        setcookie(session_name(), '', [
            'expires' => time() - 42000,
            'path' => $p['path'] ?? '/',
            'domain' => $p['domain'] ?? '',
            'secure' => (bool) ($p['secure'] ?? false),
            'httponly' => (bool) ($p['httponly'] ?? true),
            'samesite' => 'Lax',
        ]);
    }
    session_destroy();
}

/**
 * Lee la sección discord de config.php (o config.sample.php en dev).
 * Valores SAMPLE se devuelven como cadenas vacías.
 *
 * @return array{
 *     client_id: string,
 *     client_secret: string,
 *     guild_id: string,
 *     staff_role_ids: list<string>,
 *     redirect_uri: string
 * }
 */
function auth_discord_config(): array
{
    $defaults = [
        'client_id' => '',
        'client_secret' => '',
        'guild_id' => '',
        'staff_role_ids' => [],
        'redirect_uri' => '',
    ];

    $baseDir = dirname(__DIR__);
    $configPath = is_file($baseDir . '/config.php')
        ? $baseDir . '/config.php'
        : $baseDir . '/config.sample.php';

    if (!is_file($configPath)) {
        return $defaults;
    }

    $config = require $configPath;
    if (!is_array($config)) {
        return $defaults;
    }

    $raw = is_array($config['discord'] ?? null) ? $config['discord'] : [];
    $roleIds = is_array($raw['staff_role_ids'] ?? null) ? $raw['staff_role_ids'] : [];

    return [
        'client_id' => auth_sanitize_config_value($raw['client_id'] ?? ''),
        'client_secret' => auth_sanitize_config_value($raw['client_secret'] ?? ''),
        'guild_id' => auth_sanitize_config_value($raw['guild_id'] ?? ''),
        'staff_role_ids' => array_values(array_filter(
            array_map(
                static fn ($id): string => auth_sanitize_config_value($id),
                $roleIds
            ),
            static fn (string $id): bool => $id !== ''
        )),
        'redirect_uri' => auth_sanitize_config_value($raw['redirect_uri'] ?? ''),
    ];
}

/**
 * Consulta is_staff en discord_users.
 */
function auth_user_is_staff_from_db(PDO $pdo, string $discordId): bool
{
    $stmt = $pdo->prepare(
        'SELECT is_staff FROM discord_users WHERE discord_id = ? LIMIT 1'
    );
    $stmt->execute([$discordId]);
    $row = $stmt->fetch(PDO::FETCH_ASSOC);
    if (!is_array($row)) {
        return false;
    }
    return (int) ($row['is_staff'] ?? 0) === 1;
}

/** Sincroniza flag is_staff en sesión si coincide el discord_id actual. */
function auth_sync_staff_session(string $discordId, bool $isStaff): void
{
    if (auth_current_discord_id() !== $discordId) {
        return;
    }
    $_SESSION['is_staff'] = $isStaff ? 1 : 0;
}

/**
 * Convierte placeholders SAMPLE_* a cadena vacía para no usar credenciales de ejemplo.
 */
function auth_sanitize_config_value(mixed $value): string
{
    if (!is_string($value)) {
        return '';
    }
    if ($value === '' || str_starts_with($value, 'SAMPLE')) {
        return '';
    }
    return $value;
}

/**
 * True si la acción aún está en cooldown para este discord_id (timestamps en sesión).
 */
function auth_action_rate_limited(
    string $action,
    string $discordId,
    int $cooldownSeconds = AUTH_ACTION_COOLDOWN_SECONDS
): bool {
    auth_start_session();
    if ($discordId === '' || $action === '') {
        return false;
    }
    $key = 'rl_' . $action . '_' . $discordId;
    $last = $_SESSION[$key] ?? null;
    if (!is_int($last) && !is_float($last) && !(is_string($last) && ctype_digit($last))) {
        return false;
    }
    $lastTs = (int) $last;
    return $lastTs > 0 && (time() - $lastTs) < $cooldownSeconds;
}

/** Registra el timestamp de la última ejecución exitosa de la acción. */
function auth_action_rate_touch(string $action, string $discordId): void
{
    auth_start_session();
    if ($discordId === '' || $action === '') {
        return;
    }
    $_SESSION['rl_' . $action . '_' . $discordId] = time();
}
