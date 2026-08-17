<?php

declare(strict_types=1);

require_once __DIR__ . '/includes/layout.php';
require_once __DIR__ . '/includes/db.php';

// Fuerza juego PR (Hostinger puede servir /pr sin pr.php en SCRIPT_NAME).
remember_stats_game('pr');

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

// Valores por defecto cuando la BD está vacía o no responde.
$playerCount = 0;
$totalScore = 0;
$totalKills = 0;
$totalDeaths = 0;
$lastSync = null;
$lastSyncDisplay = 'Sin datos';
$topPlayers = [];
$topPlayer = null;
$topClan = null;

try {
    $pdo = createDatabaseConnection($config['db']);
    ensure_multi_server_schema($pdo);

    $countStmt = $pdo->prepare('SELECT COUNT(*) FROM players WHERE ' . server_sql_where());
    server_sql_bind($countStmt);
    $countStmt->execute();
    $playerCount = (int) $countStmt->fetchColumn();

    // Suma de score (puntos) de todos los jugadores del servidor activo.
    $scoreStmt = $pdo->prepare('SELECT COALESCE(SUM(score), 0) FROM players WHERE ' . server_sql_where());
    server_sql_bind($scoreStmt);
    $scoreStmt->execute();
    $totalScore = (int) $scoreStmt->fetchColumn();

    $killsStmt = $pdo->prepare('SELECT COALESCE(SUM(kills), 0) FROM players WHERE ' . server_sql_where());
    server_sql_bind($killsStmt);
    $killsStmt->execute();
    $totalKills = (int) $killsStmt->fetchColumn();

    $deathsStmt = $pdo->prepare('SELECT COALESCE(SUM(deaths), 0) FROM players WHERE ' . server_sql_where());
    server_sql_bind($deathsStmt);
    $deathsStmt->execute();
    $totalDeaths = (int) $deathsStmt->fetchColumn();

    // Última sync del servidor activo (payload).
    $lastSync = null;
    try {
        $syncStmt = $pdo->prepare(
            'SELECT payload_timestamp FROM sync_meta WHERE server_id = :stats_server_id LIMIT 1'
        );
        server_sql_bind($syncStmt);
        $syncStmt->execute();
        $lastSyncRaw = $syncStmt->fetchColumn();
        $lastSync = is_string($lastSyncRaw) && $lastSyncRaw !== '' ? $lastSyncRaw : null;
    } catch (Throwable $syncMetaError) {
        $lastSync = null;
    }

    $topStatement = $pdo->prepare(
        'SELECT player_id, player_name, player_clan, score, kills, deaths, rounds, treasures, created
         FROM players
         WHERE ' . server_sql_where() . '
         ORDER BY
            ' . rank_xp_sql_expression() . ' DESC,
            player_id ASC
         LIMIT 10'
    );
    server_sql_bind($topStatement);
    $topStatement->execute();
    $topPlayers = $topStatement->fetchAll(PDO::FETCH_ASSOC);
    $topPlayer = $topPlayers[0] ?? null;

    // Top clan del servidor activo (inline: no depender de helpers faltantes en deploy).
    try {
        $clanStatement = $pdo->prepare(
            "SELECT
                TRIM(player_clan) AS clan_name,
                COUNT(*) AS member_count,
                COALESCE(SUM(score), 0) AS total_score,
                COALESCE(SUM(kills), 0) AS total_kills,
                COALESCE(SUM(deaths), 0) AS total_deaths
             FROM players
             WHERE " . server_sql_where() . "
               AND TRIM(COALESCE(player_clan, '')) <> ''
               AND TRIM(player_clan) <> '=+='
             GROUP BY TRIM(player_clan)
             ORDER BY total_score DESC
             LIMIT 1"
        );
        server_sql_bind($clanStatement);
        $clanStatement->execute();
        $topClan = $clanStatement->fetch(PDO::FETCH_ASSOC);
        if ($topClan === false) {
            $topClan = null;
        }

        // XP del clan = suma del XP de cada miembro (misma formula que clans.php).
        if ($topClan !== null) {
            $clanXp = 0;
            $clanNameForXp = (string) ($topClan['clan_name'] ?? '');
            if ($clanNameForXp !== '') {
                $clanMembersStmt = $pdo->prepare(
                    'SELECT score, kills, deaths, treasures
                     FROM players
                     WHERE ' . server_sql_where() . '
                       AND TRIM(player_clan) = :clan_name'
                );
                server_sql_bind($clanMembersStmt);
                $clanMembersStmt->bindValue(':clan_name', $clanNameForXp, PDO::PARAM_STR);
                $clanMembersStmt->execute();
                $clanMembersRows = $clanMembersStmt->fetchAll(PDO::FETCH_ASSOC);
                foreach ($clanMembersRows as $memberRow) {
                    $clanXp += (int) round(rank_compute_xp(
                        (int) ($memberRow['score'] ?? 0),
                        (int) ($memberRow['kills'] ?? 0),
                        (int) ($memberRow['deaths'] ?? 0),
                        (int) ($memberRow['treasures'] ?? 0)
                    ));
                }
            }
            $topClan['total_xp'] = $clanXp;
        }
    } catch (Throwable $clanError) {
        $topClan = null;
    }
} catch (Throwable $exception) {
    // Falla de conexion/top players: tops vacios (metricas pueden quedar parciales).
    $topPlayers = [];
    $topPlayer = null;
    $topClan = null;
}

$lastSyncDisplay = format_last_sync($lastSync);

render_header('Project Reality', [
    'meta_description' => 'Estadísticas de Project Reality LATAMSQUAD: jugadores, kills, sync y tops del servidor. Ranking, rangos, clanes y tesoros.',
    'og_title' => 'Project Reality · LATAMSTATS',
    'hero_subtitle' => 'Project Reality Stats',
    'toolbar_title' => 'Project Reality - estadisticas LATAMSQUAD',
]);
?>
        <section class="seo-intro" aria-label="Project Reality - estadisticas LATAMSQUAD">
                        <p class="seo-intro__text">
                Resumen del servidor elegido: totales de jugadores, score, kills y última sincronización,
                más el top player y el top clan. Desde aquí puedes ir al ranking completo, a los rangos
                militares o a la lista de clanes.
            </p>
        </section>
        <section class="metrics" aria-label="Resumen del servidor">
            <article class="metric">
                <p class="metric__label">Jugadores totales</p>
                <p class="metric__value"><?= number_format($playerCount, 0, ',', '.') ?></p>
            </article>
            <article class="metric">
                <p class="metric__label">Puntos totales</p>
                <p class="metric__value"><?= number_format($totalScore, 0, ',', '.') ?></p>
            </article>
            <article class="metric">
                <p class="metric__label">Kills totales</p>
                <p class="metric__value"><?= number_format($totalKills, 0, ',', '.') ?></p>
            </article>
            <article class="metric">
                <p class="metric__label">Muertes totales</p>
                <p class="metric__value"><?= number_format($totalDeaths, 0, ',', '.') ?></p>
            </article>
            <article class="metric">
                <p class="metric__label">Última sync</p>
                <p class="metric__value metric__value--sync">
                    <span><?= e($lastSyncDisplay) ?></span>
                    <?php if ($lastSyncDisplay !== 'Sin datos'): ?>
                        <?= brazil_flag_img() ?>
                    <?php endif; ?>
                </p>
            </article>
        </section>

        <section class="top-highlights" aria-label="Top player y top clan">
            <article class="top-card top-card--player">
                <?php if ($topPlayer === null): ?>
                    <div class="top-card__body">
                        <p class="top-card__eyebrow">Top Player</p>
                        <h2 class="top-card__title text-muted">Sin datos</h2>
                        <p class="top-card__meta text-muted">Aún no hay jugadores.</p>
                    </div>
                <?php else: ?>
                    <?php
                        $tpId = (string) ($topPlayer['player_id'] ?? '');
                        $tpName = (string) ($topPlayer['player_name'] ?? '');
                        $tpClan = (string) ($topPlayer['player_clan'] ?? '');
                        $tpDisplay = $tpName !== '' ? $tpName : $tpId;
                        $tpKd = kd_ratio($topPlayer['kills'] ?? 0, $topPlayer['deaths'] ?? 0);
                        $tpRank = player_rank($topPlayer);
                    ?>
                    <div class="top-card__body">
                        <p class="top-card__eyebrow">Top Player</p>
                        <h2 class="top-card__title">
                            <?php if ($tpClan !== ''): ?>
                            <span class="top-card__title-clan"><?= render_clan_link($tpClan, 'Sin clan') ?></span>
                            <?php endif; ?>
                            <?php if ($tpId !== ''): ?>
                            <a href="<?= e(player_page_href($tpId)) ?>"><?= e($tpDisplay) ?></a>
                            <?php else: ?>
                            <?= e($tpDisplay) ?>
                            <?php endif; ?>
                        </h2>
                        <p class="top-card__meta">
                            XP <?= number_format((int) ($tpRank['xp'] ?? 0), 0, ',', '.') ?>
                            · Score <?= number_format((int) ($topPlayer['score'] ?? 0), 0, ',', '.') ?>
                            · K/D <?= number_format($tpKd, 2, ',', '.') ?>
                        </p>
                        <p class="top-card__stats">
                            <?= number_format((int) ($topPlayer['kills'] ?? 0), 0, ',', '.') ?> kills
                            · <?= number_format((int) ($topPlayer['deaths'] ?? 0), 0, ',', '.') ?> deaths
                            · <?= number_format((int) ($topPlayer['rounds'] ?? 0), 0, ',', '.') ?> rounds
                        </p>
                    </div>
                    <?php
                        // Insignia clickeable: lleva a la fila del rango en rangos.php.
                        $tpRankHref = stats_url('rangos.php')
                            . '#rango-' . rawurlencode((string) $tpRank['rank']['slug']);
                    ?>
                    <a
                        class="top-card__rank-showcase top-card__rank-link"
                        href="<?= e($tpRankHref) ?>"
                        aria-label="Rango <?= e((string) $tpRank['rank']['name']) ?>"
                    >
                        <?= render_rank_icon($tpRank['rank'], 'top-card__rank-icon', 96) ?>
                        <p class="top-card__rank-name"><?= e((string) $tpRank['rank']['name']) ?></p>
                    </a>
                <?php endif; ?>
            </article>

            <article class="top-card top-card--clan">
                <?php if ($topClan === null): ?>
                    <div class="top-card__body">
                        <p class="top-card__eyebrow">Top Clan</p>
                        <h2 class="top-card__title text-muted">Sin datos</h2>
                        <p class="top-card__meta text-muted">Aún no hay clanes con miembros.</p>
                    </div>
                <?php else: ?>
                    <?php
                        $clanName = (string) ($topClan['clan_name'] ?? '');
                        $clanKd = kd_ratio($topClan['total_kills'] ?? 0, $topClan['total_deaths'] ?? 0);
                        $clanMembers = (int) ($topClan['member_count'] ?? 0);
                        $clanHref = clan_page_href($clanName);
                    ?>
                    <div class="top-card__body">
                        <p class="top-card__eyebrow">Top Clan</p>
                        <h2 class="top-card__title">
                            <?php if ($clanHref !== null): ?>
                            <a href="<?= e($clanHref) ?>"><?= e($clanName) ?></a>
                            <?php else: ?>
                            <?= e($clanName) ?>
                            <?php endif; ?>
                        </h2>
                        <p class="top-card__meta">
                            XP <?= number_format((int) ($topClan['total_xp'] ?? 0), 0, ',', '.') ?>
                            · Score <?= number_format((int) ($topClan['total_score'] ?? 0), 0, ',', '.') ?>
                            · K/D <?= number_format($clanKd, 2, ',', '.') ?>
                        </p>
                        <p class="top-card__stats">
                            <?= $clanMembers ?> jugador<?= $clanMembers === 1 ? '' : 'es' ?>
                            · <?= number_format((int) ($topClan['total_kills'] ?? 0), 0, ',', '.') ?> kills
                            · <?= number_format((int) ($topClan['total_deaths'] ?? 0), 0, ',', '.') ?> deaths
                        </p>
                    </div>
                    <div class="top-card__clan-showcase" aria-label="Logo <?= e($clanName) ?>">
                        <?= render_clan_logo($clanName, 'top-card__clan-logo', 176) ?>
                    </div>
                <?php endif; ?>
            </article>
        </section>

        <div class="stats-table-wrap">
            <table class="stats-table stats-table--top10">
                <caption>Top 10 por XP</caption>
                <thead>
                    <tr>
                        <th scope="col">#</th>
                        <th scope="col">Clan</th>
                        <th scope="col">Jugador</th>
                        <th scope="col">Rango</th>
                        <?php
                            // Mismas columnas y diseño que ranking.php: cabeceras
                            // numéricas como enlaces. Cada una lleva al ranking
                            // ordenado por esa columna. El Top 10 siempre está
                            // ordenado por XP descendente, de ahí su indicador ↓.
                            $topColumns = [
                                'xp' => 'XP',
                                'score' => 'Score',
                                'kills' => 'Kills',
                                'deaths' => 'Deaths',
                                'rounds' => 'Rounds',
                                'kd' => 'K/D',
                                'treasures' => 'T',
                            ];
                        ?>
                        <?php foreach ($topColumns as $column => $label): ?>
                        <th
                            scope="col"
                            class="num"
                            aria-sort="<?= $column === 'xp' ? 'descending' : 'none' ?>"
                        >
                            <a href="<?= e(stats_url('ranking.php', ['sort' => $column, 'dir' => 'desc'])) ?>">
                                <?= e($label) ?><?= $column === 'xp' ? ' ↓' : '' ?>
                            </a>
                        </th>
                        <?php endforeach; ?>
                    </tr>
                </thead>
                <tbody>
                    <?php if ($topPlayers === []): ?>
                    <tr>
                        <td colspan="11" class="text-muted">Aún no hay jugadores registrados.</td>
                    </tr>
                    <?php else: ?>
                    <?php foreach ($topPlayers as $index => $player): ?>
                    <?php
                        $playerId = (string) ($player['player_id'] ?? '');
                        $playerName = (string) ($player['player_name'] ?? '');
                        $playerClan = (string) ($player['player_clan'] ?? '');
                        $displayName = $playerName !== '' ? $playerName : $playerId;
                        $kd = kd_ratio($player['kills'] ?? 0, $player['deaths'] ?? 0);
                        $rowRank = player_rank($player);
                        $position = $index + 1;
                        // Mismo tamaño decreciente del top 10 que en ranking.php.
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
<?php
render_footer();
