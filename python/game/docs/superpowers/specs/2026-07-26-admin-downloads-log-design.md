# Admin: vista log de descargas

Fecha: 2026-07-26  
Aprobado: opcion B (pagina + buscador).

## Alcance
- `/admin/downloads.php` + `lib/downloads_log.php`
- Nav "Descargas"
- Lee `C:/nginx/logs/downloads.log` (ultimas 200, filtro `q`)
- Solo lectura; auth staff existente

## Fuera de alcance
- Borrar/rotar log desde UI, export CSV
