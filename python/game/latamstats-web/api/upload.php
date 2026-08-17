<?php

declare(strict_types=1);

header('Content-Type: application/json; charset=utf-8');

/**
 * Finaliza la petición con una respuesta JSON consistente.
 *
 * @param array<string, mixed> $body
 */
function respond(int $status, array $body): void
{
    http_response_code($status);
    echo json_encode($body, JSON_UNESCAPED_SLASHES | JSON_UNESCAPED_UNICODE);
    exit;
}

// Se rechaza primero una petición sin clave, incluso si MySQL no está disponible.
$providedApiKey = $_SERVER['HTTP_X_API_KEY'] ?? '';
if (!is_string($providedApiKey) || $providedApiKey === '') {
    respond(401, ['ok' => false, 'error' => 'Unauthorized']);
}

$configPath = dirname(__DIR__) . '/config.php';
if (!is_file($configPath)) {
    respond(500, ['ok' => false, 'error' => 'Server configuration unavailable']);
}

$config = require $configPath;
$configuredApiKey = is_array($config) ? ($config['api_key'] ?? '') : '';

if (
    !is_string($configuredApiKey)
    || $configuredApiKey === ''
    || !hash_equals($configuredApiKey, $providedApiKey)
) {
    respond(401, ['ok' => false, 'error' => 'Unauthorized']);
}

$rawBody = file_get_contents('php://input');
$payload = json_decode($rawBody === false ? '' : $rawBody, true);

if (
    json_last_error() !== JSON_ERROR_NONE
    || !is_array($payload)
    || !isset($payload['players'])
    || !is_array($payload['players'])
) {
    respond(400, ['ok' => false, 'error' => 'Invalid payload']);
}

$serverId = isset($payload['server_id']) ? (string) $payload['server_id'] : null;

require_once dirname(__DIR__) . '/includes/db.php';
require_once dirname(__DIR__) . '/includes/servers.php';

// Acepta legacy latamsquad-N y lo guarda como pr-N.
$serverId = normalize_stats_server_id($serverId);

try {
    if (!isset($config['db']) || !is_array($config['db'])) {
        throw new RuntimeException('Invalid database configuration');
    }

    $pdo = createDatabaseConnection($config['db']);
    ensure_multi_server_schema($pdo);

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

    $pdo->beginTransaction();

    foreach ($payload['players'] as $player) {
        if (
            !is_array($player)
            || !isset($player['player_id'])
            || trim((string) $player['player_id']) === ''
        ) {
            $pdo->rollBack();
            respond(400, ['ok' => false, 'error' => 'Invalid player']);
        }

        // Los valores recibidos son totales actuales y reemplazan los anteriores.
        $statement->execute([
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
        ]);
    }

    $pdo->commit();

    // Vínculos Discord↔PR: no deben tumbar el sync si fallan (schema/consume).
    try {
        require_once dirname(__DIR__) . '/includes/auth_schema.php';
        require_once dirname(__DIR__) . '/includes/player_links.php';
        ensure_auth_schema($pdo);
        $linkServerId = ($serverId !== null && $serverId !== '')
            ? $serverId
            : LATAMSTATS_DEFAULT_SERVER_ID;
        player_links_consume_from_sync($pdo, $payload['players'], $linkServerId);
    } catch (Throwable $linkError) {
        error_log('Player link consume failed: ' . $linkError->getMessage());
    }
} catch (Throwable $error) {
    if (isset($pdo) && $pdo->inTransaction()) {
        $pdo->rollBack();
    }

    error_log('Upload failed: ' . $error->getMessage());
    respond(500, ['ok' => false, 'error' => 'Upload failed']);
}

respond(200, ['ok' => true]);
