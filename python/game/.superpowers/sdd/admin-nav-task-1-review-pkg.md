# Task 1 review package (live fs)
Verify _layout.php and site.css per brief.
    $cssV = (string) @filemtime(dirname(__DIR__) . '/assets/css/site.css');
    $logoV = (string) @filemtime(dirname(__DIR__) . '/assets/img/latamfiles-logo.png');
    $nav = [
        'home' => ['href' => '/admin/', 'label' => 'Inicio'],
        'traffic' => ['href' => '/admin/traffic.php', 'label' => 'Trafico'],
        'demos' => ['href' => '/admin/demos.php', 'label' => 'Demos'],
        'auth' => ['href' => '/admin/auth-settings.php', 'label' => 'Auth'],
    ];
    echo '<!DOCTYPE html>' . "\n";
    echo '<html lang="es">' . "\n";
    echo '<head>' . "\n";
    echo '  <meta charset="utf-8">' . "\n";
    echo '  <meta name="viewport" content="width=device-width, initial-scale=1">' . "\n";
    echo '  <meta name="robots" content="noindex,nofollow">' . "\n";
    echo '  <title>' . admin_h($title) . '</title>' . "\n";
    echo '  <link rel="icon" href="/assets/img/favicon.png" type="image/png">' . "\n";
    echo '  <link rel="preconnect" href="https://fonts.googleapis.com">' . "\n";
    echo '  <link rel="preconnect" href="https://fonts.gstatic.com" crossorigin>' . "\n";
    echo '  <link href="https://fonts.googleapis.com/css2?family=Rajdhani:wght@500;600;700&display=swap" rel="stylesheet">' . "\n";
    echo '  <link rel="stylesheet" href="/assets/css/site.css?v=' . admin_h($cssV !== '' ? $cssV : '1') . '">' . "\n";
    echo '</head>' . "\n";
    echo '<body class="latam-admin-body">' . "\n";
    echo '  <header class="latam-site-header" role="banner">' . "\n";
    echo '    <div class="latam-site-header__inner">' . "\n";
    echo '      <a class="latam-site-brand" href="/" aria-label="LATAMFILES - Inicio">' . "\n";
    echo '        <img class="latam-site-brand__logo" src="/assets/img/latamfiles-logo.png?v=' . admin_h($logoV !== '' ? $logoV : '1') . '" alt="LATAMFILES" width="180" height="36">' . "\n";
    echo '      </a>' . "\n";
    echo '      <div class="latam-site-header__auth">' . "\n";
    echo '        <nav class="latam-ext-nav" aria-label="Enlaces comunidad">' . "\n";
    echo '          <a class="latam-ext-nav__link latam-ext-nav__link--external latam-ext-nav__link--latamsquad" href="https://latamsquad.org" target="_blank" rel="noopener noreferrer"><span class="latam-ext-nav__latam">LATAM</span><span class="latam-ext-nav__squad">SQUAD</span></a>' . "\n";
    echo '          <a class="latam-ext-nav__link latam-ext-nav__link--external latam-ext-nav__link--latamstats" href="https://latamstats.pro/" target="_blank" rel="noopener noreferrer"><span class="latam-ext-nav__latam">LATAM</span><span class="latam-ext-nav__stats">STATS</span></a>' . "\n";
    echo '          <a class="latam-ext-nav__link latam-ext-nav__link--external latam-ext-nav__link--discord" href="https://discord.gg/latamsquad" target="_blank" rel="noopener noreferrer">Discord</a>' . "\n";
    echo '        </nav>' . "\n";
    $authName = auth_display_name();
    if ($authName === null || $authName === '') {
        $authName = 'Admin';
    }
    echo '        <a href="/admin/" title="Panel de administracion">' . admin_h($authName) . '</a>' . "\n";
    echo '        &middot; <a href="/auth/logout.php">Salir</a>' . "\n";
    echo '      </div>' . "\n";
    echo '    </div>' . "\n";
    echo '  </header>' . "\n";
    echo '  <div class="latam-admin">' . "\n";
    echo '    <aside class="latam-admin__sidebar" aria-label="Menu admin">' . "\n";
    $shortcuts = [
        ['href' => '/pr/logs/', 'label' => 'Visor de logs'],
        ['href' => '/pr/admins/logs/sv1/', 'label' => 'Logs crudos'],
        ['href' => '/pr/tracker/?srv=1', 'label' => 'Tracker'],
        ['href' => '/pr/demos2d/', 'label' => 'Demos 2D'],
        ['href' => '/pr/demos3d/sv1/', 'label' => 'Demos 3D'],
    ];
    echo '      <nav class="latam-admin__nav">' . "\n";
    echo '        <div class="latam-admin__nav-section">' . "\n";
    echo '          <p class="latam-admin__nav-label">Config</p>' . "\n";
    foreach ($nav as $key => $item) {
        $cls = 'latam-admin__nav-link' . ($key === $activeNav ? ' is-active' : '');
        $cur = $key === $activeNav ? ' aria-current="page"' : '';
        echo '          <a class="' . admin_h($cls) . '" href="' . admin_h($item['href']) . '"' . $cur . '>' . admin_h($item['label']) . '</a>' . "\n";
    }
    echo '        </div>' . "\n";
    echo '        <div class="latam-admin__nav-section">' . "\n";
    echo '          <p class="latam-admin__nav-label">Atajos</p>' . "\n";
    foreach ($shortcuts as $item) {
        echo '          <a class="latam-admin__nav-link" href="' . admin_h($item['href']) . '">' . admin_h($item['label']) . '</a>' . "\n";
    }
    echo '        </div>' . "\n";
    echo '      </nav>' . "\n";
    echo '    </aside>' . "\n";
    echo '    <main class="latam-admin__main">' . "\n";
    echo '      <h1 class="latam-admin__title">' . admin_h($heading) . '</h1>' . "\n";
