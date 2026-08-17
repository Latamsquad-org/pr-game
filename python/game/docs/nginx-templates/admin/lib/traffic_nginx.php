<?php
declare(strict_types=1);

require_once __DIR__ . '/traffic_settings.php';

function traffic_nginx_paths(): array
{
    return [
        'nginx_dir' => 'C:/nginx',
        'nginx_exe' => 'C:/nginx/nginx.exe',
        'zones' => 'C:/nginx/conf/latam-traffic-zones.conf',
        'limits' => 'C:/nginx/conf/latam-traffic-limits.conf',
        'backup_root' => 'C:/nginx/conf/backup',
    ];
}

function traffic_nginx_atomic_write(string $path, string $contents): void
{
    $tmp = $path . '.tmp';
    if (file_put_contents($tmp, $contents) === false) {
        throw new RuntimeException('write failed: ' . $path);
    }
    if (!rename($tmp, $path)) {
        @unlink($tmp);
        throw new RuntimeException('rename failed: ' . $path);
    }
}

function traffic_nginx_run(string $arg): array
{
    $p = traffic_nginx_paths();
    $cmd = escapeshellarg($p['nginx_exe']) . ' ' . $arg;
    $descriptors = [1 => ['pipe', 'w'], 2 => ['pipe', 'w']];
    $proc = proc_open($cmd, $descriptors, $pipes, $p['nginx_dir']);
    if (!is_resource($proc)) {
        return ['code' => 1, 'out' => '', 'err' => 'proc_open failed'];
    }
    $out = stream_get_contents($pipes[1]);
    $err = stream_get_contents($pipes[2]);
    fclose($pipes[1]);
    fclose($pipes[2]);
    $code = proc_close($proc);
    return ['code' => $code, 'out' => (string) $out, 'err' => (string) $err];
}

/**
 * Backup, write confs, nginx -t, restore or reload.
 */
function traffic_nginx_apply(array $settings): array
{
    $p = traffic_nginx_paths();
    $stamp = gmdate('Ymd-His');
    $backupDir = $p['backup_root'] . '/traffic-' . $stamp;
    if (!is_dir($p['backup_root']) && !mkdir($p['backup_root'], 0755, true) && !is_dir($p['backup_root'])) {
        return ['ok' => false, 'message' => 'No se pudo crear carpeta backup', 'backup' => null, 'nginx_log' => ''];
    }
    if (!mkdir($backupDir) && !is_dir($backupDir)) {
        return ['ok' => false, 'message' => 'No se pudo crear backup dir', 'backup' => null, 'nginx_log' => ''];
    }

    foreach (['zones', 'limits'] as $key) {
        $src = $p[$key];
        if (is_file($src)) {
            copy($src, $backupDir . '/' . basename($src));
        }
    }

    try {
        traffic_settings_save($settings);
        traffic_nginx_atomic_write($p['zones'], traffic_generate_zones_conf($settings));
        traffic_nginx_atomic_write($p['limits'], traffic_generate_limits_conf($settings));
    } catch (Throwable $e) {
        return ['ok' => false, 'message' => $e->getMessage(), 'backup' => $backupDir, 'nginx_log' => ''];
    }

    $test = traffic_nginx_run('-t');
    $log = trim($test['err'] . "\n" . $test['out']);
    if ($test['code'] !== 0) {
        foreach (['zones', 'limits'] as $key) {
            $bak = $backupDir . '/' . basename($p[$key]);
            if (is_file($bak)) {
                copy($bak, $p[$key]);
            }
        }
        return [
            'ok' => false,
            'message' => 'nginx -t fallo; se restauro el backup',
            'backup' => $backupDir,
            'nginx_log' => substr($log, 0, 2000),
        ];
    }

    $reload = traffic_nginx_run('-s reload');
    $log2 = trim($log . "\n" . $reload['err'] . "\n" . $reload['out']);
    if ($reload['code'] !== 0) {
        return [
            'ok' => false,
            'message' => 'nginx -t OK pero reload fallo',
            'backup' => $backupDir,
            'nginx_log' => substr($log2, 0, 2000),
        ];
    }

    return [
        'ok' => true,
        'message' => 'Limites aplicados y Nginx recargado',
        'backup' => $backupDir,
        'nginx_log' => substr($log2, 0, 2000),
    ];
}
