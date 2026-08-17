<?php
declare(strict_types=1);
require_once 'C:/nginx/html/admin/lib/demos_settings.php';

function assert_true($cond, $msg)
{
    if (!$cond) {
        fwrite(STDERR, "FAIL: $msg\n");
        exit(1);
    }
    echo "OK: $msg\n";
}

$empty = demos_settings_validate([
    'servers_visible' => [],
    'sort' => 'newest',
    'tab_2d' => 'PRdemos 2D',
    'tab_3d' => 'BF2demos 3D',
    'server_label' => 'Servidor',
]);
assert_true($empty['ok'] === false, 'empty servers rejected');

$ok = demos_settings_validate([
    'servers_visible' => ['1', '3'],
    'sort' => 'name',
    'tab_2d' => '  PRdemos 2D  ',
    'tab_3d' => 'BF2demos 3D',
    'server_label' => 'SV',
    'server_names' => [
        1 => '[LATAMSQUAD] #1 Mapas Mixtos - latamsquad.org',
        2 => '[LATAMSQUAD] #2 Ranking - EnemyVOIP - Tesoros - latamsquad.org',
        3 => '[LATAMSQUAD] #3 Cooperativo - latamsquad.org',
        4 => '[LATAMSQUAD] #4 Eventos - latamsquad.org',
    ],
]);
assert_true($ok['ok'] === true, 'valid settings accepted');
assert_true($ok['settings']['servers_visible'] === [1, 3], 'servers normalized');
assert_true($ok['settings']['sort'] === 'name', 'sort name kept');
assert_true($ok['settings']['tab_2d'] === 'PRdemos 2D', 'tab trimmed');
assert_true(
    $ok['settings']['server_names'][1] === '[LATAMSQUAD] #1 Mapas Mixtos - latamsquad.org',
    'server name 1 kept'
);

$badSort = demos_settings_validate([
    'servers_visible' => [1],
    'sort' => 'foo',
    'tab_2d' => 'A',
    'tab_3d' => 'B',
    'server_label' => 'C',
]);
assert_true($badSort['ok'] === false, 'bad sort rejected');

$long = demos_settings_validate([
    'servers_visible' => [1],
    'sort' => 'newest',
    'tab_2d' => str_repeat('x', 41),
    'tab_3d' => 'B',
    'server_label' => 'C',
]);
assert_true($long['ok'] === false, 'long tab rejected');

$longName = demos_settings_validate([
    'servers_visible' => [1],
    'sort' => 'newest',
    'tab_2d' => 'A',
    'tab_3d' => 'B',
    'server_label' => 'C',
    'server_names' => [1 => str_repeat('n', 81), 2 => 'ok', 3 => 'ok', 4 => 'ok'],
]);
assert_true($longName['ok'] === false, 'long server name rejected');

$defs = demos_settings_defaults();
assert_true($defs['sort'] === 'newest', 'default sort newest');
assert_true($defs['servers_visible'] === [1, 2, 3, 4], 'default servers');
assert_true(isset($defs['server_names'][2]), 'default server_names present');

$loaded = demos_settings_load();
assert_true(
    strpos($loaded['server_names'][1], 'Mapas Mixtos') !== false,
    'loaded JSON has real name for sv1'
);

echo "ALL PASS\n";
