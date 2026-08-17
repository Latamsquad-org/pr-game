<?php

declare(strict_types=1);

require_once __DIR__ . '/helpers.php';
require_once __DIR__ . '/player_links.php';
require_once __DIR__ . '/admin_logs.php';

/**
 * server_id canónico para permisos/descripciones globales (todos los servidores).
 * Las filas viejas por servidor siguen valiendo como respaldo de lectura.
 */
const CLAN_SERVER_GLOBAL = '*';

/**
 * Máximo de caracteres de la descripción editable del clan.
 * Referencia: la descripción más larga aceptada estéticamente (LDH, 380 chars).
 */
const CLAN_BLURB_MAX_CHARS = 380;

/** Mensaje cuando el vínculo Discord existe pero el jugador no está en el servidor. */
const CLAN_EDITOR_PLAYER_NOT_FOUND =
    'No encontramos tu jugador en este servidor. Juega una partida o verifica el vínculo.';

/** Mensaje cuando el tag del jugador no coincide con el clan solicitado. */
const CLAN_EDITOR_TAG_MISMATCH =
    'Tu clan tag no coincide con este clan. Solo miembros con el tag del clan pueden solicitar la edición.';

/**
 * ¿El Discord indicado puede editar blurb/datos del clan?
 * Vale el permiso global (*) o uno del servidor concreto (compatibilidad).
 */
function clan_editor_is_allowed(PDO $pdo, string $clanName, string $serverId, string $discordId): bool
{
    $clanName = clan_display_name($clanName);
    $stmt = $pdo->prepare(
        'SELECT clan_name FROM clan_editors
         WHERE discord_id = ?
           AND (server_id = ? OR server_id = ?)'
    );
    $stmt->execute([$discordId, CLAN_SERVER_GLOBAL, $serverId]);
    while ($row = $stmt->fetch(PDO::FETCH_ASSOC)) {
        if (!is_array($row)) {
            continue;
        }
        if (clan_tags_match((string) ($row['clan_name'] ?? ''), $clanName)) {
            return true;
        }
    }

    return false;
}

/**
 * Otorga permiso de editor de clan (global: vale en todos los servidores).
 * Idempotente si ya existe la fila global.
 */
function clan_editor_grant(
    PDO $pdo,
    string $clanName,
    string $serverId,
    string $discordId,
    string $grantedBy
): void {
    // Siempre persistimos como global; $serverId se conserva en la firma por compat.
    unset($serverId);
    $clanName = clan_db_canonical_name($pdo, 'clan_editors', $clanName);
    $stmt = $pdo->prepare(
        'INSERT INTO clan_editors (clan_name, server_id, discord_id, granted_by)
         VALUES (?, ?, ?, ?)
         ON DUPLICATE KEY UPDATE
            granted_by = VALUES(granted_by),
            granted_at = CURRENT_TIMESTAMP'
    );
    $stmt->execute([$clanName, CLAN_SERVER_GLOBAL, $discordId, $grantedBy]);

    // Auditoría: auto-solicitud vs grant desde admin.
    $selfGrant = ($grantedBy !== '' && $grantedBy === $discordId);
    stats_audit_log(
        $pdo,
        $grantedBy !== '' ? $grantedBy : $discordId,
        $selfGrant ? 'clan_editor_self_grant' : 'clan_editor_grant',
        $clanName,
        [
            'editor_discord_id' => $discordId,
            'granted_by' => $grantedBy,
        ],
        $selfGrant ? 'clans' : 'admin'
    );
}

/**
 * Auto-solicitud de editor: login Discord + vínculo PR + mismo clan tag → grant.
 * Devuelve true si quedó (o ya era) editor; string con mensaje de error si no.
 *
 * @return true|string
 */
function clan_editor_request_self(
    PDO $pdo,
    string $clanName,
    string $serverId,
    string $discordId
): true|string {
    $clanName = clan_display_name($clanName);
    if ($clanName === '' || $clanName === 'Sin clan') {
        return 'Clan inválido.';
    }

    if (clan_editor_is_allowed($pdo, $clanName, $serverId, $discordId)) {
        return true;
    }

    $link = player_link_for_discord($pdo, $discordId, $serverId);
    if ($link === null) {
        return 'Vincula tu cuenta de Project Reality en Mi perfil para solicitar la edición.';
    }

    $playerId = (string) ($link['player_id'] ?? '');
    if ($playerId === '') {
        return 'Vincula tu cuenta de Project Reality en Mi perfil para solicitar la edición.';
    }

    // Clan tag del jugador en el servidor activo.
    $stmt = $pdo->prepare(
        'SELECT player_clan FROM players
         WHERE player_id = :player_id
           AND ' . server_sql_where() . '
         LIMIT 1'
    );
    server_sql_bind($stmt);
    $stmt->bindValue(':player_id', $playerId, PDO::PARAM_STR);
    $stmt->execute();
    $playerClan = $stmt->fetchColumn();
    if ($playerClan === false) {
        return CLAN_EDITOR_PLAYER_NOT_FOUND;
    }

    $playerClanName = clan_display_name(is_string($playerClan) ? $playerClan : null);
    if (!clan_tags_match($playerClanName, $clanName)) {
        return CLAN_EDITOR_TAG_MISMATCH;
    }

    clan_editor_grant($pdo, $clanName, $serverId, $discordId, $discordId);

    return true;
}

/**
 * Nombre ya persistido en clan_editors / clan_blurbs (case-insensitive),
 * para no duplicar filas solo por capitalización ([KKCK] vs [kkck]).
 */
function clan_db_canonical_name(PDO $pdo, string $table, string $clanName): string
{
    $clanName = clan_display_name($clanName);
    if ($clanName === '' || $clanName === 'Sin clan') {
        return $clanName;
    }
    if ($table !== 'clan_editors' && $table !== 'clan_blurbs') {
        return $clanName;
    }

    try {
        $stmt = $pdo->query('SELECT DISTINCT clan_name FROM ' . $table);
        if ($stmt === false) {
            return $clanName;
        }
        while ($row = $stmt->fetch(PDO::FETCH_ASSOC)) {
            if (!is_array($row)) {
                continue;
            }
            $stored = (string) ($row['clan_name'] ?? '');
            if ($stored !== '' && clan_tags_match($stored, $clanName)) {
                return $stored;
            }
        }
    } catch (Throwable $ignored) {
        // Si falla la lectura, se usa el nombre de pantalla actual.
    }

    return $clanName;
}

/**
 * Revoca permiso de editor (global y filas legacy del mismo discord+clan).
 * Borra todas las variantes de capitalización del mismo tag.
 */
function clan_editor_revoke(PDO $pdo, string $clanName, string $serverId, string $discordId): void
{
    unset($serverId);
    $clanName = clan_display_name($clanName);
    $stmt = $pdo->prepare(
        'SELECT clan_name FROM clan_editors WHERE discord_id = ?'
    );
    $stmt->execute([$discordId]);
    $names = [];
    while ($row = $stmt->fetch(PDO::FETCH_ASSOC)) {
        if (!is_array($row)) {
            continue;
        }
        $stored = (string) ($row['clan_name'] ?? '');
        if ($stored !== '' && clan_tags_match($stored, $clanName)) {
            $names[$stored] = true;
        }
    }
    if ($names === []) {
        return;
    }
    $placeholders = implode(',', array_fill(0, count($names), '?'));
    $del = $pdo->prepare(
        "DELETE FROM clan_editors
         WHERE discord_id = ? AND clan_name IN ({$placeholders})"
    );
    $del->execute(array_merge([$discordId], array_keys($names)));

    $actor = $discordId;
    if (function_exists('auth_current_discord_id')) {
        $current = auth_current_discord_id();
        if (is_string($current) && $current !== '') {
            $actor = $current;
        }
    }
    stats_audit_log(
        $pdo,
        $actor,
        'clan_editor_revoke',
        $clanName,
        [
            'editor_discord_id' => $discordId,
            'clan_name_variants' => array_keys($names),
        ],
        'admin'
    );
}

/**
 * Lista editores del clan (unificados: un Discord aparece una sola vez).
 * Incluye filas guardadas con otra capitalización del mismo tag.
 *
 * @return list<array<string, mixed>>
 */
function clan_editors_list(PDO $pdo, string $clanName, string $serverId): array
{
    unset($serverId);
    $clanName = clan_display_name($clanName);
    // Preferir fila global si hay varias por el mismo discord_id.
    $stmt = $pdo->query(
        'SELECT clan_name, server_id, discord_id, granted_by, granted_at
         FROM clan_editors
         ORDER BY (server_id = ' . $pdo->quote(CLAN_SERVER_GLOBAL) . ') DESC,
                  granted_at ASC, discord_id ASC'
    );
    if ($stmt === false) {
        return [];
    }
    $rows = $stmt->fetchAll(PDO::FETCH_ASSOC);
    if (!is_array($rows)) {
        return [];
    }

    $seen = [];
    $out = [];
    foreach ($rows as $row) {
        if (!is_array($row)) {
            continue;
        }
        if (!clan_tags_match((string) ($row['clan_name'] ?? ''), $clanName)) {
            continue;
        }
        $id = (string) ($row['discord_id'] ?? '');
        if ($id === '' || isset($seen[$id])) {
            continue;
        }
        $seen[$id] = true;
        $out[] = $row;
    }
    return $out;
}

/**
 * Editores listos para mostrar en la ficha pública del clan.
 * Incluye nombre Discord + jugador PR vinculado (si existe).
 *
 * @return list<array{
 *   discord_id: string,
 *   discord_display: string,
 *   player_id: string|null,
 *   player_name: string|null
 * }>
 */
function clan_editors_public_display(PDO $pdo, string $clanName, string $serverId): array
{
    $editors = clan_editors_list($pdo, $clanName, $serverId);
    if ($editors === []) {
        return [];
    }

    $out = [];
    foreach ($editors as $row) {
        $discordId = (string) ($row['discord_id'] ?? '');
        if ($discordId === '') {
            continue;
        }

        $discordDisplay = $discordId;
        try {
            $du = $pdo->prepare(
                'SELECT username, global_name
                 FROM discord_users
                 WHERE discord_id = ?
                 LIMIT 1'
            );
            $du->execute([$discordId]);
            $discordRow = $du->fetch(PDO::FETCH_ASSOC);
            if (is_array($discordRow)) {
                $globalName = trim((string) ($discordRow['global_name'] ?? ''));
                $username = trim((string) ($discordRow['username'] ?? ''));
                if ($globalName !== '') {
                    $discordDisplay = $globalName;
                } elseif ($username !== '') {
                    $discordDisplay = $username;
                }
            }
        } catch (Throwable $ignored) {
            // Mantener discord_id como respaldo.
        }

        $playerId = null;
        $playerName = null;
        try {
            $link = player_link_for_discord($pdo, $discordId, $serverId);
            if (is_array($link)) {
                $pid = trim((string) ($link['player_id'] ?? ''));
                if ($pid !== '') {
                    $playerId = $pid;
                    // Preferir nombre en el servidor activo; si no, cualquier fila.
                    $pn = $pdo->prepare(
                        'SELECT player_name
                         FROM players
                         WHERE player_id = ?
                         ORDER BY (server_id = ?) DESC, seen DESC
                         LIMIT 1'
                    );
                    $pn->execute([$pid, $serverId]);
                    $nameRow = $pn->fetch(PDO::FETCH_ASSOC);
                    if (is_array($nameRow)) {
                        $name = trim((string) ($nameRow['player_name'] ?? ''));
                        $playerName = $name !== '' ? $name : null;
                    }
                }
            }
        } catch (Throwable $ignored) {
            // Sin vínculo: se muestra "Sin vincular".
        }

        $out[] = [
            'discord_id' => $discordId,
            'discord_display' => $discordDisplay,
            'player_id' => $playerId,
            'player_name' => $playerName,
        ];
    }

    return $out;
}

/**
 * Descripción editable del clan: primero global, luego fila del servidor.
 */
function clan_blurb_db_get(PDO $pdo, string $clanName, string $serverId): ?string
{
    $clanName = clan_db_canonical_name($pdo, 'clan_blurbs', $clanName);
    $stmt = $pdo->prepare(
        'SELECT description FROM clan_blurbs
         WHERE clan_name = ?
           AND (server_id = ? OR server_id = ?)
         ORDER BY (server_id = ?) DESC
         LIMIT 1'
    );
    // Preferir * sobre el server concreto.
    $stmt->execute([$clanName, CLAN_SERVER_GLOBAL, $serverId, CLAN_SERVER_GLOBAL]);
    $value = $stmt->fetchColumn();
    if ($value === false || $value === null) {
        return null;
    }
    return (string) $value;
}

/**
 * Normaliza URL de Discord del clan.
 * Cadena vacía = sin botón. Solo http(s) en dominios Discord.
 * Lanza RuntimeException si el valor no es vacío y es inválido.
 */
function clan_sanitize_discord_url(string $raw): string
{
    $raw = trim(strip_tags($raw));
    if ($raw === '') {
        return '';
    }

    // Completar esquema si el editor escribió "discord.gg/xxx".
    if (!preg_match('#^[a-z][a-z0-9+.-]*://#i', $raw)) {
        $raw = 'https://' . ltrim($raw, '/');
    }

    if (filter_var($raw, FILTER_VALIDATE_URL) === false) {
        throw new RuntimeException('El enlace de Discord no es una URL válida.');
    }

    $scheme = strtolower((string) (parse_url($raw, PHP_URL_SCHEME) ?? ''));
    $host = strtolower((string) (parse_url($raw, PHP_URL_HOST) ?? ''));
    if ($scheme !== 'http' && $scheme !== 'https') {
        throw new RuntimeException('El enlace de Discord debe ser http o https.');
    }

    $allowed = ['discord.gg', 'discord.com', 'www.discord.com', 'discordapp.com', 'www.discordapp.com'];
    if (!in_array($host, $allowed, true)) {
        throw new RuntimeException('Solo se permiten enlaces de Discord (discord.gg / discord.com).');
    }

    return $raw;
}

/**
 * Guarda (upsert) la descripción editable del clan de forma global.
 * $discordUrl = null deja el enlace Discord sin tocar (compat. saves solo-descripción).
 * $discordUrl = '' borra el botón; URL válida lo reemplaza.
 */
function clan_blurb_db_save(
    PDO $pdo,
    string $clanName,
    string $serverId,
    string $description,
    string $discordId,
    ?string $discordUrl = null
): void {
    unset($serverId);
    $clanName = clan_db_canonical_name($pdo, 'clan_blurbs', $clanName);
    // Sin HTML; trim.
    $clean = trim(strip_tags($description));

    // Tope de largo también en servidor: el maxlength del form se puede forjar.
    $len = function_exists('mb_strlen') ? mb_strlen($clean, 'UTF-8') : strlen($clean);
    if ($len > CLAN_BLURB_MAX_CHARS) {
        throw new RuntimeException(
            'La descripción supera el máximo de ' . CLAN_BLURB_MAX_CHARS
            . " caracteres (tiene {$len})."
        );
    }

    // Snapshot previo para el log de auditoría.
    $beforeDesc = null;
    $beforeDiscord = null;
    try {
        $prev = $pdo->prepare(
            'SELECT description, discord_url FROM clan_blurbs
             WHERE clan_name = ? AND server_id = ?
             LIMIT 1'
        );
        $prev->execute([$clanName, CLAN_SERVER_GLOBAL]);
        $prevRow = $prev->fetch(PDO::FETCH_ASSOC);
        if (is_array($prevRow)) {
            $beforeDesc = (string) ($prevRow['description'] ?? '');
            $beforeDiscord = array_key_exists('discord_url', $prevRow)
                ? ($prevRow['discord_url'] === null ? null : (string) $prevRow['discord_url'])
                : null;
        }
    } catch (Throwable $ignored) {
        // Continuar el save aunque falle la lectura previa.
    }

    if ($discordUrl === null) {
        $stmt = $pdo->prepare(
            'INSERT INTO clan_blurbs (clan_name, server_id, description, updated_by_discord_id)
             VALUES (?, ?, ?, ?)
             ON DUPLICATE KEY UPDATE
                description = VALUES(description),
                updated_by_discord_id = VALUES(updated_by_discord_id)'
        );
        $stmt->execute([$clanName, CLAN_SERVER_GLOBAL, $clean, $discordId]);
        stats_audit_log(
            $pdo,
            $discordId,
            'clan_save_blurb',
            $clanName,
            [
                'before_description' => $beforeDesc,
                'after_description' => $clean,
                'discord_changed' => false,
            ],
            'clans'
        );
        return;
    }

    $safeDiscord = clan_sanitize_discord_url($discordUrl);
    $stmt = $pdo->prepare(
        'INSERT INTO clan_blurbs (clan_name, server_id, description, discord_url, updated_by_discord_id)
         VALUES (?, ?, ?, ?, ?)
         ON DUPLICATE KEY UPDATE
            description = VALUES(description),
            discord_url = VALUES(discord_url),
            updated_by_discord_id = VALUES(updated_by_discord_id)'
    );
    $stmt->execute([$clanName, CLAN_SERVER_GLOBAL, $clean, $safeDiscord, $discordId]);
    stats_audit_log(
        $pdo,
        $discordId,
        'clan_save_blurb',
        $clanName,
        [
            'before_description' => $beforeDesc,
            'after_description' => $clean,
            'before_discord_url' => $beforeDiscord,
            'after_discord_url' => $safeDiscord,
            'discord_changed' => true,
        ],
        'clans'
    );
}

/**
 * Discord editable: null = no editado en DB; string (posible '') = valor del editor.
 */
function clan_discord_db_get(PDO $pdo, string $clanName, string $serverId): ?string
{
    $clanName = clan_db_canonical_name($pdo, 'clan_blurbs', $clanName);
    $stmt = $pdo->prepare(
        'SELECT discord_url FROM clan_blurbs
         WHERE clan_name = ?
           AND (server_id = ? OR server_id = ?)
         ORDER BY (server_id = ?) DESC
         LIMIT 1'
    );
    $stmt->execute([$clanName, CLAN_SERVER_GLOBAL, $serverId, CLAN_SERVER_GLOBAL]);
    $row = $stmt->fetch(PDO::FETCH_ASSOC);
    if (!is_array($row) || !array_key_exists('discord_url', $row)) {
        return null;
    }
    if ($row['discord_url'] === null) {
        return null;
    }
    return (string) $row['discord_url'];
}

/**
 * Discord público: si el editor ya lo tocó (incl. vacío), manda eso;
 * si no, cae al estático de clans_info.php.
 */
function clan_discord_public(PDO $pdo, string $clanName, string $serverId): string
{
    $fromDb = clan_discord_db_get($pdo, $clanName, $serverId);
    if ($fromDb !== null) {
        return $fromDb;
    }
    return clan_discord_url($clanName);
}

/**
 * Blurb público: preferir fila DB; si no hay, caer al estático clan_blurb().
 */
function clan_blurb_public(PDO $pdo, string $clanName, string $serverId): string
{
    $fromDb = clan_blurb_db_get($pdo, $clanName, $serverId);
    if ($fromDb !== null && $fromDb !== '') {
        return $fromDb;
    }
    return clan_blurb($clanName);
}
