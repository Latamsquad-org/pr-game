<?php

declare(strict_types=1);

/**
 * Upload de estadisticas Forgotten Hope 2.
 * Misma API key/payload que PR, pero solo acepta server_id fh2-1..fh2-4.
 *
 * URL recomendada: /api/upload_fh2.php
 * Alias: /fh2.php y /fh2/upload.php (segun deploy en Hostinger).
 */

header('Content-Type: application/json; charset=utf-8');

/**
 * @param array<string, mixed> $body
 */
function fh2_upload_respond(int $status, array $body): void
{
    http_response_code($status);
    echo json_encode($body, JSON_UNESCAPED_SLASHES | JSON_UNESCAPED_UNICODE);
    exit;
}

$providedApiKey = $_SERVER['HTTP_X_API_KEY'] ?? '';
if (!is_string($providedApiKey) || $providedApiKey === '') {
    fh2_upload_respond(401, ['ok' => false, 'error' => 'Unauthorized']);
}

$configPath = dirname(__DIR__) . '/config.php';
if (!is_file($configPath)) {
    fh2_upload_respond(500, ['ok' => false, 'error' => 'Server configuration unavailable']);
}

$config = require $configPath;
$configuredApiKey = is_array($config) ? ($config['api_key'] ?? '') : '';

if (
    !is_string($configuredApiKey)
    || $configuredApiKey === ''
    || !hash_equals($configuredApiKey, $providedApiKey)
) {
    fh2_upload_respond(401, ['ok' => false, 'error' => 'Unauthorized']);
}

$rawBody = file_get_contents('php://input');
$payload = json_decode($rawBody === false ? '' : $rawBody, true);

if (
    json_last_error() !== JSON_ERROR_NONE
    || !is_array($payload)
    || !isset($payload['players'])
    || !is_array($payload['players'])
) {
    fh2_upload_respond(400, ['ok' => false, 'error' => 'Invalid payload']);
}

$serverIdRaw = isset($payload['server_id']) ? (string) $payload['server_id'] : null;

require_once dirname(__DIR__) . '/includes/db.php';
require_once dirname(__DIR__) . '/includes/servers.php';

$serverId = normalize_fh2_stats_server_id($serverIdRaw);

if (!is_fh2_stats_server_id($serverId)) {
    fh2_upload_respond(400, [
        'ok' => false,
        'error' => 'Invalid FH2 server_id (expected fh2-1..fh2-4)',
        'server_id' => $serverId,
    ]);
}

try {
    if (!isset($config['db']) || !is_array($config['db'])) {
        throw new RuntimeException('Invalid database configuration');
    }

    $pdo = createDatabaseConnection($config['db']);
    ensure_multi_server_schema($pdo);

    $hasCountry = (bool) $pdo->query("SHOW COLUMNS FROM players LIKE 'player_country'")->fetchColumn();

    if ($hasCountry) {
        $statement = $pdo->prepare(
            'INSERT INTO players (
                player_id, player_name, player_clan, player_country, score, kills, deaths, rounds, treasures,
                created, seen, server_id
            ) VALUES (
                :player_id, :player_name, :player_clan, :player_country, :score, :kills, :deaths, :rounds, :treasures,
                :created, :seen, :server_id
            )
            ON DUPLICATE KEY UPDATE
                player_name = VALUES(player_name),
                player_clan = VALUES(player_clan),
                player_country = VALUES(player_country),
                score = VALUES(score),
                kills = VALUES(kills),
                deaths = VALUES(deaths),
                rounds = VALUES(rounds),
                treasures = VALUES(treasures),
                created = VALUES(created),
                seen = VALUES(seen),
                server_id = VALUES(server_id)'
        );
    } else {
        $statement = $pdo->prepare(
            'INSERT INTO players (
                player_id, player_name, player_clan, score, kills, deaths, rounds, treasures,
                created, seen, server_id
            ) VALUES (
                :player_id, :player_name, :player_clan, :score, :kills, :deaths, :rounds, :treasures,
                :created, :seen, :server_id
            )
            ON DUPLICATE KEY UPDATE
                player_name = VALUES(player_name),
                player_clan = VALUES(player_clan),
                score = VALUES(score),
                kills = VALUES(kills),
                deaths = VALUES(deaths),
                rounds = VALUES(rounds),
                treasures = VALUES(treasures),
                created = VALUES(created),
                seen = VALUES(seen),
                server_id = VALUES(server_id)'
        );
    }

    $pdo->beginTransaction();

    foreach ($payload['players'] as $player) {
        if (
            !is_array($player)
            || !isset($player['player_id'])
            || trim((string) $player['player_id']) === ''
        ) {
            $pdo->rollBack();
            fh2_upload_respond(400, ['ok' => false, 'error' => 'Invalid player']);
        }

        $row = [
            'player_id' => (string) $player['player_id'],
            'player_name' => (string) ($player['player_name'] ?? ''),
            'player_clan' => (string) ($player['player_clan'] ?? ''),
            'score' => (int) ($player['score'] ?? 0),
            'kills' => (int) ($player['kills'] ?? 0),
            'deaths' => (int) ($player['deaths'] ?? 0),
            'rounds' => (int) ($player['rounds'] ?? 0),
            'treasures' => max(0, (int) ($player['treasures'] ?? 0)),
            'created' => isset($player['created']) ? (string) $player['created'] : null,
            'seen' => isset($player['seen']) ? (string) $player['seen'] : null,
            'server_id' => $serverId,
        ];

        if ($hasCountry) {
            $country = strtoupper(trim((string) ($player['player_country'] ?? '')));
            if (strlen($country) > 8) {
                $country = substr($country, 0, 8);
            }
            $row['player_country'] = $country;
        }

        $statement->execute($row);
    }

    // Marca de sync por servidor FH2 (misma tabla que PR, distinto server_id).
    $timestamp = isset($payload['timestamp']) ? trim((string) $payload['timestamp']) : '';
    if ($timestamp === '') {
        $timestamp = gmdate('Y-m-d\TH:i:s\Z');
    }
    $sync = $pdo->prepare(
        'INSERT INTO sync_meta (server_id, payload_timestamp) VALUES (:server_id, :payload_timestamp)
         ON DUPLICATE KEY UPDATE payload_timestamp = VALUES(payload_timestamp)'
    );
    $sync->execute([
        'server_id' => $serverId,
        'payload_timestamp' => $timestamp,
    ]);

    $pdo->commit();
} catch (Throwable $error) {
    if (isset($pdo) && $pdo instanceof PDO && $pdo->inTransaction()) {
        $pdo->rollBack();
    }

    error_log('FH2 upload failed: ' . $error->getMessage());
    fh2_upload_respond(500, ['ok' => false, 'error' => 'Upload failed']);
}

fh2_upload_respond(200, ['ok' => true, 'server_id' => $serverId]);
