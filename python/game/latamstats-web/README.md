# latamstats.pro — Deploy en Hostinger

Dashboard público de estadísticas LATAMSQUAD. El servidor PR acumula totales en SQLite local y los sube al fin de cada ronda vía POST JSON.

## Requisitos

- Hosting Hostinger con PHP 8+ y MySQL
- Dominio apuntando a `public_html` (ej. `latamstats.pro`)
- Servidor PR con `latamstats.py` activo (`import latamstats` en `__init__.py`)

---

## 1. Base de datos MySQL (Hostinger)

1. En **hPanel → Bases de datos MySQL**, crear una base y un usuario con permisos completos sobre ella.
2. Anotar: host, nombre de BD, usuario y contraseña.
3. Abrir **phpMyAdmin** (o Adminer) y seleccionar la base creada.
4. Importar el archivo `schema.sql` de este repositorio. Crea la tabla `players` (índice único en `player_id`) y también las tablas Discord del feature de perfiles: `discord_users`, `player_links`, `link_codes`, `player_profiles`, `clan_blurbs`, `clan_editors`. En runtime, `ensure_auth_schema()` puede crearlas si faltan.

---

## 2. Configuración PHP

En el servidor (no subir secretos al repo):

```bash
cp config.sample.php config.php
```

Editar `config.php` y reemplazar los placeholders:

| Clave | Valor |
|-------|-------|
| `db.host` | Host MySQL de Hostinger (ej. `localhost` o el host remoto indicado en hPanel) |
| `db.port` | `3306` (por defecto) |
| `db.name` | Nombre de la base creada |
| `db.user` | Usuario MySQL |
| `db.password` | Contraseña MySQL |
| `api_key` | Clave secreta larga y aleatoria (misma que usará el servidor PR) |
| `discord.client_id` | Client ID de la app Discord (ver sección Discord abajo) |
| `discord.client_secret` | Client Secret de la app Discord |
| `discord.guild_id` | ID del servidor Discord LATAMSQUAD |
| `discord.staff_role_ids` | Array de role IDs con acceso a `/admin` |
| `discord.redirect_uri` | `https://latamstats.pro/auth/callback.php` (debe coincidir con el portal) |

`config.php` está en `.gitignore`; nunca commitear credenciales reales. Los secretos de Discord solo van en `config.php` (placeholders en `config.sample.php`).

---

## 3. Discord Developer Portal (perfiles y admin)

Configuración OAuth para “Entrar con Discord”, vínculo de cuenta PR y staff admin. **No se usa bot.**

1. En [Discord Developer Portal](https://discord.com/developers/applications) crear una aplicación (o usar una existente).
2. En **OAuth2 → Redirects**, añadir exactamente:
   `https://latamstats.pro/auth/callback.php`
3. Scopes usados por la web: `identify` y `guilds.members.read`.
4. Copiar a `config.php` (desde `config.sample.php`):
   - **Client ID** → `discord.client_id`
   - **Client Secret** → `discord.client_secret`
   - **Guild (server) ID** → `discord.guild_id`
   - **Role ID(s) de staff** → `discord.staff_role_ids` (uno o más; basta con tener alguno en el guild)
   - Confirmar `discord.redirect_uri` = la misma URL del paso 2
5. Flujo jugador:
   - Clic en **Entrar con Discord** → **Mi perfil** → generar código `LS-XXXX`
   - Poner el código en el nombre del juego → jugar una ronda (el upload lo detecta)
   - Volver a **Mi perfil** y editar bio / banner / redes / mostrar Discord
6. Flujo staff:
   - Con un rol de `staff_role_ids` en el guild → **Admin** → **Clanes** → asignar `discord_id` como editor de un clan

Smoke CLI de perfiles Discord (desde `latamstats-web/`):

```bash
php tests/run_discord_profile_smokes.php
```

Sale con código distinto de 0 si alguna prueba falla.

---

## 4. Subir archivos al hosting

Subir **todo el contenido** de la carpeta `latamstats-web/` al directorio web del dominio (`public_html` o subcarpeta del vhost de `latamstats.pro`).

Estructura esperada en el servidor:

```
public_html/
├── api/upload.php
├── assets/css/main.css
├── assets/js/ranking.js
├── includes/
├── index.php
├── ranking.php
├── player.php
├── config.php          ← creado localmente, no desde el repo
└── schema.sql          ← opcional dejar solo como referencia
```

Verificar permisos de lectura para PHP. No es necesario exponer `config.sample.php` en producción, pero no es crítico.

URLs públicas:

- Portada: `https://latamstats.pro/`
- Ranking: `https://latamstats.pro/ranking.php`
- Ficha: `https://latamstats.pro/player.php?id=<player_id>`
- API upload: `https://latamstats.pro/api/upload.php`

---

## 5. Configurar el servidor PR

Editar `latamstats.py` en el mod PR (`mods/pr/python/game/`):

```python
STATS_UPLOAD_URL = 'https://latamstats.pro/api/upload.php'
STATS_API_KEY = 'TU_MISMA_API_KEY_QUE_EN_config.php'
```

Opcionalmente ajustar:

```python
STATS_DB_PATH = 'C:/prbf2_db/stats1.sqlite3'
STATS_SERVER_ID = 'pr-1'
STATS_UPLOAD_TIMEOUT = 8
```

La API Key debe coincidir **exactamente** con `api_key` en `config.php`. Mientras `STATS_API_KEY` sea `'CHANGE_ME'`, el upload queda deshabilitado sin afectar la ronda.

---

## 6. Reiniciar servidor PR

1. Cambiar de mapa o reiniciar el servidor de juego para recargar el Python del mod.
2. Confirmar en logs que `latamstats` inicializa sin errores.

---

## 7. Checklist smoke (end-to-end)

Ejecutar tras un deploy completo y al menos una ronda jugada:

- [ ] **SQLite local:** al terminar una ronda, existen/actualizan filas en `C:/prbf2_db/stats1.sqlite3` (tabla `stats`, clave `player_id`).
- [ ] **POST upload:** el servidor PR envía JSON al fin de ronda; en logs aparece éxito o un error registrado **sin crash** del game loop (timeout/red no tumba la partida).
- [ ] **Portada:** `https://latamstats.pro/` muestra resumen y **Top 10** con datos recientes.
- [ ] **Ranking:** `https://latamstats.pro/ranking.php` lista jugadores, permite **buscar** por nombre/clan y **ordenar** columnas.
- [ ] **Ficha:** un enlace desde ranking abre `player.php?id=...` con stats del jugador.
- [ ] **Auth 401:** POST a `/api/upload.php` **sin** header `X-API-Key` devuelve HTTP **401** JSON `{"ok":false,"error":"Unauthorized"}`.

### Comandos rápidos de verificación

**Upload sin clave (debe dar 401):**

```bash
curl -s -o /dev/null -w "%{http_code}" -X POST https://latamstats.pro/api/upload.php \
  -H "Content-Type: application/json" \
  -d '{"players":[]}'
```

**Upload con clave válida (debe dar 200):**

```bash
curl -s -X POST https://latamstats.pro/api/upload.php \
  -H "Content-Type: application/json" \
  -H "X-API-Key: TU_API_KEY" \
  -d '{"server_id":"pr-1","timestamp":"2026-07-15T00:00:00Z","players":[{"player_id":"test1","player_name":"Test","player_clan":"","score":100,"kills":5,"deaths":2,"rounds":1}]}'
```

**Inspeccionar SQLite en el servidor PR (Windows):**

```powershell
sqlite3 C:\prbf2_db\stats1.sqlite3 "SELECT player_id, score, kills, deaths, rounds FROM stats LIMIT 5;"
```

---

## 8. Upload FH2 (Forgotten Hope 2)

Endpoint separado del de PR. Solo acepta `server_id` `fh2-1`..`fh2-4` (no se mezcla con las pestañas PR).

Archivos a desplegar en Hostinger (mismo `public_html` que stats):

- `api/upload_fh2.php` (principal)
- `fh2.php` (alias)
- `fh2/upload.php` (alias por si el hosting reescribe `/fh2.php` -> `/fh2`)
- `includes/servers.php` (helpers `fh2_*`)

En el servidor FH2 (`mods/fh2/python/latamstats.py`):

```python
STATS_UPLOAD_URL = 'https://stats.latamsquad.org/api/upload_fh2.php'
STATS_SERVER_ID = 'fh2-1'
```

Prueba:

```bash
curl -s -X POST https://stats.latamsquad.org/api/upload_fh2.php \
  -H "Content-Type: application/json" \
  -H "X-API-Key: TU_API_KEY" \
  -d '{"server_id":"fh2-1","timestamp":"2026-08-11T00:00:00Z","players":[{"player_id":"testfh2","player_name":"Test","player_clan":"","score":10,"kills":1,"deaths":0,"rounds":1}]}'
```

Respuesta esperada: `{"ok":true,"server_id":"fh2-1"}`.

---

## Solución de problemas

| Síntoma | Revisar |
|---------|---------|
| Portada vacía | ¿Llegó algún POST? ¿MySQL tiene filas en `players`? |
| 500 en upload | `config.php` presente, credenciales DB correctas, tabla importada |
| Upload deshabilitado en PR | `STATS_API_KEY` sigue en `CHANGE_ME` |
| 401 con clave | API Key distinta entre `latamstats.py` y `config.php` |
| Ronda crashea | No debería ocurrir; revisar logs — upload está envuelto en try/except |
