# Nginx security hardening (fase C)

Fecha: 2026-07-25  
Aprobado en chat.

## Rate limit (archivos nuevos; no tocar latam-traffic-*)
- Zones: latam_php 30r/s, latam_admin 10r/s, latam_auth 5r/m
- limit_req_status 429
- Includes por location PHP / admin / auth

## CORS
- map allowlist: https://yossizap.github.io, https://latamsquad.dev
- Reemplaza Access-Control-Allow-Origin *

## Verificacion
nginx -t, reload, tracker CORS, 429 bajo carga, panel traffic intacto
