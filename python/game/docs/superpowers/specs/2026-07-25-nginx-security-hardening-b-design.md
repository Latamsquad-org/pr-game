# Nginx security hardening (fase B)

Fecha: 2026-07-25  
Aprobado en chat: cerrar 8443 + deny paths sensibles.

## Cambios

1. Eliminar `server { listen 8443; ... }` de `latamsquad.conf`.
2. En `latamsquad-locations.conf`:
   - `location ~ /\.` deny (dotfiles)
   - deny exacto ` /pr/logs/config.php` y `/pr/tracker/config.php`
   - deny regex backups/secretos: `bak|old|sql|env` (sqlite gated por location exacta existente)

## Verificacion

- nginx -t + reload
- 8443 no responde
- config.php -> 403/404
- sitio HTTPS OK
