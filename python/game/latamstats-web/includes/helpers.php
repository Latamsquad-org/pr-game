<?php

declare(strict_types=1);

/**
 * K/D: si deaths==0 devuelve kills como float; si no kills/deaths.
 * Misma fórmula que latamstats.py (Python).
 *
 * @param int|string|null $kills
 * @param int|string|null $deaths
 */
function kd_ratio($kills, $deaths): float
{
    $k = (int) ($kills ?? 0);
    $d = (int) ($deaths ?? 0);

    if ($d === 0) {
        return (float) $k;
    }

    return $k / (float) $d;
}

/**
 * Escape seguro para salida HTML en plantillas.
 */
function e(?string $str): string
{
    return htmlspecialchars($str ?? '', ENT_QUOTES | ENT_SUBSTITUTE, 'UTF-8');
}

/**
 * Base URL del sitio ('' en la raíz del host).
 * Subcarpetas de app (admin/auth/api/…) no cuentan como raíz.
 */
function site_base_path(): string
{
    $scriptDir = str_replace('\\', '/', dirname((string) ($_SERVER['SCRIPT_NAME'] ?? '/')));
    $base = rtrim($scriptDir, '/');
    if ($base === '' || $base === '.' || $base === '/') {
        return '';
    }

    $leaf = basename($base);
    if (in_array($leaf, ['admin', 'auth', 'api', 'includes', 'tests'], true)) {
        $parent = rtrim(str_replace('\\', '/', dirname($base)), '/');
        if ($parent === '' || $parent === '.' || $parent === '/') {
            return '';
        }
        return $parent;
    }

    return $base;
}

/**
 * Ruta de un asset estático desde la raíz del sitio.
 */
function asset_url(string $path): string
{
    $base = site_base_path();
    $rel = ltrim($path, '/');

    return ($base === '' ? '' : $base) . '/' . $rel;
}

/**
 * Formatea el timestamp de sync del payload.
 * Resta 3 horas (UTC del servidor → hora local deseada).
 */
function format_last_sync(?string $timestamp): string
{
    if ($timestamp === null || trim($timestamp) === '') {
        return 'Sin datos';
    }

    try {
        $trimmed = trim($timestamp);

        // Con Z/offset: respetar esa zona. Sin zona: interpretar como UTC (payload del servidor).
        if (preg_match('/(?:[zZ]|[+-]\d{2}:?\d{2})$/', $trimmed) === 1) {
            $dt = new DateTimeImmutable($trimmed);
        } else {
            $dt = new DateTimeImmutable($trimmed, new DateTimeZone('UTC'));
        }

        // Payload viene en UTC; mostrar 3 horas menos.
        $dt = $dt->modify('-3 hours');

        return $dt->format('d/m/Y H:i');
    } catch (Throwable $error) {
        return e($timestamp);
    }
}

/**
 * Bandera de Brasil como &lt;img&gt; (data-URI; evita emoji "BR" en Windows).
 */
function brazil_flag_img(int $width = 30, int $height = 21): string
{
    $svg = '<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 20 14">'
        . '<rect width="20" height="14" fill="#009b3a"/>'
        . '<polygon points="10,1 19,7 10,13 1,7" fill="#fedf00"/>'
        . '<circle cx="10" cy="7" r="3.5" fill="#002776"/>'
        . '<path d="M6.2 7.1 Q10 9.4 13.8 7.1 Q10 6.7 6.2 7.1" fill="#fff"/>'
        . '</svg>';
    $dataUri = 'data:image/svg+xml;base64,' . base64_encode($svg);

    return '<img class="metric__flag" src="' . e($dataUri) . '" alt="Brasil" title="Brasil"'
        . ' width="' . $width . '" height="' . $height . '" loading="lazy">';
}

/**
 * Indica si la página actual coincide con el script dado (p. ej. index.php).
 */
function is_current_page(string $scriptName): bool
{
    $script = str_replace('\\', '/', (string) ($_SERVER['SCRIPT_NAME'] ?? ''));
    $current = basename($script);

    // Landing: / o /index.php cuentan como inicio del hub de juegos.
    // No marcar “Juegos” activo en /admin/index.php u otros index de subcarpeta.
    if ($scriptName === 'index.php') {
        if (str_contains($script, '/admin/') || str_contains($script, '/auth/')) {
            return false;
        }
        return $current === 'index.php' || $current === '' || $current === '/';
    }

    return $current === $scriptName;
}

/**
 * URL limpia de la landing (sin “index.php” en la barra de direcciones).
 */
function home_url(): string
{
    $base = site_base_path();

    return $base === '' ? '/' : $base . '/';
}

/**
 * Indica si el tag de clan es vacío o placeholder (jugadores sin clan real).
 * En PR el tag "=+=" suele usarse como “sin clan”.
 */
function clan_is_empty(?string $clan): bool
{
    $trimmed = trim((string) $clan);

    if ($trimmed === '') {
        return true;
    }

    // Placeholder habitual de Project Reality para jugadores sin clan.
    if ($trimmed === '=+=') {
        return true;
    }

    return false;
}

/**
 * Nombre de clan para mostrar; vacio / placeholder = Sin clan.
 */
function clan_display_name(?string $clan): string
{
    return clan_is_empty($clan) ? 'Sin clan' : trim((string) $clan);
}

/**
 * Compara tags de clan de forma flexible (mayusculas y mismo slug #clan-...).
 * Ej.: [KKCK[ y [kkck[ coinciden.
 */
function clan_tags_match(string $a, string $b): bool
{
    $left = clan_display_name($a);
    $right = clan_display_name($b);

    if ($left === 'Sin clan' || $right === 'Sin clan') {
        return $left === $right;
    }

    if (strcasecmp($left, $right) === 0) {
        return true;
    }

    return clan_anchor_key($left) === clan_anchor_key($right);
}

/**
 * Clave estable para anclas en clans.php (#clan-...).
 */
function clan_anchor_key(string $displayName): string
{
    $key = strtolower($displayName);
    $key = preg_replace('/[^a-z0-9]+/i', '-', $key) ?? 'clan';
    $key = trim($key, '-');

    return $key !== '' ? $key : 'sin-clan';
}

/**
 * Ancla HTML de un clan (#clan-...), a partir del nombre visible.
 */
function clan_html_anchor(string $clanName): string
{
    return clan_anchor_key(clan_display_name($clanName));
}

/**
 * Agrupa jugadores por clan y suma score/kills/deaths/rounds/tesoros/XP.
 * Cada jugador incluye _xp para ordenar dentro del clan.
 *
 * @param list<array<string, mixed>> $players
 * @return array<string, array{
 *   name: string,
 *   anchor: string,
 *   players: list<array<string, mixed>>,
 *   score: int,
 *   kills: int,
 *   deaths: int,
 *   rounds: int,
 *   treasures: int,
 *   xp: int
 * }>
 */
function clan_aggregate_from_players(array $players): array
{
    $clans = [];

    foreach ($players as $row) {
        // No listar jugadores sin clan real (vacio o tag =+=).
        if (clan_is_empty($row['player_clan'] ?? '')) {
            continue;
        }

        $name = clan_display_name($row['player_clan'] ?? '');
        $anchor = clan_anchor_key($name);

        if (!isset($clans[$anchor])) {
            $clans[$anchor] = [
                'name' => $name,
                'anchor' => $anchor,
                'players' => [],
                'score' => 0,
                'kills' => 0,
                'deaths' => 0,
                'rounds' => 0,
                'treasures' => 0,
                'xp' => 0,
            ];
        }

        $playerXp = (int) round(rank_compute_xp(
            (int) ($row['score'] ?? 0),
            (int) ($row['kills'] ?? 0),
            (int) ($row['deaths'] ?? 0),
            (int) ($row['treasures'] ?? 0)
        ));
        $row['_xp'] = $playerXp;

        $clans[$anchor]['players'][] = $row;
        $clans[$anchor]['score'] += (int) ($row['score'] ?? 0);
        $clans[$anchor]['kills'] += (int) ($row['kills'] ?? 0);
        $clans[$anchor]['deaths'] += (int) ($row['deaths'] ?? 0);
        $clans[$anchor]['rounds'] += (int) ($row['rounds'] ?? 0);
        $clans[$anchor]['treasures'] += (int) ($row['treasures'] ?? 0);
        $clans[$anchor]['xp'] += $playerXp;
    }

    return $clans;
}

/**
 * Extensiones de imagen aceptadas para logos de clan.
 *
 * @return list<string>
 */
function clan_logo_extensions(): array
{
    return ['png', 'jpg', 'jpeg', 'webp', 'svg', 'gif'];
}

/**
 * Extensiones permitidas en uploads de logo/banner (editores).
 *
 * @return list<string>
 */
function clan_upload_extensions(): array
{
    return ['jpg', 'jpeg', 'png', 'webp'];
}

/**
 * Extrae el texto de presentación desde una entrada de clans_info.
 * Acepta aliases: blurb, descripcion, descripción, description, texto.
 */
function clan_entry_blurb(array $entry): string
{
    foreach (['blurb', 'descripcion', 'descripción', 'description', 'texto'] as $alias) {
        if (!isset($entry[$alias]) || !is_string($entry[$alias])) {
            continue;
        }
        $text = trim($entry[$alias]);
        if ($text !== '') {
            return $text;
        }
    }

    return '';
}

/**
 * Extrae URL de Discord desde una entrada de clans_info.
 * Acepta aliases: discord, discord_url, invite.
 */
function clan_entry_discord(array $entry): string
{
    foreach (['discord', 'discord_url', 'invite'] as $alias) {
        if (!isset($entry[$alias]) || !is_string($entry[$alias])) {
            continue;
        }
        $url = trim($entry[$alias]);
        if ($url === '') {
            continue;
        }
        // Solo http(s) para evitar javascript: u otros esquemas.
        if (preg_match('#^https?://#i', $url) !== 1) {
            continue;
        }

        return $url;
    }

    return '';
}

/**
 * Carga includes/clans_info.php (logo + blurb + discord por clan).
 * Indexa cada clan por nombre original y por slug (ej. KKCK + kkck).
 *
 * @return array<string, array{logo?:string, blurb?:string, discord?:string}>
 */
function clans_info(): array
{
    static $info = null;

    if ($info !== null) {
        return $info;
    }

    $path = __DIR__ . '/clans_info.php';
    if (!is_file($path)) {
        $info = [];

        return $info;
    }

    $loaded = require $path;
    if (!is_array($loaded)) {
        $info = [];

        return $info;
    }

    $normalized = [];
    foreach ($loaded as $key => $entry) {
        $clanKey = trim((string) $key);
        if ($clanKey === '') {
            continue;
        }

        // Compat: valor string suelto = solo logo (formato viejo de clan_logo_map).
        if (is_string($entry)) {
            $logo = trim($entry);
            $row = $logo !== '' ? ['logo' => $logo] : [];
        } elseif (is_array($entry)) {
            $row = [];
            if (isset($entry['logo']) && is_string($entry['logo']) && trim($entry['logo']) !== '') {
                $row['logo'] = trim($entry['logo']);
            }
            $blurb = clan_entry_blurb($entry);
            if ($blurb !== '') {
                $row['blurb'] = $blurb;
            }
            $discord = clan_entry_discord($entry);
            if ($discord !== '') {
                $row['discord'] = $discord;
            }
        } else {
            continue;
        }

        // Registrar por clave original y por slug para que el lookup no falle.
        $normalized[$clanKey] = $row;
        $slug = clan_anchor_key($clanKey);
        if ($slug !== '' && !isset($normalized[$slug])) {
            $normalized[$slug] = $row;
        }
    }

    $info = $normalized;

    return $info;
}

/**
 * Busca la entrada de clans_info para un clan (nombre, slug o sin corchetes).
 *
 * @return array{logo?:string, blurb?:string, discord?:string}
 */
function clan_info_for(string $clanName): array
{
    $display = clan_display_name($clanName);
    $stripped = trim($display, "[] \t");
    $info = clans_info();

    $candidates = [
        $display,
        $stripped,
        clan_anchor_key($display),
        clan_anchor_key($stripped),
        trim($clanName),
        strtoupper($display),
        strtolower($display),
        strtoupper($stripped),
        strtolower($stripped),
    ];

    foreach ($candidates as $key) {
        $key = trim((string) $key);
        if ($key !== '' && isset($info[$key]) && is_array($info[$key])) {
            return $info[$key];
        }
    }

    // Último recurso: comparación case-insensitive contra todas las claves.
    $needle = strtolower($stripped !== '' ? $stripped : $display);
    if ($needle !== '') {
        foreach ($info as $key => $entry) {
            if (strtolower((string) $key) === $needle && is_array($entry)) {
                return $entry;
            }
        }
    }

    return [];
}

/**
 * Texto de presentación del clan. Por defecto: "Clan {nombre}".
 */
function clan_blurb(string $clanName): string
{
    $display = clan_display_name($clanName);
    $entry = clan_info_for($clanName);
    $blurb = clan_entry_blurb($entry);

    if ($blurb !== '') {
        return $blurb;
    }

    return 'Clan ' . $display;
}

/**
 * URL de Discord del clan, o cadena vacía si no está configurada.
 */
function clan_discord_url(string $clanName): string
{
    return clan_entry_discord(clan_info_for($clanName));
}

/**
 * Boton/enlace Discord del clan (vacio si no hay URL).
 * $urlOverride: URL publica ya resuelta (DB del editor o estatico).
 */
function render_clan_discord_link(
    string $clanName,
    string $cssClass = 'clan-discord-btn',
    ?string $urlOverride = null
): string {
    $url = $urlOverride !== null ? trim($urlOverride) : clan_discord_url($clanName);
    if ($url === '') {
        return '';
    }

    $label = 'Discord';

    return '<a class="' . e($cssClass) . '" href="' . e($url) . '"'
        . ' target="_blank" rel="noopener noreferrer">'
        . e($label) . '</a>';
}

/**
 * Mapa nombre → archivo de logo (derivado de clans_info).
 *
 * @return array<string, string>
 */
function clan_logo_map(): array
{
    $map = [];
    foreach (clans_info() as $key => $entry) {
        if (isset($entry['logo']) && is_string($entry['logo']) && $entry['logo'] !== '') {
            $map[$key] = $entry['logo'];
        }
    }

    return $map;
}

/**
 * Ruta relativa del logo de un clan (default si no hay propio).
 */
function clan_logo_relative_path(string $clanName): string
{
    $webRoot = dirname(__DIR__);
    $display = clan_display_name($clanName);
    $slug = clan_anchor_key($display);
    $entry = clan_info_for($clanName);
    $extensions = clan_logo_extensions();

    $candidates = [];

    // 1) Logo definido en clans_info.php
    if (isset($entry['logo']) && is_string($entry['logo']) && $entry['logo'] !== '') {
        $candidates[] = 'assets/img/clans/' . ltrim(str_replace('\\', '/', $entry['logo']), '/');
    }

    // 2) Archivo automático assets/img/clans/{slug}.{ext}
    foreach ($extensions as $ext) {
        $candidates[] = 'assets/img/clans/' . $slug . '.' . $ext;
    }

    // 3) default.*
    foreach ($extensions as $ext) {
        $candidates[] = 'assets/img/clans/default.' . $ext;
    }

    foreach ($candidates as $rel) {
        $abs = $webRoot . '/' . $rel;
        if (is_file($abs)) {
            return $rel;
        }
    }

    return 'assets/img/clans/default.png';
}

/**
 * URL pública del logo de clan (con ?v=mtime para evitar caché de 7 días en Hostinger).
 */
function clan_logo_url(string $clanName): string
{
    $rel = clan_logo_relative_path($clanName);
    $url = asset_url($rel);
    $abs = dirname(__DIR__) . '/' . str_replace('\\', '/', $rel);

    // Hostinger cachea PNG con max-age=604800; al cambiar el archivo cambia la URL.
    if (is_file($abs)) {
        $mtime = filemtime($abs);
        if ($mtime !== false) {
            $url .= '?v=' . $mtime;
        }
    }

    return $url;
}

/**
 * HTML &lt;img&gt; del logo de clan (grande por defecto).
 */
function render_clan_logo(string $clanName, string $cssClass = 'clan-logo', int $size = 96): string
{
    $url = clan_logo_url($clanName);
    $alt = 'Logo ' . clan_display_name($clanName);

    return '<img class="' . e($cssClass) . '" src="' . e($url) . '" alt="' . e($alt) . '"'
        . ' width="' . $size . '" height="' . $size . '" loading="lazy">';
}

/**
 * Ruta relativa del banner de fondo, o null si el clan no tiene.
 */
function clan_banner_relative_path(string $clanName): ?string
{
    $webRoot = dirname(__DIR__);
    $slug = clan_html_anchor($clanName);

    foreach (clan_upload_extensions() as $ext) {
        $rel = 'assets/img/clans/banners/' . $slug . '.' . $ext;
        if (is_file($webRoot . '/' . $rel)) {
            return $rel;
        }
    }

    return null;
}

/**
 * URL publica del banner (con ?v=mtime), o null si no hay archivo.
 */
function clan_banner_url(string $clanName): ?string
{
    $rel = clan_banner_relative_path($clanName);
    if ($rel === null) {
        return null;
    }

    $url = asset_url($rel);
    $abs = dirname(__DIR__) . '/' . str_replace('\\', '/', $rel);
    if (is_file($abs)) {
        $mtime = filemtime($abs);
        if ($mtime !== false) {
            $url .= '?v=' . $mtime;
        }
    }

    return $url;
}

/**
 * Valida un upload de imagen de clan y devuelve extension + ruta temporal.
 *
 * @param array<string, mixed> $file
 * @return array{ext: string, tmp: string}
 */
function clan_validate_image_upload(array $file, int $maxBytes, string $label): array
{
    $error = (int) ($file['error'] ?? UPLOAD_ERR_NO_FILE);
    if ($error !== UPLOAD_ERR_OK) {
        throw new RuntimeException('No se pudo subir el ' . $label . ' (codigo ' . $error . ').');
    }

    $tmp = (string) ($file['tmp_name'] ?? '');
    $size = (int) ($file['size'] ?? 0);
    if ($tmp === '' || !is_uploaded_file($tmp)) {
        throw new RuntimeException('Archivo de ' . $label . ' invalido.');
    }
    if ($size <= 0 || $size > $maxBytes) {
        $mb = number_format($maxBytes / (1024 * 1024), 1, '.', '');
        throw new RuntimeException('El ' . $label . ' supera el maximo de ' . $mb . ' MB.');
    }

    $info = @getimagesize($tmp);
    if (!is_array($info) || !isset($info['mime']) || !is_string($info['mime'])) {
        throw new RuntimeException('El ' . $label . ' no es una imagen valida.');
    }

    $mimeToExt = [
        'image/jpeg' => 'jpg',
        'image/png' => 'png',
        'image/webp' => 'webp',
    ];
    $ext = $mimeToExt[$info['mime']] ?? null;
    if ($ext === null || !in_array($ext, clan_upload_extensions(), true)) {
        throw new RuntimeException('Formato de ' . $label . ' no permitido (usa JPEG, PNG o WebP).');
    }

    return ['ext' => $ext, 'tmp' => $tmp];
}

/**
 * Borra archivos {slug}.* en un directorio (logo o banner previo).
 */
function clan_delete_slug_files(string $dirAbs, string $slug): void
{
    if (!is_dir($dirAbs)) {
        return;
    }

    foreach (clan_upload_extensions() as $ext) {
        $path = $dirAbs . '/' . $slug . '.' . $ext;
        if (is_file($path)) {
            @unlink($path);
        }
    }
}

/**
 * Guarda el logo subido en assets/img/clans/{slug}.{ext}.
 *
 * @param array<string, mixed> $file
 */
function clan_store_logo(array $file, string $clanName): string
{
    $validated = clan_validate_image_upload($file, 1572864, 'logo');
    $slug = clan_html_anchor($clanName);
    $dir = dirname(__DIR__) . '/assets/img/clans';
    if (!is_dir($dir) && !mkdir($dir, 0755, true) && !is_dir($dir)) {
        throw new RuntimeException('No se pudo crear la carpeta de logos.');
    }

    clan_delete_slug_files($dir, $slug);
    $rel = 'assets/img/clans/' . $slug . '.' . $validated['ext'];
    $abs = dirname(__DIR__) . '/' . $rel;
    if (!move_uploaded_file($validated['tmp'], $abs)) {
        throw new RuntimeException('No se pudo guardar el logo.');
    }

    return $rel;
}

/**
 * Guarda el banner en assets/img/clans/banners/{slug}.{ext}.
 *
 * @param array<string, mixed> $file
 */
function clan_store_banner(array $file, string $clanName): string
{
    $validated = clan_validate_image_upload($file, 2097152, 'banner');
    $slug = clan_html_anchor($clanName);
    $dir = dirname(__DIR__) . '/assets/img/clans/banners';
    if (!is_dir($dir) && !mkdir($dir, 0755, true) && !is_dir($dir)) {
        throw new RuntimeException('No se pudo crear la carpeta de banners.');
    }

    clan_delete_slug_files($dir, $slug);
    $rel = 'assets/img/clans/banners/' . $slug . '.' . $validated['ext'];
    $abs = dirname(__DIR__) . '/' . $rel;
    if (!move_uploaded_file($validated['tmp'], $abs)) {
        throw new RuntimeException('No se pudo guardar el banner.');
    }

    return $rel;
}

/**
 * Elimina el banner de fondo de un clan (todas las extensiones del slug).
 */
function clan_delete_banner(string $clanName): void
{
    $slug = clan_html_anchor($clanName);
    clan_delete_slug_files(dirname(__DIR__) . '/assets/img/clans/banners', $slug);
}

/**
 * URL a la sección del clan en clans.php, o null si no hay clan.
 */
function clan_page_href(?string $clan): ?string
{
    if (clan_is_empty($clan)) {
        return null;
    }

    return stats_url('clans.php') . '#clan-' . clan_anchor_key(clan_display_name($clan));
}

/**
 * HTML de clan clickeable (o texto plano si no tiene clan).
 */
function render_clan_link(?string $clan, string $emptyLabel = '—'): string
{
    $href = clan_page_href($clan);
    if ($href === null) {
        return e($emptyLabel);
    }

    $label = clan_display_name($clan);

    return '<a class="clan-link" href="' . e($href) . '">' . e($label) . '</a>';
}

/**
 * Antigüedad legible: años, meses y días (aprox. 365 / 30).
 * Ej.: "1 año, 2 meses y 5 días"
 */
function format_account_age(int $days): string
{
    $days = max(0, $days);

    if ($days === 0) {
        return '0 días';
    }

    $years = intdiv($days, 365);
    $remainder = $days % 365;
    $months = intdiv($remainder, 30);
    $dayPart = $remainder % 30;

    $parts = [];

    if ($years > 0) {
        $parts[] = $years === 1 ? '1 año' : $years . ' años';
    }
    if ($months > 0) {
        $parts[] = $months === 1 ? '1 mes' : $months . ' meses';
    }
    if ($dayPart > 0 || $parts === []) {
        $parts[] = $dayPart === 1 ? '1 día' : $dayPart . ' días';
    }

    $count = count($parts);
    if ($count === 1) {
        return $parts[0];
    }
    if ($count === 2) {
        return $parts[0] . ' y ' . $parts[1];
    }

    return $parts[0] . ', ' . $parts[1] . ' y ' . $parts[2];
}
