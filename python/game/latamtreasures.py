# -*- coding: utf-8 -*-
# latamtreasures.py - tesoros con acertijos (LATAMSQUAD)
#
# Archivo: C:/prbf2_db/latamtreasures.cfg (fallback .txt)
# Formato: map|mode|layer|x|y|z|spawnable|riddle
#   mode  = gpm_cq / gpm_insurgency / … (como en maplist / .desc del level)
#   layer = Inf / Alt / Std / Lrg (16/32/64/128; delimita DOD/área jugable)
# Anotaciones/ejemplos: ver el .cfg/.txt en C:/prbf2_db/
# Ejemplo:
#   kashan_desert|gpm_cq|Std|120.5|28.0|-340.2|1|Cerca del puente oxidado al norte
# !tesoro → pista privada. Hallazgo: proximidad al objeto (SupplyObject).
# Objeto actual: light_supply_crate - SupplyObject, armor 500 HP (light_supply_crate_armor.tweak).
# No depende de disparos: VehicleDestroyed suele no llegar / no alcanza para claim.
# Descartados: target_pr (crash), spectator_camera* (blip),
#   insrg_watercontainer_ied (crash), ammobag / ammocache / medikit (pruebas previas).
# Tras claim: teletransporte a Y=9000 (no deleteObject).
# NO llamar setDamage al spawn: en varios templates crashea el motor.
# Sin getObjectsOfTemplate.

import math

TREASURES_FILE_PATH = 'C:/prbf2_db/latamtreasures.cfg'
# Fallbacks: algunos entornos PR bloquean o fallan al leer .txt
TREASURES_FILE_CANDIDATES = (
    'C:/prbf2_db/latamtreasures.cfg',
    'C:\\prbf2_db\\latamtreasures.cfg',
    'C:/prbf2_db/latamtreasures.txt',
    'C:\\prbf2_db\\latamtreasures.txt',
)
# Caja light de suministro (SupplyObject; HP de armor = 500)
TREASURE_TEMPLATE = 'light_supply_crate'
# Soften desactivado: setDamage post-spawn crasheaba con varios templates.
TREASURE_SOFTEN_ENABLED = False
TREASURE_SPAWN_HP = 10.0
TREASURE_XP_BONUS = 5000
# Radio para validar VehicleDestroyed (fallback)
TREASURE_DESTROY_DISTANCE = 15.0
# Reclamo por acercarse (2 m: hay que llegar casi encima de la caja)
TREASURE_CLAIM_DISTANCE = 2.0
TREASURE_PROXIMITY_INTERVAL = 0.5
# Tras encontrar: subir el objeto al cielo para que desaparezca del suelo
TREASURE_DISPOSE_Y = 9000.0
# Mismo ID que realityadmin.adminPMBig / votaciones
SOUND_ID_PROMOTE = 1

MSG_ALREADY_FOUND = 'El tesoro de este mapa/modo/layer ya fue encontrado'
MSG_NOT_CONFIGURED = 'Este mapa/modo/layer no tiene tesoro configurado'
# Ayuda visual: acercarse a la caja (no hace falta destruirla)
MSG_OBJECT_HINT = 'Busca una caja de suministro.'


def tesoro_reply(entry, map_has_any_entry):
    """Texto de respuesta para !tesoro."""
    if entry is None or not map_has_any_entry:
        return MSG_NOT_CONFIGURED
    if int(entry.get('spawnable') or 0) != 1:
        return MSG_ALREADY_FOUND
    riddle = str(entry.get('riddle') or '')
    # Pista + qué objeto buscar (el acertijo va primero)
    if riddle:
        return '%s | %s' % (riddle, MSG_OBJECT_HINT)
    return MSG_OBJECT_HINT

# Estado en memoria (ronda actual)
_pending_treasures = {}  # player_id -> int
_active = None  # dict entry + runtime flags
_claimed = False
_treasure_vehicle = None  # referencia al objeto spawneado (para borrar al reclamar)
_proximity_task = None
# Claves "map|mode|layer" marcadas encontradas si falla la escritura a disco
_force_found_keys = set()

try:
    from latamstats import strip_chat_hud_prefix
except ImportError:
    def strip_chat_hud_prefix(msg_text):
        """Fallback si latamstats no expone el helper."""
        if msg_text is None:
            return ''
        text = str(msg_text).strip()
        for prefix in (
            'HUD_TEXT_CHAT_TEAM',
            'HUD_TEXT_CHAT_SQUAD',
            'HUD_TEXT_CHAT_DEADPREFIX',
            'HUD_CHAT_DEADPREFIX',
            '* ',
        ):
            if text.startswith(prefix):
                text = text[len(prefix):].lstrip()
        return text

# Imports del motor PR: protegidos para smoke/CI sin bf2
try:
    import bf2
    import host
    import realityserver
    import realitycore as rcore
    import realitydebug as rdebug
    import realityadmin as radmin
    import realitytimer as rtimer
    _IN_GAME = True
except ImportError:
    bf2 = None
    host = None
    realityserver = None
    rcore = None
    rdebug = None
    radmin = None
    rtimer = None
    _IN_GAME = False

# Exception amplio: realityspawner.py es Py2 (print sin paréntesis) y en smoke Py3
# puede lanzar SyntaxError en lugar de ImportError.
try:
    import realityspawner as rspawner
except Exception:
    rspawner = None


def normalize_mode(mode):
    """Normaliza a token gpm_* en minúsculas (acepta cq o gpm_cq)."""
    text = str(mode or '').strip().lower()
    if not text:
        return ''
    if text.startswith('gpm_'):
        return text
    return 'gpm_' + text


def normalize_layer(layer):
    """Layer abreviado case-insensitive (Inf/Alt/Std/Lrg)."""
    return str(layer or '').strip().lower()


def entry_key(entry_or_map, mode=None, layer=None):
    """Clave estable map|mode|layer para force-found y mark en disco."""
    if isinstance(entry_or_map, dict):
        map_name = entry_or_map.get('map')
        mode = entry_or_map.get('mode')
        layer = entry_or_map.get('layer')
    else:
        map_name = entry_or_map
    return '%s|%s|%s' % (
        str(map_name or ''),
        normalize_mode(mode),
        normalize_layer(layer),
    )


def parse_treasures_file(text):
    """Parsea el archivo; ignora vacíos y comentarios #."""
    entries = []
    if text is None:
        return entries
    # Py2: no usar str() sobre unicode (falla con BOM/acentos si defaultencoding=ascii)
    if not isinstance(text, type(u'')):
        try:
            text = text.decode('utf-8')
        except Exception:
            try:
                text = text.decode('latin-1')
            except Exception:
                text = u''
    # Quitar BOM UTF-8 si vino en el archivo
    if text and text[0] == u'\ufeff':
        text = text[1:]
    for line_index, raw in enumerate(text.splitlines()):
        line = raw.strip()
        if not line or line.startswith(u'#') or line.startswith('#'):
            continue
        # map|mode|layer|x|y|z|spawnable|riddle  (riddle puede tener |)
        parts = line.split(u'|', 7) if isinstance(line, type(u'')) else line.split('|', 7)
        if len(parts) < 8:
            continue
        map_name = parts[0].strip()
        mode = normalize_mode(parts[1])
        layer = parts[2].strip()  # conservar capitalización de archivo
        try:
            x = float(parts[3].strip())
            y = float(parts[4].strip())
            z = float(parts[5].strip())
            spawnable = 1 if _to_native_str(parts[6].strip()) == '1' else 0
        except (TypeError, ValueError):
            continue
        riddle = parts[7].strip()
        map_name = _to_native_str(map_name)
        mode = _to_native_str(mode)
        layer = _to_native_str(layer)
        riddle = _to_native_str(riddle)
        if not map_name or not mode or not layer:
            continue
        entries.append({
            'map': map_name,
            'mode': mode,
            'layer': layer,
            'x': x, 'y': y, 'z': z,
            'spawnable': spawnable,
            'riddle': riddle,
            'line_index': line_index,
        })
    return entries


def _to_native_str(value):
    """Convierte unicode → str utf-8 en Py2; deja str en Py3."""
    if value is None:
        return ''
    try:
        # Py2: unicode es el tipo texto
        if isinstance(value, unicode):  # noqa: F821 - solo existe en Py2
            return value.encode('utf-8')
    except NameError:
        pass
    return str(value)


def find_round_entry(entries, map_name, mode, layer):
    """Primera entrada que coincide con mapa + modo + layer de la ronda."""
    name = str(map_name or '').strip().lower()
    mode_n = normalize_mode(mode)
    layer_n = normalize_layer(layer)
    for e in entries or []:
        if str(e.get('map') or '').strip().lower() != name:
            continue
        if mode_n and normalize_mode(e.get('mode')) != mode_n:
            continue
        if layer_n and normalize_layer(e.get('layer')) != layer_n:
            continue
        return e
    return None


def find_entries_for_map(entries, map_name):
    """Todas las entradas del mapa (case-insensitive), para diagnóstico."""
    name = str(map_name or '').strip().lower()
    out = []
    for e in entries or []:
        if str(e.get('map') or '').strip().lower() == name:
            out.append(e)
    return out


def debug_log(msg):
    """Append de diagnóstico a C:/prbf2_db/latamtreasures_debug.log."""
    line = '%s %s\n' % (
        __import__('time').strftime('%Y-%m-%d %H:%M:%S'),
        str(msg),
    )
    try:
        handle = open('C:/prbf2_db/latamtreasures_debug.log', 'ab')
        try:
            handle.write(line.encode('utf-8'))
        finally:
            handle.close()
    except Exception:
        pass
    if _IN_GAME and rdebug:
        try:
            rdebug.debugMessage('latamtreasures: %s' % msg, 'latamtreasures')
        except Exception:
            pass


# Última ruta que se pudo leer (para reescribir spawnable=0 en el mismo archivo)
_last_loaded_path = None


def load_entries_from_disk(path=None):
    """Lee el archivo de tesoros; retorna (entries, raw_text) o ([], None)."""
    global _last_loaded_path
    candidates = []
    if path:
        candidates.append(path)
    candidates.extend(TREASURES_FILE_CANDIDATES)
    # Quitar duplicados preservando orden
    seen = set()
    unique = []
    for cand in candidates:
        key = str(cand).replace('\\', '/').lower()
        if key in seen:
            continue
        seen.add(key)
        unique.append(cand)

    last_err = None
    for p in unique:
        try:
            # Evitar 'with' por compatibilidad con Python embebido de PR
            handle = open(p, 'rb')
            try:
                raw = handle.read()
            finally:
                handle.close()
        except Exception as exc:
            last_err = '%s: %s' % (p, exc)
            continue
        try:
            text = raw.decode('utf-8')
        except Exception:
            try:
                text = raw.decode('latin-1')
            except Exception as exc:
                last_err = 'decode %s: %s' % (p, exc)
                continue
        # Quitar BOM UTF-8 (Notepad / PowerShell Set-Content -Encoding UTF8)
        if text.startswith(u'\ufeff'):
            text = text[1:]
        elif isinstance(text, type('')) and text.startswith('\xef\xbb\xbf'):
            text = text[3:]
        try:
            entries = parse_treasures_file(text)
        except Exception as exc:
            # Archivo leído pero parse falló: no reportar como MISSING
            debug_log('parse error %s: %s' % (p, exc))
            _last_loaded_path = p
            return [], text
        _last_loaded_path = p
        debug_log('load ok path=%s bytes=%s entries=%s' % (p, len(raw), len(entries)))
        return entries, text

    _last_loaded_path = None
    if last_err:
        debug_log('load FAIL %s' % last_err)
    else:
        debug_log('load FAIL no candidates')
    return [], None


def write_file_text(path, text):
    """Escribe texto UTF-8 al path indicado (sin 'with' por compat PR)."""
    if text is None:
        data = ''
    else:
        try:
            # unicode (Py2) o str (Py3) → bytes utf-8
            data = text.encode('utf-8')
        except AttributeError:
            # Ya es bytes / buffer
            data = text
        except UnicodeDecodeError:
            # Py2: str ya es utf-8 (bytes); no re-encodear
            data = text
    handle = open(path, 'wb')
    try:
        handle.write(data)
    finally:
        handle.close()


def mark_map_found_on_disk(map_name, path=None, mode=None, layer=None):
    """Marca spawnable=0 en disco para map(+mode+layer); True si hubo cambio."""
    p = path or _last_loaded_path or TREASURES_FILE_PATH
    try:
        entries, text = load_entries_from_disk(p)
        if text is None:
            return False
        # Preferir la ruta que realmente se leyó
        p = _last_loaded_path or p
        new_text, changed = mark_spawnable_zero(text, map_name, mode=mode, layer=layer)
        if not changed:
            return False
        write_file_text(p, new_text)
        return True
    except Exception as exc:
        try:
            debug_log('mark_map_found_on_disk fail: %s' % exc)
        except Exception:
            pass
        return False


# Alias legacy para callers/tests antiguos
def find_map_entry(entries, map_name, mode=None, layer=None):
    """Compat: sin mode/layer busca solo por mapa (primera coincidencia)."""
    if mode is None and layer is None:
        name = str(map_name or '')
        for e in entries or []:
            if e.get('map') == name:
                return e
        return None
    return find_round_entry(entries, map_name, mode, layer)


def mark_spawnable_zero(file_text, map_name, mode=None, layer=None):
    """
    Reescribe a spawnable=0 la primera línea que coincida.
    Con mode+layer: match exacto de ronda. Sin ellos: primera del mapa (legacy).
    """
    # Evitar str(unicode) en Py2 (ASCII default → UnicodeEncodeError con - / acentos)
    name = _to_native_str(map_name or '')
    mode_n = normalize_mode(mode) if mode is not None else None
    layer_n = normalize_layer(layer) if layer is not None else None
    text = _to_native_str(file_text or '')
    lines = text.splitlines(True)
    changed = False
    out = []
    for raw in lines:
        stripped = raw.strip()
        if changed or not stripped or stripped.startswith('#'):
            out.append(raw)
            continue
        parts = stripped.split('|', 7)
        if len(parts) < 8:
            out.append(raw)
            continue
        if _to_native_str(parts[0]).strip() != name:
            out.append(raw)
            continue
        if mode_n is not None and normalize_mode(parts[1]) != mode_n:
            out.append(raw)
            continue
        if layer_n is not None and normalize_layer(parts[2]) != layer_n:
            out.append(raw)
            continue
        parts[6] = '0'
        if raw.endswith('\r\n'):
            nl = '\r\n'
        elif raw.endswith('\n'):
            nl = '\n'
        else:
            nl = ''
        out.append('|'.join(parts) + nl)
        changed = True
    return (''.join(out), changed)


def compute_treasure_xp_bonus(treasures):
    """Bonus aditivo de XP por tesoros encontrados."""
    return int(treasures or 0) * int(TREASURE_XP_BONUS)


def get_pending_treasures():
    """Copia del dict player_id -> tesoros acreditados en la ronda."""
    return dict(_pending_treasures)


def clear_pending_treasures():
    """Vacía créditos pending (tests o reset manual)."""
    _pending_treasures.clear()


def take_pending_treasures():
    """Devuelve pending y lo limpia (EndGame / latamstats flush)."""
    out = dict(_pending_treasures)
    _pending_treasures.clear()
    return out


def credit_pending(player_id, amount=1):
    """Suma crédito en memoria (EndGame lo persiste vía latamstats)."""
    if not player_id:
        return
    pid = str(player_id)
    _pending_treasures[pid] = int(_pending_treasures.get(pid, 0)) + int(amount)


def get_current_round_ids():
    """(map_name, mode gpm_*, layer abbr) de la ronda actual, o ('','','')."""
    map_name = ''
    mode = ''
    layer = ''
    if not _IN_GAME or rcore is None:
        return (map_name, mode, layer)
    try:
        map_name = str(rcore.getMapName() or '')
    except Exception:
        map_name = ''
    if not map_name and host is not None:
        try:
            map_name = str(host.sgl_getMapName() or '').strip()
        except Exception:
            pass
    try:
        # Preferir token crudo del motor (gpm_cq); fallback a getGameMode()
        raw = ''
        if bf2 is not None and hasattr(bf2, 'serverSettings'):
            raw = str(bf2.serverSettings.getGameMode() or '')
        mode = normalize_mode(raw)
        if not mode:
            mode = normalize_mode(rcore.getGameMode())
    except Exception:
        mode = ''
    try:
        layer = str(rcore.getMapLayerNameAbbr() or '')
        # Si abbr falla, mapear el int de layer (16/32/64/128)
        if not layer:
            layer_num = int(rcore.getMapLayer() or 0)
            layer = {
                16: 'Inf',
                32: 'Alt',
                64: 'Std',
                128: 'Lrg',
            }.get(layer_num, '')
    except Exception:
        layer = ''
    return (map_name, mode, layer)


def format_round_key(map_name, mode, layer):
    """Texto corto map|mode|layer para mensajes de diagnóstico."""
    return '%s|%s|%s' % (
        str(map_name or '?'),
        str(mode or '?'),
        str(layer or '?'),
    )


def _horizontal_distance(ax, az, bx, bz):
    """Distancia horizontal en el plano XZ (ignora altura)."""
    dx = float(bx) - float(ax)
    dz = float(bz) - float(az)
    return math.sqrt(dx * dx + dz * dz)


def _vehicle_near_active(vehicle, active_entry):
    """True si el vehículo destruido está cerca del tesoro activo."""
    if vehicle is None or active_entry is None:
        return False
    try:
        pos = vehicle.getPosition()
        vx, vy, vz = float(pos[0]), float(pos[1]), float(pos[2])
    except Exception:
        return False
    ax = active_entry.get('x', 0.0)
    az = active_entry.get('z', 0.0)
    return _horizontal_distance(ax, az, vx, vz) <= TREASURE_DESTROY_DISTANCE


def is_tesoro_command(msg_text):
    """True si el mensaje es exactamente !tesoro (sin argumentos)."""
    text = strip_chat_hud_prefix(msg_text)
    if not text.startswith('!'):
        return False
    parts = text[1:].split()
    return len(parts) == 1 and parts[0].lower() == 'tesoro'


def spawn_treasure_for_map(map_name, entry):
    """Spawnea TREASURE_TEMPLATE en coords del cfg; retorna True/False."""
    if rspawner is None or entry is None:
        return False
    # teamonvehicle=0: evita iconos de vehículo de equipo en minimapa
    props = {
        'template': TREASURE_TEMPLATE,
        'position': (entry['x'], entry['y'], entry['z']),
        'rotation': (0.0, 0.0, 0.0),
        'minspawndelay': 0,
        'maxspawndelay': 0,
        'spawndelayatstart': 0,
        'team': 1,
        'teamonvehicle': 0,
    }
    try:
        return bool(rspawner.createSpawner(
            'latam_treasure', props, delete=False, reset=True, sufix=True,
        ))
    except Exception:
        return False


def is_treasure_template(template_name):
    """True si el template es el del tesoro configurado."""
    try:
        tname = str(template_name or '').lower()
    except Exception:
        return False
    want = TREASURE_TEMPLATE.lower()
    return tname == want or tname.startswith(want)


def _find_treasure_object_near_active():
    """
    Busca el light_supply_crate cerca del punto del cfg.
    SupplyObject no dispara VehicleSpawned, así que a veces no hay ref previa.
    """
    if _active is None or rcore is None:
        return None
    ax = float(_active.get('x', 0.0))
    ay = float(_active.get('y', 0.0))
    az = float(_active.get('z', 0.0))
    limit = float(TREASURE_DESTROY_DISTANCE)
    limit_sq = limit * limit
    try:
        objs = list(rcore.getObjectsOfTemplate(TREASURE_TEMPLATE) or [])
    except Exception as exc:
        try:
            debug_log('find treasure getObjects fail: %s' % exc)
        except Exception:
            pass
        return None
    best = None
    best_d = None
    for obj in objs:
        try:
            if obj is None:
                continue
            tname = str(obj.templateName or '').lower()
            if not is_treasure_template(tname):
                continue
            pos = obj.getPosition()
            dx = float(pos[0]) - ax
            dy = float(pos[1]) - ay
            dz = float(pos[2]) - az
            d2 = dx * dx + dy * dy + dz * dz
            if d2 > limit_sq:
                continue
            if best_d is None or d2 < best_d:
                best = obj
                best_d = d2
        except Exception:
            continue
    if best is not None:
        try:
            debug_log('find treasure ok dist=%.2f' % (best_d ** 0.5))
        except Exception:
            pass
    return best


def _try_track_treasure_object(data=None):
    """Intenta guardar referencia al objeto spawneado (post-delay)."""
    global _treasure_vehicle
    if _claimed or _active is None:
        return
    if _treasure_vehicle is not None:
        return
    obj = _find_treasure_object_near_active()
    if obj is None:
        try:
            debug_log('track treasure: object not found yet')
        except Exception:
            pass
        return
    _treasure_vehicle = obj
    try:
        pos = obj.getPosition()
        debug_log(
            'treasure vehicle tracked (scan) template=%s pos=%.2f/%.2f/%.2f'
            % (obj.templateName, float(pos[0]), float(pos[1]), float(pos[2]))
        )
    except Exception:
        try:
            debug_log('treasure vehicle tracked (scan)')
        except Exception:
            pass


def _schedule_track_treasure():
    """Agenda 1-2 intentos de track tras el spawn (SupplyObject tarda en existir)."""
    if rtimer is None:
        _try_track_treasure_object()
        return
    try:
        rtimer.fireOnce(_try_track_treasure_object, 1.0)
        rtimer.fireOnce(_try_track_treasure_object, 3.0)
    except Exception:
        _try_track_treasure_object()


def claim_treasure_for_finder(finder_player):
    """
    Marca tesoro encontrado, crédito pending y anuncio.
    finder_player: Player cercano (proximidad) o atacante (Destroyed fallback).
    Retorna True si se acreditó en esta llamada.
    """
    global _claimed, _active
    if _claimed or _active is None:
        return False
    _claimed = True

    map_name = _active.get('map')
    mode = _active.get('mode')
    layer = _active.get('layer')
    key = entry_key(_active)

    disk_ok = False
    try:
        disk_ok = mark_map_found_on_disk(map_name, mode=mode, layer=layer)
    except Exception as exc:
        try:
            debug_log('mark disk exception: %s' % exc)
        except Exception:
            pass
        disk_ok = False
    if not disk_ok:
        _force_found_keys.add(key)

    name = 'Alguien'
    player_hash = None
    if finder_player is not None:
        try:
            name = str(finder_player.getName() or '').strip() or 'Alguien'
        except Exception:
            name = 'Alguien'
        try:
            player_hash = realityserver.getPlayerHash(finder_player)
        except Exception:
            player_hash = None
    if player_hash:
        credit_pending(player_hash, 1)
    try:
        debug_log('claim name=%s hash=%s' % (name, player_hash))
        announce_treasure_found(name)
    except Exception as exc:
        try:
            debug_log('announce fail: %s' % exc)
        except Exception:
            pass

    _active['spawnable'] = 0
    # Quitar la caja del suelo: teletransporte al cielo
    _dispose_treasure_vehicle()
    _stop_proximity_watch()
    return True


def _dispose_treasure_vehicle(vehicle=None):
    """Tras encontrar: teletransporta el objeto a Y=9000 (fuera del mapa jugable)."""
    global _treasure_vehicle
    if vehicle is None:
        vehicle = _treasure_vehicle
    if vehicle is None:
        # SupplyObject: a menudo nunca llegó VehicleSpawned → buscar en el mapa
        vehicle = _find_treasure_object_near_active()
    if vehicle is None:
        try:
            debug_log('treasure dispose skip: no object ref')
        except Exception:
            pass
        _treasure_vehicle = None
        return

    try:
        pos = vehicle.getPosition()
        new_pos = (float(pos[0]), float(TREASURE_DISPOSE_Y), float(pos[2]))
    except Exception:
        if _active is not None:
            new_pos = (
                float(_active.get('x', 0.0)),
                float(TREASURE_DISPOSE_Y),
                float(_active.get('z', 0.0)),
            )
        else:
            try:
                debug_log('treasure dispose skip: no position')
            except Exception:
                pass
            _treasure_vehicle = None
            return

    moved = False
    # 1) API Python setPosition
    try:
        vehicle.setPosition(new_pos)
        moved = True
        debug_log('treasure dispose setPosition y=%s' % TREASURE_DISPOSE_Y)
    except Exception as exc:
        try:
            debug_log('treasure dispose setPosition fail: %s' % exc)
        except Exception:
            pass

    # 2) Fallback rcon Object.absolutePosition (más fiable en PR)
    if rcore is not None:
        try:
            oid = rcore.getObjectId(vehicle)
            if oid and rcore.editObject(oid, new_pos, None):
                moved = True
                debug_log(
                    'treasure dispose editObject id=%s y=%s'
                    % (oid, TREASURE_DISPOSE_Y)
                )
            elif not moved:
                debug_log('treasure dispose editObject fail id=%s' % oid)
        except Exception as exc:
            try:
                debug_log('treasure dispose editObject fail: %s' % exc)
            except Exception:
                pass

    if not moved:
        try:
            debug_log('treasure dispose FAILED both methods')
        except Exception:
            pass
    _treasure_vehicle = None


def _stop_proximity_watch():
    """Detiene el poll de proximidad si está activo."""
    global _proximity_task
    if _proximity_task is None:
        return
    try:
        _proximity_task.destroy()
    except Exception:
        pass
    _proximity_task = None


def _start_proximity_watch():
    """Arranca poll: jugador vivo cerca del punto → reclamar."""
    global _proximity_task
    _stop_proximity_watch()
    if rtimer is None or _active is None:
        return
    try:
        _proximity_task = rtimer.repeatingTask(
            _check_treasure_proximity, float(TREASURE_PROXIMITY_INTERVAL),
        )
        debug_log('proximity watch start dist=%s' % TREASURE_CLAIM_DISTANCE)
    except Exception as exc:
        try:
            debug_log('proximity watch fail: %s' % exc)
        except Exception:
            pass


def _claim_anchor_xz():
    """Punto XZ del tesoro: posición real del objeto si está trackeado, si no coords del cfg."""
    global _treasure_vehicle
    if _treasure_vehicle is not None:
        try:
            pos = _treasure_vehicle.getPosition()
            return float(pos[0]), float(pos[2]), 'vehicle'
        except Exception:
            # Objeto inválido: soltar referencia y caer al cfg
            _treasure_vehicle = None
    if _active is None:
        return None, None, 'none'
    return float(_active.get('x', 0.0)), float(_active.get('z', 0.0)), 'cfg'


def _check_treasure_proximity(data=None):
    """Cada tick: si un jugador vivo está cerca del tesoro → claim."""
    if _claimed or _active is None:
        _stop_proximity_watch()
        return
    if rcore is None:
        return
    ax, az, anchor = _claim_anchor_xz()
    if ax is None:
        return
    limit = float(TREASURE_CLAIM_DISTANCE)
    limit_sq = limit * limit
    try:
        players = list(rcore.getPlayers())
    except Exception:
        try:
            players = list(bf2.playerManager.getPlayers())
        except Exception:
            return

    nearest_sq = None
    nearest_name = None
    for player in players:
        try:
            if player is None or not player.isValid() or player.isAIPlayer():
                continue
            # PR usa isAlive()/killed - isDead() no existe y hacía skip de todos
            if getattr(player, 'killed', False):
                continue
            try:
                if not player.isAlive():
                    continue
            except Exception:
                pass
        except Exception:
            continue
        try:
            pos = player.getDefaultVehicle().getPosition()
            px, pz = float(pos[0]), float(pos[2])
        except Exception:
            continue
        dx = px - ax
        dz = pz - az
        dist_sq = dx * dx + dz * dz
        if nearest_sq is None or dist_sq < nearest_sq:
            nearest_sq = dist_sq
            try:
                nearest_name = str(player.getName() or '')
            except Exception:
                nearest_name = '?'
        if dist_sq > limit_sq:
            continue
        debug_log(
            'proximity claim player=%s dist=%.2f anchor=%s'
            % (nearest_name, dist_sq ** 0.5, anchor)
        )
        claim_treasure_for_finder(player)
        return

    # Diagnóstico: cada ~5 s loguear jugador más cercano (si hay)
    try:
        import time as _time
        now = _time.time()
        last = getattr(_check_treasure_proximity, '_last_dbg', 0.0)
        if nearest_sq is not None and (now - last) >= 5.0:
            _check_treasure_proximity._last_dbg = now
            debug_log(
                'proximity nearest=%.2fm name=%s anchor=%s limit=%s'
                % (nearest_sq ** 0.5, nearest_name, anchor, limit)
            )
    except Exception:
        pass


def on_vehicle_spawned(vehicle):
    """Guarda referencia al tesoro; opcionalmente baja HP (desactivado)."""
    global _treasure_vehicle
    if _active is None or _claimed or vehicle is None:
        return
    try:
        tname = vehicle.templateName
    except Exception:
        return
    if not is_treasure_template(tname):
        return
    # Solo el objeto cerca del punto del cfg (no otros del mapa)
    if not _vehicle_near_active(vehicle, _active):
        try:
            debug_log('treasure spawn ignored far template=%s' % tname)
        except Exception:
            pass
        return
    _treasure_vehicle = vehicle
    try:
        pos = vehicle.getPosition()
        debug_log(
            'treasure vehicle tracked template=%s pos=%.2f/%.2f/%.2f'
            % (tname, float(pos[0]), float(pos[1]), float(pos[2]))
        )
    except Exception:
        try:
            debug_log('treasure vehicle tracked template=%s' % tname)
        except Exception:
            pass
    if not TREASURE_SOFTEN_ENABLED:
        return
    try:
        vehicle.setDamage(float(TREASURE_SPAWN_HP))
        debug_log('treasure soften setDamage=%s template=%s' % (
            TREASURE_SPAWN_HP, tname,
        ))
    except Exception as exc:
        try:
            debug_log('treasure soften fail: %s' % exc)
        except Exception:
            pass


def _pm(player, msg):
    """Mensaje privado al jugador (mismo patrón que latamstats/latamlink)."""
    if player is None:
        return
    try:
        if not player.isValid() or player.isAIPlayer():
            return
    except Exception:
        return
    try:
        text = '\xc2\xa7C1001' + str(msg)
        if len(text) > 240:
            text = text[:239]
        host.sgl_sendTextMessage(player.index, 14, 1, text, 0)
    except Exception:
        pass


def resolve_finder_name(attacker):
    """
    Nombre del jugador que destruyó el tesoro.
    VehicleDestroyed a veces pasa el arma/objeto en vez del Player: hay que resolver el dueño.
    """
    if attacker is None:
        return 'Alguien'

    # 1) Player directo
    try:
        name = attacker.getName()
        if name is not None:
            name = str(name).strip()
            if name:
                return name
    except Exception:
        pass

    # 2) Attacker = arma → dueño (mismo patrón que realitycore.getWeaponOwner)
    if rcore is not None:
        try:
            owner = rcore.getWeaponOwner(attacker)
            if owner is not None:
                name = str(owner.getName() or '').strip()
                if name:
                    return name
        except Exception:
            pass
        try:
            occ = attacker.getOccupyingPlayers()
            if occ and len(occ) > 0 and occ[0] is not None:
                name = str(occ[0].getName() or '').strip()
                if name:
                    return name
        except Exception:
            pass

    # 3) Hash del attacker → nombre entre jugadores online
    if realityserver is not None and rcore is not None:
        try:
            ph = realityserver.getPlayerHash(attacker)
            if ph:
                for player in rcore.getPlayers():
                    try:
                        if realityserver.getPlayerHash(player) == ph:
                            name = str(player.getName() or '').strip()
                            if name:
                                return name
                    except Exception:
                        continue
        except Exception:
            pass

    return 'Alguien'


def resolve_finder_player(attacker):
    """Player object del hallazgo (para hash/crédito), o None."""
    if attacker is None:
        return None
    # ¿Ya es un player válido con getName?
    try:
        if hasattr(attacker, 'isValid') and attacker.isValid():
            name = str(attacker.getName() or '').strip()
            if name:
                return attacker
    except Exception:
        pass
    if rcore is not None:
        try:
            owner = rcore.getWeaponOwner(attacker)
            if owner is not None:
                return owner
        except Exception:
            pass
        try:
            occ = attacker.getOccupyingPlayers()
            if occ and len(occ) > 0:
                return occ[0]
        except Exception:
            pass
    return None


def announce_treasure_found(finder_name):
    """
    Anuncio a TODOS: chat grande coloreado + HUD (rhooks) + sonido promote.
    Mismo estilo visual/sonoro que adminPMBig / inicio de votación en realityadmin.
    """
    name = str(finder_name or '').strip() or 'Alguien'
    chat_msg = '%s ha encontrado el tesoro del mapa! Aumenta el multiplicador de XP!' % name
    # HUD admite salto de línea como los avisos admin
    hud_msg = '%s ha encontrado el tesoro del mapa!\r\nFelicitaciones!' % name

    # Chat global grande + color (preferir globalMessage de admin: conserva el nombre)
    if radmin is not None:
        try:
            radmin.globalMessage(chat_msg, big=True, color=True)
        except Exception:
            if rcore is not None:
                try:
                    rcore.sendMessageToAll(rcore.BIGCOLOREDTEXT + chat_msg)
                except Exception:
                    pass
    elif rcore is not None:
        try:
            rcore.sendMessageToAll(rcore.BIGCOLOREDTEXT + chat_msg)
        except Exception:
            try:
                host.rcon_invoke('game.sayall "%s"' % chat_msg)
            except Exception:
                pass
    elif host is not None:
        try:
            host.rcon_invoke('game.sayall "%s"' % chat_msg)
        except Exception:
            pass

    # HUD grande + sonido por jugador (patrón initializeVote / adminPMBig)
    players = []
    if rcore is not None:
        try:
            players = list(rcore.getPlayers())
        except Exception:
            players = []
    for player in players:
        try:
            if player is None or not player.isValid() or player.isAIPlayer():
                continue
        except Exception:
            continue
        if radmin is not None:
            try:
                radmin.sendRhooksAdminWarnEventWrapper(
                    player, hud_msg, history=False,
                )
            except Exception:
                pass
        if rcore is not None:
            try:
                rcore.playSoundForPlayer(player, SOUND_ID_PROMOTE)
            except Exception:
                pass


def _reset_round_state():
    """Limpia estado de ronda (no toca pending; lo consume latamstats)."""
    global _active, _claimed, _treasure_vehicle
    _stop_proximity_watch()
    _active = None
    _claimed = False
    _treasure_vehicle = None


def _prepare_active_for_round(map_name, mode, layer):
    """Recarga archivo y prepara _active para map+mode+layer; spawnea si aplica."""
    global _active, _claimed, _treasure_vehicle
    _stop_proximity_watch()
    _active = None
    _claimed = False
    _treasure_vehicle = None

    entries, _text = load_entries_from_disk()
    entry = find_round_entry(entries, map_name, mode, layer)
    if entry is None:
        return

    key = entry_key(entry)
    spawnable_count = sum(
        1 for e in entries
        if entry_key(e) == key and int(e.get('spawnable') or 0) == 1
    )
    if spawnable_count > 1 and _IN_GAME and rdebug:
        try:
            rdebug.debugMessage(
                'latamtreasures: %d entradas spawnable=1 para %s'
                % (spawnable_count, key),
                'latamtreasures',
            )
        except Exception:
            pass

    _active = dict(entry)
    # Si el disco falló al marcar encontrado, no respawnear en esta sesión
    if key in _force_found_keys:
        _active['spawnable'] = 0
    if int(_active.get('spawnable') or 0) == 1:
        spawned = spawn_treasure_for_map(map_name, _active)
        debug_log('spawn on Playing key=%s ok=%s' % (key, spawned))
        # Hallazgo principal: acercarse al punto (SupplyObject no depende de Destroyed)
        _schedule_track_treasure()
        _start_proximity_watch()
        if not spawned and _IN_GAME and rdebug:
            try:
                rdebug.debugMessage(
                    'latamtreasures: spawn falló para %s' % key,
                    'latamtreasures',
                )
            except Exception:
                pass
    else:
        debug_log('skip spawn key=%s spawnable=%s' % (
            key, _active.get('spawnable'),
        ))


def on_game_status_changed(status):
    """Playing: carga/spawn tesoro. EndGame: pending lo toma latamstats."""
    if not _IN_GAME:
        return
    if status == bf2.GameStatus.Playing:
        map_name, mode, layer = get_current_round_ids()
        if rdebug:
            try:
                rdebug.debugMessage(
                    'latamtreasures Playing: %s'
                    % format_round_key(map_name, mode, layer),
                    'latamtreasures',
                )
            except Exception:
                pass
        _prepare_active_for_round(map_name, mode, layer)
    elif status == bf2.GameStatus.EndGame:
        _reset_round_state()


def on_vehicle_destroyed(vehicle, attacker):
    """Fallback: si el SupplyObject sí se destruye, también acredita."""
    if _claimed or _active is None or vehicle is None:
        return
    try:
        tname = vehicle.templateName
    except Exception:
        return
    if not is_treasure_template(tname):
        return
    if not _vehicle_near_active(vehicle, _active):
        return

    finder = resolve_finder_player(attacker)
    if finder is None and attacker is not None:
        # Último intento: tratar attacker como player
        finder = attacker
    try:
        debug_log('Destroyed claim template=%s' % tname)
    except Exception:
        pass
    # Asegurar referencia para el teletransporte a Y=9000
    global _treasure_vehicle
    if _treasure_vehicle is None:
        _treasure_vehicle = vehicle
    claim_treasure_for_finder(finder)


def on_chat_message(player_id, msg_text, channel, flags):
    """Handler ChatMessage: !tesoro envía la pista en privado."""
    global _active, _claimed
    if player_id == -1:
        return
    if not is_tesoro_command(msg_text):
        return

    try:
        player = bf2.playerManager.getPlayerByIndex(player_id)
    except Exception:
        return
    if player is None:
        return

    map_name, mode, layer = get_current_round_ids()
    round_key = format_round_key(map_name, mode, layer)

    # Siempre releer disco (así un .txt editado mid-ronda se ve en !tesoro)
    entries, text = load_entries_from_disk()
    n_entries = len(entries or [])
    disk_entry = find_round_entry(entries, map_name, mode, layer)
    map_entries = find_entries_for_map(entries, map_name)

    debug_log(
        'tesoro cmd round=%s entries=%s match=%s map_entries=%s file=%s'
        % (
            round_key,
            n_entries,
            'yes' if disk_entry else 'no',
            len(map_entries),
            'ok' if text is not None else 'MISSING',
        )
    )

    if disk_entry is None:
        # Ayuda: si el mapa tiene líneas pero mode/layer no calzan
        if map_entries:
            options = ', '.join(
                '%s/%s' % (e.get('mode'), e.get('layer')) for e in map_entries[:6]
            )
            _pm(
                player,
                'Sin match. Ahora: %s | En archivo para este mapa: %s'
                % (round_key, options),
            )
        elif text is None:
            _pm(
                player,
                'No se pudo leer latamtreasures.cfg/.txt en C:/prbf2_db (ver latamtreasures_debug.log)',
            )
        elif n_entries == 0:
            _pm(
                player,
                'Archivo leido pero 0 entradas validas. Revisar formato map|mode|layer|x|y|z|spawnable|riddle',
            )
        else:
            _pm(
                player,
                '%s (ahora: %s | entradas en archivo: %s)'
                % (MSG_NOT_CONFIGURED, round_key, n_entries),
            )
        return

    # Si aún no hay tesoro activo esta ronda, sincronizar y spawnear
    if _active is None and int(disk_entry.get('spawnable') or 0) == 1 and not _claimed:
        _active = dict(disk_entry)
        key = entry_key(_active)
        if key not in _force_found_keys:
            spawned = spawn_treasure_for_map(map_name, _active)
            debug_log('spawn via !tesoro key=%s ok=%s' % (key, spawned))
            _schedule_track_treasure()
            _start_proximity_watch()
            if not spawned and rdebug:
                try:
                    rdebug.debugMessage(
                        'latamtreasures: spawn (via !tesoro) falló para %s' % key,
                        'latamtreasures',
                    )
                except Exception:
                    pass

    entry = _active if _active is not None else disk_entry
    reply = tesoro_reply(entry, True)
    _pm(player, reply)


class TreasureSystem(object):
    """Registra handlers de tesoros en el servidor PR."""

    def __init__(self):
        host.registerGameStatusHandler(on_game_status_changed)
        # Track del objeto al spawnear (+ soften opcional)
        host.registerHandler('VehicleSpawned', on_vehicle_spawned, 1)
        # Fallback si el objeto se destruye
        host.registerHandler('VehicleDestroyed', on_vehicle_destroyed, 1)
        host.registerHandler('ChatMessage', on_chat_message, 1)
        # Hallazgo principal: proximidad (realitytimer.repeatingTask)


def init():
    """Registra el sistema de tesoros al iniciar el mod."""
    if _IN_GAME:
        TreasureSystem()


if _IN_GAME:
    init()
