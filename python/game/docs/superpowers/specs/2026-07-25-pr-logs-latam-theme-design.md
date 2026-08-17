# PR Logs LATAM theme (design)

Fecha: 2026-07-25  
Aprobado en chat: opcion C (tema + header + login).

## Objetivo

Alinear `https://…/pr/logs/` (index y login) con el estilo visual de demos2d y tracker: fondo militar oscuro, Rajdhani, acentos oliva/naranja, header LATAMFILES.

## Alcance

- `C:/nginx/html/pr/logs/public/index.php`
- `C:/nginx/html/pr/logs/public/login.php`
- Nueva hoja `C:/nginx/html/pr/logs/public/style/logs-theme.css` (overrides Bootstrap)
- Cargar `/assets/css/site.css` + Rajdhani en ambas paginas

## Fuera de alcance

- Logica Angular/PHP de busqueda y parseo
- README / nombres DIVSUL en docs de vendor
- Cambiar textos de comandos o i18n

## Enfoque

CSS override encima de Bootstrap 4 (sin reescribir markup Angular). Header HTML igual que tracker/admin.

## UI

- Header: logo, LATAMSQUAD, LATAMSTATS (naranja), Discord, ADMINS
- Listas, tablas, inputs, modales, botones en tokens LATAM
- Login centrado con mismo fondo/header
- Footer: `Created by gerbesf   -   Reworked by Chaziz`

## Criterio de exito

Index y login se ven oscuros como demos2d/tracker; header presente; funcionalidad de logs intacta.
