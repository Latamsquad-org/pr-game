<?php

declare(strict_types=1);

/**
 * Servidores PR (tabs). Clave tab = 1..4; id en BD = pr-N.
 */
const LATAMSTATS_SERVER_COOKIE = 'latamstats_s';
const LATAMSTATS_SERVER_COOKIE_FH2 = 'latamstats_s_fh2';
const LATAMSTATS_GAME_COOKIE = 'latamstats_g';
const LATAMSTATS_SERVER_COOKIE_TTL = 31536000; // 1 año

/** server_id por defecto (Servidor 1 PR). */
const LATAMSTATS_DEFAULT_SERVER_ID = 'pr-1';

/** server_id por defecto FH2. */
const LATAMSTATS_FH2_DEFAULT_SERVER_ID = 'fh2-1';

/**
 * Mapa legacy latamsquad-N -> pr-N (uploads viejos / filas MySQL).
 *
 * @return array<string, string>
 */
function legacy_stats_server_id_map(): array
{
    return [
        'latamsquad-1' => 'pr-1',
        'latamsquad-2' => 'pr-2',
        'latamsquad-3' => 'pr-3',
        'latamsquad-4' => 'pr-4',
    ];
}

/**
 * Normaliza server_id entrante (acepta legacy latamsquad-N).
 */
function normalize_stats_server_id(?string $serverId): string
{
    $raw = trim((string) $serverId);
    if ($raw === '') {
        return LATAMSTATS_DEFAULT_SERVER_ID;
    }

    $map = legacy_stats_server_id_map();
    if (isset($map[$raw])) {
        return $map[$raw];
    }

    return $raw;
}

/**
 * Servidores FH2 permitidos (fh2-1..fh2-4).
 *
 * @return array<string, array{key:string, id:string, label:string}>
 */
function fh2_stats_servers(): array
{
    return [
        '1' => ['key' => '1', 'id' => 'fh2-1', 'label' => 'Servidor 1'],
        '2' => ['key' => '2', 'id' => 'fh2-2', 'label' => 'Servidor 2'],
        '3' => ['key' => '3', 'id' => 'fh2-3', 'label' => 'Servidor 3'],
        '4' => ['key' => '4', 'id' => 'fh2-4', 'label' => 'Servidor 4'],
    ];
}

/**
 * True si el server_id es un id FH2 conocido (fh2-1..4).
 */
function is_fh2_stats_server_id(string $serverId): bool
{
    foreach (fh2_stats_servers() as $server) {
        if ($server['id'] === $serverId) {
            return true;
        }
    }

    return false;
}

/**
 * True si el server_id es un id PR conocido (pr-1..4).
 */
function is_pr_stats_server_id(string $serverId): bool
{
    foreach (stats_servers() as $server) {
        if ($server['id'] === $serverId) {
            return true;
        }
    }

    return false;
}

/**
 * Normaliza server_id para uploads FH2. Default fh2-1.
 */
function normalize_fh2_stats_server_id(?string $serverId): string
{
    $raw = trim((string) $serverId);
    if ($raw === '') {
        return LATAMSTATS_FH2_DEFAULT_SERVER_ID;
    }

    if (is_fh2_stats_server_id($raw)) {
        return $raw;
    }

    return $raw;
}


/**
 * Servidores PR (pr-1..pr-4).
 *
 * @return array<string, array{key:string, id:string, label:string}>
 */
function pr_stats_servers(): array
{
    return [
        '1' => ['key' => '1', 'id' => 'pr-1', 'label' => 'Servidor 1'],
        '2' => ['key' => '2', 'id' => 'pr-2', 'label' => 'Servidor 2'],
        '3' => ['key' => '3', 'id' => 'pr-3', 'label' => 'Servidor 3'],
        '4' => ['key' => '4', 'id' => 'pr-4', 'label' => 'Servidor 4'],
    ];
}

/**
 * Guarda el juego activo (pr|fh2) en cookie.
 */
function remember_stats_game(string $game): void
{
    if ($game !== 'pr' && $game !== 'fh2') {
        return;
    }

    // Evita setcookie repetido en la misma request (rompe limites de headers).
    $current = strtolower(trim((string) ($_COOKIE[LATAMSTATS_GAME_COOKIE] ?? '')));
    if ($current === $game) {
        return;
    }

    if (headers_sent()) {
        $_COOKIE[LATAMSTATS_GAME_COOKIE] = $game;

        return;
    }

    $secure = (!empty($_SERVER['HTTPS']) && $_SERVER['HTTPS'] !== 'off');
    setcookie(LATAMSTATS_GAME_COOKIE, $game, [
        'expires' => time() + LATAMSTATS_SERVER_COOKIE_TTL,
        'path' => stats_cookie_path(),
        'secure' => $secure,
        'httponly' => true,
        'samesite' => 'Lax',
    ]);
    $_COOKIE[LATAMSTATS_GAME_COOKIE] = $game;
}

/**
 * Juego activo de la UI: pr (default) o fh2.
 */
function current_stats_game(): string
{
    $raw = strtolower(trim((string) ($_GET['g'] ?? '')));
    if ($raw === 'fh2' || $raw === 'pr') {
        remember_stats_game($raw);

        return $raw;
    }

    // Hostinger puede servir /pr o /fh2stats sin extension en SCRIPT_NAME.
    $scriptPath = str_replace('\\', '/', (string) ($_SERVER['SCRIPT_NAME'] ?? ''));
    $script = basename($scriptPath);
    $scriptBase = preg_replace('/\.php$/', '', $script);
    if ($script === 'fh2stats.php' || $scriptBase === 'fh2stats') {
        remember_stats_game('fh2');

        return 'fh2';
    }
    if ($script === 'pr.php' || $scriptBase === 'pr') {
        remember_stats_game('pr');

        return 'pr';
    }

    $cookie = strtolower(trim((string) ($_COOKIE[LATAMSTATS_GAME_COOKIE] ?? '')));
    if ($cookie === 'fh2' || $cookie === 'pr') {
        return $cookie;
    }

    return 'pr';
}

/**
 * server_id por defecto segun juego activo.
 */
function default_stats_server_id(): string
{
    return current_stats_game() === 'fh2'
        ? LATAMSTATS_FH2_DEFAULT_SERVER_ID
        : LATAMSTATS_DEFAULT_SERVER_ID;
}

/**
 * Nombre de cookie de pestana de servidor (separado PR/FH2).
 */
function server_cookie_name(): string
{
    return current_stats_game() === 'fh2'
        ? LATAMSTATS_SERVER_COOKIE_FH2
        : LATAMSTATS_SERVER_COOKIE;
}

/**
 * Script inicio del juego activo.
 */
function stats_home_script(): string
{
    return current_stats_game() === 'fh2' ? 'fh2stats.php' : 'pr.php';
}

/**
 * Tabs del juego activo (PR o FH2).
 *
 * @return array<string, array{key:string, id:string, label:string}>
 */
function stats_servers(): array
{
    return current_stats_game() === 'fh2'
        ? fh2_stats_servers()
        : pr_stats_servers();
}

/**
 * Ruta del cookie según carpeta del sitio (subdirectorio o raíz).
 */
function stats_cookie_path(): string
{
    $scriptDir = dirname($_SERVER['SCRIPT_NAME'] ?? '/');
    $base = rtrim(str_replace('\\', '/', $scriptDir), '/');

    if ($base === '' || $base === '.') {
        return '/';
    }

    return $base . '/';
}

/**
 * Guarda la pestaña de servidor elegida para futuras visitas.
 */
function remember_server_key(string $key): void
{
    $servers = stats_servers();
    if (!isset($servers[$key])) {
        return;
    }

    if (headers_sent()) {
        $_COOKIE[server_cookie_name()] = $key;

        return;
    }

    $secure = (!empty($_SERVER['HTTPS']) && $_SERVER['HTTPS'] !== 'off');

    setcookie(server_cookie_name(), $key, [
        'expires' => time() + LATAMSTATS_SERVER_COOKIE_TTL,
        'path' => stats_cookie_path(),
        'secure' => $secure,
        'httponly' => true,
        'samesite' => 'Lax',
    ]);

    $_COOKIE[server_cookie_name()] = $key;
}

/**
 * Tab activa: ?s=1..4, cookie guardada, o servidor 1 por defecto.
 */
function current_server_key(): string
{
    $servers = stats_servers();
    $raw = trim((string) ($_GET['s'] ?? ''));

    if ($raw !== '' && isset($servers[$raw])) {
        remember_server_key($raw);

        return $raw;
    }

    $cookie = trim((string) ($_COOKIE[server_cookie_name()] ?? ''));
    if ($cookie !== '' && isset($servers[$cookie])) {
        return $cookie;
    }

    return '1';
}

/**
 * Si no hay ?s= en la URL pero sí cookie, redirige para fijar la pestaña activa.
 */
function maybe_redirect_persisted_server(): void
{
    if (php_sapi_name() === 'cli') {
        return;
    }

    if (($_SERVER['REQUEST_METHOD'] ?? 'GET') !== 'GET') {
        return;
    }

    $raw = trim((string) ($_GET['s'] ?? ''));
    if ($raw !== '') {
        return;
    }

    $cookie = trim((string) ($_COOKIE[server_cookie_name()] ?? ''));
    $servers = stats_servers();
    if ($cookie === '' || !isset($servers[$cookie])) {
        return;
    }

    $script = basename($_SERVER['SCRIPT_NAME'] ?? '');
    $statsPages = ['pr.php', 'fh2stats.php', 'ranking.php', 'clans.php', 'player.php', 'rangos.php'];
    if (!in_array($script, $statsPages, true)) {
        return;
    }

    $query = $_GET;
    $query['s'] = $cookie;
    $built = http_build_query($query, '', '&', PHP_QUERY_RFC3986);
    $target = $script . ($built !== '' ? '?' . $built : '');

    if (!headers_sent()) {
        header('Location: ' . $target, true, 302);
        exit;
    }
}

/**
 * server_id de MySQL para la tab activa.
 */
function current_server_id(): string
{
    $servers = stats_servers();
    $key = current_server_key();

    return $servers[$key]['id'];
}

/**
 * Etiqueta legible del servidor activo.
 */
function current_server_label(): string
{
    $servers = stats_servers();
    $key = current_server_key();

    return $servers[$key]['label'];
}

/**
 * Fragmento SQL para filtrar filas del servidor activo.
 */
function server_sql_where(string $tableAlias = ''): string
{
    $prefix = $tableAlias !== '' ? $tableAlias . '.' : '';

    return "COALESCE({$prefix}server_id, '" . default_stats_server_id() . "') = :stats_server_id";
}

/**
 * Enlaza :stats_server_id en un statement preparado.
 */
function server_sql_bind(PDOStatement $statement): void
{
    $statement->bindValue(':stats_server_id', current_server_id(), PDO::PARAM_STR);
}

/**
 * URL de páginas de stats preservando servidor.
 * No reutiliza `q`/`sort`/`dir`: hay que pasarlos explícitos
 * (p. ej. enlaces de orden o el formulario de búsqueda en ranking).
 *
 * @param array<string, string|int> $query
 */
function stats_url(string $script, array $query = []): string
{
    if (!isset($query['s'])) {
        $query['s'] = current_server_key();
    }

    if (!isset($query['g']) && current_stats_game() === 'fh2') {
        $query['g'] = 'fh2';
    }

    // Omitir parámetros vacíos (p. ej. q='') para URLs limpias.
    foreach ($query as $key => $value) {
        if ($value === null || $value === '') {
            unset($query[$key]);
        }
    }

    $path = ltrim($script, '/');
    $built = http_build_query($query, '', '&', PHP_QUERY_RFC3986);

    return $built !== '' ? $path . '?' . $built : $path;
}

/**
 * URL de ficha de jugador en el servidor activo.
 */
function player_page_href(string $playerId): string
{
    return stats_url('player.php', ['id' => $playerId]);
}

/**
 * Migra esquema para stats multi-servidor (idempotente).
 */
function ensure_multi_server_schema(PDO $pdo): void
{
    static $ensured = false;

    if ($ensured) {
        return;
    }

    $ensured = true;

    $pdo->exec(
        'CREATE TABLE IF NOT EXISTS sync_meta (
            server_id VARCHAR(64) NOT NULL PRIMARY KEY,
            payload_timestamp VARCHAR(64) NOT NULL DEFAULT \'\',
            received_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP
        )'
    );

    try {
        $hasLegacyId = $pdo->query("SHOW COLUMNS FROM sync_meta LIKE 'id'")->fetchColumn();
        if ($hasLegacyId) {
            $legacy = $pdo->query(
                'SELECT payload_timestamp, server_id FROM sync_meta WHERE id = 1 LIMIT 1'
            )->fetch(PDO::FETCH_ASSOC);

            $pdo->exec('DROP TABLE sync_meta');
            $pdo->exec(
                'CREATE TABLE sync_meta (
                    server_id VARCHAR(64) NOT NULL PRIMARY KEY,
                    payload_timestamp VARCHAR(64) NOT NULL DEFAULT \'\',
                    received_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP
                )'
            );

            if (is_array($legacy) && trim((string) ($legacy['payload_timestamp'] ?? '')) !== '') {
                $legacyServer = trim((string) ($legacy['server_id'] ?? ''));
                if ($legacyServer === '') {
                    $legacyServer = 'pr-1';
                }

                $legacyServer = normalize_stats_server_id($legacyServer);

                $insert = $pdo->prepare(
                    'INSERT INTO sync_meta (server_id, payload_timestamp) VALUES (:server_id, :payload_timestamp)'
                );
                $insert->execute([
                    'server_id' => $legacyServer,
                    'payload_timestamp' => (string) $legacy['payload_timestamp'],
                ]);
            }
        }
    } catch (Throwable $error) {
        error_log('ensure_multi_server_schema sync_meta: ' . $error->getMessage());
    }

    try {
        $hasComposite = $pdo->query(
            "SHOW INDEX FROM players WHERE Key_name = 'uq_player_server'"
        )->fetchColumn();

        if (!$hasComposite) {
            $pdo->exec(
                "UPDATE players SET server_id = '" . LATAMSTATS_DEFAULT_SERVER_ID . "'
                 WHERE server_id IS NULL OR TRIM(server_id) = ''"
            );

            try {
                $pdo->exec('ALTER TABLE players DROP INDEX uq_player_id');
            } catch (Throwable) {
                // El índice antiguo puede tener otro nombre o no existir.
            }

            $pdo->exec(
                'ALTER TABLE players ADD UNIQUE KEY uq_player_server (player_id, server_id)'
            );
        }
    } catch (Throwable $error) {
        error_log('ensure_multi_server_schema players: ' . $error->getMessage());
    }

    // Columna país (ISO-2) desde GeoIP del servidor de juego.
    try {
        $hasCountry = $pdo->query("SHOW COLUMNS FROM players LIKE 'player_country'")->fetchColumn();
        if (!$hasCountry) {
            $pdo->exec(
                "ALTER TABLE players ADD COLUMN player_country VARCHAR(8) NOT NULL DEFAULT '' AFTER player_clan"
            );
        }
    } catch (Throwable $error) {
        error_log('ensure_multi_server_schema player_country: ' . $error->getMessage());
    }

    // Columna tesoros encontrados (sync desde servidor de juego).
    try {
        $hasTreasures = $pdo->query("SHOW COLUMNS FROM players LIKE 'treasures'")->fetchColumn();
        if (!$hasTreasures) {
            $pdo->exec(
                "ALTER TABLE players ADD COLUMN treasures INT NOT NULL DEFAULT 0 AFTER rounds"
            );
        }
    } catch (Throwable $error) {
        error_log('ensure_multi_server_schema treasures: ' . $error->getMessage());
    }

    // Renombra server_id legacy latamsquad-N -> pr-N en todas las tablas conocidas.
    migrate_legacy_stats_server_ids($pdo);
}

/**
 * Actualiza filas MySQL con server_id antiguo (idempotente).
 */
function migrate_legacy_stats_server_ids(PDO $pdo): void
{
    $map = legacy_stats_server_id_map();
    $tables = [
        'players',
        'sync_meta',
        'player_links',
        'player_profiles',
        'clan_blurbs',
        'clan_editors',
    ];

    foreach ($map as $oldId => $newId) {
        foreach ($tables as $table) {
            try {
                $exists = $pdo->query("SHOW TABLES LIKE " . $pdo->quote($table))->fetchColumn();
                if (!$exists) {
                    continue;
                }
                $stmt = $pdo->prepare(
                    "UPDATE {$table} SET server_id = :new_id WHERE server_id = :old_id"
                );
                $stmt->execute([
                    'new_id' => $newId,
                    'old_id' => $oldId,
                ]);
            } catch (Throwable $error) {
                error_log(
                    'migrate_legacy_stats_server_ids ' . $table . ': ' . $error->getMessage()
                );
            }
        }
    }
}

/**
 * Tabs Servidor 1..4 (misma página, distinto ?s=).
 */
function render_server_tabs(): void
{
    $script = basename($_SERVER['SCRIPT_NAME'] ?? stats_home_script());
    $current = current_server_key();

    echo '<nav class="server-tabs" aria-label="Servidor" data-current-server="' . e($current) . '">';
    foreach (stats_servers() as $key => $server) {
        // PHP convierte claves '1'..'4' a int en foreach; normalizar a string.
        $key = (string) $key;
        $active = $key === $current ? ' is-active' : '';
        // URL limpia: solo cambia el servidor, sin arrastrar búsqueda/orden.
        $href = stats_url($script, ['s' => $key]);
        echo '<a class="server-tabs__link' . $active . '" href="' . e($href) . '"'
            . ' data-server="' . e($key) . '"'
            . ($key === $current ? ' aria-current="page"' : '') . '>'
            . e($server['label']) . '</a>';
    }
    echo '</nav>';
}
