<?php
declare(strict_types=1);
require_once __DIR__ . '/auth/lib.php';
auth_start_session();
$id = auth_current_discord_id();
$name = auth_display_name();
$isStaff = $id !== null && auth_is_staff();
$logoV = (string) @filemtime(__DIR__ . '/assets/img/latamfiles-logo.png');
$cssV = (string) @filemtime(__DIR__ . '/assets/css/site.css');
$origin = 'https://latamsquad.dev';
$canonical = $origin . '/pr.php';
$ogImage = $origin . '/assets/img/latamfiles-logo.png';
$title = 'Project Reality - Archivos | LATAMFILES';
$description = 'Archivos y demos de Project Reality en LATAMFILES: tracker, demos 2D/3D y extras.';
$jsonLd = [
    '@context' => 'https://schema.org',
    '@type' => 'WebPage',
    'name' => $title,
    'url' => $canonical,
    'description' => $description,
    'isPartOf' => [
        '@type' => 'WebSite',
        'name' => 'LATAMFILES',
        'url' => $origin . '/',
    ],
];
$jsonLdEncoded = json_encode(
    $jsonLd,
    JSON_UNESCAPED_SLASHES | JSON_UNESCAPED_UNICODE | JSON_HEX_TAG | JSON_HEX_AMP
);
?>
<!DOCTYPE html>
<html lang="es">
<head>
  <meta charset="utf-8">
  <title><?= htmlspecialchars($title, ENT_QUOTES, 'UTF-8') ?></title>
  <meta name="viewport" content="width=device-width, initial-scale=1">
  <meta name="description" content="<?= htmlspecialchars($description, ENT_QUOTES, 'UTF-8') ?>">
  <meta name="robots" content="index,follow">
  <link rel="canonical" href="<?= htmlspecialchars($canonical, ENT_QUOTES, 'UTF-8') ?>">
  <meta name="theme-color" content="#6b8f3c">
  <meta property="og:type" content="website">
  <meta property="og:site_name" content="LATAMFILES">
  <meta property="og:locale" content="es_LA">
  <meta property="og:title" content="<?= htmlspecialchars($title, ENT_QUOTES, 'UTF-8') ?>">
  <meta property="og:description" content="<?= htmlspecialchars($description, ENT_QUOTES, 'UTF-8') ?>">
  <meta property="og:url" content="<?= htmlspecialchars($canonical, ENT_QUOTES, 'UTF-8') ?>">
  <meta property="og:image" content="<?= htmlspecialchars($ogImage, ENT_QUOTES, 'UTF-8') ?>">
  <meta name="twitter:card" content="summary_large_image">
  <meta name="twitter:title" content="<?= htmlspecialchars($title, ENT_QUOTES, 'UTF-8') ?>">
  <meta name="twitter:description" content="<?= htmlspecialchars($description, ENT_QUOTES, 'UTF-8') ?>">
  <meta name="twitter:image" content="<?= htmlspecialchars($ogImage, ENT_QUOTES, 'UTF-8') ?>">
  <link rel="icon" href="/assets/img/favicon.png" type="image/png">
  <link rel="preconnect" href="https://fonts.googleapis.com">
  <link rel="preconnect" href="https://fonts.gstatic.com" crossorigin>
  <link href="https://fonts.googleapis.com/css2?family=Rajdhani:wght@500;600;700&display=swap" rel="stylesheet">
  <link rel="stylesheet" href="/assets/css/site.css?v=<?= htmlspecialchars($cssV !== '' ? $cssV : '1', ENT_QUOTES, 'UTF-8') ?>">
  <?php if (is_string($jsonLdEncoded) && $jsonLdEncoded !== ''): ?>
  <script type="application/ld+json"><?= $jsonLdEncoded ?></script>
  <?php endif; ?>
</head>
<body>
  <header class="latam-site-header" role="banner">
    <div class="latam-site-header__inner">
      <a class="latam-site-brand" href="/" aria-label="LATAMFILES - Inicio">
        <img
          class="latam-site-brand__logo"
          src="/assets/img/latamfiles-logo.png?v=<?= htmlspecialchars($logoV !== '' ? $logoV : '1', ENT_QUOTES, 'UTF-8') ?>"
          alt="LATAMFILES - logo LATAMSQUAD"
          width="625"
          height="91"
        >
      </a>
      <div class="latam-site-header__auth">
        <nav class="latam-ext-nav" aria-label="Enlaces comunidad">
          <a class="latam-ext-nav__link latam-ext-nav__link--external latam-ext-nav__link--latamsquad" href="https://latamsquad.org" target="_blank" rel="noopener noreferrer"><span class="latam-ext-nav__latam">LATAM</span><span class="latam-ext-nav__squad">SQUAD</span></a>
          <a class="latam-ext-nav__link latam-ext-nav__link--external latam-ext-nav__link--latamstats" href="https://stats.latamsquad.org/" target="_blank" rel="noopener noreferrer"><span class="latam-ext-nav__latam">LATAM</span><span class="latam-ext-nav__stats">STATS</span></a>
          <a class="latam-ext-nav__link latam-ext-nav__link--external latam-ext-nav__link--latamtorneos" href="https://torneos.latamsquad.org/" target="_blank" rel="noopener noreferrer"><span class="latam-ext-nav__latam">LATAM</span><span class="latam-ext-nav__torneos">TORNEOS</span></a>
          <a class="latam-ext-nav__link latam-ext-nav__link--external latam-ext-nav__link--discord" href="https://discord.gg/latamsquad" target="_blank" rel="noopener noreferrer">Discord</a>
        </nav>
        <?php if ($id === null): ?>
          <a class="latam-site-header__admins" href="/auth/discord.php">Entrar</a>
        <?php else: ?>
          <?= auth_account_chip_html((string) ($name ?? 'Usuario'), $isStaff ? '/admin/' : null) ?>
          &middot; <a href="/auth/logout.php">Salir</a>
        <?php endif; ?>
      </div>
    </div>
  </header>

  <main class="latam-main">
    <div class="pr-page">
      <a class="pr-back" href="/">&larr; Juegos</a>
      <h1>Project Reality - Archivos</h1>
      <p>Tracker, demos y archivos del servidor Project Reality de LATAMSQUAD.</p>
      <ul class="pr-links">
        <li><a href="/pr/tracker/?srv=1">Listado de Partidas</a></li>
        <li><a href="/pr/demos2d/sv1/">.PRdemos (2D)</a></li>
        <li><a href="/pr/demos3d/sv1/">.BF2demos (3D)</a></li>
        <li><a href="/pr/logs/">Visor de logs</a></li>
        <li><a href="/pr/extras/">Extras</a></li>
      </ul>
    </div>
  </main>
  <?php latam_render_footer(['pr_nav' => true]); ?>
</body>
</html>
