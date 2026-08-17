<?php

declare(strict_types=1);

/**
 * Información unificada de clanes (logo + presentación + Discord).
 *
 * Editá SOLO este archivo para logos, textos y Discord de clans.php.
 *
 * Clave = nombre exacto del clan (como en el juego) o slug (ej. "kkck").
 * Valor = array con claves opcionales:
 *   - logo    => archivo en assets/img/clans/ (png, jpg, webp, svg, gif)
 *   - blurb   => texto de presentación (si falta → "Clan {nombre}")
 *     (también acepta: descripcion, description, texto)
 *   - discord => URL de invitación (ej. https://discord.gg/xxxx)
 *     Si falta o está vacío → no se muestra el botón
 *
 * La clave puede ser el nombre en el juego (KKCK) o el slug (kkck).
 *
 * Si no hay logo aquí, se busca automáticamente:
 *   assets/img/clans/{slug}.png|jpg|jpeg|webp|svg|gif
 * Si tampoco existe, se usa default.png
 *
 * Ejemplos:
 *   'KKCK' => [
 *       'logo' => 'kkck.png',
 *       'blurb' => 'Comunidad competitiva de Project Reality.',
 *       'discord' => 'https://discord.gg/xxxx',
 *   ],
 *   'BRAVO' => [
 *       'logo' => 'bravo.jpg',
 *   ],
 */
return [
    'KKCK' => [
        'logo' => 'kkck.png',
        'blurb' => 'Para ser KKCK hay que embarrarse la cara de mierda.',
        // 'discord' => 'https://discord.gg/xxxx',
    ],
    'BRAVO' => [
        'logo' => 'bravo.png',
        // 'discord' => 'https://discord.gg/xxxx',
    ],
    'FI' => [
        'logo' => 'fi.png',
        // 'discord' => 'https://discord.gg/xxxx',
    ],
    'LDH' => [
        'logo' => 'ldh.jpg',
        'blurb' => 'Somos la legión, un clan dedicado íntegramente a PROJECT REALITY y otros simuladores militares, con miembros de mas de tres años de experiencia en la infantería, reconocimiento y combate cercano. Ligados al apartado competitivo tanto a nivel interno del grupo como en el apartado externo en eventos de otras comunidades tanto de habla Hispana, Anglosajona, Brasilera y Eslava.',
        // 'discord' => 'https://discord.gg/xxxx',
    ],
    // 'NOMBRE_DEL_CLAN' => [
    //     'logo' => 'archivo.png',
    //     'blurb' => 'Texto de presentación del clan.',
    //     'discord' => 'https://discord.gg/xxxx',
    // ],
];
