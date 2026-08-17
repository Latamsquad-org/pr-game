# LATAMFILES - ACL de borrado de partidas (owner Chaziz)

## Objetivo

Solo el owner (Chaziz) puede conceder o revocar el permiso de borrar partidas del tracker (PRdemo + JSON + BF2demo). Por defecto ningun otro staff puede borrar.

## Owner

- Discord ID fijo: `357055203348054027`
- Siempre puede borrar; no se puede quitar a si mismo de la ACL
- Unico que ve y usa `/admin/delete-acl.php`

## Comportamiento

- Default: whitelist vacia; solo owner borra
- Owner agrega Discord IDs (label opcional) y puede quitarlos
- Tracker: boton × solo si `delete_acl_can_delete(session_id)`
- `deleteRound.php`: mismo check ademas de staff + CSRF

## Almacenamiento

- JSON: `/admin/data/delete-acl.json` (protegido por nginx `^~ /admin/data/`)
- Forma: `{ "can_delete": [ { "id": "<discord_id>", "label": "nombre" } ] }`
- Owner no vive en el JSON (constante en PHP)

## UI admin

- Nav Config: item "Borrado" visible solo para owner
- Pagina: lista + form agregar ID + boton quitar; CSRF admin
- Otros staff: 403 si abren la URL a mano

## Fuera de alcance

- No cambia quien es staff (rol Discord)
- No lista automatica de todo el staff del guild
- No aplica a otros borrados fuera del tracker
