# Log de descargas LATAMFILES

Fecha: 2026-07-25  
Aprobado: opcion C (archivos bajo /pr/, sin HTML/PHP).

## Diseno
- Archivo: `C:/nginx/logs/downloads.log`
- Formato: `latam_downloads` (ISO8601, IP, status, bytes, metodo+URI, referer, UA)
- Condicion: status 200/206 y URI que no termine en `/` (excluye autoindex)
- Locations: demos2d, demos3d, extras via include `latam-download-log.conf`

## Fuera de alcance
- Vista admin, rotacion automatica
