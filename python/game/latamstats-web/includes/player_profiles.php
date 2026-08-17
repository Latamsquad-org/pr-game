<?php

declare(strict_types=1);

/** Tamaño máximo de banner: 1.5 MB. */
const PROFILE_BANNER_MAX_BYTES = 1572864;

/** Claves de redes permitidas en socials JSON. */
const PROFILE_SOCIAL_KEYS = ['x', 'youtube', 'twitch', 'instagram'];

/**
 * Obtiene el perfil de un jugador en un servidor, o null si no existe.
 *
 * @return array<string, mixed>|null
 */
function profile_get(PDO $pdo, string $playerId, string $serverId): ?array
{
    $stmt = $pdo->prepare(
        'SELECT player_id, server_id, bio, banner_path, show_discord, socials, updated_at
         FROM player_profiles
         WHERE player_id = ? AND server_id = ?
         LIMIT 1'
    );
    $stmt->execute([$playerId, $serverId]);
    $row = $stmt->fetch(PDO::FETCH_ASSOC);
    if (!is_array($row)) {
        return null;
    }

    // socials puede venir como JSON string desde MySQL.
    $socials = $row['socials'] ?? null;
    if (is_string($socials) && $socials !== '') {
        $decoded = json_decode($socials, true);
        $row['socials'] = is_array($decoded) ? profile_sanitize_socials($decoded) : [];
    } elseif (!is_array($socials)) {
        $row['socials'] = [];
    } else {
        $row['socials'] = profile_sanitize_socials($socials);
    }

    $row['show_discord'] = (int) ($row['show_discord'] ?? 1) === 1 ? 1 : 0;
    return $row;
}

/**
 * Inserta o actualiza campos de perfil (bio, banner, show_discord, socials).
 *
 * @param array<string, mixed> $fields
 */
function profile_save(PDO $pdo, string $playerId, string $serverId, array $fields): void
{
    $existing = profile_get($pdo, $playerId, $serverId);

    $bio = array_key_exists('bio', $fields)
        ? profile_sanitize_bio((string) $fields['bio'])
        : (string) ($existing['bio'] ?? '');

    $bannerPath = array_key_exists('banner_path', $fields)
        ? (string) $fields['banner_path']
        : (string) ($existing['banner_path'] ?? '');

    // Solo paths relativos bajo uploads/banners (nunca URL externa).
    if ($bannerPath !== '' && !preg_match('#^assets/uploads/banners/[A-Za-z0-9._-]+$#', $bannerPath)) {
        $bannerPath = (string) ($existing['banner_path'] ?? '');
    }

    $showDiscord = array_key_exists('show_discord', $fields)
        ? ((int) $fields['show_discord'] === 1 ? 1 : 0)
        : (int) ($existing['show_discord'] ?? 1);

    $socialsIn = array_key_exists('socials', $fields) && is_array($fields['socials'])
        ? $fields['socials']
        : (is_array($existing['socials'] ?? null) ? $existing['socials'] : []);
    $socials = profile_sanitize_socials($socialsIn);
    $socialsJson = json_encode($socials, JSON_UNESCAPED_SLASHES);
    if ($socialsJson === false) {
        $socialsJson = '{}';
    }

    $stmt = $pdo->prepare(
        'INSERT INTO player_profiles (player_id, server_id, bio, banner_path, show_discord, socials)
         VALUES (?, ?, ?, ?, ?, ?)
         ON DUPLICATE KEY UPDATE
            bio = VALUES(bio),
            banner_path = VALUES(banner_path),
            show_discord = VALUES(show_discord),
            socials = VALUES(socials)'
    );
    $stmt->execute([$playerId, $serverId, $bio, $bannerPath, $showDiscord, $socialsJson]);
}

/**
 * Bio pública: trim, sin HTML, máximo 500 caracteres.
 */
function profile_sanitize_bio(string $bio): string
{
    $clean = trim(strip_tags($bio));
    if (function_exists('mb_substr')) {
        return mb_substr($clean, 0, 500, 'UTF-8');
    }
    return substr($clean, 0, 500);
}

/**
 * Filtra redes a whitelist; solo URLs http(s) válidas (o vacío).
 *
 * @param array<string, mixed> $input
 * @return array<string, string>
 */
function profile_sanitize_socials(array $input): array
{
    $out = [];
    foreach (PROFILE_SOCIAL_KEYS as $key) {
        if (!array_key_exists($key, $input)) {
            continue;
        }
        $raw = trim((string) $input[$key]);
        if ($raw === '') {
            $out[$key] = '';
            continue;
        }
        if (filter_var($raw, FILTER_VALIDATE_URL) === false) {
            $out[$key] = '';
            continue;
        }
        $scheme = strtolower((string) (parse_url($raw, PHP_URL_SCHEME) ?? ''));
        $out[$key] = ($scheme === 'http' || $scheme === 'https') ? $raw : '';
    }
    return $out;
}

/**
 * URL CDN del avatar Discord (o default si no hay hash).
 */
function profile_discord_avatar_url(string $discordId, string $avatarHash, int $size = 128): string
{
    $size = max(16, min(4096, $size));
    $hash = trim($avatarHash);
    if ($hash === '') {
        // Avatar por defecto según snowflake (usuarios sin avatar custom).
        $index = 0;
        if (ctype_digit($discordId)) {
            $index = (int) ((int) substr($discordId, -2) % 6);
        }
        return 'https://cdn.discordapp.com/embed/avatars/' . $index . '.png?size=' . $size;
    }

    $ext = str_starts_with($hash, 'a_') ? 'gif' : 'png';
    return 'https://cdn.discordapp.com/avatars/'
        . rawurlencode($discordId) . '/'
        . rawurlencode($hash) . '.' . $ext
        . '?size=' . $size;
}

/**
 * Guarda un banner subido (JPEG/PNG/WebP ≤ 1.5 MB) con nombre no predecible.
 * Retorna path relativo desde la raíz web (assets/uploads/banners/...).
 *
 * @param array<string, mixed> $file Entrada estilo $_FILES['banner']
 */
function profile_store_banner(array $file): string
{
    $error = (int) ($file['error'] ?? UPLOAD_ERR_NO_FILE);
    if ($error !== UPLOAD_ERR_OK) {
        throw new RuntimeException('No se pudo subir el banner.');
    }

    $size = (int) ($file['size'] ?? 0);
    if ($size <= 0 || $size > PROFILE_BANNER_MAX_BYTES) {
        throw new RuntimeException('El banner debe pesar como máximo 1.5 MB.');
    }

    $tmp = (string) ($file['tmp_name'] ?? '');
    // is_uploaded_file en HTTP; en CLI/smokes permitir archivo temporal real.
    $tmpOk = $tmp !== '' && (is_uploaded_file($tmp) || (PHP_SAPI === 'cli' && is_file($tmp)));
    if (!$tmpOk) {
        throw new RuntimeException('Archivo temporal de banner inválido.');
    }

    $finfo = new finfo(FILEINFO_MIME_TYPE);
    $mime = (string) $finfo->file($tmp);
    $map = [
        'image/jpeg' => 'jpg',
        'image/png' => 'png',
        'image/webp' => 'webp',
    ];
    if (!isset($map[$mime])) {
        throw new RuntimeException('Formato de banner no permitido (solo JPEG, PNG o WebP).');
    }

    $dir = dirname(__DIR__) . '/assets/uploads/banners';
    if (!is_dir($dir) && !mkdir($dir, 0755, true) && !is_dir($dir)) {
        throw new RuntimeException('No se pudo crear el directorio de banners.');
    }

    $name = bin2hex(random_bytes(16)) . '.' . $map[$mime];
    $dest = $dir . '/' . $name;
    $moved = is_uploaded_file($tmp) ? move_uploaded_file($tmp, $dest) : rename($tmp, $dest);
    if (!$moved) {
        throw new RuntimeException('No se pudo guardar el banner.');
    }

    return 'assets/uploads/banners/' . $name;
}
