# Nginx security hardening (fase A)

Fecha: 2026-07-25  
Aprobado en chat: opcion A.

## Objetivo

Endurecer nginx de latamsquad.dev sin cerrar 8443, sin CSP estricto y sin tocar rate limit/CORS mas alla de reaplicar cabeceras donde haga falta.

## Cambios

### http (`latam-security.conf`)
- `server_tokens off`
- `client_max_body_size 16m`
- `client_body_timeout` / `client_header_timeout` 12s
- `large_client_header_buffers` acotados

### server 443 (`latamsquad.conf` + `latam-security-headers.conf`)
- TLS 1.2/1.3, ciphers modernos, session cache, tickets off
- Headers always: HSTS (1 ano, sin preload/includeSubDomains), nosniff, SAMEORIGIN, Referrer-Policy, Permissions-Policy basica

### Locations con `add_header` propio
- Incluir `latam-security-headers.conf` (favicon, CORS demos) para no perder headers por regla de herencia nginx.

## Fuera de alcance
- Puerto 8443, CSP, rate limit amplio, CORS origin restringido.

## Verificacion
- `nginx -t` + reload
- Comprobar headers en respuesta HTTPS
