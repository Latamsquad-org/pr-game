<?php

declare(strict_types=1);

require_once __DIR__ . '/auth.php';

/** Endpoint OAuth2 de autorización de Discord. */
const DISCORD_OAUTH_AUTHORIZE_URL = 'https://discord.com/api/oauth2/authorize';

/** Endpoint de intercambio de código por tokens. */
const DISCORD_OAUTH_TOKEN_URL = 'https://discord.com/api/oauth2/token';

/** API REST de Discord (v10). */
const DISCORD_API_BASE = 'https://discord.com/api/v10';

/** Scopes OAuth usados por el login de perfiles. */
const DISCORD_OAUTH_SCOPES = 'identify guilds.members.read';

/**
 * Construye la URL de authorize con client_id / redirect / state explícitos (útil en tests).
 */
function discord_build_authorize_url(string $clientId, string $redirectUri, string $state): string
{
    $query = http_build_query([
        'client_id' => $clientId,
        'redirect_uri' => $redirectUri,
        'response_type' => 'code',
        'scope' => DISCORD_OAUTH_SCOPES,
        'state' => $state,
    ], '', '&', PHP_QUERY_RFC3986);

    return DISCORD_OAUTH_AUTHORIZE_URL . '?' . $query;
}

/**
 * URL de authorize usando la config discord del sitio.
 * Devuelve cadena vacía si falta client_id o redirect_uri.
 */
function discord_authorize_url(string $state): string
{
    $cfg = auth_discord_config();
    if ($cfg['client_id'] === '' || $cfg['redirect_uri'] === '') {
        return '';
    }
    return discord_build_authorize_url($cfg['client_id'], $cfg['redirect_uri'], $state);
}

/**
 * Intercambia el code OAuth por tokens (access / refresh / expires_in).
 *
 * @return array<string, mixed>
 */
function discord_exchange_code(string $code): array
{
    $cfg = auth_discord_config();
    if ($cfg['client_id'] === '' || $cfg['client_secret'] === '' || $cfg['redirect_uri'] === '') {
        throw new RuntimeException('Discord OAuth no está configurado.');
    }

    $body = http_build_query([
        'client_id' => $cfg['client_id'],
        'client_secret' => $cfg['client_secret'],
        'grant_type' => 'authorization_code',
        'code' => $code,
        'redirect_uri' => $cfg['redirect_uri'],
    ]);

    $response = discord_http_request('POST', DISCORD_OAUTH_TOKEN_URL, [
        'Content-Type: application/x-www-form-urlencoded',
    ], $body);

    if ($response['status'] < 200 || $response['status'] >= 300) {
        throw new RuntimeException('No se pudo intercambiar el código OAuth con Discord.');
    }

    $data = json_decode($response['body'], true);
    if (!is_array($data) || empty($data['access_token'])) {
        throw new RuntimeException('Respuesta de tokens Discord inválida.');
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
    $response = discord_http_request('GET', DISCORD_API_BASE . '/users/@me', [
        'Authorization: Bearer ' . $accessToken,
    ]);

    if ($response['status'] < 200 || $response['status'] >= 300) {
        throw new RuntimeException('No se pudo obtener el usuario Discord.');
    }

    $data = json_decode($response['body'], true);
    if (!is_array($data) || empty($data['id'])) {
        throw new RuntimeException('Respuesta de usuario Discord inválida.');
    }

    return $data;
}

/**
 * Consulta el miembro del guild del usuario autenticado.
 * status 0 = sin token/guild o fallo de red; 404 = no está en el guild;
 * 2xx = cuerpo parseado en member; 429/5xx/otros = error transitorio.
 *
 * @return array{status: int, member: ?array<string, mixed>}
 */
function discord_fetch_guild_member(string $accessToken, string $guildId): array
{
    if ($accessToken === '' || $guildId === '') {
        return ['status' => 0, 'member' => null];
    }

    $url = DISCORD_API_BASE . '/users/@me/guilds/' . rawurlencode($guildId) . '/member';
    $response = discord_http_request('GET', $url, [
        'Authorization: Bearer ' . $accessToken,
    ]);

    $status = (int) $response['status'];
    if ($status < 200 || $status >= 300) {
        return ['status' => $status, 'member' => null];
    }

    $data = json_decode($response['body'], true);
    return [
        'status' => $status,
        'member' => is_array($data) ? $data : null,
    ];
}

/**
 * Resuelve is_staff según la respuesta HTTP del guild member.
 * Alineado con discord_revalidate_staff:
 * - 404 → is_staff false (escribir)
 * - 2xx → roles staff (escribir)
 * - 429/5xx/red/otros → conservar previousIsStaff (no escribir)
 *
 * @param array<string, mixed>|null $member
 * @param list<string> $staffRoleIds
 * @return array{is_staff: bool, write: bool}
 */
function discord_resolve_staff_flag(
    int $httpStatus,
    ?array $member,
    array $staffRoleIds,
    bool $previousIsStaff
): array {
    if ($httpStatus === 404) {
        return ['is_staff' => false, 'write' => true];
    }

    if ($httpStatus >= 200 && $httpStatus < 300) {
        return [
            'is_staff' => discord_member_has_staff_role($member, $staffRoleIds),
            'write' => true,
        ];
    }

    return ['is_staff' => $previousIsStaff, 'write' => false];
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
 * Inserta o actualiza discord_users con perfil y tokens.
 * Si $isStaff es null (error transitorio al consultar guild), no toca is_staff
 * en UPDATE; en INSERT nuevo queda 0.
 *
 * @param array<string, mixed> $user
 * @param array<string, mixed> $tokens
 */
function discord_upsert_user(PDO $pdo, array $user, array $tokens, ?bool $isStaff): void
{
    ensure_auth_schema($pdo);

    $discordId = (string) ($user['id'] ?? '');
    if ($discordId === '') {
        throw new InvalidArgumentException('Usuario Discord sin id.');
    }

    $expiresIn = isset($tokens['expires_in']) ? (int) $tokens['expires_in'] : 0;
    $expiresAt = $expiresIn > 0 ? (time() + $expiresIn) : null;

    $staffSql = $isStaff === null
        ? 'is_staff = is_staff'
        : 'is_staff = VALUES(is_staff)';

    $stmt = $pdo->prepare(
        'INSERT INTO discord_users (
            discord_id, username, global_name, avatar_hash,
            access_token, refresh_token, token_expires_at, is_staff
        ) VALUES (
            ?, ?, ?, ?, ?, ?, ?, ?
        ) ON DUPLICATE KEY UPDATE
            username = VALUES(username),
            global_name = VALUES(global_name),
            avatar_hash = VALUES(avatar_hash),
            access_token = VALUES(access_token),
            refresh_token = VALUES(refresh_token),
            token_expires_at = VALUES(token_expires_at),
            ' . $staffSql
    );

    $stmt->execute([
        $discordId,
        (string) ($user['username'] ?? ''),
        (string) ($user['global_name'] ?? ''),
        (string) ($user['avatar'] ?? ''),
        isset($tokens['access_token']) ? (string) $tokens['access_token'] : null,
        isset($tokens['refresh_token']) ? (string) $tokens['refresh_token'] : null,
        $expiresAt,
        $isStaff === true ? 1 : 0,
    ]);
}

/**
 * Revalida is_staff contra Discord y persiste el resultado.
 * - 2xx: calcula staff por roles y actualiza DB.
 * - 404: no está en el guild → is_staff=0.
 * - Otro error / sin token: conserva el valor en DB (fallback).
 */
function discord_revalidate_staff(PDO $pdo, string $discordId): bool
{
    ensure_auth_schema($pdo);
    $cfg = auth_discord_config();

    $stmt = $pdo->prepare(
        'SELECT access_token, is_staff FROM discord_users WHERE discord_id = ? LIMIT 1'
    );
    $stmt->execute([$discordId]);
    $row = $stmt->fetch(PDO::FETCH_ASSOC);
    if (!is_array($row)) {
        return false;
    }

    $fallback = (int) ($row['is_staff'] ?? 0) === 1;
    $accessToken = (string) ($row['access_token'] ?? '');
    if ($accessToken === '' || $cfg['guild_id'] === '') {
        return $fallback;
    }

    $fetched = discord_fetch_guild_member($accessToken, $cfg['guild_id']);
    $resolved = discord_resolve_staff_flag(
        (int) $fetched['status'],
        $fetched['member'],
        $cfg['staff_role_ids'],
        $fallback
    );

    if (!$resolved['write']) {
        return $resolved['is_staff'];
    }

    $update = $pdo->prepare('UPDATE discord_users SET is_staff = ? WHERE discord_id = ?');
    $update->execute([$resolved['is_staff'] ? 1 : 0, $discordId]);

    return $resolved['is_staff'];
}

/**
 * Petición HTTP a Discord (curl si existe; si no, file_get_contents + stream_context).
 *
 * @param list<string> $headers
 * @return array{status: int, body: string}
 */
function discord_http_request(string $method, string $url, array $headers = [], ?string $body = null): array
{
    if (function_exists('curl_init')) {
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

    $headerLines = implode("\r\n", $headers);
    $context = stream_context_create([
        'http' => [
            'method' => strtoupper($method),
            'header' => $headerLines !== '' ? $headerLines . "\r\n" : '',
            'content' => $body ?? '',
            'timeout' => 15,
            'ignore_errors' => true,
        ],
    ]);

    $responseBody = @file_get_contents($url, false, $context);
    $status = 0;
    if (isset($http_response_header[0]) && is_string($http_response_header[0])) {
        if (preg_match('/\s(\d{3})\s/', $http_response_header[0], $m)) {
            $status = (int) $m[1];
        }
    }

    return [
        'status' => $status,
        'body' => is_string($responseBody) ? $responseBody : '',
    ];
}
