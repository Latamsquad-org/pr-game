# Design: Unificar cola !mvote por nombre

Fecha: 2026-07-24  
Estado: aprobado por usuario

## Problema

La cola `g_mvote_admin_queue` usa claves distintas:
- Ingame: `h:<hash>`
- PRISM: `p:<nombre>`

Un admin conectado a la vez ingame y por PRISM ocupa dos lugares.

## Solucion

Clave unica por nombre canónico: `n:<nombre_normalizado>`.

Normalizacion:
1. lower
2. strip espacios
3. quitar prefijo de clan `[...]` al inicio
4. trim de `.` `_` y espacios en bordes

## Comportamiento

- Add/remove/prune/can_start/give/list usan `n:...`
- Display: si hay ingame y PRISM con el mismo canon -> `Nombre (+PRISM)`; si solo PRISM -> `Nombre (PRISM)`; si solo ingame -> nombre ingame
- Al desconectar una sesion, solo se quita de la cola si no queda la otra sesion del mismo nombre
- Compat: claves viejas `h:` / `p:` se migran/interpretan en prune y name_for_key

## Alcance

`realityadmin.py` en prbf2_1, prbf2_2 y prbf2_3.
