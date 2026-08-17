<?php

declare(strict_types=1);

/**
 * Sistema de rangos militares (cálculo al vuelo).
 * Spec: docs/superpowers/specs/2026-07-15-latamstats-military-ranks-design.md
 */

/**
 * @return list<array{id:int,slug:string,name:string,abbr:string,xp_min:int,icon:string}>
 */
function ranks_table(): array
{
    return [
        ['id' => 1, 'slug' => 'recluta', 'name' => 'Recluta', 'abbr' => 'REC', 'xp_min' => 0, 'icon' => 'assets/img/ranks/recluta.svg'],
        ['id' => 2, 'slug' => 'soldado', 'name' => 'Soldado', 'abbr' => 'SLD', 'xp_min' => 30000, 'icon' => 'assets/img/ranks/soldado.svg'],
        ['id' => 3, 'slug' => 'cabo', 'name' => 'Cabo', 'abbr' => 'CAB', 'xp_min' => 100000, 'icon' => 'assets/img/ranks/cabo.svg'],
        ['id' => 4, 'slug' => 'cabo-primero', 'name' => 'Cabo Primero', 'abbr' => 'CAB1', 'xp_min' => 250000, 'icon' => 'assets/img/ranks/cabo-primero.svg'],
        ['id' => 5, 'slug' => 'sargento', 'name' => 'Sargento', 'abbr' => 'SGT', 'xp_min' => 500000, 'icon' => 'assets/img/ranks/sargento.svg'],
        ['id' => 6, 'slug' => 'sargento-primero', 'name' => 'Sargento Primero', 'abbr' => 'SGT1', 'xp_min' => 1000000, 'icon' => 'assets/img/ranks/sargento-primero.svg'],
        ['id' => 7, 'slug' => 'teniente', 'name' => 'Teniente', 'abbr' => 'TTE', 'xp_min' => 1500000, 'icon' => 'assets/img/ranks/teniente.svg'],
        ['id' => 8, 'slug' => 'capitan', 'name' => 'Capitán', 'abbr' => 'CAP', 'xp_min' => 2500000, 'icon' => 'assets/img/ranks/capitan.svg'],
        ['id' => 9, 'slug' => 'mayor', 'name' => 'Mayor', 'abbr' => 'MYR', 'xp_min' => 4000000, 'icon' => 'assets/img/ranks/mayor.svg'],
        ['id' => 10, 'slug' => 'teniente-coronel', 'name' => 'Teniente Coronel', 'abbr' => 'TCOL', 'xp_min' => 6000000, 'icon' => 'assets/img/ranks/teniente-coronel.svg'],
        ['id' => 11, 'slug' => 'coronel', 'name' => 'Coronel', 'abbr' => 'COR', 'xp_min' => 8000000, 'icon' => 'assets/img/ranks/coronel.svg'],
        ['id' => 12, 'slug' => 'general', 'name' => 'General', 'abbr' => 'GEN', 'xp_min' => 10000000, 'icon' => 'assets/img/ranks/general.svg'],
    ];
}

/**
 * URL pública del SVG de insignia, o string vacío si no hay archivo.
 *
 * @param array{icon?:string,name?:string,slug?:string} $rank
 */
function rank_icon_url(array $rank): string
{
    $icon = trim((string) ($rank['icon'] ?? ''));
    if ($icon === '') {
        return '';
    }

    $absolute = dirname(__DIR__) . '/' . str_replace('\\', '/', $icon);
    if (!is_file($absolute)) {
        return '';
    }

    return asset_url($icon);
}

/**
 * HTML &lt;img&gt; de insignia, o vacío si no hay archivo.
 *
 * @param array{icon?:string,name?:string} $rank
 */
function render_rank_icon(array $rank, string $cssClass = 'rank-badge__icon', int $size = 20): string
{
    $url = rank_icon_url($rank);
    if ($url === '') {
        return '';
    }

    $name = (string) ($rank['name'] ?? 'Rango');

    return '<img class="' . e($cssClass) . '" src="' . e($url) . '" alt="' . e($name) . '"'
        . ' width="' . $size . '" height="' . $size . '" loading="lazy">';
}

/**
 * @return array{id:int,slug:string,name:string,abbr:string,xp_min:int,icon:string}|null
 */
function rank_by_id(int $id): ?array
{
    foreach (ranks_table() as $rank) {
        if ($rank['id'] === $id) {
            return $rank;
        }
    }

    return null;
}

function rank_account_days(?string $created, ?int $nowTs = null): int
{
    if ($created === null || trim($created) === '') {
        return 0;
    }

    $trimmed = trim($created);

    // Rechazar fechas MySQL nulas o inválidas antes de parsear.
    if (preg_match('/^0000-00-00/', $trimmed)) {
        return 0;
    }

    $utc = new DateTimeZone('UTC');

    try {
        // MySQL naive datetime (Y-m-d H:i:s) → interpretar como UTC.
        if (preg_match('/^\d{4}-\d{2}-\d{2} \d{2}:\d{2}:\d{2}$/', $trimmed)) {
            $createdDt = DateTimeImmutable::createFromFormat('Y-m-d H:i:s', $trimmed, $utc);
            if ($createdDt === false) {
                return 0;
            }
            $parseErrors = DateTimeImmutable::getLastErrors();
            if ($parseErrors !== false && ($parseErrors['warning_count'] > 0 || $parseErrors['error_count'] > 0)) {
                return 0;
            }
        } elseif (preg_match('/(Z|[+-]\d{2}:?\d{2})$/', $trimmed)) {
            // ISO 8601 u otro formato con offset explícito → normalizar a UTC.
            $createdDt = (new DateTimeImmutable($trimmed))->setTimezone($utc);
            $parseErrors = DateTimeImmutable::getLastErrors();
            if ($parseErrors !== false && ($parseErrors['warning_count'] > 0 || $parseErrors['error_count'] > 0)) {
                return 0;
            }
        } else {
            // Sin zona horaria → tratar instante como UTC.
            $createdDt = new DateTimeImmutable($trimmed, $utc);
            $parseErrors = DateTimeImmutable::getLastErrors();
            if ($parseErrors !== false && ($parseErrors['warning_count'] > 0 || $parseErrors['error_count'] > 0)) {
                return 0;
            }
        }

        $now = $nowTs ?? time();
        $days = (int) floor(($now - $createdDt->getTimestamp()) / 86400);

        return max(0, $days);
    } catch (Throwable) {
        return 0;
    }
}

function rank_max_id_for_days(int $days): int
{
    if ($days < 7) {
        return 3; // Cabo
    }
    if ($days < 30) {
        return 5; // Sargento
    }
    if ($days < 90) {
        return 7; // Teniente
    }
    if ($days < 180) {
        return 8; // Capitán
    }
    if ($days < 365) {
        return 11; // Coronel
    }

    return 12; // General
}

function rank_next_age_unlock_days(int $days): ?int
{
    if ($days < 7) {
        return 7;
    }
    if ($days < 30) {
        return 30;
    }
    if ($days < 90) {
        return 90;
    }
    if ($days < 180) {
        return 180;
    }
    if ($days < 365) {
        return 365;
    }

    return null;
}

/**
 * XP extra por cada tesoro encontrado (alineado con TREASURE_XP_BONUS in-game).
 */
const RANK_TREASURE_XP_BONUS = 5000;

/**
 * Expresion SQL de XP (misma formula que rank_compute_xp).
 * Columnas sin alias: score, kills, deaths, treasures.
 */
function rank_xp_sql_expression(): string
{
    $bonus = (int) RANK_TREASURE_XP_BONUS;

    return '((score * 3) + kills - (deaths * 2))'
        . ' * (1 + ((kills / GREATEST(deaths, 1)) * 0.25))'
        . ' + (COALESCE(treasures, 0) * ' . $bonus . ')';
}

function rank_compute_xp(int $score, int $kills, int $deaths, int $treasures = 0): float
{
    $kd = $kills / (float) max($deaths, 1);
    $base = ($score * 3) + $kills - ($deaths * 2);
    $bonus = $treasures * RANK_TREASURE_XP_BONUS;

    return $base * (1.0 + ($kd * 0.25)) + $bonus;
}

/**
 * @param array<string, mixed> $player
 * @return array{
 *   xp: int,
 *   rank: array{id:int,slug:string,name:string,abbr:string,xp_min:int},
 *   next: ?array{id:int,slug:string,name:string,abbr:string,xp_min:int},
 *   progress: float,
 *   max_rank_id: int,
 *   capped_by_age: bool,
 *   days: int
 * }
 */
function player_rank(array $player, ?int $nowTs = null): array
{
    $score = (int) ($player['score'] ?? 0);
    $kills = (int) ($player['kills'] ?? 0);
    $deaths = (int) ($player['deaths'] ?? 0);
    $treasures = (int) ($player['treasures'] ?? 0);
    $created = isset($player['created']) ? (string) $player['created'] : null;

    $xpFloat = rank_compute_xp($score, $kills, $deaths, $treasures);
    $xp = (int) round($xpFloat);
    $days = rank_account_days($created, $nowTs);
    $maxRankId = rank_max_id_for_days($days);

    $table = ranks_table();
    $xpUnlockedId = 1;
    $current = $table[0];

    // Un solo recorrido: rango más alto con XP suficiente y dentro del tope por antigüedad.
    foreach ($table as $rank) {
        if ($rank['xp_min'] <= $xpFloat) {
            $xpUnlockedId = $rank['id'];
        }
        if ($rank['xp_min'] <= $xpFloat && $rank['id'] <= $maxRankId) {
            $current = $rank;
        }
    }

    $cappedByAge = $xpUnlockedId > $maxRankId;

    $next = null;
    foreach ($table as $rank) {
        if ($rank['id'] <= $maxRankId && $rank['xp_min'] > $xpFloat) {
            $next = $rank;
            break;
        }
    }

    $progress = 1.0;
    if ($next !== null) {
        $span = $next['xp_min'] - $current['xp_min'];
        if ($span > 0) {
            $progress = ($xpFloat - $current['xp_min']) / (float) $span;
            $progress = max(0.0, min(1.0, $progress));
        }
    }

    return [
        'xp' => $xp,
        'rank' => $current,
        'next' => $next,
        'progress' => $progress,
        'max_rank_id' => $maxRankId,
        'capped_by_age' => $cappedByAge,
        'days' => $days,
    ];
}

/**
 * Badge HTML compacto para tablas.
 *
 * @param array<string, mixed> $rankResult resultado de player_rank()
 */
function render_rank_badge(array $rankResult): string
{
    $rank = $rankResult['rank'] ?? null;
    if (!is_array($rank)) {
        return '';
    }

    $name = (string) ($rank['name'] ?? '');
    $abbr = (string) ($rank['abbr'] ?? '');
    $slug = (string) ($rank['slug'] ?? '');
    $capped = !empty($rankResult['capped_by_age']);

    $class = 'rank-badge rank-badge--' . preg_replace('/[^a-z0-9-]/', '', $slug);
    if ($capped) {
        $class .= ' is-capped';
    }

    $title = $name;
    if ($capped) {
        $title .= ' (tope por antigüedad)';
    }

    $iconHtml = render_rank_icon($rank, 'rank-badge__icon', 20);

    return '<span class="' . e($class) . '" title="' . e($title) . '">'
        . $iconHtml
        . '<span class="rank-badge__abbr">' . e($abbr) . '</span> '
        . '<span class="rank-badge__name">' . e($name) . '</span>'
        . '</span>';
}
