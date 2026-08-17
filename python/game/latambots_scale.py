# -*- coding: utf-8 -*-
"""
latambots_scale.py - srv3 coop: 56 bots siempre, liberados segun humanos online.

Camino 2: posiciones por mapa/capa/equipo en latambots_scale_maps.json (override)
y latambots_scale_cache.json (auto-detect en primera ronda del mapa).

Bots "retenidos" se teletransportan a una zona segura en main; al subir humanos,
se sueltan cerca del punto de release (spawn/main) y ESAI toma el control.
"""

from __future__ import print_function

import json
import os
import time

try:
    import bf2
    import host
    import realityconstants as CONSTANTS
    import realitycore as rcore
    import realitymemory as rmemory
    import realityserver
    import realitytimer as rtimer
    _IN_GAME = True
except ImportError:
    bf2 = None
    host = None
    CONSTANTS = None
    rcore = None
    rmemory = None
    realityserver = None
    rtimer = None
    _IN_GAME = False

# getRoot es opcional (soldados a veces no necesitan root de vehiculo).
try:
    import realityvehicles as rvehicles
except ImportError:
    rvehicles = None

# --- Rutas srv3 ---
_GAME_DIR = os.path.dirname(os.path.abspath(__file__))
_MAPS_JSON = os.path.join(_GAME_DIR, 'latambots_scale_maps.json')
_CACHE_JSON = os.path.join(_GAME_DIR, 'latambots_scale_cache.json')
_LOG_PATH = 'C:/prbf2_db/sv3/latambots_scale.log'

# Estado de ronda (solo en memoria).
_round_ready = False
_map_key = None
_layer_key = None
_team_positions = {}  # team int -> {'hold': tuple, 'release': tuple}
_held_indices = set()  # player.index retenidos

# Defaults si realityconfig_coop no define tiers.
_DEFAULT_TIERS = (
    (1, 32),
    (3, 40),
    (6, 48),
    (10, 56),
)


# ---------------------------------------------------------------------------
# Funciones puras (testeables sin bf2)
# ---------------------------------------------------------------------------

def tier_active_bots(human_count, tiers):
    """
    Devuelve cuantos bots deben estar activos segun humanos conectados.
    tiers: secuencia de (min_humanos, bots_activos) ordenada ascendente.
    """
    humans = max(0, int(human_count))
    active = 0
    if not tiers:
        return 0
    active = int(tiers[0][1])
    for min_h, bot_count in tiers:
        if humans >= int(min_h):
            active = int(bot_count)
    return active


def split_team_limits(total_active, team1_bots, team2_bots):
    """Reparte el cupo activo entre equipos segun cuantos bots hay en cada uno."""
    t1 = max(0, int(team1_bots))
    t2 = max(0, int(team2_bots))
    total = t1 + t2
    total_active = max(0, int(total_active))
    if total_active <= 0 or total <= 0:
        return (0, 0)
    if total_active >= total:
        return (t1, t2)
    # Reparto proporcional; el redondeo se corrige en team 2.
    t1_active = int(round(total_active * (float(t1) / float(total))))
    if t1_active > t1:
        t1_active = t1
    t2_active = total_active - t1_active
    if t2_active > t2:
        t2_active = t2
        t1_active = total_active - t2_active
    return (t1_active, t2_active)


def normalize_coords(value):
    """Convierte lista/tuple de 3 numeros a tuple de float, o None."""
    if value is None:
        return None
    if not isinstance(value, (list, tuple)) or len(value) < 3:
        return None
    try:
        return (float(value[0]), float(value[1]), float(value[2]))
    except (TypeError, ValueError):
        return None


def spaced_slot_offset(slot, spacing, cols):
    """
    Offset XZ en grilla centrada para un slot (0..N-1).
    Evita apilar todos los bots en el mismo punto (colisiones / TK vehiculos).
    """
    slot = max(0, int(slot))
    spacing = float(spacing)
    cols = max(1, int(cols))
    row = slot // cols
    col = slot % cols
    # Centrar la grilla alrededor del origen.
    x = (col - (cols - 1) * 0.5) * spacing
    z = (row - 0.5) * spacing
    return (x, 0.0, z)


def apply_slot_offset(base_pos, slot, spacing, cols):
    """Suma offset de grilla a una posicion base (x,y,z)."""
    if base_pos is None:
        return None
    ox, oy, oz = spaced_slot_offset(slot, spacing, cols)
    return (
        float(base_pos[0]) + ox,
        float(base_pos[1]) + oy,
        float(base_pos[2]) + oz,
    )


def resolve_team_positions(maps_data, cache_data, map_id, layer, team, auto_positions):
    """
    Prioridad: override maps.json -> cache.json -> auto_positions (detectado en ronda).
    auto_positions: dict team -> {'hold': tuple, 'release': tuple}
    """
    layer_key = str(int(layer))
    team_key = str(int(team))
    for source in (maps_data, cache_data):
        try:
            entry = source['maps'][map_id][layer_key][team_key]
            hold = normalize_coords(entry.get('hold'))
            release = normalize_coords(entry.get('release'))
            if hold and release:
                return {'hold': hold, 'release': release, 'source': entry.get('source', 'file')}
        except (KeyError, TypeError, ValueError):
            pass
    auto = auto_positions.get(int(team))
    if auto and auto.get('hold') and auto.get('release'):
        return {
            'hold': auto['hold'],
            'release': auto['release'],
            'source': 'auto',
        }
    return None


# ---------------------------------------------------------------------------
# Utilidades runtime
# ---------------------------------------------------------------------------

def _cfg(key, default=None):
    try:
        value = realityserver.C(key)
        if value is None:
            return default
        return value
    except Exception:
        return default


def _enabled():
    if not _IN_GAME:
        return False
    try:
        if not realityserver.isCoopServer():
            return False
    except Exception:
        return False
    return bool(_cfg('BOT_SCALE_ENABLED', 1))


def _tiers():
    tiers = _cfg('BOT_SCALE_TIERS', None)
    if not tiers:
        return _DEFAULT_TIERS
    return tuple((int(a), int(b)) for a, b in tiers)


def _log(message):
    try:
        line = '%s %s\n' % (time.strftime('%Y-%m-%d %H:%M:%S'), message)
        log_dir = os.path.dirname(_LOG_PATH)
        if log_dir and not os.path.isdir(log_dir):
            os.makedirs(log_dir)
        with open(_LOG_PATH, 'a') as handle:
            handle.write(line)
    except Exception:
        pass


def _load_json(path):
    if not os.path.isfile(path):
        return {'maps': {}}
    try:
        with open(path, 'r') as handle:
            data = json.load(handle)
        if 'maps' not in data:
            data['maps'] = {}
        return data
    except Exception as exc:
        _log('load_json fail %s: %s' % (path, exc))
        return {'maps': {}}


def _save_json(path, data):
    try:
        tmp = path + '.tmp'
        with open(tmp, 'w') as handle:
            json.dump(data, handle, indent=2, sort_keys=True)
            handle.write('\n')
        try:
            os.replace(tmp, path)
        except AttributeError:
            # Python 2.7
            if os.path.isfile(path):
                os.remove(path)
            os.rename(tmp, path)
    except Exception as exc:
        _log('save_json fail %s: %s' % (path, exc))


def _count_humans():
    count = 0
    try:
        for player in bf2.playerManager.getPlayers():
            if player.isAIPlayer():
                continue
            if not player.isValid():
                continue
            count += 1
    except Exception:
        pass
    return count


def _bots_per_team():
    t1 = t2 = 0
    try:
        for player in bf2.playerManager.getPlayers():
            if not player.isAIPlayer() or not player.isValid():
                continue
            if player.getTeam() == 1:
                t1 += 1
            elif player.getTeam() == 2:
                t2 += 1
    except Exception:
        pass
    return t1, t2


def _list_ai_players(team=None):
    players = []
    try:
        for player in bf2.playerManager.getPlayers():
            if not player.isAIPlayer() or not player.isValid():
                continue
            if team is not None and player.getTeam() != team:
                continue
            if not player.isAlive():
                continue
            players.append(player)
    except Exception:
        pass
    players.sort(key=lambda p: p.index)
    return players


def _physics_root(veh):
    """Objeto con fisica dinamico (root del vehiculo/soldado si aplica)."""
    if veh is None:
        return None
    if rvehicles is not None:
        try:
            return rvehicles.getRoot(veh)
        except Exception:
            pass
    return veh


def _zero_velocity(veh):
    """
    Pone velocidad lineal y angular en 0.
    Usa realitymemory.setVelocity / setAngularVelocity (API interna PR).
    """
    if rmemory is None or veh is None:
        return False
    try:
        target = _physics_root(veh)
        if target is None:
            return False
        # Solo si el objeto tiene fisica dinamica (soldados/vehiculos).
        if hasattr(rmemory, 'getObjectHasDynamicPhysics'):
            if not rmemory.getObjectHasDynamicPhysics(target):
                return False
        rmemory.setVelocity(target, (0.0, 0.0, 0.0))
        if hasattr(rmemory, 'setAngularVelocity'):
            rmemory.setAngularVelocity(target, (0.0, 0.0, 0.0))
        return True
    except Exception:
        return False


def _teleport_player(player, pos):
    """Teletransporta y anula velocidad para que no 'salgan volando'."""
    if player is None or pos is None:
        return False
    try:
        veh = player.getVehicle()
        if veh is None:
            return False
        # Antes: cortar caida/impulso residual.
        _zero_velocity(veh)
        veh.setPosition((float(pos[0]), float(pos[1]), float(pos[2])))
        # Despues: por si el motor aplica gravedad en el mismo tick.
        _zero_velocity(veh)
        return True
    except Exception:
        return False


def _player_far_from(pos, player, max_dist):
    try:
        veh = player.getVehicle()
        if veh is None:
            return True
        dist = rcore.getVectorDistance(veh.getPosition(), pos)
        return dist > float(max_dist)
    except Exception:
        return True


def _detect_main_base_cp(team):
    """Main base del equipo: flag home (Top) con menor sgid."""
    try:
        cps = rcore.getControlPoints(team)
    except Exception:
        cps = []
    if not cps:
        return None
    tops = []
    for cp in cps:
        if getattr(cp, 'flagPosition', None) == CONSTANTS.Top:
            tops.append(cp)
    pool = tops if tops else list(cps)
    return min(pool, key=lambda cp: getattr(cp, 'sgid', 999))


def _auto_team_positions():
    """Detecta hold/release desde control points de main base."""
    hold_dist = float(_cfg('BOT_SCALE_HOLD_DISTANCE', -80.0))
    release_dist = float(_cfg('BOT_SCALE_RELEASE_DISTANCE', 10.0))
    # Y absoluta en el cielo (no offset relativo): evita enterrar y salir volando.
    abs_y = float(_cfg('BOT_SCALE_HOLD_ABS_Y', 5000.0))
    result = {}
    for team in (1, 2):
        cp = _detect_main_base_cp(team)
        if cp is None:
            continue
        try:
            hold = rcore.getPositionFromObject(cp, hold_dist)
            release = rcore.getPositionFromObject(cp, release_dist)
            hold = (hold[0], abs_y, hold[2])
            result[team] = {'hold': hold, 'release': release}
        except Exception as exc:
            _log('auto team %s fail: %s' % (team, exc))
    return result


def _cache_auto_positions(auto_positions):
    """Persiste auto-detect en cache para camino 2 (tabla por mapa)."""
    if not _map_key or not _layer_key:
        return
    cache = _load_json(_CACHE_JSON)
    maps = cache.setdefault('maps', {})
    layer_map = maps.setdefault(_map_key, {})
    layer_entry = layer_map.setdefault(_layer_key, {})
    changed = False
    for team, pos in auto_positions.items():
        team_key = str(int(team))
        current = layer_entry.get(team_key, {})
        if normalize_coords(current.get('hold')) and normalize_coords(current.get('release')):
            continue
        layer_entry[team_key] = {
            'hold': list(pos['hold']),
            'release': list(pos['release']),
            'source': 'auto',
            'updated': time.strftime('%Y-%m-%dT%H:%M:%SZ', time.gmtime()),
        }
        changed = True
    if changed:
        _save_json(_CACHE_JSON, cache)
        _log('cache updated map=%s layer=%s teams=%s' % (_map_key, _layer_key, sorted(auto_positions.keys())))


def _load_round_positions():
    global _team_positions, _map_key, _layer_key
    _team_positions = {}
    try:
        map_id = rcore.getMapName()
        layer = rcore.getMapLayer()
    except Exception:
        return False
    _map_key = str(map_id).lower()
    _layer_key = str(int(layer))
    auto = _auto_team_positions()
    maps_data = _load_json(_MAPS_JSON)
    cache_data = _load_json(_CACHE_JSON)
    missing_auto = False
    for team in (1, 2):
        resolved = resolve_team_positions(maps_data, cache_data, _map_key, layer, team, auto)
        if resolved:
            _team_positions[team] = resolved
        elif team in auto:
            missing_auto = True
    if missing_auto and auto:
        _cache_auto_positions(auto)
        for team in (1, 2):
            if team in _team_positions:
                continue
            resolved = resolve_team_positions(
                maps_data, _load_json(_CACHE_JSON), _map_key, layer, team, auto,
            )
            if resolved:
                _team_positions[team] = resolved
    ok = len(_team_positions) > 0
    if ok:
        _log(
            'round positions map=%s layer=%s teams=%s humans=%d active=%d' % (
                _map_key,
                _layer_key,
                ','.join(str(t) for t in sorted(_team_positions.keys())),
                _count_humans(),
                tier_active_bots(_count_humans(), _tiers()),
            )
        )
    else:
        _log('round positions FAILED map=%s layer=%s' % (_map_key, _layer_key))
    return ok


def _team_limits():
    humans = _count_humans()
    total_active = tier_active_bots(humans, _tiers())
    t1, t2 = _bots_per_team()
    return split_team_limits(total_active, t1, t2)


def _hold_pos(team):
    entry = _team_positions.get(int(team))
    if not entry:
        return None
    pos = entry.get('hold')
    if pos is None:
        return None
    # Siempre forzar altura de jaula (cielo). Ignora Y vieja del cache.
    abs_y = float(_cfg('BOT_SCALE_HOLD_ABS_Y', 5000.0))
    return (float(pos[0]), abs_y, float(pos[2]))


def _release_pos(team):
    entry = _team_positions.get(int(team))
    if not entry:
        return None
    return entry.get('release')


def _hold_spacing():
    return float(_cfg('BOT_SCALE_HOLD_SPACING', 6.0))


def _hold_cols():
    return int(_cfg('BOT_SCALE_HOLD_COLS', 8))


def _release_spacing():
    return float(_cfg('BOT_SCALE_RELEASE_SPACING', 4.0))


def _release_cols():
    return int(_cfg('BOT_SCALE_RELEASE_COLS', 6))


def _slot_hold_pos(team, slot):
    """Posicion hold con espaciado de grilla para un bot."""
    return apply_slot_offset(
        _hold_pos(team), slot, _hold_spacing(), _hold_cols(),
    )


def _slot_release_pos(team, slot):
    """Posicion release con espaciado de grilla para un bot."""
    return apply_slot_offset(
        _release_pos(team), slot, _release_spacing(), _release_cols(),
    )


def _apply_hold(player, slot=0):
    pos = _slot_hold_pos(player.getTeam(), slot)
    if pos is None:
        return False
    _held_indices.add(player.index)
    return _teleport_player(player, pos)


def _apply_release(player, slot=0):
    """
    Suelta un bot retenido: teletransporta cerca del spawn/release.
    No usar killPlayer en bots: el motor responde "Do not mess with bots input".
    """
    _held_indices.discard(player.index)
    # Velocidad a 0 + teleport a release (en suelo, no desde Y=5000).
    pos = _slot_release_pos(player.getTeam(), slot)
    if pos is None:
        return False
    return _teleport_player(player, pos)


def _reconcile_team(team, team_limit):
    """Mantiene solo team_limit bots activos; el resto va a hold espaciado."""
    if team not in _team_positions:
        return
    alive = _list_ai_players(team)
    if not alive:
        return
    limit = max(0, int(team_limit))
    # Indices que deben quedar activos (los primeros N no retenidos).
    active_keep = set()
    for player in alive:
        if len(active_keep) >= limit:
            break
        if player.index not in _held_indices:
            active_keep.add(player.index)
    # Si faltan activos, liberar retenidos (espaciados al release).
    release_slot = 0
    if len(active_keep) < limit:
        for player in alive:
            if len(active_keep) >= limit:
                break
            if player.index in _held_indices:
                if _apply_release(player, release_slot):
                    active_keep.add(player.index)
                    release_slot += 1
    # Retener sobrantes en grilla (slot estable por orden de index).
    hold_list = [p for p in alive if p.index not in active_keep]
    for slot, player in enumerate(hold_list):
        _apply_hold(player, slot)


def reconcile_all(_timer_data=None):
    """Recalcula hold/release para todos los equipos con posiciones cargadas."""
    try:
        if not _enabled() or not _round_ready:
            return
        limits = _team_limits()
        _reconcile_team(1, limits[0])
        _reconcile_team(2, limits[1])
    except Exception as exc:
        _log('reconcile_all error: %s' % exc)


def _enforce_held_positions(_timer_data=None):
    """
    Re-teletransporta SIEMPRE a los bots retenidos a su casilla en el cielo.
    Sin esto caen por gravedad desde Y=5000.
    """
    if not _enabled() or not _round_ready:
        return
    for team in (1, 2):
        held = [
            p for p in _list_ai_players(team)
            if p.index in _held_indices
        ]
        for slot, player in enumerate(held):
            target = _slot_hold_pos(team, slot)
            if target is None:
                continue
            _teleport_player(player, target)


def _on_enforce_tick(_timer_data=None):
    _enforce_held_positions(_timer_data)
    reconcile_all(_timer_data)


def _on_player_spawn(player, soldier):
    if not _enabled() or not _round_ready:
        return
    if player is None or not player.isAIPlayer():
        reconcile_all()
        return
    # Pequeno delay para que el soldado/vehiculo exista antes del teleport.
    try:
        rtimer.fireOnce(_delayed_bot_spawn, 0.75, player.index)
    except Exception:
        reconcile_all()


def _delayed_bot_spawn(player_index):
    try:
        player = bf2.playerManager.getPlayerByIndex(player_index)
    except Exception:
        player = None
    if player is None or not player.isAIPlayer() or not player.isValid():
        return
    reconcile_all()


def _on_player_connect(player):
    if not _enabled() or player is None or player.isAIPlayer():
        return
    try:
        rtimer.fireOnce(reconcile_all, 2.0, '')
    except Exception:
        reconcile_all()


def _on_player_disconnect(player):
    if not _enabled():
        return
    try:
        rtimer.fireOnce(reconcile_all, 2.0, '')
    except Exception:
        reconcile_all()


def _on_round_start(_unused=None):
    global _round_ready, _held_indices
    _held_indices = set()
    _round_ready = False
    if not _enabled():
        return
    try:
        delay = float(_cfg('BOT_SCALE_SETUP_DELAY', 6.0))
        rtimer.fireOnce(_setup_round, delay, '')
    except Exception:
        _setup_round()


def _setup_round(_timer_data=None):
    global _round_ready
    try:
        if not _enabled():
            return
        if not _load_round_positions():
            _round_ready = False
            _log('setup aborted: no positions')
            return
        _round_ready = True
        interval = float(_cfg('BOT_SCALE_ENFORCE_INTERVAL', 8.0))
        try:
            rtimer.repeatingTask(_on_enforce_tick, interval)
        except Exception:
            pass
        reconcile_all('')
        _log('setup OK active_limit=%d' % tier_active_bots(_count_humans(), _tiers()))
    except Exception as exc:
        _round_ready = False
        _log('setup_round error: %s' % exc)


def _on_round_end(winner=None):
    global _round_ready, _held_indices
    _round_ready = False
    _held_indices = set()


def init():
    """Registra handlers solo en servidor coop srv3."""
    if not _IN_GAME or not _enabled():
        return
    host.registerHandler('RoundStart', _on_round_start, 1)
    host.registerHandler('RoundEnd', _on_round_end, 1)
    host.registerHandler('PlayerSpawn', _on_player_spawn, 1)
    host.registerHandler('PlayerConnect', _on_player_connect, 1)
    host.registerHandler('PlayerDisconnect', _on_player_disconnect, 1)
    _log('init OK')


if _IN_GAME:
    init()
