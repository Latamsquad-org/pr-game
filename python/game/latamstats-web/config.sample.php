<?php

declare(strict_types=1);

// Copie este archivo como config.php y reemplace únicamente los valores SAMPLE.
return [
    'db' => [
        'host' => 'SAMPLE_DB_HOST',
        'port' => 3306,
        'name' => 'SAMPLE_DB_NAME',
        'user' => 'SAMPLE_DB_USER',
        'password' => 'SAMPLE_DB_PASSWORD',
        'charset' => 'utf8mb4',
    ],
    'api_key' => 'SAMPLE_API_KEY',
    'discord' => [
        'client_id' => 'SAMPLE_DISCORD_CLIENT_ID',
        'client_secret' => 'SAMPLE_DISCORD_CLIENT_SECRET',
        'guild_id' => 'SAMPLE_DISCORD_GUILD_ID',
        'staff_role_ids' => ['SAMPLE_STAFF_ROLE_ID'],
        'redirect_uri' => 'https://latamstats.pro/auth/callback.php',
    ],
];
