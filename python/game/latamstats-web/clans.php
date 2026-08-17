<?php

declare(strict_types=1);

require_once __DIR__ . '/includes/layout.php';
require_once __DIR__ . '/includes/db.php';
require_once __DIR__ . '/includes/clan_permissions.php';
require_once __DIR__ . '/includes/auth_schema.php';

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

$players = [];
$loadError = false;
/** @var PDO|null $pdo */
$pdo = null;

try {
    $pdo = createDatabaseConnection($config['db']);
    ensure_multi_server_schema($pdo);
    ensure_auth_schema($pdo);
    $statement = $pdo->prepare(
        'SELECT player_id, player_name, player_clan, score, kills, deaths, rounds, treasures, seen, created
         FROM players
         WHERE ' . server_sql_where() . '
         ORDER BY
           CASE WHEN TRIM(COALESCE(player_clan, \'\')) = \'\' THEN 1 ELSE 0 END,
           player_clan ASC,
           score DESC,
           player_name ASC'
    );
    server_sql_bind($statement);
    $statement->execute();
    $players = $statement->fetchAll(PDO::FETCH_ASSOC);
} catch (Throwable $error) {
    error_log('Clans page failed: ' . $error->getMessage());
    $loadError = true;
}

$clans = clan_aggregate_from_players($players);

// Dentro de cada clan: jugadores de mayor a menor XP.
foreach ($clans as $anchor => &$clanRef) {
    usort(
        $clanRef['players'],
        static function (array $a, array $b): int {
            $xpCmp = ((int) ($b['_xp'] ?? 0)) <=> ((int) ($a['_xp'] ?? 0));
            if ($xpCmp !== 0) {
                return $xpCmp;
            }

            return strcasecmp((string) ($a['player_name'] ?? ''), (string) ($b['player_name'] ?? ''));
        }
    );
}
unset($clanRef);

// Ordenar clanes por XP total (Sin clan al final)
uasort($clans, static function (array $a, array $b): int {
    if ($a['name'] === 'Sin clan' && $b['name'] !== 'Sin clan') {
        return 1;
    }
    if ($b['name'] === 'Sin clan' && $a['name'] !== 'Sin clan') {
        return -1;
    }

    return $b['xp'] <=> $a['xp'];
});

// Posición global de cada clan (se asigna antes del filtro de búsqueda
// para que el número no cambie al buscar).
$clanPosition = 0;
foreach ($clans as $anchor => $clanRow) {
    $clanPosition++;
    $clans[$anchor]['position'] = $clanPosition;
}

$searchQuery = trim((string) ($_GET['q'] ?? ''));
$allClanCount = count($clans);

if ($searchQuery !== '') {
    $clans = array_filter(
        $clans,
        static function (array $clan) use ($searchQuery): bool {
            if (stripos($clan['name'], $searchQuery) !== false) {
                return true;
            }

            foreach ($clan['players'] as $player) {
                $playerName = (string) ($player['player_name'] ?? '');
                if ($playerName !== '' && stripos($playerName, $searchQuery) !== false) {
                    return true;
                }
            }

            return false;
        }
    );
}

$focusClan = trim((string) ($_GET['clan'] ?? ''));
$focusAnchor = $focusClan !== '' ? clan_html_anchor(clan_display_name($focusClan)) : '';

$flashOk = '';
$flashErr = '';
$editorDiscordId = auth_current_discord_id();
$serverId = current_server_id();

// POST: editores autorizados guardan blurb (CSRF + 403 si no permitido).
if (
    !$loadError
    && $pdo instanceof PDO
    && ($_SERVER['REQUEST_METHOD'] ?? 'GET') === 'POST'
) {
    $action = isset($_POST['action']) && is_string($_POST['action']) ? $_POST['action'] : '';
    if ($action === 'save_clan_blurb') {
        $clanPost = isset($_POST['clan']) && is_string($_POST['clan'])
            ? clan_display_name($_POST['clan'])
            : '';
        $csrf = isset($_POST['csrf']) && is_string($_POST['csrf']) ? $_POST['csrf'] : '';
        $description = isset($_POST['description']) && is_string($_POST['description'])
            ? $_POST['description']
            : '';
        $discordPost = isset($_POST['discord_url']) && is_string($_POST['discord_url'])
            ? $_POST['discord_url']
            : '';

        // Sin login o sin permiso de editor → 403 (aunque forjen el form).
        if (
            $editorDiscordId === null
            || $clanPost === ''
            || !clan_editor_is_allowed($pdo, $clanPost, $serverId, $editorDiscordId)
        ) {
            http_response_code(403);
            echo 'No autorizado.';
            exit;
        }

        if (!auth_csrf_validate($csrf)) {
            $flashErr = 'Token de seguridad inválido. Recarga la página e intenta de nuevo.';
        } else {
            try {
                clan_blurb_db_save(
                    $pdo,
                    $clanPost,
                    $serverId,
                    $description,
                    $editorDiscordId,
                    $discordPost
                );
                $flashOk = 'Datos del clan actualizados.';

                // Logo opcional: solo si el editor eligió un archivo.
                if (
                    isset($_FILES['logo']) && is_array($_FILES['logo'])
                    && (int) ($_FILES['logo']['error'] ?? UPLOAD_ERR_NO_FILE) !== UPLOAD_ERR_NO_FILE
                ) {
                    try {
                        $logoPath = clan_store_logo($_FILES['logo'], $clanPost);
                        $flashOk = 'Datos y logo del clan actualizados.';
                        if ($editorDiscordId !== null) {
                            require_once __DIR__ . '/includes/admin_logs.php';
                            stats_audit_log(
                                $pdo,
                                $editorDiscordId,
                                'clan_upload_logo',
                                $clanPost,
                                ['path' => $logoPath],
                                'clans'
                            );
                        }
                    } catch (Throwable $logoEx) {
                        $flashOk = '';
                        $flashErr = $logoEx->getMessage();
                    }
                }

                // Banner opcional: archivo nuevo o pedido de quitarlo.
                if (isset($_POST['remove_banner']) && $_POST['remove_banner'] === '1') {
                    clan_delete_banner($clanPost);
                    $flashOk = ($flashOk !== '' ? $flashOk . ' ' : '') . 'Banner eliminado.';
                    if ($editorDiscordId !== null) {
                        require_once __DIR__ . '/includes/admin_logs.php';
                        stats_audit_log(
                            $pdo,
                            $editorDiscordId,
                            'clan_remove_banner',
                            $clanPost,
                            [],
                            'clans'
                        );
                    }
                } elseif (
                    isset($_FILES['banner']) && is_array($_FILES['banner'])
                    && (int) ($_FILES['banner']['error'] ?? UPLOAD_ERR_NO_FILE) !== UPLOAD_ERR_NO_FILE
                ) {
                    try {
                        $bannerPath = clan_store_banner($_FILES['banner'], $clanPost);
                        $flashOk = ($flashOk !== '' ? $flashOk . ' ' : '') . 'Banner actualizado.';
                        if ($editorDiscordId !== null) {
                            require_once __DIR__ . '/includes/admin_logs.php';
                            stats_audit_log(
                                $pdo,
                                $editorDiscordId,
                                'clan_upload_banner',
                                $clanPost,
                                ['path' => $bannerPath],
                                'clans'
                            );
                        }
                    } catch (Throwable $bannerEx) {
                        $flashOk = '';
                        $flashErr = $bannerEx->getMessage();
                    }
                }
            } catch (Throwable $saveEx) {
                $flashErr = $saveEx->getMessage();
            }

            // Mantener foco en el clan editado tras guardar.
            $focusAnchor = clan_html_anchor($clanPost);
        }
    } elseif ($action === 'request_clan_editor') {
        $clanPost = isset($_POST['clan']) && is_string($_POST['clan'])
            ? clan_display_name($_POST['clan'])
            : '';
        $csrf = isset($_POST['csrf']) && is_string($_POST['csrf']) ? $_POST['csrf'] : '';
        $returnPath = stats_url('clans.php', ['clan' => $clanPost]);

        if ($editorDiscordId === null) {
            // Login y volver a este clan.
            header(
                'Location: /auth/discord.php?return=' . rawurlencode($returnPath),
                true,
                302
            );
            exit;
        }

        if ($clanPost === '' || $clanPost === 'Sin clan') {
            $flashErr = 'Clan inválido.';
        } elseif (!auth_csrf_validate($csrf)) {
            $flashErr = 'Token de seguridad inválido. Recarga la página e intenta de nuevo.';
        } else {
            $result = clan_editor_request_self($pdo, $clanPost, $serverId, $editorDiscordId);
            if ($result === true) {
                $flashOk = 'Ya eres editor autorizado de este clan. Puedes editar la ficha.';
                $focusAnchor = clan_html_anchor($clanPost);
            } else {
                $flashErr = $result;
                // Avisos de vínculo/tag: quedar arriba (sin saltar al clan).
                $keepFlashFocus = $flashErr === CLAN_EDITOR_PLAYER_NOT_FOUND
                    || $flashErr === CLAN_EDITOR_TAG_MISMATCH;
                if ($keepFlashFocus) {
                    $focusAnchor = '';
                } else {
                    $focusAnchor = clan_html_anchor($clanPost);
                }
            }
        }
    }
}

$csrfToken = auth_csrf_token();

render_header('Clanes', [
    'meta_description' => 'Clanes de Project Reality LATAMSQUAD: ranking por XP sumado de miembros, logos, descripciones y editores.',
    'og_title' => 'Clanes · LATAMSTATS',
    'toolbar_title' => 'Clanes - Project Reality LATAMSQUAD',
]);
?>

<?php if ($flashOk !== ''): ?>
    <p class="profile-flash profile-flash--ok" role="status"><?= e($flashOk) ?></p>
<?php endif; ?>
<?php if ($flashErr !== ''): ?>
    <?php
    // Parpadeo + foco en avisos de vínculo/tag (no scrollear al clan).
    $flashBlink = $flashErr === CLAN_EDITOR_PLAYER_NOT_FOUND
        || $flashErr === CLAN_EDITOR_TAG_MISMATCH;
    ?>
    <p
        id="clans-flash"
        class="profile-flash profile-flash--err<?= $flashBlink ? ' profile-flash--blink' : '' ?>"
        role="alert"
        <?= $flashBlink ? 'tabindex="-1"' : '' ?>
    ><?= e($flashErr) ?></p>
<?php endif; ?>

    <section class="seo-intro" aria-label="Clanes - Project Reality LATAMSQUAD">
                <p class="seo-intro__text">
            Ranking de clanes por XP total (suma del XP de cada miembro, incluyendo bonus por tesoros).
            Consulta miembros, logos y fichas públicas de cada clan.
        </p>
    </section>

    <section class="xp-ranking-guide" aria-labelledby="clans-ranking-guide-title">
        <h3 id="clans-ranking-guide-title" class="xp-ranking-guide__title">
            Cómo se organiza el ranking de clanes
        </h3>
        <p class="ranks-guide__formula">
            <strong>XP de cada jugador</strong> =
            (score × 3 + kills − deaths × 2) × (1 + K/D × 0.25)
            <span class="ranks-guide__formula-treasure">+ (tesoros × 5000)</span>
        </p>
        <p class="ranks-guide__explain">
            El <strong>XP del clan</strong> es la suma del XP de todos sus miembros.
            La posición se asigna de mayor a menor XP total: el clan con más XP ocupa
            el puesto 1.
        </p>
        <ul class="ranks-guide__legend">
            <li><strong>Score × 3</strong>: premia la actividad y el aporte al equipo.</li>
            <li><strong>+ Kills</strong>: cada baja suma XP.</li>
            <li><strong>− Deaths × 2</strong>: morir con frecuencia reduce el XP.</li>
            <li><strong>Multiplicador K/D</strong>: una mejor relación entre bajas y
                muertes hace que el XP de cada miembro valga más.</li>
            <li class="ranks-guide__legend-treasure">
                <strong>+ (tesoros × 5000)</strong>: cada tesoro encontrado por un
                miembro suma 5000 XP al total del clan.
            </li>
        </ul>
        <p class="ranks-guide__note text-muted">
            Los clanes con más miembros pueden acumular más XP porque se suman los
            puntos de todos. Buscar un clan no modifica su posición global.
        </p>
    </section>

<?php if ($loadError): ?>
    <p class="text-muted">No se pudieron cargar los clanes. Revisa la conexión a la base de datos.</p>
<?php elseif ($allClanCount === 0): ?>
    <p class="text-muted">Aún no hay jugadores con clan registrados.</p>
<?php else: ?>
    <form class="search-bar" method="get" action="clans" role="search">
        <label class="sr-only" for="clans-search">Buscar clan o jugador</label>
        <input type="hidden" name="s" value="<?= e(current_server_key()) ?>">
        <input
            type="search"
            id="clans-search"
            name="q"
            value="<?= e($searchQuery) ?>"
            placeholder="Buscar clan o jugador…"
            autocomplete="off"
        >
        <button type="submit">Buscar</button>
        <?php if ($searchQuery !== ''): ?>
        <a class="btn" href="<?= e(stats_url('clans.php')) ?>">Limpiar</a>
        <?php endif; ?>
    </form>

    <?php if ($searchQuery !== '' && count($clans) === 0): ?>
    <p class="text-muted">Ningún clan coincide con «<?= e($searchQuery) ?>».</p>
    <?php else: ?>
    <p class="text-muted clans-intro">
        <?php
            $clanMemberCount = 0;
            foreach ($clans as $clanRow) {
                $clanMemberCount += count($clanRow['players']);
            }
        ?>
        <?= count($clans) ?> clan<?= count($clans) === 1 ? '' : 'es' ?> · <?= $clanMemberCount ?> jugadores con clan
        <?php if ($searchQuery !== ''): ?>
        · filtro: «<?= e($searchQuery) ?>»
        <?php else: ?>
        — ordenados por XP total; cada clan agrupa a sus miembros y suma score, kills y rounds.
        <?php endif; ?>
    </p>

    <div class="clan-list">
        <?php foreach ($clans as $clan): ?>
            <?php
            $memberCount = count($clan['players']);
            $kd = kd_ratio($clan['kills'], $clan['deaths']);
            $isFocus = $focusAnchor !== '' && $focusAnchor === $clan['anchor'];
            $blurbText = $pdo instanceof PDO
                ? clan_blurb_public($pdo, $clan['name'], $serverId)
                : clan_blurb($clan['name']);
            // Discord público: DB del editor (vacío = sin botón) o estático.
            $discordPublic = $pdo instanceof PDO
                ? clan_discord_public($pdo, $clan['name'], $serverId)
                : clan_discord_url($clan['name']);
            // Valor del formulario: si ya editó en DB, ese valor; si no, el estático.
            $discordEditValue = $discordPublic;
            if ($pdo instanceof PDO) {
                $dbDiscord = clan_discord_db_get($pdo, $clan['name'], $serverId);
                if ($dbDiscord !== null) {
                    $discordEditValue = $dbDiscord;
                }
            }
            // Solo editores logueados ven el form bajo el blurb.
            $canEditBlurb = $pdo instanceof PDO
                && $editorDiscordId !== null
                && clan_editor_is_allowed($pdo, $clan['name'], $serverId, $editorDiscordId);
            ?>
            <section
                class="clan-block<?= $isFocus ? ' is-focus' : '' ?>"
                id="clan-<?= e($clan['anchor']) ?>"
            >
                <?php
                // Top 10: clase clan-block__pos--N para achicar el número (igual que el ranking).
                $clanPos = (int) ($clan['position'] ?? 0);
                $posClass = ($clanPos >= 1 && $clanPos <= 10)
                    ? ' clan-block__pos--' . $clanPos
                    : '';
                ?>
                <?php
                // Banner del clan (editable): fondo del encabezado con velo
                // oscuro para mantener el texto legible.
                $clanBannerUrl = clan_banner_url($clan['name']);
                $headerClass = 'clan-block__header';
                $headerStyle = '';
                if ($clanBannerUrl !== null) {
                    $headerClass .= ' clan-block__header--banner';
                    $headerStyle = ' style="background-image: linear-gradient('
                        . 'rgba(10, 10, 10, 0.62), rgba(10, 10, 10, 0.82)), '
                        . "url('" . e($clanBannerUrl) . "');\"";
                }
                ?>
                <header class="<?= $headerClass ?>"<?= $headerStyle ?>>
                    <div class="clan-block__identity">
                        <span class="clan-block__pos<?= e($posClass) ?>"><?= $clanPos ?></span>
                        <?= render_clan_logo($clan['name'], 'clan-block__logo clan-block__logo--zoomable', 88) ?>
                        <div class="clan-block__text">
                            <h3 class="clan-block__name"><?= e($clan['name']) ?></h3>
                            <p class="clan-block__meta text-muted">
                                <?= $memberCount ?> jugador<?= $memberCount === 1 ? '' : 'es' ?>
                            </p>
                            <?php
                            $clanDiscord = render_clan_discord_link(
                                $clan['name'],
                                'clan-discord-btn',
                                $discordPublic
                            );
                            if ($clanDiscord !== ''):
                            ?>
                                <?= $clanDiscord ?>
                            <?php endif; ?>
                            <?php
                            // Editores autorizados: debajo del botón Discord del clan.
                            $publicEditors = $pdo instanceof PDO
                                ? clan_editors_public_display($pdo, $clan['name'], $serverId)
                                : [];
                            if ($publicEditors !== []):
                                $editorsTitle = count($publicEditors) === 1
                                    ? 'Editor Autorizado'
                                    : 'Editores Autorizados';
                            ?>
                            <div class="clan-block__editors" aria-label="<?= e($editorsTitle) ?>">
                                <p class="clan-block__editors-title"><?= e($editorsTitle) ?></p>
                                <ul class="clan-block__editors-list">
                                    <?php foreach ($publicEditors as $editorInfo): ?>
                                    <?php
                                    $edPlayerId = $editorInfo['player_id'];
                                    $edPlayerName = $editorInfo['player_name'];
                                    ?>
                                    <li class="clan-block__editor">
                                        <span class="clan-block__editor-player">
                                            <?php if (is_string($edPlayerId) && $edPlayerId !== ''): ?>
                                                <a class="player-name" href="<?= e(player_page_href($edPlayerId)) ?>">
                                                    <?= e(
                                                        is_string($edPlayerName) && $edPlayerName !== ''
                                                            ? $edPlayerName
                                                            : $edPlayerId
                                                    ) ?>
                                                </a>
                                            <?php else: ?>
                                                <span class="text-muted">Sin vincular</span>
                                            <?php endif; ?>
                                        </span>
                                    </li>
                                    <?php endforeach; ?>
                                </ul>
                            </div>
                            <?php else: ?>
                            <?php
                            // Sin editor: ofrecer auto-solicitud (login + clan tag).
                            $requestReturn = stats_url('clans.php', ['clan' => $clan['name']]);
                            $loginHref = '/auth/discord.php?return=' . rawurlencode($requestReturn);
                            ?>
                            <div class="clan-block__editors clan-block__editors--request">
                                <?php if ($editorDiscordId !== null): ?>
                                <form
                                    class="clan-block__request-form"
                                    method="post"
                                    action="<?= e(stats_url('clans.php')) ?>"
                                >
                                    <input type="hidden" name="csrf" value="<?= e($csrfToken) ?>">
                                    <input type="hidden" name="action" value="request_clan_editor">
                                    <input type="hidden" name="clan" value="<?= e($clan['name']) ?>">
                                    <button type="submit" class="clan-block__request-edit">
                                        Solicitar edición
                                    </button>
                                </form>
                                <?php else: ?>
                                <a class="clan-block__request-edit" href="<?= e($loginHref) ?>">
                                    Solicitar edición
                                </a>
                                <?php endif; ?>
                            </div>
                            <?php endif; ?>
                        </div>
                    </div>
                    <p class="clan-block__blurb"><?= e($blurbText) ?></p>
                    <ul class="clan-block__stats" aria-label="Totales del clan">
                        <li><span class="label">XP</span> <strong><?= number_format((int) ($clan['xp'] ?? 0), 0, ',', '.') ?></strong></li>
                        <li><span class="label">Score</span> <strong><?= number_format($clan['score'], 0, ',', '.') ?></strong></li>
                        <li><span class="label">Kills</span> <strong><?= number_format($clan['kills'], 0, ',', '.') ?></strong></li>
                        <li><span class="label">Deaths</span> <strong><?= number_format($clan['deaths'], 0, ',', '.') ?></strong></li>
                        <li><span class="label">K/D</span> <strong><?= number_format($kd, 2, ',', '.') ?></strong></li>
                        <li><span class="label">Rounds</span> <strong><?= number_format($clan['rounds'], 0, ',', '.') ?></strong></li>
                        <li><span class="label">Tesoros</span> <strong><?= number_format((int) ($clan['treasures'] ?? 0), 0, ',', '.') ?></strong></li>
                    </ul>
                    <?php if ($canEditBlurb): ?>
                    <form
                        class="clan-blurb-edit"
                        method="post"
                        enctype="multipart/form-data"
                        action="<?= e(stats_url('clans.php')) ?>#clan-<?= e($clan['anchor']) ?>"
                    >
                        <input type="hidden" name="csrf" value="<?= e($csrfToken) ?>">
                        <input type="hidden" name="action" value="save_clan_blurb">
                        <input type="hidden" name="clan" value="<?= e($clan['name']) ?>">
                        <label class="clan-blurb-edit__label" for="clan-blurb-<?= e($clan['anchor']) ?>">
                            Editar descripción <span class="text-muted">(máx. <?= CLAN_BLURB_MAX_CHARS ?> caracteres)</span>
                        </label>
                        <textarea
                            class="clan-blurb-edit__textarea"
                            id="clan-blurb-<?= e($clan['anchor']) ?>"
                            name="description"
                            rows="3"
                            maxlength="<?= CLAN_BLURB_MAX_CHARS ?>"
                        ><?= e($blurbText) ?></textarea>
                        <label class="clan-blurb-edit__label" for="clan-discord-<?= e($clan['anchor']) ?>">
                            Enlace de Discord <span class="text-muted">(vacío = ocultar botón · discord.gg / discord.com)</span>
                        </label>
                        <input
                            class="clan-blurb-edit__input"
                            type="text"
                            id="clan-discord-<?= e($clan['anchor']) ?>"
                            name="discord_url"
                            value="<?= e($discordEditValue) ?>"
                            placeholder="discord.gg/tu-invite"
                            maxlength="512"
                            autocomplete="off"
                        >
                        <label class="clan-blurb-edit__label" for="clan-logo-<?= e($clan['anchor']) ?>">
                            Cambiar logo <span class="text-muted">(JPEG, PNG o WebP · máx. 1.5 MB · ideal cuadrado, ej. 256 × 256 px)</span>
                        </label>
                        <input
                            class="clan-blurb-edit__file"
                            type="file"
                            id="clan-logo-<?= e($clan['anchor']) ?>"
                            name="logo"
                            accept="image/jpeg,image/png,image/webp"
                        >
                        <label class="clan-blurb-edit__label" for="clan-banner-<?= e($clan['anchor']) ?>">
                            Cambiar banner de fondo <span class="text-muted">(JPEG, PNG o WebP · máx. 2 MB · ideal 1600 × 400 px)</span>
                        </label>
                        <input
                            class="clan-blurb-edit__file"
                            type="file"
                            id="clan-banner-<?= e($clan['anchor']) ?>"
                            name="banner"
                            accept="image/jpeg,image/png,image/webp"
                        >
                        <?php if ($clanBannerUrl !== null): ?>
                        <label class="clan-blurb-edit__check">
                            <input type="checkbox" name="remove_banner" value="1">
                            Quitar el banner actual
                        </label>
                        <?php endif; ?>
                        <button class="btn" type="submit">Guardar cambios</button>
                    </form>
                    <?php endif; ?>
                </header>

                <?php
                // Abrir la lista solo si la búsqueda marcó algún jugador de este clan.
                $hasSearchHit = false;
                if ($searchQuery !== '') {
                    foreach ($clan['players'] as $hitPlayer) {
                        $hitName = (string) ($hitPlayer['player_name'] ?? '');
                        if ($hitName !== '' && stripos($hitName, $searchQuery) !== false) {
                            $hasSearchHit = true;
                            break;
                        }
                    }
                }
                ?>
                <details class="clan-block__players"<?= $hasSearchHit ? ' open' : '' ?>>
                    <summary class="clan-block__players-toggle">
                        <span class="clan-block__players-toggle-label">Ver jugadores</span><span class="clan-block__players-toggle-count"><?= (int) $memberCount ?></span>
                    </summary>
                    <div class="stats-table-wrap">
                        <table class="stats-table">
                            <thead>
                                <tr>
                                    <th scope="col">#</th>
                                    <th scope="col">Jugador</th>
                                    <th class="num" scope="col">XP</th>
                                    <th class="num" scope="col">Score</th>
                                    <th class="num" scope="col">Kills</th>
                                    <th class="num" scope="col">Deaths</th>
                                    <th class="num" scope="col">K/D</th>
                                    <th class="num" scope="col">Rounds</th>
                                    <th class="num" scope="col" title="Tesoros">Tesoros</th>
                                </tr>
                            </thead>
                            <tbody>
                                <?php foreach ($clan['players'] as $index => $player): ?>
                                    <?php
                                    $playerKd = kd_ratio(
                                        (int) ($player['kills'] ?? 0),
                                        (int) ($player['deaths'] ?? 0)
                                    );
                                    $playerId = (string) ($player['player_id'] ?? '');
                                    $playerName = (string) ($player['player_name'] ?? '');
                                    $playerRank = player_rank($player);
                                    $playerHighlight = $searchQuery !== ''
                                        && $playerName !== ''
                                        && stripos($playerName, $searchQuery) !== false;
                                    ?>
                                    <tr<?= $playerHighlight ? ' class="is-search-hit" id="search-hit-' . e($playerId) . '"' : '' ?>>
                                        <td class="num"><?= $index + 1 ?></td>
                                        <td>
                                            <a class="player-name" href="<?= e(player_page_href($playerId)) ?>">
                                                <?= e($playerName !== '' ? $playerName : $playerId) ?>
                                            </a>
                                            <div><?= render_rank_badge($playerRank, false, true) ?></div>
                                        </td>
                                        <td class="num"><?= number_format((int) ($playerRank['xp'] ?? 0), 0, ',', '.') ?></td>
                                        <td class="num"><?= number_format((int) ($player['score'] ?? 0), 0, ',', '.') ?></td>
                                        <td class="num"><?= number_format((int) ($player['kills'] ?? 0), 0, ',', '.') ?></td>
                                        <td class="num"><?= number_format((int) ($player['deaths'] ?? 0), 0, ',', '.') ?></td>
                                        <td class="num"><?= number_format($playerKd, 2, ',', '.') ?></td>
                                        <td class="num"><?= number_format((int) ($player['rounds'] ?? 0), 0, ',', '.') ?></td>
                                        <td class="num"><?= number_format((int) ($player['treasures'] ?? 0), 0, ',', '.') ?></td>
                                    </tr>
                                <?php endforeach; ?>
                            </tbody>
                        </table>
                    </div>
                </details>
            </section>
        <?php endforeach; ?>
    </div>
    <?php endif; ?>
<?php endif; ?>

        <script src="<?= e(asset_url('assets/js/clans.js')) ?>?v=20260726nofocus" defer></script>
<?php
render_footer();
