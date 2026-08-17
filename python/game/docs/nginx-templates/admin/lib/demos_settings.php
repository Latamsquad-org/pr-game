<?php
declare(strict_types=1);

/**
 * Default display names from each PR install sv.serverName (serversettings.con).
 *
 * @return array<int, string>
 */
function demos_settings_default_server_names(): array
{
    return [
        1 => '[LATAMSQUAD] #1 Mapas Mixtos - latamsquad.org',
        2 => '[LATAMSQUAD] #2 Ranking - EnemyVOIP - Tesoros - latamsquad.org',
        3 => '[LATAMSQUAD] #3 Cooperativo - latamsquad.org',
        4 => '[LATAMSQUAD] #4 Eventos - latamsquad.org',
    ];
}

/**
 * Defaults for public demos listing settings.
 */
function demos_settings_defaults(): array
{
    return [
        'servers_visible' => [1, 2, 3, 4],
        'sort' => 'newest',
        'tab_2d' => 'PRdemos 2D',
        'tab_3d' => 'BF2demos 3D',
        // Legacy single hint; kept for old JSON. UI uses server_names[current].
        'server_label' => 'Servidor',
        'server_names' => demos_settings_default_server_names(),
    ];
}

/**
 * Path to public JSON under html/assets.
 */
function demos_settings_path(): string
{
    return dirname(__DIR__, 2) . '/assets/demos-settings.json';
}

/**
 * Load settings merged with defaults.
 */
function demos_settings_load(): array
{
    $defaults = demos_settings_defaults();
    $path = demos_settings_path();
    if (!is_file($path)) {
        return $defaults;
    }
    $raw = file_get_contents($path);
    $data = json_decode(is_string($raw) ? $raw : '', true);
    if (!is_array($data)) {
        return $defaults;
    }
    $parsed = demos_settings_validate(array_merge($defaults, $data));
    return $parsed['settings'];
}

/**
 * Normalize server_names map (keys 1-4, non-empty strings).
 *
 * @param mixed $raw
 * @param array<int, string> $fallback
 * @return array{names: array<int, string>, errors: list<string>}
 */
function demos_settings_normalize_server_names($raw, array $fallback): array
{
    $errors = [];
    $names = $fallback;
    if (!is_array($raw)) {
        return ['names' => $names, 'errors' => $errors];
    }
    for ($i = 1; $i <= 4; $i++) {
        if (!array_key_exists($i, $raw) && !array_key_exists((string) $i, $raw)) {
            continue;
        }
        $val = $raw[$i] ?? $raw[(string) $i];
        $name = trim((string) $val);
        if ($name === '' || strlen($name) > 80) {
            $errors[] = "server_names[$i] debe tener 1-80 caracteres";
            continue;
        }
        $names[$i] = $name;
    }
    return ['names' => $names, 'errors' => $errors];
}

/**
 * Validate input (form POST or JSON). Returns ok/errors/settings.
 *
 * @param array $in
 * @return array{ok: bool, errors: list<string>, settings: array}
 */
function demos_settings_validate(array $in): array
{
    $errors = [];
    $defaults = demos_settings_defaults();

    $rawServers = $in['servers_visible'] ?? [];
    if (!is_array($rawServers)) {
        $rawServers = [];
    }
    $servers = [];
    foreach ($rawServers as $v) {
        $n = filter_var($v, FILTER_VALIDATE_INT);
        if ($n === false || $n < 1 || $n > 4) {
            continue;
        }
        $servers[$n] = $n;
    }
    $servers = array_values($servers);
    sort($servers, SORT_NUMERIC);
    if ($servers === []) {
        $errors[] = 'Debes elegir al menos un servidor (1-4)';
        $servers = $defaults['servers_visible'];
    }

    $sort = isset($in['sort']) ? trim((string) $in['sort']) : '';
    if ($sort !== 'newest' && $sort !== 'name') {
        $errors[] = 'sort debe ser newest o name';
        $sort = $defaults['sort'];
    }

    $tab2d = isset($in['tab_2d']) ? trim((string) $in['tab_2d']) : '';
    if ($tab2d === '' || strlen($tab2d) > 40) {
        $errors[] = 'tab_2d debe tener 1-40 caracteres';
        $tab2d = $defaults['tab_2d'];
    }

    $tab3d = isset($in['tab_3d']) ? trim((string) $in['tab_3d']) : '';
    if ($tab3d === '' || strlen($tab3d) > 40) {
        $errors[] = 'tab_3d debe tener 1-40 caracteres';
        $tab3d = $defaults['tab_3d'];
    }

    // Legacy field: still accepted from old JSON/forms.
    $label = isset($in['server_label']) ? trim((string) $in['server_label']) : '';
    if ($label === '' || strlen($label) > 24) {
        if (isset($in['server_label'])) {
            $errors[] = 'server_label debe tener 1-24 caracteres';
        }
        $label = $defaults['server_label'];
    }

    $normNames = demos_settings_normalize_server_names(
        $in['server_names'] ?? $defaults['server_names'],
        $defaults['server_names']
    );
    $errors = array_merge($errors, $normNames['errors']);

    $settings = [
        'servers_visible' => $servers,
        'sort' => $sort,
        'tab_2d' => $tab2d,
        'tab_3d' => $tab3d,
        'server_label' => $label,
        'server_names' => $normNames['names'],
    ];

    return [
        'ok' => $errors === [],
        'errors' => $errors,
        'settings' => $settings,
    ];
}

/**
 * Atomic save of settings JSON.
 */
function demos_settings_save(array $settings): void
{
    $path = demos_settings_path();
    $dir = dirname($path);
    if (!is_dir($dir) && !mkdir($dir, 0755, true) && !is_dir($dir)) {
        throw new RuntimeException('No se pudo crear assets/');
    }
    $json = json_encode($settings, JSON_PRETTY_PRINT | JSON_UNESCAPED_SLASHES | JSON_UNESCAPED_UNICODE);
    if ($json === false) {
        throw new RuntimeException('JSON encode failed');
    }
    $tmp = $path . '.tmp';
    if (file_put_contents($tmp, $json . "\n") === false) {
        throw new RuntimeException('No se pudo escribir demos-settings tmp');
    }
    if (!rename($tmp, $path)) {
        @unlink($tmp);
        throw new RuntimeException('No se pudo renombrar demos-settings');
    }
}
