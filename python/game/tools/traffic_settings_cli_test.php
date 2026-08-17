<?php
declare(strict_types=1);
require_once 'C:/nginx/html/admin/lib/traffic_settings.php';

function assert_true($cond, $msg) {
    if (!$cond) { fwrite(STDERR, "FAIL: $msg\n"); exit(1); }
    echo "OK: $msg\n";
}

$bad = traffic_settings_validate(['enabled' => true, 'demo_conn_per_ip' => 0, 'demo_rate_mbs' => 8, 'autoindex_req_per_min' => 60]);
assert_true($bad['ok'] === false, 'conn 0 rejected');

$ok = traffic_settings_validate(['enabled' => '1', 'demo_conn_per_ip' => '2', 'demo_rate_mbs' => '8.5', 'autoindex_req_per_min' => '60']);
assert_true($ok['ok'] === true, 'valid settings accepted');
assert_true($ok['settings']['demo_rate_mbs'] === 8.5, 'rate float kept');

$zones = traffic_generate_zones_conf($ok['settings']);
assert_true(strpos($zones, 'limit_conn_zone') !== false, 'zones has conn zone');
assert_true(strpos($zones, 'rate=60r/m') !== false, 'zones has req rate');

$limOn = traffic_generate_limits_conf($ok['settings']);
assert_true(strpos($limOn, 'limit_conn') !== false, 'limits on has conn');
assert_true(strpos($limOn, 'limit_rate') !== false, 'limits on has rate');

$off = $ok['settings'];
$off['enabled'] = false;
$limOff = traffic_generate_limits_conf($off);
assert_true(strpos($limOff, 'limit_conn') === false, 'limits off has no limit_conn');

echo "ALL PASS\n";
