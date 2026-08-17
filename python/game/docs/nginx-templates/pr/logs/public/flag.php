<?php
/**
 * Sirve bandera de pais para una IP o codigo ISO (cc).
 * Cache local para no depender de geonames/freegeoip en cada request.
 * Content-Type correcto: necesario por X-Content-Type-Options: nosniff.
 */

error_reporting(0);
ini_set('display_errors', '0');

$cacheDir = __DIR__ . '/flags_cache';
if (!is_dir($cacheDir)) {
    @mkdir($cacheDir, 0755, true);
}

$cc = '';
if (!empty($_GET['cc'])) {
    $cc = strtolower(preg_replace('/[^a-zA-Z]/', '', $_GET['cc']));
} elseif (!empty($_GET['ip'])) {
    $cc = resolveCountryCode(trim($_GET['ip']), $cacheDir);
}

if ($cc === '' || strlen($cc) !== 2) {
    serveEmptyPng();
    exit;
}

$cacheFile = $cacheDir . '/' . $cc . '.png';
if (!is_file($cacheFile) || filesize($cacheFile) < 50) {
    $png = @file_get_contents('https://flagcdn.com/w40/' . $cc . '.png');
    if ($png === false || strlen($png) < 50) {
        $png = @file_get_contents('https://flagcdn.com/24x18/' . $cc . '.png');
    }
    if ($png !== false && strlen($png) >= 50) {
        @file_put_contents($cacheFile, $png);
    }
}

if (is_file($cacheFile) && filesize($cacheFile) >= 50) {
    header('Content-Type: image/png');
    header('Cache-Control: public, max-age=86400');
    readfile($cacheFile);
    exit;
}

serveEmptyPng();

/**
 * GeoIP con cache por IP (archivo) y APIs de respaldo.
 */
function resolveCountryCode($ip, $cacheDir)
{
    if (!filter_var($ip, FILTER_VALIDATE_IP)) {
        return '';
    }

    $ipKey = preg_replace('/[^0-9a-fA-F\.:]/', '', $ip);
    $geoCache = $cacheDir . '/geo_' . md5($ipKey) . '.txt';
    if (is_file($geoCache) && (time() - filemtime($geoCache)) < 604800) {
        $cached = trim(@file_get_contents($geoCache));
        if (preg_match('/^[a-z]{2}$/', $cached)) {
            return $cached;
        }
    }

    $cc = '';

    $json = @file_get_contents('https://freegeoip.app/json/' . rawurlencode($ip));
    if ($json) {
        $data = json_decode($json);
        if (!empty($data->country_code)) {
            $cc = strtolower($data->country_code);
        }
    }

    if ($cc === '') {
        $json = @file_get_contents('http://ip-api.com/json/' . rawurlencode($ip) . '?fields=status,countryCode');
        if ($json) {
            $data = json_decode($json);
            if (!empty($data->status) && $data->status === 'success' && !empty($data->countryCode)) {
                $cc = strtolower($data->countryCode);
            }
        }
    }

    if ($cc !== '' && preg_match('/^[a-z]{2}$/', $cc)) {
        @file_put_contents($geoCache, $cc);
        return $cc;
    }

    return '';
}

function serveEmptyPng()
{
    $png = base64_decode(
        'iVBORw0KGgoAAAANSUhEUgAAAAEAAAABCAYAAAAfFcSJAAAADUlEQVR42mP8z8BQDwAEhQGAhKmMIQAAAABJRU5ErkJggg=='
    );
    header('Content-Type: image/png');
    header('Cache-Control: no-cache');
    echo $png;
}
