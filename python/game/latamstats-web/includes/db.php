<?php

declare(strict_types=1);

/**
 * Crea una conexión PDO reutilizable con errores convertidos en excepciones.
 *
 * @param array<string, mixed> $databaseConfig
 */
function createDatabaseConnection(array $databaseConfig): PDO
{
    $requiredKeys = ['host', 'port', 'name', 'user', 'password', 'charset'];

    foreach ($requiredKeys as $key) {
        if (!array_key_exists($key, $databaseConfig)) {
            throw new RuntimeException("Falta la configuración de base de datos: {$key}");
        }
    }

    $dsn = sprintf(
        'mysql:host=%s;port=%d;dbname=%s;charset=%s',
        $databaseConfig['host'],
        (int) $databaseConfig['port'],
        $databaseConfig['name'],
        $databaseConfig['charset']
    );

    return new PDO(
        $dsn,
        (string) $databaseConfig['user'],
        (string) $databaseConfig['password'],
        [
            PDO::ATTR_ERRMODE => PDO::ERRMODE_EXCEPTION,
            PDO::ATTR_DEFAULT_FETCH_MODE => PDO::FETCH_ASSOC,
            PDO::ATTR_EMULATE_PREPARES => false,
        ]
    );
}
