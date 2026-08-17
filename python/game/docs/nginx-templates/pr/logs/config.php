<?php
// Load Session class used by public/*.php (upstream has no composer autoload in tree)
require_once __DIR__ . '/app/Session.php';

$config = [];

$config['date_format'] = 'Y-m-d';
$config['hour_format'] = 'H:i:s';
$config['expiration_time'] = '30 minutes';
$config['require_login'] = false;
$config['hide_ips'] = true;
$config['with_md5'] = false;
$config['auth'] = [];

$config['servers_list'] = [];

$config['servers_list'][] = [
    'id' => 1,
    'name' => '[LATAMSQUAD] #1 Mapas Mixtos - latamsquad.org',
    'ra_adminlog' => 'C:/prbf2_1/admin/logs/ra_adminlog.txt',
    'ra_adminlog_main' => 'C:/prbf2_1/admin/logs/ra_adminlog_main.txt',
    // PR moderno: joinlog.log tiene nick/hash/IP; cdhash.txt suele estar vacio
    'cdhash' => 'C:/prbf2_1/admin/logs/joinlog.log',
    'cdhash_main' => '',
    'whitelist' => 'C:/prbf2_1/admin/logs/whitelist.txt',
    'banlist' => 'C:/prbf2_1/admin/logs/banlist.con',
    'local_name' => 'latam_sv1.txt',
];

$config['servers_list'][] = [
    'id' => 2,
    'name' => '[LATAMSQUAD] #2 Ranking - EnemyVOIP - Tesoros - latamsquad.org',
    'ra_adminlog' => 'C:/prbf2_2/admin/logs/ra_adminlog.txt',
    'ra_adminlog_main' => 'C:/prbf2_2/admin/logs/ra_adminlog_main.txt',
    'cdhash' => 'C:/prbf2_2/admin/logs/joinlog.log',
    'cdhash_main' => '',
    'whitelist' => 'C:/prbf2_2/admin/logs/whitelist.txt',
    'banlist' => 'C:/prbf2_2/admin/logs/banlist.con',
    'local_name' => 'latam_sv2.txt',
];

$config['servers_list'][] = [
    'id' => 3,
    'name' => '[LATAMSQUAD] #3 Cooperativo - latamsquad.org',
    'ra_adminlog' => 'C:/prbf2_3/admin/logs/ra_adminlog.txt',
    'ra_adminlog_main' => 'C:/prbf2_3/admin/logs/ra_adminlog_main.txt',
    'cdhash' => 'C:/prbf2_3/admin/logs/joinlog.log',
    'cdhash_main' => '',
    'whitelist' => 'C:/prbf2_3/admin/logs/whitelist.txt',
    'banlist' => 'C:/prbf2_3/admin/logs/banlist.con',
    'local_name' => 'latam_sv3.txt',
];

$config['servers_list'][] = [
    'id' => 4,
    'name' => '[LATAMSQUAD] #4 Eventos - latamsquad.org',
    'ra_adminlog' => 'C:/prbf2_4/admin/logs/ra_adminlog.txt',
    'ra_adminlog_main' => 'C:/prbf2_4/admin/logs/ra_adminlog_main.txt',
    'cdhash' => 'C:/prbf2_4/admin/logs/joinlog.log',
    'cdhash_main' => '',
    'whitelist' => 'C:/prbf2_4/admin/logs/whitelist.txt',
    'banlist' => 'C:/prbf2_4/admin/logs/banlist.con',
    'local_name' => 'latam_sv4.txt',
];

$config['server_commands'] = [
    ['name' => 'SETNEXT', 'color' => 'success', 'value' => ['SETNEXT']],
    ['name' => 'RUNNEXT', 'color' => 'danger', 'value' => ['RUNNEXT']],
    ['name' => 'MAPVOTE', 'color' => 'success', 'value' => ['MAPVOTE']],
    ['name' => 'REPORT', 'color' => 'danger', 'value' => ['REPORT']],
    ['name' => 'REPORT PLAYER', 'color' => 'danger', 'value' => ['REPORTP']],
    ['name' => 'WARNING', 'color' => 'warning', 'value' => ['WARN']],
    ['name' => 'KICK', 'color' => 'danger', 'value' => ['KICK']],
    ['name' => 'TEMP BAN', 'color' => 'danger', 'value' => ['TEMPBAN']],
    ['name' => 'PERM BAN', 'color' => 'danger', 'value' => ['BAN']],
    ['name' => 'RESIGN', 'color' => 'danger', 'value' => ['RESIGN']],
    ['name' => 'HISTORY', 'color' => 'success', 'value' => ['HISTORY']],
    ['name' => 'SCRAMBLE', 'color' => 'danger', 'value' => ['SCRAMBLE']],
    ['name' => 'SAY / SAYTEAM', 'color' => 'success', 'value' => ['SAY', 'SAYTEAM']],
    ['name' => 'SWITCH', 'color' => 'success', 'value' => ['SWITCH']],
    ['name' => 'SWAPTEAMS', 'color' => 'success', 'value' => 'SWAPTEAMS'],
    ['name' => 'FLY', 'color' => 'success', 'value' => ['FLY']],
    ['name' => 'UNBAN', 'color' => 'danger', 'value' => ['UNBAN']],
    ['name' => 'INIT', 'color' => 'success', 'value' => 'INIT'],
    ['name' => 'RELOAD', 'color' => 'success', 'value' => 'RELOAD'],
    ['name' => 'TICKETS', 'color' => 'warning', 'value' => 'TICKETS'],
    ['name' => 'TIMEBAN', 'color' => 'danger', 'value' => 'TIMEBAN'],
    ['name' => 'STOPSERVER', 'color' => 'danger', 'value' => 'STOPSERVER'],
    ['name' => 'MESSAGE', 'color' => 'success', 'value' => 'MESSAGE'],
    ['name' => 'KILL', 'color' => 'danger', 'value' => 'KILL'],
    ['name' => 'RESIGNALL', 'color' => 'danger', 'value' => 'RESIGNALL'],
];

$config['full_width'] = false;
$config['modal_height'] = '700px';

$GLOBALS['config'] = $config;
