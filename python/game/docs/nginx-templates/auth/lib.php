<?php

declare(strict_types=1);

require_once __DIR__ . '/sso.php';

/** Endpoint OAuth2 de autorizacion de Discord. */
const AUTH_OAUTH_AUTHORIZE = 'https://discord.com/api/oauth2/authorize';

/** Endpoint de intercambio de codigo por tokens. */
const AUTH_OAUTH_TOKEN = 'https://discord.com/api/oauth2/token';

/** API REST de Discord (v10). */
const AUTH_API_BASE = 'https://discord.com/api/v10';

/** Scopes OAuth usados por el login. */
const AUTH_OAUTH_SCOPES = 'identify guilds.members.read';

/**
 * Carga config.php si existe; si no, config.sample.php.
 *
 * @return array{client_id: string, client_secret: string, guild_id: string, staff_role_ids: list<string>, redirect_uri: string}
 */
function auth_config(): array
{
    static $cached = null;
    if (is_array($cached)) {
        return $cached;
    }

    $path = __DIR__ . '/config.php';
    if (!is_file($path)) {
        $path = __DIR__ . '/config.sample.php';
    }

    $loaded = require $path;
    if (!is_array($loaded)) {
        throw new RuntimeException('Config auth invalida.');
    }

    $cached = auth_normalize_config($loaded);
    return $cached;
}

/**
 * Normaliza claves de config a strings y lista de roles staff.
 *
 * @param array<string, mixed> $loaded
 * @return array{client_id: string, client_secret: string, guild_id: string, staff_role_ids: list<string>, redirect_uri: string}
 */
function auth_normalize_config(array $loaded): array
{
    $staffRoleIds = [];
    $rawRoles = $loaded['staff_role_ids'] ?? [];
    if (is_array($rawRoles)) {
        foreach ($rawRoles as $roleId) {
            if (is_string($roleId) || is_int($roleId)) {
                $id = (string) $roleId;
                if ($id !== '') {
                    $staffRoleIds[] = $id;
                }
            }
        }
    }

    return [
        'client_id' => (string) ($loaded['client_id'] ?? ''),
        'client_secret' => (string) ($loaded['client_secret'] ?? ''),
        'guild_id' => (string) ($loaded['guild_id'] ?? ''),
        'staff_role_ids' => $staffRoleIds,
        'redirect_uri' => (string) ($loaded['redirect_uri'] ?? ''),
    ];
}

/**
 * Marca la respuesta como no indexable (auth / privadas).
 */
function auth_send_noindex(): void
{
    if (!headers_sent()) {
        header('X-Robots-Tag: noindex, nofollow');
    }
}

/**
 * Pagina HTML de aviso con estilo LATAMFILES.
 *
 * @param list<array{href: string, label: string, primary?: bool}> $actions
 */
function auth_render_notice_page(
    string $title,
    string $heading,
    string $lead,
    string $detail,
    array $actions,
    int $status = 403
): void {
    http_response_code($status);
    header('Content-Type: text/html; charset=utf-8');
    auth_send_noindex();

    $cssV = (string) @filemtime(dirname(__DIR__) . '/assets/css/site.css');
    $logoV = (string) @filemtime(dirname(__DIR__) . '/assets/img/latamfiles-logo.png');
    $e = static function (string $s): string {
        return htmlspecialchars($s, ENT_QUOTES, 'UTF-8');
    };

    $actionsHtml = '';
    foreach ($actions as $action) {
        $href = (string) ($action['href'] ?? '#');
        $label = (string) ($action['label'] ?? '');
        $primary = !empty($action['primary']);
        $class = $primary ? 'auth-notice__btn auth-notice__btn--primary' : 'auth-notice__btn';
        $actionsHtml .= '<a class="' . $e($class) . '" href="' . $e($href) . '">' . $e($label) . '</a>';
    }

    echo '<!DOCTYPE html>' . "\n";
    echo '<html lang="es">' . "\n";
    echo '<head>' . "\n";
    echo '  <meta charset="utf-8">' . "\n";
    echo '  <meta name="viewport" content="width=device-width, initial-scale=1">' . "\n";
    echo '  <meta name="robots" content="noindex,nofollow">' . "\n";
    echo '  <title>' . $e($title) . '</title>' . "\n";
    echo '  <link rel="icon" href="/assets/img/favicon.png" type="image/png">' . "\n";
    echo '  <link rel="preconnect" href="https://fonts.googleapis.com">' . "\n";
    echo '  <link rel="preconnect" href="https://fonts.gstatic.com" crossorigin>' . "\n";
    echo '  <link href="https://fonts.googleapis.com/css2?family=Rajdhani:wght@500;600;700&display=swap" rel="stylesheet">' . "\n";
    echo '  <link rel="stylesheet" href="/assets/css/site.css?v=' . $e($cssV !== '' ? $cssV : '1') . '">' . "\n";
    echo '</head>' . "\n";
    echo '<body>' . "\n";
    echo '  <header class="latam-site-header" role="banner">' . "\n";
    echo '    <div class="latam-site-header__inner">' . "\n";
    echo '      <a class="latam-site-brand" href="/" aria-label="LATAMFILES - Inicio">' . "\n";
    echo '        <img class="latam-site-brand__logo" src="/assets/img/latamfiles-logo.png?v=' . $e($logoV !== '' ? $logoV : '1') . '" alt="LATAMFILES" width="625" height="91">' . "\n";
    echo '      </a>' . "\n";
    echo '    </div>' . "\n";
    echo '  </header>' . "\n";
    echo '  <main class="latam-main auth-notice">' . "\n";
    echo '    <div class="auth-notice__card">' . "\n";
    echo '      <p class="auth-notice__eyebrow">LATAMFILES</p>' . "\n";
    echo '      <h1 class="auth-notice__title">' . $e($heading) . '</h1>' . "\n";
    echo '      <p class="auth-notice__lead">' . $e($lead) . '</p>' . "\n";
    echo '      <p class="auth-notice__detail">' . $e($detail) . '</p>' . "\n";
    echo '      <div class="auth-notice__actions">' . $actionsHtml . '</div>' . "\n";
    echo '    </div>' . "\n";
    echo '  </main>' . "\n";
    latam_render_footer();
    echo '</body>' . "\n";
    echo '</html>';
    exit;
}

/**
 * Inicia sesion PHP con cookie HttpOnly, Secure (si HTTPS) y SameSite=Lax.
 */
function auth_start_session(): void
{
    if (session_status() !== PHP_SESSION_ACTIVE) {
        if (!headers_sent()) {
            if (session_status() === PHP_SESSION_NONE) {
                session_name('latamfiles_sess');
            }
            session_set_cookie_params([
                'lifetime' => 0,
                'path' => '/',
                'domain' => '.latamsquad.org',
                'secure' => (!empty($_SERVER['HTTPS']) && $_SERVER['HTTPS'] !== 'off'),
                'httponly' => true,
                'samesite' => 'Lax',
            ]);
            session_start();
        } elseif (session_status() !== PHP_SESSION_ACTIVE) {
            return;
        }
    }
    if (session_status() === PHP_SESSION_ACTIVE) {
        latamsquad_sso_files_bootstrap_session();
    }
}

/**
 * Discord ID del usuario logueado, o null si no hay sesion.
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
 * Nombre visible (global_name o username) o null si no hay sesion.
 */
function auth_display_name(): ?string
{
    auth_start_session();
    if (session_status() !== PHP_SESSION_ACTIVE) {
        return null;
    }
    $global = $_SESSION['global_name'] ?? '';
    if (is_string($global) && trim($global) !== '') {
        return trim($global);
    }
    $username = $_SESSION['username'] ?? '';
    if (is_string($username) && trim($username) !== '') {
        return trim($username);
    }
    return null;
}

/**
 * URL del avatar Discord (CDN) o null si no hay sesion.
 * Si no hay hash de avatar, usa el avatar por defecto del snowflake.
 */
function auth_avatar_url(int $size = 64): ?string
{
    $id = auth_current_discord_id();
    if ($id === null) {
        return null;
    }
    $size = max(16, min(512, $size));
    // Solo potencias de 2 tipicas del CDN
    if (($size & ($size - 1)) !== 0) {
        $size = 64;
    }
    auth_start_session();
    $avatar = $_SESSION['avatar'] ?? '';
    if (is_string($avatar) && $avatar !== '' && preg_match('/^[a-fA-F0-9_]+$/', $avatar) === 1) {
        $ext = (strpos($avatar, 'a_') === 0) ? 'gif' : 'png';
        return 'https://cdn.discordapp.com/avatars/' . rawurlencode($id) . '/'
            . rawurlencode($avatar) . '.' . $ext . '?size=' . $size;
    }
    // Default avatar: (user_id >> 22) % 6 (sistema sin discriminator)
    $idx = 0;
    if (PHP_INT_SIZE >= 8 && ctype_digit($id)) {
        $idx = (int) ((((int) $id) >> 22) % 6);
        if ($idx < 0) {
            $idx = 0;
        }
    }
    return 'https://cdn.discordapp.com/embed/avatars/' . $idx . '.png';
}

/**
 * HTML del chip de cuenta en la nav: avatar + nombre.
 * Si $href no es null, envuelve en <a>; si no, en <span>.
 */
function auth_account_chip_html(string $name, ?string $href = null): string
{
    $name = trim($name);
    if ($name === '') {
        $name = 'Usuario';
    }
    $avatarUrl = auth_avatar_url(64);
    $img = '';
    if ($avatarUrl !== null) {
        $img = '<img class="latam-site-header__avatar" src="'
            . htmlspecialchars($avatarUrl, ENT_QUOTES, 'UTF-8')
            . '" alt="" width="28" height="28" decoding="async" referrerpolicy="no-referrer">';
    }
    $label = '<span class="latam-site-header__user-name">'
        . htmlspecialchars($name, ENT_QUOTES, 'UTF-8') . '</span>';
    $inner = $img . $label;
    if ($href !== null && $href !== '') {
        return '<a class="latam-site-header__user" href="'
            . htmlspecialchars($href, ENT_QUOTES, 'UTF-8')
            . '" title="Panel de administracion">' . $inner . '</a>';
    }
    return '<span class="latam-site-header__user">' . $inner . '</span>';
}

/** URL publica LATAMSQUAD (footer). */
const LATAM_WEB_URL = 'https://latamsquad.org';

/** Invitacion Discord LATAMSQUAD (footer / nav). */
const LATAM_DISCORD_URL = 'https://discord.gg/latamsquad';

/**
 * Pie de pagina LATAMFILES (mismo patron que stats.latamsquad.org).
 *
 * @param array{pr_nav?: bool} $options pr_nav=true agrega enlaces del area PR
 */
function latam_render_footer(array $options = []): void
{
    $year = (int) date('Y');
    $prNav = !empty($options['pr_nav']);
    $e = static function (string $s): string {
        return htmlspecialchars($s, ENT_QUOTES, 'UTF-8');
    };
    ?>
<footer class="site-footer">
  <div class="site-footer__inner">
    <p class="site-footer__copy">
      &copy; 2021 - <?= $year ?>
      <a href="<?= $e(LATAM_WEB_URL) ?>" target="_blank" rel="noopener noreferrer">LATAMSQUAD</a>
    </p>
    <p class="site-footer__links">
      <a href="/">Juegos</a>
      <?php if ($prNav): ?>
      <span aria-hidden="true">&middot;</span>
      <a href="/pr.php">Inicio</a>
      <span aria-hidden="true">&middot;</span>
      <a href="/pr/tracker/?srv=1">Tracker</a>
      <span aria-hidden="true">&middot;</span>
      <a href="/pr/logs/">Logs</a>
      <?php endif; ?>
      <span aria-hidden="true">&middot;</span>
      <a href="<?= $e(LATAM_DISCORD_URL) ?>" target="_blank" rel="noopener noreferrer">Discord</a>
    </p>
  </div>
</footer>
    <?php
}

/**
 * True si la sesion actual tiene flag is_staff.
 */
function auth_is_staff(): bool
{
    auth_start_session();
    if (session_status() !== PHP_SESSION_ACTIVE) {
        return false;
    }
    return !empty($_SESSION['is_staff']);
}

/**
 * Registra usuario Discord en sesion tras login OAuth.
 *
 * @param array<string, mixed> $user
 */
function auth_login_user(array $user, bool $isStaff): void
{
    auth_start_session();
    if (!headers_sent()) {
        session_regenerate_id(true);
    }
    $_SESSION['discord_id'] = (string) ($user['id'] ?? '');
    $_SESSION['sso_login_at'] = time();
    latamsquad_sso_set_cookie((string) ($_SESSION['discord_id'] ?? ''));
    $_SESSION['username'] = (string) ($user['username'] ?? '');
    $_SESSION['global_name'] = (string) ($user['global_name'] ?? '');
    // Hash de avatar Discord (null/vacio = usar default del CDN)
    $avatar = $user['avatar'] ?? '';
    $_SESSION['avatar'] = is_string($avatar) ? $avatar : '';
    $_SESSION['is_staff'] = $isStaff;
}

/** Cierra sesion y elimina la cookie de sesion. */
function auth_logout(): void
{
    latamsquad_sso_clear_cookie();
    latamsquad_sso_mark_logout();
    latamsquad_sso_clear_peer_session_cookies();
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
 * URL de authorize OAuth usando la config del sitio.
 */
function discord_authorize_url(string $state): string
{
    $cfg = auth_config();
    if ($cfg['client_id'] === '' || $cfg['redirect_uri'] === '') {
        return '';
    }

    $query = http_build_query([
        'client_id' => $cfg['client_id'],
        'redirect_uri' => $cfg['redirect_uri'],
        'response_type' => 'code',
        'scope' => AUTH_OAUTH_SCOPES,
        'state' => $state,
    ], '', '&', PHP_QUERY_RFC3986);

    return AUTH_OAUTH_AUTHORIZE . '?' . $query;
}

/**
 * Intercambia el code OAuth por tokens.
 *
 * @return array<string, mixed>
 */
function discord_exchange_code(string $code): array
{
    $cfg = auth_config();
    auth_assert_oauth_ready($cfg);

    $body = http_build_query([
        'client_id' => $cfg['client_id'],
        'client_secret' => $cfg['client_secret'],
        'grant_type' => 'authorization_code',
        'code' => $code,
        'redirect_uri' => $cfg['redirect_uri'],
    ]);

    $response = discord_http_request('POST', AUTH_OAUTH_TOKEN, [
        'Content-Type: application/x-www-form-urlencoded',
    ], $body);

    if ($response['status'] < 200 || $response['status'] >= 300) {
        throw new RuntimeException('No se pudo intercambiar el codigo OAuth con Discord.');
    }

    $data = json_decode($response['body'], true);
    if (!is_array($data) || empty($data['access_token'])) {
        throw new RuntimeException('Respuesta de tokens Discord invalida.');
    }

    return $data;
}

/**
 * Obtiene el usuario Discord autenticado (@me).
 *
 * @return array<string, mixed>
 */
function discord_fetch_user(string $accessToken): array
{
    $response = discord_http_request('GET', AUTH_API_BASE . '/users/@me', [
        'Authorization: Bearer ' . $accessToken,
    ]);

    if ($response['status'] < 200 || $response['status'] >= 300) {
        throw new RuntimeException('No se pudo obtener el usuario Discord.');
    }

    $data = json_decode($response['body'], true);
    if (!is_array($data) || empty($data['id'])) {
        throw new RuntimeException('Respuesta de usuario Discord invalida.');
    }

    return $data;
}

/**
 * Consulta el miembro del guild del usuario autenticado.
 *
 * @return array{status: int, body: ?array<string, mixed>}
 */
function discord_fetch_guild_member(string $accessToken, string $guildId): array
{
    if ($accessToken === '' || $guildId === '') {
        return ['status' => 0, 'body' => null];
    }

    $url = AUTH_API_BASE . '/users/@me/guilds/' . rawurlencode($guildId) . '/member';
    $response = discord_http_request('GET', $url, [
        'Authorization: Bearer ' . $accessToken,
    ]);

    $status = (int) $response['status'];
    if ($status < 200 || $status >= 300) {
        return ['status' => $status, 'body' => null];
    }

    $data = json_decode($response['body'], true);
    return [
        'status' => $status,
        'body' => is_array($data) ? $data : null,
    ];
}

/**
 * True si el miembro tiene alguno de los roles staff configurados.
 *
 * @param array<string, mixed>|null $member
 * @param list<string> $staffRoleIds
 */
function discord_member_has_staff_role(?array $member, array $staffRoleIds): bool
{
    if ($member === null || $staffRoleIds === []) {
        return false;
    }

    $roles = $member['roles'] ?? null;
    if (!is_array($roles)) {
        return false;
    }

    $memberRoles = [];
    foreach ($roles as $role) {
        if (is_string($role) || is_int($role)) {
            $memberRoles[] = (string) $role;
        }
    }

    foreach ($staffRoleIds as $staffRoleId) {
        if ($staffRoleId !== '' && in_array((string) $staffRoleId, $memberRoles, true)) {
            return true;
        }
    }

    return false;
}

/**
 * Peticion HTTP a Discord via curl (timeout 15s).
 *
 * @param list<string> $headers
 * @return array{status: int, body: string}
 */
function discord_http_request(string $method, string $url, array $headers = [], ?string $body = null): array
{
    if (!function_exists('curl_init')) {
        return ['status' => 0, 'body' => ''];
    }

    $ch = curl_init($url);
    if ($ch === false) {
        return ['status' => 0, 'body' => ''];
    }

    $opts = [
        CURLOPT_RETURNTRANSFER => true,
        CURLOPT_CUSTOMREQUEST => strtoupper($method),
        CURLOPT_HTTPHEADER => $headers,
        CURLOPT_TIMEOUT => 15,
        CURLOPT_CONNECTTIMEOUT => 10,
    ];
    if ($body !== null) {
        $opts[CURLOPT_POSTFIELDS] = $body;
    }
    curl_setopt_array($ch, $opts);

    $responseBody = curl_exec($ch);
    $status = (int) curl_getinfo($ch, CURLINFO_HTTP_CODE);
    curl_close($ch);

    return [
        'status' => $status,
        'body' => is_string($responseBody) ? $responseBody : '',
    ];
}

/**
 * @param array{client_id: string, client_secret: string, guild_id: string, staff_role_ids: list<string>, redirect_uri: string} $cfg
 */
function auth_assert_oauth_ready(array $cfg): void
{
    if ($cfg['client_id'] === '' || $cfg['client_secret'] === '' || $cfg['redirect_uri'] === '') {
        throw new RuntimeException('Discord OAuth no esta configurado.');
    }
}
