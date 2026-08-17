<?php
declare(strict_types=1);

/**
 * Extrae un código LS-XXXX del nombre del jugador (case-insensitive).
 * Retorna normalizado en mayúsculas o null si no hay coincidencia válida.
 */
function link_code_extract_from_name(string $playerName): ?string
{
    // Case-insensitive: el nombre en juego puede traer ls-xxxx.
    if (preg_match('/\bLS-([A-Za-z0-9]{4})\b/i', $playerName, $m) !== 1) {
        return null;
    }

    return 'LS-' . strtoupper($m[1]);
}

/**
 * Genera un código nuevo para el Discord dado; invalida códigos previos del mismo user.
 * TTL: 45 minutos (2700 s).
 */
function link_code_generate(PDO $pdo, string $discordId, ?int $now = null): string
{
    $now = $now ?? time();
    $expiresAt = $now + 2700;

    $delete = $pdo->prepare('DELETE FROM link_codes WHERE discord_id = ?');
    $delete->execute([$discordId]);

    $insert = $pdo->prepare(
        'INSERT INTO link_codes (code, discord_id, expires_at, created_at)
         VALUES (?, ?, ?, ?)'
    );

    // Reintentos ante colisión de PRIMARY KEY en code.
    for ($attempt = 0; $attempt < 8; $attempt++) {
        $code = 'LS-' . link_code_random_suffix(4);
        try {
            $insert->execute([$code, $discordId, $expiresAt, $now]);
            return $code;
        } catch (PDOException $e) {
            if ((string) $e->getCode() !== '23000') {
                throw $e;
            }
        }
    }

    throw new RuntimeException('No se pudo generar un código de vínculo único');
}

/**
 * Consume un código válido: crea player_links y borra el código.
 * Retorna false si el código no existe, expiró o hay conflicto de unicidad.
 */
function link_code_consume(
    PDO $pdo,
    string $code,
    string $playerId,
    string $serverId,
    ?int $now = null
): bool {
    $now = $now ?? time();
    $normalized = strtoupper(trim($code));

    if (preg_match('/^LS-[A-Z0-9]{4}$/', $normalized) !== 1) {
        return false;
    }

    $select = $pdo->prepare(
        'SELECT code, discord_id, expires_at FROM link_codes WHERE code = ? LIMIT 1'
    );
    $select->execute([$normalized]);
    $row = $select->fetch();
    if ($row === false) {
        return false;
    }

    if ((int) $row['expires_at'] < $now) {
        $pdo->prepare('DELETE FROM link_codes WHERE code = ?')->execute([$normalized]);
        return false;
    }

    try {
        $insert = $pdo->prepare(
            'INSERT INTO player_links (discord_id, player_id, server_id)
             VALUES (?, ?, ?)'
        );
        $insert->execute([(string) $row['discord_id'], $playerId, $serverId]);
    } catch (PDOException $e) {
        // Conflicto UNIQUE (discord/server o player/server ya vinculados).
        if ((string) $e->getCode() === '23000') {
            return false;
        }
        throw $e;
    }

    $pdo->prepare('DELETE FROM link_codes WHERE code = ?')->execute([$normalized]);
    return true;
}

/**
 * Recorre el payload de sync y vincula jugadores cuyo nombre lleva un código válido.
 * Retorna la cantidad de vínculos creados en esta corrida.
 *
 * @param array<int, mixed> $players
 */
function player_links_consume_from_sync(
    PDO $pdo,
    array $players,
    string $serverId,
    ?int $now = null
): int {
    $linked = 0;

    foreach ($players as $player) {
        if (!is_array($player)) {
            continue;
        }

        $playerId = trim((string) ($player['player_id'] ?? ''));
        if ($playerId === '') {
            continue;
        }

        $code = link_code_extract_from_name((string) ($player['player_name'] ?? ''));
        if ($code === null) {
            continue;
        }

        if (link_code_consume($pdo, $code, $playerId, $serverId, $now)) {
            $linked++;
        }
    }

    return $linked;
}

/**
 * Vínculo activo para un Discord en un servidor, o null.
 *
 * @return array<string, mixed>|null
 */
function player_link_for_discord(PDO $pdo, string $discordId, string $serverId): ?array
{
    $stmt = $pdo->prepare(
        'SELECT * FROM player_links WHERE discord_id = ? AND server_id = ? LIMIT 1'
    );
    $stmt->execute([$discordId, $serverId]);
    $row = $stmt->fetch();

    return $row === false ? null : $row;
}

/**
 * Vínculo activo para un player_id en un servidor, o null.
 *
 * @return array<string, mixed>|null
 */
function player_link_for_player(PDO $pdo, string $playerId, string $serverId): ?array
{
    $stmt = $pdo->prepare(
        'SELECT * FROM player_links WHERE player_id = ? AND server_id = ? LIMIT 1'
    );
    $stmt->execute([$playerId, $serverId]);
    $row = $stmt->fetch();

    return $row === false ? null : $row;
}

/**
 * Sufijo aleatorio A-Z0-9 de longitud fija.
 */
function link_code_random_suffix(int $length): string
{
    $alphabet = 'ABCDEFGHIJKLMNOPQRSTUVWXYZ0123456789';
    $max = strlen($alphabet) - 1;
    $out = '';
    for ($i = 0; $i < $length; $i++) {
        $out .= $alphabet[random_int(0, $max)];
    }

    return $out;
}
