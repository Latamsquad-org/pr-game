<?php

declare(strict_types=1);

require_once __DIR__ . '/includes/layout.php';

/**
 * Juegos del hub. Project Reality y Forgotten Hope 2 activos.
 *
 * @return list<array{label: string, href: ?string, logo: string, logo_class: string}>
 */
function landing_games(): array
{
    return [
        [
            'label' => 'ARMA 3',
            'href' => null,
            'logo' => 'arma3.png',
            'logo_class' => '',
        ],
        [
            'label' => 'ARMA Reforger',
            'href' => null,
            'logo' => 'arma-reforger.png',
            'logo_class' => '',
        ],
        [
            'label' => 'SQUAD',
            'href' => null,
            'logo' => 'squad.png',
            'logo_class' => '',
        ],
        [
            'label' => 'Project Reality',
            'href' => 'pr.php',
            'logo' => 'project-reality.png',
            'logo_class' => 'game-picker__logo--pr',
        ],
        [
            'label' => 'Realitymod BF3',
            'href' => null,
            'logo' => 'realitymod-bf3.png',
            'logo_class' => '',
        ],
        [
            'label' => 'Forgotten Hope 2',
            'href' => 'fh2stats.php',
            'logo' => 'forgotten-hope-2.png',
            'logo_class' => '',
        ],
        [
            'label' => 'Multi Theft Auto',
            'href' => null,
            'logo' => 'multi-theft-auto.png',
            'logo_class' => 'game-picker__logo--mta',
        ],
    ];
}

render_header('', [
    'stats_nav' => false,
    'hero_subtitle' => 'Estadísticas de LATAMSQUAD',
    'default_title' => 'LATAMSQUAD Stats',
    'meta_description' => 'Estadísticas LATAMSQUAD: elegí un juego para ver rankings y clanes.',
]);
?>
        <section class="game-picker" aria-label="Selección de juego">
            <h2 class="game-picker__title">Seleccioná un juego</h2>
            <p class="game-picker__lead text-muted">
                Project Reality y Forgotten Hope 2 ya tienen estadísticas. El resto estará disponible pronto.
            </p>
            <ul class="game-picker__grid">
                <?php foreach (landing_games() as $game): ?>
                <?php
                    $logoSrc = asset_url('assets/img/games/' . $game['logo']);
                    $logoClass = 'game-picker__logo';
                    if ($game['logo_class'] !== '') {
                        $logoClass .= ' ' . $game['logo_class'];
                    }
                ?>
                <li class="game-picker__item">
                    <?php if ($game['href'] !== null): ?>
                    <a class="game-picker__btn game-picker__btn--active" href="<?= e($game['href']) ?>">
                        <img
                            class="<?= e($logoClass) ?>"
                            src="<?= e($logoSrc) ?>"
                            alt=""
                            width="160"
                            height="80"
                            decoding="async"
                        >
                        <span class="game-picker__label"><?= e($game['label']) ?></span>
                        <span class="game-picker__soon game-picker__soon--spacer" aria-hidden="true">Próximamente</span>
                    </a>
                    <?php else: ?>
                    <button type="button" class="game-picker__btn game-picker__btn--disabled" disabled>
                        <img
                            class="<?= e($logoClass) ?>"
                            src="<?= e($logoSrc) ?>"
                            alt=""
                            width="160"
                            height="80"
                            decoding="async"
                        >
                        <span class="game-picker__label"><?= e($game['label']) ?></span>
                        <span class="game-picker__soon">Próximamente</span>
                    </button>
                    <?php endif; ?>
                </li>
                <?php endforeach; ?>
            </ul>
        </section>
<?php
render_footer();
