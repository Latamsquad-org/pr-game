<?php

declare(strict_types=1);

require_once __DIR__ . '/includes/layout.php';
require_once __DIR__ . '/includes/db.php';

$configPath = __DIR__ . '/config.php';
if (!is_file($configPath)) {
    http_response_code(500);
    echo 'Configuración no disponible.';
    exit;
}

$config = require $configPath;
if (!is_array($config) || !isset($config['db']) || !is_array($config['db'])) {
    http_response_code(500);
    echo 'Configuración de base de datos inválida.';
    exit;
}

/** Máximo de jugadores por página del ranking. */
const RANKING_PAGE_SIZE = 500;

/** Columnas permitidas para ORDER BY (whitelist). */
const RANKING_SORT_COLUMNS = [
    // Misma fórmula que rank_compute_xp() / !stats (incluye tesoros × 5000).
    'xp' => '((score * 3) + kills - (deaths * 2)) * (1 + ((kills / GREATEST(deaths, 1)) * 0.25)) + (COALESCE(treasures, 0) * 5000)',
    'score' => 'score',
    'kills' => 'kills',
    'deaths' => 'deaths',
    'rounds' => 'rounds',
    'kd' => 'kills / GREATEST(deaths, 1)',
    'treasures' => 'COALESCE(treasures, 0)',
];

/** Etiquetas legibles para cabeceras ordenables. */
const RANKING_SORT_LABELS = [
    'xp' => 'XP',
    'score' => 'Score',
    'kills' => 'Kills',
    'deaths' => 'Deaths',
    'rounds' => 'Rounds',
    'kd' => 'K/D',
    'treasures' => 'T',
];

/**
 * Normaliza el parámetro sort contra la whitelist.
 */
function ranking_sort_param(?string $sort): string
{
    if ($sort !== null && isset(RANKING_SORT_COLUMNS[$sort])) {
        return $sort;
    }

    // Por defecto XP: refleja score, kills, K/D y deaths combinados.
    return 'xp';
}

/**
 * Normaliza asc|desc; por defecto desc.
 */
function ranking_dir_param(?string $dir): string
{
    $normalized = strtolower(trim((string) ($dir ?? '')));

    return $normalized === 'asc' ? 'asc' : 'desc';
}

/**
 * Número de página (>= 1).
 */
function ranking_page_param(?string $page): int
{
    $n = (int) ($page ?? 1);

    return $n < 1 ? 1 : $n;
}

/**
 * Construye URL de ranking preservando búsqueda, orden y página.
 *
 * @param array<string, string|int> $overrides
 */
function ranking_url(array $overrides = []): string
{
    $params = [
        's' => current_server_key(),
        'q' => trim((string) ($_GET['q'] ?? '')),
        'sort' => ranking_sort_param($_GET['sort'] ?? null),
        'dir' => ranking_dir_param($_GET['dir'] ?? null),
        'page' => ranking_page_param(isset($_GET['page']) ? (string) $_GET['page'] : null),
    ];
    $params = array_merge($params, $overrides);

    if ($params['q'] === '' || $params['q'] === null) {
        unset($params['q']);
    }

    // Página 1 sin ?page= para URL limpia.
    if (!isset($params['page']) || (int) $params['page'] <= 1) {
        unset($params['page']);
    }

    $query = http_build_query($params, '', '&', PHP_QUERY_RFC3986);

    return 'ranking' . ($query !== '' ? '?' . $query : '');
}

/**
 * Href para alternar orden al pulsar una columna (vuelve a página 1).
 */
function ranking_sort_href(string $column, string $currentSort, string $currentDir, string $query): string
{
    $nextDir = 'desc';
    if ($column === $currentSort) {
        $nextDir = $currentDir === 'desc' ? 'asc' : 'desc';
    }

    return ranking_url([
        'sort' => $column,
        'dir' => $nextDir,
        'q' => $query,
        'page' => 1,
    ]);
}

/**
 * aria-sort para accesibilidad en cabeceras activas.
 */
function ranking_aria_sort(string $column, string $currentSort, string $currentDir): string
{
    if ($column !== $currentSort) {
        return 'none';
    }

    return $currentDir === 'asc' ? 'ascending' : 'descending';
}

/**
 * Indicador visual de dirección de orden.
 */
function ranking_sort_indicator(string $column, string $currentSort, string $currentDir): string
{
    if ($column !== $currentSort) {
        return '';
    }

    return $currentDir === 'asc' ? ' ↑' : ' ↓';
}

$searchQuery = trim((string) ($_GET['q'] ?? ''));
$sort = ranking_sort_param($_GET['sort'] ?? null);
$dir = ranking_dir_param($_GET['dir'] ?? null);
$page = ranking_page_param(isset($_GET['page']) ? (string) $_GET['page'] : null);
$orderExpression = RANKING_SORT_COLUMNS[$sort];

$players = [];
$totalPlayers = 0;
$totalPages = 1;
$loadError = false;

/**
 * Prefija con un alias de tabla las columnas usadas en la expresión de orden.
 * Necesario para comparar la misma fórmula entre dos alias (p y q) en SQL.
 */
function ranking_qualify_expression(string $expression, string $alias): string
{
    return (string) preg_replace(
        '/\b(score|kills|deaths|rounds|treasures|player_id)\b/',
        $alias . '.$1',
        $expression
    );
}

try {
    $pdo = createDatabaseConnection($config['db']);
    ensure_multi_server_schema($pdo);

    // Alias "p" en la consulta principal para poder correlacionar la subconsulta de posición.
    $whereSql = 'WHERE ' . server_sql_where('p');
    $bind = [];

    if ($searchQuery !== '') {
        $whereSql .= ' AND (p.player_name LIKE :search_name OR p.player_clan LIKE :search_clan)';
        $like = '%' . $searchQuery . '%';
        $bind[':search_name'] = $like;
        $bind[':search_clan'] = $like;
    }

    // Total para paginación.
    $countSql = 'SELECT COUNT(*) FROM players p ' . $whereSql;
    $countStmt = $pdo->prepare($countSql);
    server_sql_bind($countStmt);
    foreach ($bind as $key => $value) {
        $countStmt->bindValue($key, $value, PDO::PARAM_STR);
    }
    $countStmt->execute();
    $totalPlayers = (int) $countStmt->fetchColumn();

    $totalPages = max(1, (int) ceil($totalPlayers / RANKING_PAGE_SIZE));
    if ($page > $totalPages) {
        $page = $totalPages;
    }

    $offset = ($page - 1) * RANKING_PAGE_SIZE;

    // Expresión de orden calificada para cada alias (p = fila mostrada, q = comparación).
    $exprP = ranking_qualify_expression($orderExpression, 'p');
    $exprQ = ranking_qualify_expression($orderExpression, 'q');

    // Con búsqueda activa la fila N del resultado NO es la posición N del ranking:
    // se calcula la posición global con una subconsulta correlacionada.
    // Posición global = 1 + cuántos jugadores del servidor (sin filtro de búsqueda)
    // van antes según el mismo ORDER BY, con desempate por player_id ASC.
    $positionSelect = 'NULL AS global_position';
    if ($searchQuery !== '') {
        $beforeCmp = $dir === 'asc' ? '<' : '>';
        $positionSelect = sprintf(
            '(SELECT COUNT(*) + 1 FROM players q
               WHERE COALESCE(q.server_id, \'pr-1\') = :stats_server_id_pos
                 AND ((%1$s %2$s %3$s) OR ((%1$s = %3$s) AND q.player_id < p.player_id))) AS global_position',
            $exprQ,
            $beforeCmp,
            $exprP
        );
    }

    $sql = 'SELECT p.player_id, p.player_name, p.player_clan, p.score, p.kills, p.deaths, p.rounds, p.treasures, p.created,
            ' . $positionSelect . '
            FROM players p
            ' . $whereSql
        . sprintf(' ORDER BY %s %s, p.player_id ASC', $exprP, $dir)
        . ' LIMIT :limit OFFSET :offset';

    $statement = $pdo->prepare($sql);
    server_sql_bind($statement);
    if ($searchQuery !== '') {
        $statement->bindValue(':stats_server_id_pos', current_server_id(), PDO::PARAM_STR);
    }
    foreach ($bind as $key => $value) {
        $statement->bindValue($key, $value, PDO::PARAM_STR);
    }
    $statement->bindValue(':limit', RANKING_PAGE_SIZE, PDO::PARAM_INT);
    $statement->bindValue(':offset', $offset, PDO::PARAM_INT);
    $statement->execute();
    $players = $statement->fetchAll();
} catch (Throwable $exception) {
    $players = [];
    $totalPlayers = 0;
    $totalPages = 1;
    $page = 1;
    $loadError = true;
}

$pagePlayerCount = count($players);
$rangeFrom = $totalPlayers === 0 ? 0 : (($page - 1) * RANKING_PAGE_SIZE) + 1;
$rangeTo = $totalPlayers === 0 ? 0 : $rangeFrom + $pagePlayerCount - 1;
$captionSuffix = $searchQuery !== '' ? ' · filtro: «' . $searchQuery . '»' : '';
$hasPrev = $page > 1;
$hasNext = $page < $totalPages;

render_header('Ranking', [
    'meta_description' => 'Ranking de jugadores de Project Reality LATAMSQUAD ordenado por XP (score, kills, deaths, K/D y tesoros × 5000).',
    'og_title' => 'Ranking de jugadores · LATAMSTATS',
    'toolbar_title' => 'Ranking de jugadores - Project Reality',
]);
?>
        <section class="seo-intro" aria-label="Ranking de jugadores - Project Reality">
                        <p class="seo-intro__text">
                Clasificación de la comunidad LATAMSQUAD por XP. Buscá por nombre o clan,
                ordená columnas y abrí el perfil de cada jugador.
            </p>
        </section>
        <section class="xp-ranking-guide" aria-labelledby="player-ranking-guide-title">
            <h3 id="player-ranking-guide-title" class="xp-ranking-guide__title">
                Cómo se organiza el ranking de jugadores
            </h3>
            <p class="ranks-guide__formula">
                <strong>XP</strong> =
                (score × 3 + kills − deaths × 2) × (1 + K/D × 0.25)
                <span class="ranks-guide__formula-treasure">+ (tesoros × 5000)</span>
            </p>
            <p class="ranks-guide__explain">
                La posición se asigna de mayor a menor XP: el jugador con más XP
                ocupa el puesto 1.
            </p>
            <ul class="ranks-guide__legend">
                <li><strong>Score × 3</strong>: premia la actividad y el aporte al equipo.</li>
                <li><strong>+ Kills</strong>: cada baja suma XP.</li>
                <li><strong>− Deaths × 2</strong>: morir con frecuencia reduce el XP.</li>
                <li><strong>Multiplicador K/D</strong>: una mejor relación entre bajas
                    y muertes hace que todo el XP obtenido valga más.</li>
                <li class="ranks-guide__legend-treasure">
                    <strong>+ (tesoros × 5000)</strong>: cada tesoro encontrado suma
                    5000 XP extra.
                </li>
            </ul>
            <p class="ranks-guide__note text-muted">
                Buscar un jugador o clan no modifica su posición global. Las columnas
                también pueden ordenarse por Score, Kills, Deaths, Rounds, K/D o T (tesoros).
            </p>
        </section>

        <form class="search-bar" method="get" action="ranking" role="search">
            <label class="sr-only" for="ranking-search">Buscar jugador o clan</label>
            <input
                type="search"
                id="ranking-search"
                name="q"
                value="<?= e($searchQuery) ?>"
                placeholder="Buscar por nombre o clan…"
                autocomplete="off"
            >
            <input type="hidden" name="s" value="<?= e(current_server_key()) ?>">
            <input type="hidden" name="sort" value="<?= e($sort) ?>">
            <input type="hidden" name="dir" value="<?= e($dir) ?>">
            <button type="submit">Buscar</button>
            <?php if ($searchQuery !== ''): ?>
            <a class="btn" href="<?= e(ranking_url(['q' => '', 'sort' => $sort, 'dir' => $dir, 'page' => 1])) ?>">Limpiar</a>
            <?php endif; ?>
        </form>

        <div class="stats-table-wrap">
            <table class="stats-table">
                <caption>
                    Ranking
                    (<?= number_format($totalPlayers, 0, ',', '.') ?> jugador<?= $totalPlayers === 1 ? '' : 'es' ?>)
                    <?php if ($totalPlayers > 0): ?>
                    · mostrando <?= number_format($rangeFrom, 0, ',', '.') ?>–<?= number_format($rangeTo, 0, ',', '.') ?>
                    · página <?= (int) $page ?>/<?= (int) $totalPages ?>
                    <?php endif; ?>
                    <?= e($captionSuffix) ?>
                </caption>
                <thead>
                    <tr>
                        <th scope="col">#</th>
                        <th scope="col">Clan</th>
                        <th scope="col">Jugador</th>
                        <th scope="col">Rango</th>
                        <?php foreach (RANKING_SORT_LABELS as $column => $label): ?>
                        <th
                            scope="col"
                            class="num"
                            aria-sort="<?= e(ranking_aria_sort($column, $sort, $dir)) ?>"
                        >
                            <a href="<?= e(ranking_sort_href($column, $sort, $dir, $searchQuery)) ?>">
                                <?= e($label) ?><?= ranking_sort_indicator($column, $sort, $dir) ?>
                            </a>
                        </th>
                        <?php endforeach; ?>
                    </tr>
                </thead>
                <tbody>
                    <?php if ($loadError): ?>
                    <tr>
                        <td colspan="11" class="text-muted">No se pudo cargar el ranking.</td>
                    </tr>
                    <?php elseif ($players === []): ?>
                    <tr>
                        <td colspan="11" class="text-muted">
                            <?= $searchQuery !== ''
                                ? 'Ningún jugador coincide con la búsqueda.'
                                : 'Aún no hay jugadores registrados.' ?>
                        </td>
                    </tr>
                    <?php else: ?>
                    <?php foreach ($players as $index => $player): ?>
                    <?php
                        $playerId = (string) ($player['player_id'] ?? '');
                        $playerName = (string) ($player['player_name'] ?? '');
                        $playerClan = (string) ($player['player_clan'] ?? '');
                        $displayName = $playerName !== '' ? $playerName : $playerId;
                        $kd = kd_ratio($player['kills'] ?? 0, $player['deaths'] ?? 0);
                        $rowRank = player_rank($player);
                        // Sin búsqueda: la posición se deduce de página + fila.
                        // Con búsqueda: se usa la posición global calculada en SQL,
                        // para no renumerar desde 1 los resultados filtrados.
                        $position = isset($player['global_position']) && $player['global_position'] !== null
                            ? (int) $player['global_position']
                            : (($page - 1) * RANKING_PAGE_SIZE) + $index + 1;
                        // Top 10: clase ranking-pos--N para ir achicando el número.
                        $posClass = $position <= 10
                            ? 'ranking-pos ranking-pos--' . $position
                            : 'ranking-pos';
                    ?>
                    <tr>
                        <td class="num <?= e($posClass) ?>"><?= $position ?></td>
                        <td><?= render_clan_link($playerClan) ?></td>
                        <td>
                            <?php if ($playerId !== ''): ?>
                            <a class="player-name" href="<?= e(player_page_href($playerId)) ?>"><?= e($displayName) ?></a>
                            <?php else: ?>
                            <?= e($displayName) ?>
                            <?php endif; ?>
                        </td>
                        <td><?= render_rank_badge($rowRank, false, true) ?></td>
                        <td class="num"><?= number_format((int) ($rowRank['xp'] ?? 0), 0, ',', '.') ?></td>
                        <td class="num"><?= number_format((int) ($player['score'] ?? 0), 0, ',', '.') ?></td>
                        <td class="num"><?= number_format((int) ($player['kills'] ?? 0), 0, ',', '.') ?></td>
                        <td class="num"><?= number_format((int) ($player['deaths'] ?? 0), 0, ',', '.') ?></td>
                        <td class="num"><?= number_format((int) ($player['rounds'] ?? 0), 0, ',', '.') ?></td>
                        <td class="num"><?= number_format($kd, 2, ',', '.') ?></td>
                        <td class="num"><?= number_format((int) ($player['treasures'] ?? 0), 0, ',', '.') ?></td>
                    </tr>
                    <?php endforeach; ?>
                    <?php endif; ?>
                </tbody>
            </table>
        </div>

        <?php if ($totalPages > 1): ?>
        <nav class="ranking-pagination" aria-label="Páginas del ranking">
            <?php if ($hasPrev): ?>
            <a class="btn ranking-pagination__btn" href="<?= e(ranking_url(['page' => $page - 1, 'sort' => $sort, 'dir' => $dir, 'q' => $searchQuery])) ?>">
                ← Anterior
            </a>
            <?php else: ?>
            <span class="btn ranking-pagination__btn is-disabled" aria-disabled="true">← Anterior</span>
            <?php endif; ?>

            <span class="ranking-pagination__status">
                Página <?= (int) $page ?> de <?= (int) $totalPages ?>
            </span>

            <?php if ($hasNext): ?>
            <a class="btn ranking-pagination__btn" href="<?= e(ranking_url(['page' => $page + 1, 'sort' => $sort, 'dir' => $dir, 'q' => $searchQuery])) ?>">
                Siguiente →
            </a>
            <?php else: ?>
            <span class="btn ranking-pagination__btn is-disabled" aria-disabled="true">Siguiente →</span>
            <?php endif; ?>
        </nav>
        <?php endif; ?>

        <script src="<?= e(asset_url('assets/js/ranking.js')) ?>" defer></script>
<?php
render_footer();
