<?php

declare(strict_types=1);

require_once dirname(__DIR__) . '/includes/auth.php';

/**
 * Cierra la sesión PHP y vuelve al hub de juegos.
 */
auth_logout();

header('Location: /index.php', true, 302);
exit;
