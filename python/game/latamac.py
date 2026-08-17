# -*- coding: utf-8 -*-
# latamac.py - Anti-Cheat server-side LATAMSQUAD (Fase 1)
#
# Detectores: teleport, fly/noclip a pie, kill distance, snap aim.
# Scoring con decay + log SQLite.
#
# Comandos:
#   !ac status [jugador]  - score y ultimas violaciones
#   !ac reset [jugador]   - limpiar score (falso positivo)
#   !ac fool [jugador]    - grilla kits aliados/enemigos bajo tierra
#   !ac unfool [jugador]  - quitar kits fool
#   !ac bait [jugador]    - admin sigue al tramposo desde bajo tierra (ESP bait)
#   !ac unbait [jugador]  - deja de seguir / sacar bait
#   !ac body [jugador|reset] - template fool = cuerpo de jugador muerto
#   !ac spawnmode create|spawner - modo de spawn del fool
#   !ac reload            - recargar latamac_config.py

import math
import os
import re
import sqlite3
import time

try:
    import bf2
    import host
    import realityadmin as radmin
    import realityconfig_admin as ras
    import realityconstants as rconstants
    import realitycore as rcore
    import realityserver as rserver
    import realitytimer as rtimer
    _IN_GAME = True
except ImportError:
    bf2 = None
    host = None
    radmin = None
    ras = None
    rconstants = None
    rcore = None
    rserver = None
    rtimer = None
    _IN_GAME = False

try:
    import realityvehicles as rvehicles
except Exception:
    rvehicles = None

try:
    import realityplayerdata as rplayerdata
except Exception:
    rplayerdata = None

try:
    import latamac_config as _latamac_cfg_mod
except Exception:
    _latamac_cfg_mod = None

try:
    import realityspawner as rspawner
except Exception:
    rspawner = None

try:
    import realitykits as rkits
except Exception:
    rkits = None

try:
    import realityserver as rserver_mod
except Exception:
    rserver_mod = None


# ------------------------------------------------------------------
# Config
# ------------------------------------------------------------------
LATAMAC_ENABLED = True
# Instancia PR (1..4). None = auto desde ruta prbf2_N o latamstats STATS_SERVER_ID.
LATAMAC_SERVER_NUM = None


def _server_num_from_stats_id(server_id):
    text = str(server_id or '').strip()
    match = re.search(r'-(\d+)\s*$', text)
    if match:
        return int(match.group(1))
    return None


def detect_latamac_server_num():
    if LATAMAC_SERVER_NUM is not None:
        return int(LATAMAC_SERVER_NUM)
    if _IN_GAME and host is not None:
        try:
            mod_dir = host.sgl_getModDirectory().replace('\\', '/').lower()
            match = re.search(r'prbf2_(\d+)', mod_dir)
            if match:
                return int(match.group(1))
        except Exception:
            pass
    try:
        import latamstats as _ls
        num = _server_num_from_stats_id(_ls.STATS_SERVER_ID)
        if num is not None:
            return num
    except Exception:
        pass
    return 1


def latamac_db_path(server_num=None):
    num = detect_latamac_server_num() if server_num is None else int(server_num)
    return 'C:/prbf2_db/latamac%d.sqlite3' % num


LATAMAC_DB_PATH = latamac_db_path(1)

LATAMAC_TICK_SEC = 1.0
LATAMAC_SCORE_DECAY_INTERVAL = 60.0
LATAMAC_SCORE_DECAY_FACTOR = 0.85

LATAMAC_LOG_THRESHOLD = 15

LATAMAC_SPAWN_GRACE_SEC = 30.0
LATAMAC_VEHICLE_CHANGE_GRACE_SEC = 3.0
LATAMAC_MAX_PING = 250

# Limites de velocidad horizontal (m/s), generosos por lag.
LATAMAC_SPEED_FOOT = 18.0
LATAMAC_SPEED_GROUND_VEH = 95.0

# Tolerancia de mira vs victima en kill (grados).
LATAMAC_AIM_TOLERANCE_DEG = 22.0

POINTS_TELEPORT = 40
POINTS_FLY = 50
POINTS_KILL_DISTANCE = 30
POINTS_SNAP_AIM = 25

_fool_follow_task = None
_bait_follow_task = None

# Alcance maximo estimado por tipo de arma (metros horizontales).
_WEAPON_RANGE_BY_TYPE = None

# Estado global
_tracker = None
_fooled = {}
_baited = {}
_round_tag = ''
# Cuerpo prestado pendiente de adjuntar al proximo fool (oid, obj).
_pending_fool_body = None


def _weapon_range_table():
    global _WEAPON_RANGE_BY_TYPE
    if _WEAPON_RANGE_BY_TYPE is not None:
        return _WEAPON_RANGE_BY_TYPE
    if rconstants is None:
        _WEAPON_RANGE_BY_TYPE = {}
        return _WEAPON_RANGE_BY_TYPE
    _WEAPON_RANGE_BY_TYPE = {
        rconstants.WEAPON_TYPE_SNIPER: 900.0,
        rconstants.WEAPON_TYPE_LMG: 650.0,
        rconstants.WEAPON_TYPE_ASSAULT: 450.0,
        rconstants.WEAPON_TYPE_ASSAULTGRN: 450.0,
        rconstants.WEAPON_TYPE_CARBINE: 400.0,
        rconstants.WEAPON_TYPE_SMG: 200.0,
        rconstants.WEAPON_TYPE_PISTOL: 150.0,
        rconstants.WEAPON_TYPE_SHOTGUN: 100.0,
        rconstants.WEAPON_TYPE_ATAA: 850.0,
    }
    return _WEAPON_RANGE_BY_TYPE


def _normalize_fool_spawn_mode(value):
    text = str(value or '').strip().lower()
    if text in ('create', 'object.create', 'objectcreate', 'objcreate'):
        return 'create'
    if text in ('spawner', 'objectspawner', 'object.spawner', 'spawn'):
        return 'spawner'
    return 'spawner'


# ------------------------------------------------------------------
# Config: solo latamac_config.py (sin defaults duplicados aqui)
# ------------------------------------------------------------------
def _fool_get(name):
    """Lee un setting de fool desde latamac_config."""
    if _latamac_cfg_mod is None:
        return None
    return getattr(_latamac_cfg_mod, name, None)


def _fool_set(name, value):
    """Escribe un setting de fool en latamac_config (runtime; !ac reload lo pisa)."""
    if _latamac_cfg_mod is None:
        return False
    setattr(_latamac_cfg_mod, name, value)
    return True


def _fool_template():
    return str(_fool_get('LATAMAC_FOOL_TEMPLATE') or '').strip()


def _fool_head_offset_y():
    return float(_fool_get('LATAMAC_FOOL_HEAD_OFFSET_Y') or 0.0)


def _fool_radius():
    return float(_fool_get('LATAMAC_FOOL_RADIUS') or 0.0)


def _fool_spin_deg_per_sec():
    return float(_fool_get('LATAMAC_FOOL_SPIN_DEG_PER_SEC') or 0.0)


def _fool_follow_sec():
    val = float(_fool_get('LATAMAC_FOOL_FOLLOW_SEC') or 0.05)
    if val < 0.05:
        return 0.05
    return val


def _fool_hide_y():
    return float(_fool_get('LATAMAC_FOOL_HIDE_Y') or 9000.0)


def _fool_spawn_mode():
    return _normalize_fool_spawn_mode(_fool_get('LATAMAC_FOOL_SPAWN_MODE'))


def _fool_spawn_cooldown_sec():
    return float(_fool_get('LATAMAC_FOOL_SPAWN_COOLDOWN_SEC') or 2.0)


def _fool_respawn_sec():
    """Intervalo destroy+create periodico. 0 desactiva."""
    val = _fool_get('LATAMAC_FOOL_RESPAWN_SEC')
    if val is None:
        return 10.0
    try:
        return float(val)
    except Exception:
        return 10.0


def _fool_kit_grid_enabled():
    val = _fool_get('LATAMAC_FOOL_KIT_GRID')
    if val is None:
        return True
    return bool(val)


def _fool_kit_count():
    try:
        n = int(_fool_get('LATAMAC_FOOL_KIT_COUNT') or 20)
    except Exception:
        n = 20
    if n < 1:
        return 1
    if n > 40:
        return 40
    return n


def _fool_kit_spacing():
    return float(_fool_get('LATAMAC_FOOL_KIT_SPACING') or 2.5)


def _fool_kit_bury_y():
    return float(_fool_get('LATAMAC_FOOL_KIT_BURY_Y') or 30.0)


def _fool_kit_cols():
    try:
        n = int(_fool_get('LATAMAC_FOOL_KIT_COLS') or 5)
    except Exception:
        n = 5
    if n < 1:
        return 1
    return n


def _fool_kit_side_gap():
    return float(_fool_get('LATAMAC_FOOL_KIT_SIDE_GAP') or 8.0)


def _fool_kit_ttl_sec():
    val = _fool_get('LATAMAC_FOOL_KIT_TTL_SEC')
    if val is None:
        return 30.0
    try:
        n = float(val)
    except Exception:
        return 30.0
    if n < 0.0:
        return 0.0
    return n


def _bait_bury_y():
    val = _fool_get('LATAMAC_BAIT_BURY_Y')
    if val is None:
        return 30.0
    return float(val)


def _bait_sky_y():
    val = _fool_get('LATAMAC_BAIT_SKY_Y')
    if val is None:
        return 80.0
    return float(val)


def _bait_mode():
    text = str(_fool_get('LATAMAC_BAIT_MODE') or 'under').strip().lower()
    if text in ('sky', 'air', 'above', 'up'):
        return 'sky'
    return 'under'


def _bait_follow_sec():
    val = float(_fool_get('LATAMAC_BAIT_FOLLOW_SEC') or 0.05)
    if val < 0.05:
        return 0.05
    return val


def _bait_force_hits():
    try:
        hits = int(_fool_get('LATAMAC_BAIT_FORCE_HITS') or 4)
    except Exception:
        hits = 4
    if hits < 1:
        return 1
    if hits > 10:
        return 10
    return hits


def _bait_look_deg():
    return float(_fool_get('LATAMAC_BAIT_LOOK_DEG') or 18.0)


def _bait_look_hold_sec():
    return float(_fool_get('LATAMAC_BAIT_LOOK_HOLD_SEC') or 0.8)


def _bait_look_cooldown_sec():
    return float(_fool_get('LATAMAC_BAIT_LOOK_COOLDOWN_SEC') or 15.0)


def _bait_points():
    return float(_fool_get('LATAMAC_BAIT_POINTS') or 35.0)


def reload_latamac_config():
    """reload(latamac_config). Los valores se leen siempre del modulo."""
    global _latamac_cfg_mod
    try:
        if _latamac_cfg_mod is None:
            import latamac_config
            _latamac_cfg_mod = latamac_config
    except Exception as exc:
        return False, str(exc)
    try:
        reload(_latamac_cfg_mod)
    except Exception as exc:
        return False, str(exc)
    return True, ''


def _refresh_fooled_objects():
    """Recrea grillas de kits fool (sin caja orbitando)."""
    for ph, entry in list(_fooled.items()):
        player = _player_by_hash(ph)
        _clear_fool_orbit(entry)
        if player is not None and _fool_kit_grid_enabled():
            _spawn_fool_kit_grid(player, entry)


def _restart_fool_follow_task():
    """Reprograma el timer de seguimiento/giro de !ac fool."""
    global _fool_follow_task
    if not _IN_GAME or rtimer is None:
        return
    try:
        if _fool_follow_task is not None:
            _fool_follow_task.destroy()
    except Exception:
        pass
    interval = _fool_follow_sec()
    _fool_follow_task = rtimer.repeatingTask(
        _update_fool_follow,
        interval,
    )


def _ensure_fool_follow_task():
    """Garantiza que el timer de follow este vivo mientras haya fools."""
    global _fool_follow_task
    if not _IN_GAME or rtimer is None:
        return
    if _fool_follow_task is not None:
        return
    _restart_fool_follow_task()


# ------------------------------------------------------------------
# Helpers
# ------------------------------------------------------------------
def _player_hash(player):
    if player is None or rserver is None:
        return ''
    try:
        h = rserver.getPlayerHash(player)
        if h is True or h is None:
            return ''
        return str(h)
    except Exception:
        return ''


def _player_display_name(player):
    try:
        return str(player.getName() or '')
    except Exception:
        return ''


def _get_db_path():
    return latamac_db_path()


def _ensure_db_dir():
    parent = os.path.dirname(_get_db_path())
    if parent and not os.path.isdir(parent):
        try:
            os.makedirs(parent)
        except Exception:
            pass


def _ensure_db_schema(con):
    cur = con.cursor()
    cur.execute(
        'CREATE TABLE IF NOT EXISTS violations ('
        'id INTEGER PRIMARY KEY AUTOINCREMENT, '
        'ts REAL NOT NULL, '
        'round_tag TEXT, '
        'player_hash TEXT NOT NULL, '
        'player_name TEXT, '
        'rule_id TEXT NOT NULL, '
        'detail TEXT, '
        'points INTEGER NOT NULL)'
    )
    cur.execute(
        'CREATE INDEX IF NOT EXISTS idx_violations_hash_ts '
        'ON violations (player_hash, ts DESC)'
    )
    con.commit()


def _log_violation_db(player_hash, player_name, rule_id, detail, points):
    if not player_hash:
        return
    try:
        _ensure_db_dir()
        con = sqlite3.connect(_get_db_path())
        _ensure_db_schema(con)
        cur = con.cursor()
        cur.execute(
            'INSERT INTO violations '
            '(ts, round_tag, player_hash, player_name, rule_id, detail, points) '
            'VALUES (?, ?, ?, ?, ?, ?, ?)',
            (
                time.time(),
                _round_tag,
                player_hash,
                player_name,
                rule_id,
                detail,
                int(points),
            ),
        )
        con.commit()
        con.close()
    except Exception:
        pass


def _fetch_recent_violations(player_hash, limit=8):
    if not player_hash:
        return []
    try:
        con = sqlite3.connect(_get_db_path())
        _ensure_db_schema(con)
        cur = con.cursor()
        cur.execute(
            'SELECT ts, rule_id, detail, points FROM violations '
            'WHERE player_hash = ? ORDER BY ts DESC LIMIT ?',
            (player_hash, int(limit)),
        )
        rows = cur.fetchall()
        con.close()
        return rows
    except Exception:
        return []


def _weapon_template_name(weapon):
    if weapon is None:
        return ''
    try:
        string_types = (str, unicode)
    except NameError:
        string_types = (str,)
    if isinstance(weapon, string_types):
        return weapon.lower()
    try:
        return str(weapon.templateName).lower()
    except Exception:
        return ''


def _weapon_name_variants(name):
    if not name:
        return []
    variants = [name]
    if name.endswith('_projectile'):
        base = name[:-len('_projectile')]
        if base and base not in variants:
            variants.append(base)
    else:
        proj = name + '_projectile'
        if proj not in variants:
            variants.append(proj)
    return variants


def _is_exempt_kill_weapon(name):
    """True si el arma no aplica check de distancia (explosivos, vehiculo, etc.)."""
    if not name:
        return True
    if rconstants is None:
        return False
    for variant in _weapon_name_variants(name):
        wtype = rconstants.getWeaponType(variant)
        if wtype in (
            rconstants.WEAPON_TYPE_C4,
            rconstants.WEAPON_TYPE_CLAYMORE,
            rconstants.WEAPON_TYPE_ATMINE,
            rconstants.WEAPON_TYPE_HANDGRENADE,
            rconstants.WEAPON_TYPE_KNIFE,
            rconstants.WEAPON_TYPE_SHOCKPAD,
            rconstants.WEAPON_TYPE_TARGETING,
        ):
            return True
        ptype = rconstants.getProjectileType(variant)
        if ptype != rconstants.PROJECTILE_TYPE_UNKNOWN:
            return True
        for marker in (
            'artillery', 'mortar', 'jdam', 'bomb', 'rocket', 'missile',
            'hellfire', 'tnk_', 'c4_', 'mine', '_ied', 'claymore',
        ):
            if marker in variant:
                return True
    return False


def _max_kill_range_for_weapon(name):
    if _is_exempt_kill_weapon(name):
        return None
    if rconstants is None:
        return 500.0
    for variant in _weapon_name_variants(name):
        wtype = rconstants.getWeaponType(variant)
        if wtype == rconstants.WEAPON_TYPE_UNKNOWN:
            continue
        table = _weapon_range_table()
        if wtype in table:
            return table[wtype]
    return 500.0


def _vehicle_template_name(vehicle):
    if vehicle is None:
        return ''
    try:
        return str(vehicle.templateName).lower()
    except Exception:
        return ''


def _is_parachute(player):
    try:
        veh = player.getVehicle()
    except Exception:
        return False
    return _vehicle_template_name(veh) == 'parachute'


def _is_flying_vehicle(player):
    try:
        veh = player.getVehicle()
    except Exception:
        return False
    if veh is None:
        return False
    if rvehicles is not None:
        try:
            root = bf2.objectManager.getRootParent(veh)
            return bool(rvehicles.isFlyingVehicle(root))
        except Exception:
            pass
    if rconstants is not None:
        try:
            root = bf2.objectManager.getRootParent(veh)
            vt = rconstants.getVehicleType(root.templateName)
            return vt in (
                rconstants.VEHICLE_TYPE_HELI,
                rconstants.VEHICLE_TYPE_HELIATTACK,
                rconstants.VEHICLE_TYPE_JET,
                rconstants.VEHICLE_TYPE_UAV,
                rconstants.VEHICLE_TYPE_TURBOPROP,
            )
        except Exception:
            pass
    return False


def _is_on_foot(player):
    try:
        veh = player.getDefaultVehicle()
    except Exception:
        return True
    if veh is None:
        return True
    if rcore is not None:
        try:
            return bool(rcore.isSoldier(veh))
        except Exception:
            pass
    vname = _vehicle_template_name(veh)
    return vname == '' or 'soldier' in vname


def _movement_speed_limit(player):
    if _is_on_foot(player) or _is_parachute(player):
        return LATAMAC_SPEED_FOOT
    if _is_flying_vehicle(player):
        return None
    return LATAMAC_SPEED_GROUND_VEH


def _is_ac_exempt(player):
    """Jugadores que no se analizan (AI, admin, whitelist, conectando)."""
    if player is None:
        return True
    try:
        if not player.isValid() or player.isAIPlayer():
            return True
    except Exception:
        return True
    try:
        if getattr(player, 'isAdmin', False):
            return True
    except Exception:
        pass
    if rplayerdata is not None:
        try:
            if rplayerdata.isPlayerWhitelisted(player):
                return True
        except Exception:
            pass
    try:
        if radmin is not None and hasattr(radmin, 'AFKDetection'):
            if radmin.AFKDetection.isConnecting(player):
                return True
    except Exception:
        pass
    return False


def _player_by_hash(player_hash):
    if not player_hash:
        return None
    try:
        for player in bf2.playerManager.getPlayers():
            if _player_hash(player) == player_hash:
                return player
    except Exception:
        pass
    return None


# ------------------------------------------------------------------
# !ac fool - objeto girando sobre la cabeza
# ------------------------------------------------------------------
def _player_can_wear_fool(player):
    """True si el jugador puede llevar el fool (vivo/mandown, no en aire)."""
    try:
        if not player.isValid() or player.isAIPlayer():
            return False
    except Exception:
        return False
    if not player.isAlive() and not player.isManDown():
        return False
    if _is_parachute(player) or _is_flying_vehicle(player):
        return False
    # No exigir is_on_foot: si isSoldier falla, la caja quedaba quieta en el piso.
    return True


def _fool_orbit_pose(player, angle_deg):
    """Posicion en orbita horizontal alrededor del jugador. Sin giro propio."""
    if player is None:
        return None, None
    try:
        if not player.isValid():
            return None, None
    except Exception:
        return None, None
    try:
        soldier = player.getDefaultVehicle()
        if soldier is None:
            try:
                soldier = player.getVehicle()
            except Exception:
                soldier = None
        if soldier is None:
            return None, None
        pos = soldier.getPosition()
        angle = math.radians(float(angle_deg) % 360.0)
        radius = _fool_radius()
        orbit = (
            float(pos[0]) + radius * math.sin(angle),
            float(pos[1]) + _fool_head_offset_y(),
            float(pos[2]) + radius * math.cos(angle),
        )
        # Rotacion fija: no gira sobre su propio eje.
        return orbit, (0.0, 0.0, 0.0)
    except Exception:
        return None, None


def _destroy_fool_kits(entry):
    if not entry:
        return
    _cancel_fool_kit_expire(entry)
    for oid in list(entry.get('kit_ids') or []):
        if not oid or rcore is None:
            continue
        try:
            rcore.editObject(oid, (0.0, _fool_hide_y(), 0.0), None)
        except Exception:
            pass
        try:
            rcore.deleteObjectId(oid)
        except Exception:
            pass
    entry['kit_ids'] = []
    entry['kit_ally'] = 0
    entry['kit_enemy'] = 0


def _cancel_fool_kit_expire(entry):
    if not entry:
        return
    task = entry.pop('kit_expire_task', None)
    if task is None:
        return
    try:
        task.destroy()
    except Exception:
        try:
            task.cancel()
        except Exception:
            pass


def _expire_fool_kits(ph, gen):
    """Callback TTL: borra kits y saca al jugador del fool."""
    entry = _fooled.get(ph)
    if entry is None:
        return
    if int(entry.get('kit_gen', 0) or 0) != int(gen):
        return
    entry['kit_expire_task'] = None
    _destroy_fool_object(entry)
    _fooled.pop(ph, None)


def _schedule_fool_kit_expire(ph, entry):
    """Programa borrado de kits tras LATAMAC_FOOL_KIT_TTL_SEC."""
    if not entry or not ph:
        return
    _cancel_fool_kit_expire(entry)
    ttl = _fool_kit_ttl_sec()
    if ttl <= 0.0 or rtimer is None or not _IN_GAME:
        return
    gen = int(entry.get('kit_gen', 0) or 0) + 1
    entry['kit_gen'] = gen
    try:
        entry['kit_expire_task'] = rtimer.fireOnce(
            lambda args=None, _ph=ph, _gen=gen: _expire_fool_kits(_ph, _gen),
            ttl,
        )
    except Exception:
        entry['kit_expire_task'] = None


def _clear_fool_orbit(entry):
    """Quita la caja orbitando (legacy); no toca los kits."""
    if not entry:
        return
    obj_id = entry.get('obj_id')
    borrowed = bool(entry.get('borrowed'))
    if obj_id and rcore is not None and not borrowed:
        try:
            rcore.editObject(obj_id, (0.0, _fool_hide_y(), 0.0), None)
        except Exception:
            pass
        try:
            rcore.deleteObjectId(obj_id)
        except Exception:
            pass
    entry['obj_id'] = None
    entry['obj_ref'] = None
    entry['borrowed'] = False
    entry['attached'] = False
    entry['gone'] = False


def _destroy_fool_object(entry):
    if not entry:
        return
    _destroy_fool_kits(entry)
    _clear_fool_orbit(entry)


def _mark_fool_needs_respawn(entry):
    """Caja destruida/perdida: limpia refs y permite respawn con cooldown."""
    if not entry:
        return
    entry['obj_id'] = None
    entry['obj_ref'] = None
    entry['attached'] = False
    entry['gone'] = False
    entry['borrowed'] = False
    # Evita spawnear otra en el mismo tick / spam.
    entry['spawn_ts'] = time.time()


def _fool_object_alive(entry):
    """True si la caja sigue existiendo en el mundo."""
    if not entry:
        return False
    obj = entry.get('obj_ref')
    if obj is not None:
        try:
            if hasattr(obj, 'isValid') and not obj.isValid():
                return False
            obj.getPosition()
            return True
        except Exception:
            return False
    return bool(entry.get('obj_id'))


def _used_fool_object_ids():
    used = set()
    for entry in _fooled.values():
        oid = entry.get('obj_id')
        if oid:
            used.add(str(oid))
    return used


def _find_fool_object_near(pos, max_dist=None, max_dy=2.5):
    """Busca FOOL_TEMPLATE cerca de la orbita. Devuelve (obj_id, obj) o (None, None)."""
    template = _fool_template()
    if rcore is None or not template or pos is None:
        return None, None
    if max_dist is None:
        max_dist = max(3.0, _fool_radius() + 2.0)
    try:
        objs = list(rcore.getObjectsOfTemplate(template) or [])
    except Exception:
        return None, None
    used = _used_fool_object_ids()
    limit_sq = float(max_dist) * float(max_dist)
    best_id = None
    best_obj = None
    best_d = None
    for obj in objs:
        try:
            if obj is None:
                continue
            tname = str(obj.templateName or '').lower()
            want = template.lower()
            if tname != want and not tname.startswith(want):
                continue
            oid = rcore.getObjectId(obj)
            if not oid or str(oid) in used:
                continue
            op = obj.getPosition()
            dy = float(op[1]) - float(pos[1])
            if abs(dy) > float(max_dy):
                continue
            dx = float(op[0]) - float(pos[0])
            dz = float(op[2]) - float(pos[2])
            d2 = dx * dx + dy * dy + dz * dz
            if d2 > limit_sq:
                continue
            if best_d is None or d2 < best_d:
                best_d = d2
                best_id = oid
                best_obj = obj
        except Exception:
            continue
    return best_id, best_obj


def _normalize_object_id(oid):
    if oid is None:
        return None
    text = str(oid).strip()
    if not text:
        return None
    if text.lower().startswith('id'):
        text = text[2:]
    return text


def _resolve_fool_object(entry, near_pos=None):
    """Reatacha obj_ref vivo por id o por cercania al template."""
    if not entry or rcore is None:
        return None
    obj = entry.get('obj_ref')
    if obj is not None:
        try:
            if hasattr(obj, 'isValid') and not obj.isValid():
                obj = None
            else:
                obj.getPosition()
                return obj
        except Exception:
            obj = None
        entry['obj_ref'] = None

    oid = _normalize_object_id(entry.get('obj_id'))
    template = _fool_template()
    if not template:
        return None
    try:
        objs = list(rcore.getObjectsOfTemplate(template) or [])
    except Exception:
        return None

    best = None
    best_d = None
    for cand in objs:
        try:
            if cand is None:
                continue
            cid = _normalize_object_id(rcore.getObjectId(cand))
            if oid and cid and cid == oid:
                entry['obj_ref'] = cand
                entry['obj_id'] = cid
                return cand
            if near_pos is None:
                continue
            op = cand.getPosition()
            dx = float(op[0]) - float(near_pos[0])
            dy = float(op[1]) - float(near_pos[1])
            dz = float(op[2]) - float(near_pos[2])
            d2 = dx * dx + dy * dy + dz * dz
            if best_d is None or d2 < best_d:
                best_d = d2
                best = cand
        except Exception:
            continue
    if best is not None and best_d is not None and best_d <= (8.0 * 8.0):
        try:
            entry['obj_ref'] = best
            entry['obj_id'] = _normalize_object_id(rcore.getObjectId(best))
        except Exception:
            entry['obj_ref'] = best
        return best
    return None


def _rcon_move_object(oid, pos, rot=None):
    """Mueve por rcon Object.absolutePosition (mas fiable con SupplyObject)."""
    if host is None or not oid or pos is None:
        return False
    sid = _normalize_object_id(oid)
    if not sid:
        return False
    try:
        host.rcon_invoke('Object.active id%s' % sid)
        host.rcon_invoke(
            'Object.absolutePosition %s/%s/%s'
            % (float(pos[0]), float(pos[1]), float(pos[2]))
        )
        if rot is not None:
            host.rcon_invoke(
                'Object.rotation %s/%s/%s'
                % (float(rot[0]), float(rot[1]), float(rot[2]))
            )
        return True
    except Exception:
        return False


def _move_fool_object(entry, pos, rot):
    """Fuerza movimiento: setPosition + editObject + rcon absolutePosition."""
    if not entry or pos is None:
        return False
    obj = _resolve_fool_object(entry, pos)
    oid = _normalize_object_id(entry.get('obj_id'))
    if obj is not None and not oid and rcore is not None:
        try:
            oid = _normalize_object_id(rcore.getObjectId(obj))
            if oid:
                entry['obj_id'] = oid
        except Exception:
            pass

    moved = False
    if obj is not None:
        try:
            obj.setPosition(pos)
            moved = True
        except Exception:
            pass
        if rot is not None:
            try:
                obj.setRotation(rot)
            except Exception:
                pass

    if oid and rcore is not None:
        try:
            if rcore.editObject(oid, pos, rot):
                moved = True
        except Exception:
            pass

    if _rcon_move_object(oid, pos, rot):
        moved = True

    # Si sigue lejos del target, reintentar solo rcon (gravedad SupplyObject).
    if moved and obj is not None:
        try:
            cur = obj.getPosition()
            dx = float(cur[0]) - float(pos[0])
            dy = float(cur[1]) - float(pos[1])
            dz = float(cur[2]) - float(pos[2])
            if (dx * dx + dy * dy + dz * dz) > 1.0:
                _rcon_move_object(oid, pos, rot)
                try:
                    obj.setPosition(pos)
                except Exception:
                    pass
        except Exception:
            pass
    return moved


def _attach_fool_object(entry, oid, obj, borrowed=False):
    if not entry:
        return
    entry['obj_id'] = _normalize_object_id(oid) or oid
    entry['obj_ref'] = obj
    entry['attached'] = True
    entry['gone'] = False
    entry['borrowed'] = bool(borrowed)


def _set_pending_fool_body(oid, obj):
    global _pending_fool_body
    if oid and obj is not None:
        _pending_fool_body = (oid, obj)
    else:
        _pending_fool_body = None


def _take_pending_fool_body():
    """Consume el cuerpo pendiente si sigue valido. Devuelve (oid, obj) o (None, None)."""
    global _pending_fool_body
    pending = _pending_fool_body
    _pending_fool_body = None
    if not pending:
        return None, None
    oid, obj = pending
    if obj is not None:
        try:
            if hasattr(obj, 'isValid') and not obj.isValid():
                return None, None
            obj.getPosition()
            return oid, obj
        except Exception:
            return None, None
    return None, None


def _dead_player_body(player):
    """
    Si el jugador esta muerto o mandown con soldado valido,
    devuelve (template, obj_id, soldier). Si no, (None, None, None).
    """
    if player is None:
        return None, None, None
    try:
        if not player.isValid():
            return None, None, None
    except Exception:
        return None, None, None
    try:
        alive = bool(player.isAlive())
        mandown = bool(player.isManDown())
    except Exception:
        return None, None, None
    # Vivo y no mandown: no hay cuerpo usable.
    if alive and not mandown:
        return None, None, None
    try:
        soldier = player.getDefaultVehicle()
    except Exception:
        soldier = None
    if soldier is None:
        return None, None, None
    try:
        if hasattr(soldier, 'isValid') and not soldier.isValid():
            return None, None, None
    except Exception:
        return None, None, None
    try:
        template = str(soldier.templateName or '').strip()
    except Exception:
        template = ''
    if not template:
        return None, None, None
    oid = None
    if rcore is not None:
        try:
            oid = rcore.getObjectId(soldier)
        except Exception:
            oid = None
    return template, oid, soldier


def _refresh_fooled_with_body(body_oid=None, body_obj=None):
    """Fool ya no usa caja/cuerpo; solo refresca grillas de kits."""
    _refresh_fooled_objects()
    if body_oid and body_obj is not None:
        _set_pending_fool_body(body_oid, body_obj)


def _spawn_fool_object_create(pos, rot):
    """Spawn via Object.create (rcore.createObject). Devuelve (obj_id, obj)."""
    template = _fool_template()
    if rcore is None or not template:
        return None, None
    try:
        oid = rcore.createObject(
            template,
            pos,
            rot or (0.0, 0.0, 0.0),
        )
    except Exception:
        return None, None
    if not oid:
        return None, None
    found_id, obj = _find_fool_object_near(pos)
    if found_id:
        return found_id, obj
    return str(oid), None


def _spawn_fool_object_spawner(pos, rot):
    """Spawn via ObjectSpawner (igual que latamtreasures). Devuelve (obj_id, obj)."""
    template = _fool_template()
    if rspawner is None or not template:
        return None, None
    props = {
        'template': template,
        'position': pos,
        'rotation': rot or (0.0, 0.0, 0.0),
        'minspawndelay': 0,
        'maxspawndelay': 0,
        'spawndelayatstart': 0,
        'team': 1,
        'teamonvehicle': 0,
    }
    try:
        ok = rspawner.createSpawner(
            'latamac_fool', props, delete=False, reset=True, sufix=True,
        )
    except Exception:
        return None, None
    if not ok:
        return None, None
    return _find_fool_object_near(pos)


def _spawn_fool_object(player, angle_deg=0.0):
    """
    Spawnea UNA caja segun LATAMAC_FOOL_SPAWN_MODE del config:
      - 'spawner' -> ObjectSpawner (createSpawner)
      - 'create'  -> Object.create (rcore.createObject)
    Devuelve (obj_id, obj) o (None, None).
    """
    if not _fool_template() or rcore is None:
        return None, None
    pos, rot = _fool_orbit_pose(player, angle_deg)
    if pos is None:
        return None, None
    if _fool_spawn_mode() == 'create':
        return _spawn_fool_object_create(pos, rot)
    return _spawn_fool_object_spawner(pos, rot)


# ------------------------------------------------------------------
# !ac fool - grilla de kits aliados/enemigos bajo tierra
# ------------------------------------------------------------------
_FOOL_KIT_TYPE_FALLBACK = (
    'rifleman', 'medic', 'assault', 'support', 'engineer', 'riflemanat',
    'marksman', 'grenadier', 'officer', 'sniper', 'aa', 'at', 'mg',
    'specialist', 'riflemanap', 'spotter', 'sapper', 'crewman', 'tanker',
    'pilot',
)


def _team_faction_name(team):
    name = ''
    if rcore is not None:
        try:
            name = str(rcore.getTeamName(int(team)) or '').lower().strip()
        except Exception:
            name = ''
    if not name and bf2 is not None:
        try:
            name = str(bf2.gameLogic.getTeamName(int(team)) or '').lower().strip()
        except Exception:
            name = ''
    return name


def _kit_types_for_faction(faction):
    faction = str(faction or '').lower().strip()
    types = []
    if rserver_mod is not None and faction:
        try:
            limits = rserver_mod.C('KIT_LIMITS') or {}
            if faction in limits and isinstance(limits[faction], dict):
                types = list(limits[faction].keys())
        except Exception:
            types = []
    if not types:
        types = list(_FOOL_KIT_TYPE_FALLBACK)
    return types


def _kit_template_exists(name):
    if not name:
        return False
    if rkits is not None:
        try:
            return bool(rkits.kitExists(name))
        except Exception:
            pass
    if host is None:
        return True
    try:
        host.rcon_invoke('ObjectTemplate.active %s' % name)
        typ = host.rcon_invoke('ObjectTemplate.type').replace('\n', '').strip().lower()
        if 'no object template' in typ or typ == '':
            return False
        return True
    except Exception:
        return False


def _kit_templates_for_team(team):
    """Lista de templates de kit validos para la faccion del team (1|2)."""
    faction = _team_faction_name(team)
    if not faction:
        return []
    out = []
    seen = set()
    for kit_type in _kit_types_for_faction(faction):
        for suffix in ('', '_alt'):
            name = '%s_%s%s' % (faction, kit_type, suffix)
            key = name.lower()
            if key in seen:
                continue
            if not _kit_template_exists(name):
                continue
            seen.add(key)
            out.append(name)
    return out


def _find_object_near_any(templates, pos, max_dist=4.0, max_dy=8.0):
    if rcore is None or pos is None or not templates:
        return None, None
    used = set()
    for entry in _fooled.values():
        for oid in entry.get('kit_ids') or []:
            used.add(str(oid))
        oid = entry.get('obj_id')
        if oid:
            used.add(str(oid))
    limit_sq = float(max_dist) * float(max_dist)
    best_id = None
    best_obj = None
    best_d = None
    for template in templates:
        try:
            objs = list(rcore.getObjectsOfTemplate(template) or [])
        except Exception:
            continue
        want = str(template).lower()
        for obj in objs:
            try:
                if obj is None:
                    continue
                tname = str(obj.templateName or '').lower()
                if tname != want and not tname.startswith(want):
                    continue
                oid = _normalize_object_id(rcore.getObjectId(obj))
                if not oid or str(oid) in used:
                    continue
                op = obj.getPosition()
                dy = float(op[1]) - float(pos[1])
                if abs(dy) > float(max_dy):
                    continue
                dx = float(op[0]) - float(pos[0])
                dz = float(op[2]) - float(pos[2])
                d2 = dx * dx + dy * dy + dz * dz
                if d2 > limit_sq:
                    continue
                if best_d is None or d2 < best_d:
                    best_d = d2
                    best_id = oid
                    best_obj = obj
            except Exception:
                continue
    return best_id, best_obj


def _spawn_one_fool_kit(template, pos, team, player):
    """Spawnea un kit en pos. Devuelve obj_id o None."""
    if not template or pos is None:
        return None
    rot = (0.0, 0.0, 0.0)
    spawned = False

    if rkits is not None and player is not None:
        try:
            rkits.spawnerKit(player, pos, template, int(team), sound=False)
            spawned = True
        except TypeError:
            try:
                rkits.spawnerKit(player, pos, template, int(team))
                spawned = True
            except Exception:
                spawned = False
        except Exception:
            spawned = False

    if not spawned and rspawner is not None:
        props = {
            'template': template,
            'position': pos,
            'rotation': rot,
            'minspawndelay': 0,
            'maxspawndelay': 0,
            'spawndelayatstart': 0,
            'team': int(team),
            'teamonvehicle': 0,
        }
        try:
            spawned = bool(
                rspawner.createSpawner(
                    'latamac_foolkit', props, delete=False, reset=True, sufix=True,
                )
            )
        except Exception:
            spawned = False

    if not spawned and rcore is not None:
        try:
            oid = rcore.createObject(template, pos, rot)
            if oid:
                oid = _normalize_object_id(oid)
                _rcon_move_object(oid, pos, rot)
                return oid
        except Exception:
            return None

    oid, obj = _find_object_near_any([template], pos, max_dist=5.0, max_dy=12.0)
    if oid:
        _rcon_move_object(oid, pos, rot)
        if obj is not None:
            try:
                obj.setPosition(pos)
            except Exception:
                pass
        return oid
    return None


def _grid_positions(origin, count, cols, spacing, x_sign):
    """Posiciones en grilla bajo tierra. x_sign: -1 aliados, +1 enemigos."""
    positions = []
    cols = max(1, int(cols))
    spacing = float(spacing)
    side_gap = _fool_kit_side_gap()
    bury = _fool_kit_bury_y()
    ox, oy, oz = float(origin[0]), float(origin[1]), float(origin[2])
    rows = (int(count) + cols - 1) // cols
    for i in range(int(count)):
        col = i % cols
        row = i // cols
        # Centrar la grilla en su lado.
        x = ox + float(x_sign) * (side_gap + col * spacing)
        z = oz + (row - (rows - 1) * 0.5) * spacing
        y = oy - bury
        positions.append((x, y, z))
    return positions


def _spawn_fool_kit_grid(player, entry):
    """
    Crea N kits aliados + N enemigos bajo tierra en grilla.
    No siguen al jugador; quedan fijos (se fuerza Y bajo tierra al crear).
    """
    if not _fool_kit_grid_enabled() or player is None or entry is None:
        return 0, 0
    try:
        ally_team = int(player.getTeam())
    except Exception:
        return 0, 0
    if ally_team not in (1, 2):
        return 0, 0
    enemy_team = 1 if ally_team == 2 else 2

    try:
        soldier = player.getDefaultVehicle()
        if soldier is None:
            soldier = player.getVehicle()
        origin = soldier.getPosition()
    except Exception:
        return 0, 0

    count = _fool_kit_count()
    cols = _fool_kit_cols()
    spacing = _fool_kit_spacing()

    ally_kits = _kit_templates_for_team(ally_team)
    enemy_kits = _kit_templates_for_team(enemy_team)
    if not ally_kits and not enemy_kits:
        return 0, 0

    _destroy_fool_kits(entry)
    kit_ids = []
    ally_n = 0
    enemy_n = 0

    if ally_kits:
        for i, pos in enumerate(_grid_positions(origin, count, cols, spacing, -1)):
            template = ally_kits[i % len(ally_kits)]
            oid = _spawn_one_fool_kit(template, pos, ally_team, player)
            if oid:
                kit_ids.append(oid)
                ally_n += 1

    if enemy_kits:
        for i, pos in enumerate(_grid_positions(origin, count, cols, spacing, 1)):
            template = enemy_kits[i % len(enemy_kits)]
            oid = _spawn_one_fool_kit(template, pos, enemy_team, player)
            if oid:
                kit_ids.append(oid)
                enemy_n += 1

    entry['kit_ids'] = kit_ids
    entry['kit_ally'] = ally_n
    entry['kit_enemy'] = enemy_n
    entry['kit_ally_faction'] = _team_faction_name(ally_team)
    entry['kit_enemy_faction'] = _team_faction_name(enemy_team)
    ph = _player_hash(player) or entry.get('ph')
    if ph:
        entry['ph'] = ph
        if kit_ids:
            _schedule_fool_kit_expire(ph, entry)
    return ally_n, enemy_n


def _apply_fool(player):
    """Aplica fool: grilla de kits aliados/enemigos bajo tierra (sin caja)."""
    ph = _player_hash(player)
    if not ph:
        return False
    name = _player_display_name(player)
    entry = _fooled.get(ph)
    if entry is None:
        entry = {
            'name': name,
            'obj_id': None,
            'obj_ref': None,
            'yaw': 0.0,
            'spawn_ts': 0.0,
            'attached': False,
            'gone': False,
            'borrowed': False,
            'player_index': None,
            'kit_ids': [],
        }
        _fooled[ph] = entry
    else:
        entry['name'] = name
        _clear_fool_orbit(entry)

    try:
        entry['player_index'] = int(player.index)
    except Exception:
        entry['player_index'] = None

    if not _fool_kit_grid_enabled():
        return False
    _spawn_fool_kit_grid(player, entry)
    return True


def _remove_fool_by_hash(ph):
    entry = _fooled.pop(ph, None)
    if entry is not None:
        _destroy_fool_object(entry)


def _is_fooled(player):
    ph = _player_hash(player)
    return bool(ph and ph in _fooled)


def _maybe_respawn_fool(entry, player, yaw, now):
    """Busca caja pendiente o spawnea otra tras cooldown (1 a la vez)."""
    if entry is None or player is None:
        return
    pos, _rot = _fool_orbit_pose(player, yaw)
    if pos is None:
        return
    oid, obj = _find_fool_object_near(pos)
    if oid:
        _attach_fool_object(entry, oid, obj)
        return
    last = float(entry.get('spawn_ts', 0.0) or 0.0)
    if last > 0.0 and (now - last) < _fool_spawn_cooldown_sec():
        return
    oid, obj = _spawn_fool_object(player, yaw)
    entry['spawn_ts'] = now
    if oid:
        _attach_fool_object(entry, oid, obj)


def _maybe_periodic_recreate_fool(entry, player, yaw, now):
    """
    Cada LATAMAC_FOOL_RESPAWN_SEC: destruye el objeto y lo crea de nuevo.
    No aplica a cuerpos prestados (borrowed).
    """
    if entry is None or player is None:
        return False
    interval = _fool_respawn_sec()
    if interval <= 0.0:
        return False
    if entry.get('borrowed'):
        return False
    if not entry.get('obj_id'):
        return False
    last = float(entry.get('spawn_ts', 0.0) or 0.0)
    if last <= 0.0 or (now - last) < interval:
        return False

    _destroy_fool_object(entry)
    entry['attached'] = False
    entry['gone'] = False
    oid, obj = _spawn_fool_object(player, yaw)
    entry['spawn_ts'] = now
    if oid:
        _attach_fool_object(entry, oid, obj, borrowed=False)
        pos, rot = _fool_orbit_pose(player, yaw)
        if pos is not None:
            _move_fool_object(entry, pos, rot)
    return True


def _update_fool_follow(args=None):
    """Legacy: fool ya no orbita; limpia cajas viejas y jugadores ausentes."""
    if not _fooled:
        return
    for ph, entry in list(_fooled.items()):
        if entry.get('obj_id'):
            _clear_fool_orbit(entry)
        player = _player_by_hash(ph)
        if player is None:
            _destroy_fool_object(entry)
            _fooled.pop(ph, None)
            continue
        entry['name'] = _player_display_name(player)


# ------------------------------------------------------------------
# !ac bait - admin sigue al tramposo (honeypot ESP)
# ------------------------------------------------------------------
def _bait_pose_for(player):
    """Posicion de carnada: bajo tierra o en el cielo segun config."""
    if player is None:
        return None
    try:
        if not player.isValid():
            return None
    except Exception:
        return None
    try:
        soldier = player.getDefaultVehicle()
        if soldier is None:
            soldier = player.getVehicle()
        if soldier is None:
            return None
        pos = soldier.getPosition()
        if _bait_mode() == 'sky':
            return (
                float(pos[0]),
                float(pos[1]) + _bait_sky_y(),
                float(pos[2]),
            )
        return (
            float(pos[0]),
            float(pos[1]) - _bait_bury_y(),
            float(pos[2]),
        )
    except Exception:
        return None


def _player_surface_pos(player):
    try:
        soldier = player.getDefaultVehicle()
        if soldier is None:
            soldier = player.getVehicle()
        if soldier is None:
            return None
        return soldier.getPosition()
    except Exception:
        return None


def _force_player_position(player, pos, hits=None):
    """
    Fuerza posicion del soldado/vehiculo.
    setPosition solo no alcanza: el terreno/fisica lo devuelve a superficie.
    Martilla setPosition + editObject + rcon Object.absolutePosition.
    """
    if player is None or pos is None:
        return False
    if hits is None:
        hits = _bait_force_hits()
    want = (float(pos[0]), float(pos[1]), float(pos[2]))
    veh = None
    try:
        veh = player.getVehicle()
        if veh is None:
            veh = player.getDefaultVehicle()
    except Exception:
        veh = None
    if veh is None:
        return False

    oid = None
    if rcore is not None:
        try:
            oid = _normalize_object_id(rcore.getObjectId(veh))
        except Exception:
            oid = None

    ok = False
    for _ in range(max(1, int(hits))):
        try:
            veh.setPosition(want)
            ok = True
        except Exception:
            pass
        if oid and rcore is not None:
            try:
                if rcore.editObject(oid, want, None):
                    ok = True
            except Exception:
                pass
        if _rcon_move_object(oid, want, None):
            ok = True

    # Si el motor ya lo empujó hacia arriba, martillar otra vez.
    try:
        cur = veh.getPosition()
        if abs(float(cur[1]) - want[1]) > 2.0:
            for _ in range(2):
                try:
                    veh.setPosition(want)
                except Exception:
                    pass
                _rcon_move_object(oid, want, None)
                if oid and rcore is not None:
                    try:
                        rcore.editObject(oid, want, None)
                    except Exception:
                        pass
    except Exception:
        pass
    return ok


def _teleport_player_to(player, pos):
    return _force_player_position(player, pos)


def _admin_can_bait(admin):
    if admin is None:
        return False
    try:
        if not admin.isValid() or admin.isAIPlayer():
            return False
        if not admin.isAlive() or admin.isManDown():
            return False
    except Exception:
        return False
    return True


def _clear_bait_sessions_for_admin(admin_hash):
    """Un admin solo puede cebar a un target a la vez."""
    if not admin_hash:
        return
    for ph, entry in list(_baited.items()):
        if entry.get('admin_hash') == admin_hash:
            _stop_bait_session(ph, restore_admin=True)


def _stop_bait_session(target_hash, restore_admin=True):
    entry = _baited.pop(target_hash, None)
    if entry is None:
        return
    if not restore_admin:
        return
    admin = _player_by_hash(entry.get('admin_hash'))
    if admin is None:
        return
    ret = entry.get('return_pos')
    if ret is not None:
        _force_player_position(admin, ret)
        return
    target = _player_by_hash(target_hash)
    if target is not None:
        surf = _player_surface_pos(target)
        if surf is not None:
            _force_player_position(
                admin,
                (float(surf[0]), float(surf[1]) + 1.0, float(surf[2])),
            )


def _apply_bait(target, admin):
    """Admin = carnada: sigue al target under/sky segun config."""
    th = _player_hash(target)
    ah = _player_hash(admin)
    if not th or not ah:
        return False, 'hash invalido'
    if th == ah:
        return False, 'no podes cebarte a vos mismo'
    if not _admin_can_bait(admin):
        return False, 'tenes que estar vivo'

    _clear_bait_sessions_for_admin(ah)
    if th in _baited:
        _stop_bait_session(th, restore_admin=True)

    return_pos = _player_surface_pos(admin)
    bait_pos = _bait_pose_for(target)
    if bait_pos is None:
        return False, 'no se pudo obtener posicion del target'

    if not _force_player_position(admin, bait_pos):
        return False, 'no se pudo forzar posicion del admin'

    _baited[th] = {
        'name': _player_display_name(target),
        'admin_hash': ah,
        'admin_name': _player_display_name(admin),
        'bait_pos': bait_pos,
        'return_pos': return_pos,
        'look_since': 0.0,
        'last_score_ts': 0.0,
    }
    _ensure_bait_follow_task()
    return True, ''


def _remove_bait_by_hash(ph, restore_admin=True):
    _stop_bait_session(ph, restore_admin=restore_admin)


def _is_baited(player):
    ph = _player_hash(player)
    return bool(ph and ph in _baited)


def _restart_bait_follow_task():
    global _bait_follow_task
    if not _IN_GAME or rtimer is None:
        return
    try:
        if _bait_follow_task is not None:
            _bait_follow_task.destroy()
    except Exception:
        pass
    _bait_follow_task = rtimer.repeatingTask(
        _update_bait_follow,
        _bait_follow_sec(),
    )


def _ensure_bait_follow_task():
    global _bait_follow_task
    if not _IN_GAME or rtimer is None:
        return
    if _bait_follow_task is not None:
        return
    _restart_bait_follow_task()


def _refresh_baited_objects():
    if _baited:
        _restart_bait_follow_task()


def _check_bait_look(target, entry, bait_pos, now):
    if _tracker is None or rcore is None or bait_pos is None:
        return
    try:
        if not target.isAlive() or target.isManDown():
            entry['look_since'] = 0.0
            return
    except Exception:
        entry['look_since'] = 0.0
        return

    looking = False
    try:
        looking = bool(
            rcore.isPlayerLookingAtPoint(target, bait_pos, _bait_look_deg())
        )
    except Exception:
        looking = False

    if not looking:
        entry['look_since'] = 0.0
        return

    if not entry.get('look_since'):
        entry['look_since'] = now
        return

    if (now - float(entry['look_since'])) < _bait_look_hold_sec():
        return

    last = float(entry.get('last_score_ts', 0.0) or 0.0)
    if last > 0.0 and (now - last) < _bait_look_cooldown_sec():
        return

    detail = 'mode=%s offset=%.1fm admin=%s' % (
        _bait_mode(),
        _bait_sky_y() if _bait_mode() == 'sky' else _bait_bury_y(),
        entry.get('admin_name') or '?',
    )
    _tracker.add_violation(target, 'bait_look', detail, _bait_points())
    entry['last_score_ts'] = now
    entry['look_since'] = 0.0


def _update_bait_follow(args=None):
    if not _baited:
        return
    _ensure_bait_follow_task()
    now = time.time()
    for th, entry in list(_baited.items()):
        target = _player_by_hash(th)
        admin = _player_by_hash(entry.get('admin_hash'))

        if target is None:
            _stop_bait_session(th, restore_admin=True)
            continue
        if admin is None or not _admin_can_bait(admin):
            _stop_bait_session(th, restore_admin=False)
            continue

        entry['name'] = _player_display_name(target)
        entry['admin_name'] = _player_display_name(admin)

        try:
            target_ok = bool(target.isAlive() or target.isManDown())
        except Exception:
            target_ok = False
        if not target_ok:
            entry['look_since'] = 0.0
            continue

        bait_pos = _bait_pose_for(target)
        if bait_pos is None:
            continue

        _force_player_position(admin, bait_pos)
        entry['bait_pos'] = bait_pos
        _check_bait_look(target, entry, bait_pos, now)


def _spawn_grace_active(player, state, now):
    if state is None:
        return True
    spawn_t = state.get('spawn_time', 0.0)
    if spawn_t <= 0:
        return True
    return (now - spawn_t) < LATAMAC_SPAWN_GRACE_SEC


def _vehicle_change_grace_active(state, now):
    if state is None:
        return False
    change_t = state.get('vehicle_change_time', 0.0)
    if change_t <= 0:
        return False
    return (now - change_t) < LATAMAC_VEHICLE_CHANGE_GRACE_SEC


def _player_ping(player):
    try:
        return int(player.getPing())
    except Exception:
        return 0


def _get_position(player):
    try:
        veh = player.getDefaultVehicle()
        if veh is None:
            return None
        return veh.getPosition()
    except Exception:
        return None


def _vehicle_key(player):
    try:
        veh = player.getVehicle()
        if veh is None:
            return 'foot'
        root = bf2.objectManager.getRootParent(veh)
        return _vehicle_template_name(root) or 'unknown'
    except Exception:
        return 'unknown'


# ------------------------------------------------------------------
# Tracker + scoring
# ------------------------------------------------------------------
class PlayerTracker(object):
    def __init__(self):
        self.players = {}

    def get(self, player_hash):
        if not player_hash:
            return None
        if player_hash not in self.players:
            self.players[player_hash] = {
                'name': '',
                'score': 0.0,
                'pos': None,
                'pos_t': 0.0,
                'spawn_time': 0.0,
                'vehicle_key': 'foot',
                'vehicle_change_time': 0.0,
                'last_decay': time.time(),
            }
        return self.players[player_hash]

    def remove(self, player_hash):
        if player_hash in self.players:
            del self.players[player_hash]

    def touch_name(self, player_hash, name):
        st = self.get(player_hash)
        if st is not None:
            st['name'] = name

    def on_spawn(self, player):
        ph = _player_hash(player)
        st = self.get(ph)
        if st is None:
            return
        now = time.time()
        st['spawn_time'] = now
        st['pos'] = _get_position(player)
        st['pos_t'] = now
        st['vehicle_key'] = _vehicle_key(player)
        st['vehicle_change_time'] = now
        st['name'] = _player_display_name(player)

    def decay_all(self):
        now = time.time()
        for ph, st in self.players.items():
            last = st.get('last_decay', now)
            if now - last < LATAMAC_SCORE_DECAY_INTERVAL:
                continue
            st['score'] *= LATAMAC_SCORE_DECAY_FACTOR
            st['last_decay'] = now
            if st['score'] < 0.5:
                st['score'] = 0.0

    def add_violation(self, player, rule_id, detail, points):
        ph = _player_hash(player)
        if not ph:
            return 0.0
        st = self.get(ph)
        st['name'] = _player_display_name(player)
        st['score'] = float(st.get('score', 0.0)) + float(points)

        _log_violation_db(ph, st['name'], rule_id, detail, points)

        return st['score']


# ------------------------------------------------------------------
# Detectores
# ------------------------------------------------------------------
def _check_movement(player, state, pos, now):
    if _is_ac_exempt(player):
        return
    if not player.isAlive() or player.isManDown():
        return
    if _spawn_grace_active(player, state, now):
        return
    if _vehicle_change_grace_active(state, now):
        return
    ping = _player_ping(player)
    if ping > LATAMAC_MAX_PING:
        return

    prev_pos = state.get('pos')
    prev_t = state.get('pos_t', 0.0)
    if prev_pos is None or prev_t <= 0:
        state['pos'] = pos
        state['pos_t'] = now
        return

    dt = now - prev_t
    if dt <= 0.05:
        state['pos'] = pos
        state['pos_t'] = now
        return

    dx = pos[0] - prev_pos[0]
    dz = pos[2] - prev_pos[2]
    horiz = math.sqrt(dx * dx + dz * dz)
    speed = horiz / dt

    vkey = _vehicle_key(player)
    if vkey != state.get('vehicle_key'):
        state['vehicle_key'] = vkey
        state['vehicle_change_time'] = now
        state['pos'] = pos
        state['pos_t'] = now
        return

    limit = _movement_speed_limit(player)
    if limit is not None and speed > limit:
        detail = 'speed=%.1f limit=%.1f dt=%.2fs veh=%s' % (
            speed, limit, dt, vkey,
        )
        _tracker.add_violation(player, 'teleport', detail, POINTS_TELEPORT)

    if _is_on_foot(player) and not _is_parachute(player) and not _is_flying_vehicle(player):
        dy = pos[1] - prev_pos[1]
        vert_speed = dy / dt
        if vert_speed > 12.0 and dy > 4.0:
            detail = 'dy=%.1fm vert=%.1fm/s' % (dy, vert_speed)
            _tracker.add_violation(player, 'fly', detail, POINTS_FLY)

    state['pos'] = pos
    state['pos_t'] = now


def _check_kill(victim, attacker, weapon):
    if _tracker is None:
        return
    if attacker is None or victim is None:
        return
    if _is_ac_exempt(attacker):
        return
    try:
        if not attacker.isValid() or not victim.isValid():
            return
        if attacker.getTeam() == victim.getTeam():
            return
    except Exception:
        return

    try:
        att_pos = attacker.getDefaultVehicle().getPosition()
        vic_pos = victim.getDefaultVehicle().getPosition()
    except Exception:
        return

    if rcore is not None:
        dist = math.sqrt(rcore.getSquareHorizDistance(att_pos, vic_pos))
    else:
        dx = att_pos[0] - vic_pos[0]
        dz = att_pos[2] - vic_pos[2]
        dist = math.sqrt(dx * dx + dz * dz)

    wname = _weapon_template_name(weapon)
    max_range = _max_kill_range_for_weapon(wname)
    if max_range is not None and dist > max_range + 25.0:
        detail = 'dist=%.0fm max=%.0fm weapon=%s' % (dist, max_range, wname)
        _tracker.add_violation(attacker, 'kill_distance', detail, POINTS_KILL_DISTANCE)

    if rcore is not None and _is_on_foot(attacker) and max_range is not None:
        if not rcore.isPlayerLookingAtPoint(attacker, vic_pos, LATAMAC_AIM_TOLERANCE_DEG):
            detail = 'dist=%.0fm weapon=%s' % (dist, wname)
            _tracker.add_violation(attacker, 'snap_aim', detail, POINTS_SNAP_AIM)


# ------------------------------------------------------------------
# Handlers
# ------------------------------------------------------------------
def on_position_tick(args=None):
    # Backup del follow: si el timer rapido muere, igual empuja la caja.
    if _baited:
        try:
            _update_bait_follow()
        except Exception:
            pass
    if _tracker is None or not LATAMAC_ENABLED:
        return
    _tracker.decay_all()
    now = time.time()
    try:
        players = bf2.playerManager.getPlayers()
    except Exception:
        return
    for player in players:
        if _is_ac_exempt(player):
            continue
        ph = _player_hash(player)
        st = _tracker.get(ph)
        if st is None:
            continue
        pos = _get_position(player)
        if pos is None:
            continue
        _check_movement(player, st, pos, now)


def on_player_spawn(player, soldier):
    if _tracker is not None:
        _tracker.on_spawn(player)
    ph = _player_hash(player)
    if ph in _fooled:
        entry = _fooled[ph]
        _clear_fool_orbit(entry)
        if _fool_kit_grid_enabled():
            _spawn_fool_kit_grid(player, entry)
    if ph in _baited:
        # Target respawneo: el admin sigue en bait; no hace falta recrear caja.
        entry = _baited[ph]
        entry['look_since'] = 0.0


def on_player_connect(player):
    if _tracker is not None:
        ph = _player_hash(player)
        _tracker.touch_name(ph, _player_display_name(player))


def on_player_disconnect(player):
    ph = _player_hash(player)
    if ph in _fooled:
        _destroy_fool_object(_fooled.pop(ph))
    # Si se desconecta el target o el admin bait, cortar sesion.
    if ph in _baited:
        _stop_bait_session(ph, restore_admin=True)
    for th, entry in list(_baited.items()):
        if entry.get('admin_hash') == ph:
            _stop_bait_session(th, restore_admin=False)
    if _tracker is not None:
        _tracker.remove(ph)


def on_enemy_killed(victim, attacker, weapon, assists, obj):
    _check_kill(victim, attacker, weapon)


def on_round_start(data=''):
    global _round_tag
    global _pending_fool_body
    _round_tag = time.strftime('%Y-%m-%d_%H-%M')
    _pending_fool_body = None
    for ph in list(_fooled.keys()):
        _remove_fool_by_hash(ph)
    for ph in list(_baited.keys()):
        _remove_bait_by_hash(ph)
    if _tracker is None:
        return
    for st in _tracker.players.values():
        st['spawn_time'] = 0.0


# ------------------------------------------------------------------
# Comando !ac
# ------------------------------------------------------------------
def _pm(admin, msg):
    if radmin is None or admin is None:
        return
    try:
        radmin.personalMessage(str(msg), admin)
    except Exception:
        pass


def command_ac(args, admin):
    args = [str(a) for a in list(args or []) if a is not None and str(a).strip()]
    if len(args) == 0:
        _pm(admin, 'Uso: !ac status|reset|fool|unfool|bait|unbait|body|spawnmode|reload')
        return False

    sub = args[0].lower()
    if sub in ('help', '?'):
        _pm(admin, 'Uso: !ac status|reset|fool|unfool|bait|unbait|body|spawnmode|reload')
        _pm(admin, 'bait: VOS seguis al tramposo (mode=%s)' % _bait_mode())
        return True

    if sub == 'reload':
        ok, err = reload_latamac_config()
        if not ok:
            _pm(admin, 'Error recargando latamac_config: %s' % err)
            return False
        _restart_fool_follow_task()
        _restart_bait_follow_task()
        _refresh_fooled_objects()
        _refresh_baited_objects()
        _pm(
            admin,
            'latamac_config: fool=%s bait_mode=%s offset=%.1fm force=%sx/%.2fs'
            % (
                _fool_template(),
                _bait_mode(),
                _bait_sky_y() if _bait_mode() == 'sky' else _bait_bury_y(),
                _bait_force_hits(),
                _bait_follow_sec(),
            ),
        )
        if radmin is not None:
            try:
                radmin.logAdmin('!ac reload', admin.getName(), '', _fool_template())
            except Exception:
                pass
        return True

    if sub in ('bait', 'unbait'):
        if radmin is None:
            return False
        if sub == 'unbait' and len(args) < 2:
            # Sin arg: cortar todas las sesiones de este admin.
            ah = _player_hash(admin)
            n = 0
            for th, entry in list(_baited.items()):
                if entry.get('admin_hash') == ah:
                    _stop_bait_session(th, restore_admin=True)
                    n += 1
            _pm(admin, 'Bait detenido (%s sesion/es). Volviste a tu posicion.' % n)
            return True
        if len(args) < 2:
            _pm(admin, 'Falta jugador.')
            return False
        found = radmin.findPlayer(args[1], admin)
        if not found:
            return False
        target = found[0]
        ph = _player_hash(target)
        name = _player_display_name(target)
        if sub == 'bait':
            ok, err = _apply_bait(target, admin)
            if not ok:
                _pm(admin, 'No se pudo bait a %s: %s' % (name, err or '?'))
                return False
            _pm(
                admin,
                'Bait activo: seguis a %s (%s offset=%.0fm, force rcon). !ac unbait para volver.'
                % (
                    name,
                    _bait_mode(),
                    _bait_sky_y() if _bait_mode() == 'sky' else _bait_bury_y(),
                ),
            )
            try:
                radmin.logAdmin('!ac bait', admin.getName(), name, ph[:16])
            except Exception:
                pass
            return True
        _remove_bait_by_hash(ph, restore_admin=True)
        _pm(admin, 'Bait removido para %s (admin restaurado).' % name)
        try:
            radmin.logAdmin('!ac unbait', admin.getName(), name, ph[:16])
        except Exception:
            pass
        return True

    if sub in ('spawnmode', 'spawn', 'mode'):
        if len(args) < 2:
            _pm(
                admin,
                'spawnmode actual: %s (create=Object.create, spawner=ObjectSpawner)'
                % _fool_spawn_mode(),
            )
            return True
        raw = args[1].lower()
        if raw not in (
            'create', 'object.create', 'objectcreate', 'objcreate',
            'spawner', 'objectspawner', 'object.spawner', 'spawn',
        ):
            _pm(admin, 'Uso: !ac spawnmode create|spawner')
            return False
        mode = _normalize_fool_spawn_mode(raw)
        if not _fool_set('LATAMAC_FOOL_SPAWN_MODE', mode):
            _pm(admin, 'latamac_config no disponible')
            return False
        _refresh_fooled_objects()
        _pm(admin, 'Fool spawnmode = %s (recreados fooled activos)' % _fool_spawn_mode())
        if radmin is not None:
            try:
                radmin.logAdmin(
                    '!ac spawnmode', admin.getName(), '', _fool_spawn_mode(),
                )
            except Exception:
                pass
        return True

    if sub in ('body', 'template', 'corps'):
        if len(args) < 2:
            _pm(admin, 'Fool template actual: %s' % _fool_template())
            return True
        if args[1].lower() in ('reset', 'default', 'crate', 'config'):
            _set_pending_fool_body(None, None)
            ok, err = reload_latamac_config()
            if not ok:
                _pm(admin, 'Error restaurando config: %s' % err)
                return False
            _restart_fool_follow_task()
            _refresh_fooled_objects()
            _pm(admin, 'Fool template restaurado: %s' % _fool_template())
            return True
        if radmin is None:
            return False
        found = radmin.findPlayer(args[1], admin)
        if not found:
            return False
        donor = found[0]
        donor_name = _player_display_name(donor)
        template, body_oid, body_obj = _dead_player_body(donor)
        if not template:
            _pm(
                admin,
                '%s no tiene cuerpo usable (debe estar muerto o mandown).'
                % donor_name,
            )
            return False
        if not _fool_set('LATAMAC_FOOL_TEMPLATE', template):
            _pm(admin, 'latamac_config no disponible')
            return False
        if _fooled:
            _refresh_fooled_with_body(body_oid, body_obj)
            note = 'cuerpo adjunto a fool activo' if body_oid else 'template aplicado'
        else:
            _set_pending_fool_body(body_oid, body_obj)
            note = 'pendiente para el proximo !ac fool'
        _pm(
            admin,
            'Fool template = %s (de %s, %s)'
            % (_fool_template(), donor_name, note),
        )
        try:
            radmin.logAdmin('!ac body', admin.getName(), donor_name, template)
        except Exception:
            pass
        return True

    if sub == 'status':
        target = admin
        if len(args) >= 2 and radmin is not None:
            found = radmin.findPlayer(args[1], admin)
            if not found:
                return False
            target = found[0]
        ph = _player_hash(target)
        st = _tracker.get(ph) if _tracker is not None else None
        score = st.get('score', 0.0) if st else 0.0
        _pm(
            admin,
            '%s score=%.0f fool=%s bait=%s hash=%s'
            % (
                _player_display_name(target),
                score,
                _is_fooled(target),
                _is_baited(target),
                ph[:12],
            ),
        )
        rows = _fetch_recent_violations(ph, 6)
        if not rows:
            _pm(admin, 'Sin violaciones registradas.')
            return True
        for ts, rule_id, detail, points in rows:
            when = time.strftime('%H:%M:%S', time.localtime(ts))
            _pm(admin, '%s %s +%s %s' % (when, rule_id, points, detail or ''))
        return True

    if sub == 'reset':
        if len(args) < 2:
            _pm(admin, 'Falta jugador.')
            return False
        if radmin is None:
            return False
        found = radmin.findPlayer(args[1], admin)
        if not found:
            return False
        target = found[0]
        ph = _player_hash(target)
        name = _player_display_name(target)
        st = _tracker.get(ph) if _tracker is not None else None
        if st is not None:
            st['score'] = 0.0
        _pm(admin, 'Score AC reseteado para %s' % name)
        return True

    if sub in ('fool', 'unfool'):
        if len(args) < 2:
            _pm(admin, 'Falta jugador.')
            return False
        if radmin is None:
            return False
        found = radmin.findPlayer(args[1], admin)
        if not found:
            return False
        target = found[0]
        ph = _player_hash(target)
        name = _player_display_name(target)
        if sub == 'fool':
            if not ph:
                _pm(admin, 'No se pudo obtener hash de %s' % name)
                return False
            if not _apply_fool(target):
                _pm(admin, 'No se pudo aplicar fool a %s' % name)
                return False
            entry = _fooled.get(ph) or {}
            _pm(
                admin,
                'Fool activo para %s (kits=%s/%s fac=%s vs %s bury=%.0fm ttl=%.0fs)'
                % (
                    name,
                    entry.get('kit_ally', 0),
                    entry.get('kit_enemy', 0),
                    entry.get('kit_ally_faction') or '?',
                    entry.get('kit_enemy_faction') or '?',
                    _fool_kit_bury_y(),
                    _fool_kit_ttl_sec(),
                ),
            )
            try:
                radmin.logAdmin('!ac fool', admin.getName(), name, ph[:16])
            except Exception:
                pass
            return True
        _remove_fool_by_hash(ph)
        _pm(admin, 'Fool removido para %s' % name)
        try:
            radmin.logAdmin('!ac unfool', admin.getName(), name, ph[:16])
        except Exception:
            pass
        return True

    _pm(admin, 'Subcomando desconocido. Uso: !ac status|reset|fool|unfool|bait|unbait|reload')
    return False


# ------------------------------------------------------------------
# Init
# ------------------------------------------------------------------
def init():
    global _tracker
    global LATAMAC_DB_PATH
    global _latamac_cfg_mod
    if not _IN_GAME or not LATAMAC_ENABLED:
        return

    if _latamac_cfg_mod is None:
        try:
            import latamac_config
            _latamac_cfg_mod = latamac_config
        except Exception:
            pass

    LATAMAC_DB_PATH = latamac_db_path()

    _ensure_db_dir()
    try:
        con = sqlite3.connect(_get_db_path())
        _ensure_db_schema(con)
        con.close()
    except Exception:
        pass

    _tracker = PlayerTracker()

    def _power(name, default):
        if ras is None:
            return default
        return ras.adm_adminPowerLevels.get(name, default)

    radmin.addCommand('ac', command_ac, _power('ac', 1))

    host.registerHandler('PlayerConnect', on_player_connect, 1)
    host.registerHandler('PlayerDisconnect', on_player_disconnect, 1)
    host.registerHandler('PlayerSpawn', on_player_spawn, 1)
    host.registerHandler('PlayerEnemyKilled', on_enemy_killed, 1)
    host.registerHandler('RoundStart', on_round_start, 1)
    rtimer.repeatingTask(on_position_tick, LATAMAC_TICK_SEC)
    _restart_fool_follow_task()
    _restart_bait_follow_task()


if _IN_GAME:
    init()
