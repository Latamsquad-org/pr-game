<?php

declare(strict_types=1);

require_once dirname(__DIR__) . '/includes/layout.php';
require_once dirname(__DIR__) . '/includes/db.php';
require_once dirname(__DIR__) . '/includes/auth_schema.php';

$configPath = dirname(__DIR__) . '/config.php';
if (!is_file($configPath)) {
    http_response_code(500);
    echo 'Configuración no disponible.';
    exit;
}

$config = require $configPath;
if (!is_array($config) || !isset($config['db']) || !is_array($config['db'])) {
    http_response_code(500);
    echo 'Configuración de base de datos inválida.';
    exit;
}

try {
    $pdo = createDatabaseConnection($config['db']);
    ensure_auth_schema($pdo);
    auth_require_staff($pdo);
} catch (Throwable $e) {
    http_response_code(500);
    echo 'No se pudo abrir el panel admin.';
    exit;
}

render_header('Admin', [
    'stats_nav' => true,
    'hero_subtitle' => 'Panel de staff',
]);
?>
        <section class="profile-panel">
            <h3 class="profile-section-title">Herramientas</h3>
            <?php
            $clanesQs = isset($_GET['s']) && is_string($_GET['s']) && $_GET['s'] !== ''
                ? '?s=' . rawurlencode($_GET['s'])
                : '';
            ?>
            <p>
                <a class="btn" href="/admin/clanes.php<?= e($clanesQs) ?>">Clanes</a>
                <span class="text-muted"> Asignar o revocar editores de descripción de clan.</span>
            </p>
        </section>
<?php
render_footer();
