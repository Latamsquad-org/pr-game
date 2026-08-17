<?php

declare(strict_types=1);

require_once __DIR__ . '/includes/layout.php';

$ranks = ranks_table();

// Mapa id de rango → etiqueta de antigüedad (tope de cuenta).
$ageLabelById = [];
foreach (rank_age_caps_table() as $ageRow) {
    $ageLabelById[(int) $ageRow['id']] = (string) $ageRow['label'];
}

// Los rangos son iguales en todos los servidores: se ocultan las pestañas Servidor 1..4.
render_header('Rangos', [
    'server_tabs' => false,
    'toolbar_title' => 'Rangos militares - Project Reality',
    'meta_description' => 'Rangos militares de Project Reality LATAMSQUAD: tabla de grados, fórmula de XP y tope por antigüedad de cuenta.',
    'og_title' => 'Rangos militares · LATAMSTATS',
]);
?>
        <section class="seo-intro" aria-label="Rangos militares - Project Reality">
                        <p class="seo-intro__text">
                Tabla de rangos de LATAMSQUAD según XP de actividad y antigüedad de la cuenta.
                El mismo XP se usa en el ranking de jugadores y en el de clanes.
            </p>
        </section>
        <section class="xp-ranking-guide" aria-labelledby="ranks-guide-title">
            <h3 id="ranks-guide-title" class="xp-ranking-guide__title">
                Cómo funcionan los rangos y el XP
            </h3>
            <p class="ranks-guide__lead">
                El rango se calcula con un XP de actividad. Todos empiezan como
                <strong>Insurgente</strong>; la antigüedad de la cuenta limita el
                rango máximo (hasta <strong>3 años</strong> para General).
            </p>
            <p class="ranks-guide__formula">
                <strong>XP</strong> =
                (score × 3 + kills − deaths × 2) × (1 + K/D × 0.25)
                <span class="ranks-guide__formula-treasure">+ (tesoros × 5000)</span>
            </p>
            <p class="ranks-guide__explain">
                Primero se suma tu actividad y luego se multiplica según tu puntería.
                Cuanto mejor sea tu relación de bajas por muerte (K/D), más rinde todo lo que hacés.
            </p>
            <ul class="ranks-guide__legend">
                <li><strong>Score × 3</strong>: es lo que más suma. Se gana jugando en equipo
                    (banderas, curar, reparar, transportar, construir…).</li>
                <li><strong>+ Kills</strong>: cada baja aporta un punto extra.</li>
                <li><strong>− Deaths × 2</strong>: cada muerte resta el doble, así que morir mucho penaliza.</li>
                <li><strong>× (1 + K/D × 0.25)</strong>: multiplicador por eficiencia.
                    Con K/D 2 tu XP sube un 50&nbsp;%; con K/D 4 se duplica. Jugar limpio
                    (más bajas que muertes) hace que todo tu XP valga más.</li>
                <li class="ranks-guide__legend-treasure">
                    <strong>+ (tesoros × 5000)</strong>: cada tesoro encontrado suma
                    5000 XP extra (igual que en ranking y clanes).
                </li>
            </ul>
            <p class="ranks-guide__note text-muted">
                En resumen: <strong>participá y aportá al equipo</strong> para subir el score,
                <strong>eliminá enemigos</strong> y sobre todo <strong>evitá morir</strong>;
                un buen K/D multiplica tu progreso.
            </p>
        </section>

        <div class="stats-table-wrap">
            <table class="stats-table">
                <caption>Rangos: XP mínimo y tope por antigüedad</caption>
                <thead>
                    <tr>
                        <th scope="col">#</th>
                        <th scope="col">Insignia</th>
                        <th scope="col">Rango</th>
                        <th scope="col" class="num">XP mínimo</th>
                        <th scope="col">Antigüedad</th>
                        <th scope="col">Descripción</th>
                    </tr>
                </thead>
                <tbody>
                    <?php foreach ($ranks as $rank): ?>
                    <?php
                        $rankId = (int) $rank['id'];
                        $ageLabel = $ageLabelById[$rankId] ?? '—';
                        // Ancla por rango: permite enlazar directo (ej. rangos.php#rango-general).
                        $rankAnchor = 'rango-' . (string) $rank['slug'];
                        $rankDesc = (string) ($rank['description'] ?? '');
                    ?>
                    <tr id="<?= e($rankAnchor) ?>">
                        <td class="num"><?= $rankId ?></td>
                        <td class="rank-guide__icon-cell">
                            <?= render_rank_icon($rank, 'rank-guide__icon', 64) ?>
                        </td>
                        <td><?= e($rank['name']) ?></td>
                        <td class="num"><?= number_format((int) $rank['xp_min'], 0, ',', '.') ?></td>
                        <td><?= e($ageLabel) ?></td>
                        <td class="rank-guide__desc"><?= e($rankDesc) ?></td>
                    </tr>
                    <?php endforeach; ?>
                </tbody>
            </table>
        </div>
<?php
render_footer();
