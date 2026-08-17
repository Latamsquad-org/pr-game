# -*- coding: utf-8 -*-
# latamadmin.py - comandos admin extra de LATAMSQUAD
#
# !mute <jugador> <all|team>  → silencia al jugador en allchat o teamchat
# !unmute <jugador>           → le quita todos los mutes
#
# Mute all:
#   Intenta bloqueo real por jugador con la variable HUD PythonAllChatEnabled
#   (la misma que usa disable_allchat del servidor).
#   Si el cliente igual logra hablar, queda el castigo de respaldo (aviso + kick).
#
# Mute team:
#   No hay variable HUD equivalente para team/squad chat → solo castigo de respaldo.
#
# Todos los mutes se eliminan automáticamente al comenzar la ronda siguiente.
#
# Auto TK kick:
#   Sistema propio, independiente de !aa / sv.tkPunishEnabled.
#   Se controla con !ak on|off. Arranca segun adm_autoTkKick.
#   Con !ak on, kickea tras N teamkills; cada adm_autoTkKickExpireSec se resta 1 TK
#   (default 3 TK / -1 cada 5 min).
#   No cuenta: minas/IED/claymore, C4/dinamita a mano, carbomber, bombas/misiles CAS,
#   canon principal de tanque/APC/IFV (las ametralladoras coax/.50 SI cuentan).
#
# Anti-robo kit especial tras TK:
#   Si TKeas a un aliado con Heavy AT / Sniper / Marksman / AA y agarras ESE kit
#   → aviso + 5s para soltarlo; si no, dano ~30s hasta soltarlo o morir.
#   La marca dura 5 minutos (luego se puede volver a tomar el kit).
#   Independiente de !ak on/off. No aplica a riflemanat (Light AT).
#
# Espectador admin:
#   !spec JUGADOR  - camara libre PR siguiendo al target (!unspec para salir)
#   !unspec        - termina espectador y borra la camara
#
# Coop - bloqueo de equipo bots:
#   En mapas gpm_coop, impide que humanos se pasen al equipo con mas AI.
#   Si lo intentan, se los devuelve al otro equipo con aviso.
#   Los admins (isAdmin) pueden saltarse el bloqueo.

import time

try:
    import bf2
    import host
    import realityadmin as radmin
    import realityconfig_admin as ras
    import realitymemory as rmemory
    import realityserver
    import realitytimer as rtimer
    _IN_GAME = True
except ImportError:
    bf2 = None
    host = None
    radmin = None
    ras = None
    rmemory = None
    realityserver = None
    rtimer = None
    _IN_GAME = False

# realityconstants/realityvehicles son Py2; en tests Py3 pueden fallar al importar.
try:
    import realityconstants as rconstants
except Exception:
    rconstants = None

try:
    import realityvehicles as rvehicles
except Exception:
    rvehicles = None

try:
    import realitycore as rcore
except Exception:
    rcore = None

try:
    import realityserver as rserver
except Exception:
    rserver = None

# admin_hash -> {'cam_id', 'target_hash', 'target_name'}
_spec_sessions = {}
_spec_follow_task = None
_SPEC_FOLLOW_SEC = 0.35
_SPEC_CAM_HEIGHT = 6.0
_SPEC_CAM_BACK = 5.0

# Alias aceptados para cada alcance del mute.
_SCOPE_ALIASES = {
    'all': 'all',
    'allchat': 'all',
    'global': 'all',
    'team': 'team',
    'teamchat': 'team',
    'squad': 'team',
}

# Canales del motor cubiertos por cada alcance.
_SCOPE_CHANNELS = {
    'all': ('global',),
    'team': ('team', 'squad'),
}

# player_hash -> set de alcances muteados ({'all'}, {'team'} o ambos)
_muted = {}

# player_hash -> timestamp del ultimo castigo (evita doble kick por spam)
_last_punish = {}
_PUNISH_COOLDOWN_SEC = 3

# Hashes que ya recibieron la advertencia: la proxima infraccion es autokick.
_warned = set()

# Cada cuantos segundos se reafirma el bloqueo HUD a los muteados.
# Cierra la ventana del truco "tecla rapida + enter" tras algun rebroadcast.
_REAPPLY_INTERVAL_SEC = 0.5

# Referencia al sendAllChatStatus original (para reaplicar mute tras broadcasts)
_orig_send_allchat_status = None

# Contador de teamkills por hash: {'count': int, 'last_change': float}.
# Cada adm_autoTkKickExpireSec sin (o al vencer el timer) se resta 1 TK.
_tk_counts = {}
# Timers fireOnce para restar 1 TK automaticamente a los 5 min.
_tk_decay_timers = {}

# Estado runtime del kick por TK (independiente de sv.tkPunishEnabled / !aa).
# Se inicializa en init() desde adm_autoTkKick.
_auto_tk_kick_active = True

# Limite por defecto si la config no esta disponible (tests / offline).
_DEFAULT_TK_KICK_LIMIT = 3
# Segundos entre cada -1 TK del contador (default 5 minutos).
_DEFAULT_TK_KICK_EXPIRE_SEC = 300

# --- Anti-robo de kit especial tras TK (estilo kit enemigo) ---
# Tokens de kit protegidos (segundo segmento del template: us_sniper -> sniper).
_PROTECTED_KIT_TOKENS = frozenset(['at', 'sniper', 'marksman', 'aa'])
# Duracion del castigo (segundos), alineada al manual de PR para kit enemigo.
TK_KIT_STEAL_DURATION_SEC = 30
TK_KIT_STEAL_TICK_SEC = 1.0
# Segundos de aviso sin daño para que pueda soltar el kit.
TK_KIT_STEAL_GRACE_SEC = 5
# Tras este tiempo la marca caduca y se puede volver a tomar el kit.
TK_KIT_STEAL_MARK_TTL_SEC = 300
# Aviso HUD: "DEJA DE HACER ESO!" (antes STOP DOING THAT via 1220104).
MSG_TK_KIT_STEAL_FALLBACK = 'DEJA DE HACER ESO!'
# Texto extra en PythonGameWarning (HudVar timed).
MSG_TK_KIT_STEAL_HUD = 'ADVERTENCIA:\nNo puedes tomar este kit especial luego de un TK. SUELTALO!'
MSG_TK_KIT_STEAL_HUD_SEC = 8
# attacker_hash -> list de marcas {template, kit_id}
_stolen_kit_marks = {}
# attacker_hash -> estado de castigo activo
_kit_steal_punish = {}
# Timers de daño por hash (para cancelar)
_kit_steal_timers = {}

# Minas/trampas de WEAPONS_NO_PUNISH (sin artilleria). Fuente: realityscoring.py.
_TK_EXEMPT_WEAPON_TEMPLATES = frozenset([
    'at_mine',
    'at_mine_linked',
    'at_mine_tm35',
    'argmin_fmk1',
    'argmin_fmk1_linked',
    'argmin_fmk3',
    'germin_smine',
    'germin_smine_q1',
    'germin_smine_q2',
    'insgr_hgr_trap',
    'insgr_hgr_trap_q1',
    'insgr_hgr_trap_soviet',
    'insgr_hgr_trap_soviet_q4',
    'insrg_watercontainer_ied',
    'insrg_watercontainer_ied_idx6',
    'rumin_tm35',
    'rumin_pomz',
    'tm62m_mine',
    'usmin_m1a1',
    'usmin_m2a3',
    'usmin_m2a3_idx7_q2',
    'usmin_m2a3_q1',
    'vnhgr_betty',
    'vnhgr_betty_idx7',
    'vnhgr_betty_idx7_q2',
    'vnhgr_betty_q1',
])

# Marcadores en templateName (IED usa _ied para no matchear "allied").
_TK_EXEMPT_NAME_MARKERS = (
    'mine',
    'claymore',
    'betty',
    'pomz',
    'smine',
    'hgr_trap',
)

# Templates aereos tipados raro (p.ej. ATAA) que igual deben contar como TK.
_AIR_GUN_TEMPLATES = frozenset()

# Bombas / misiles tipicos de CAS (JDAM de commander + nombres de ordnance aereo).
_CAS_ORDNANCE_TEMPLATES = frozenset([
    'jdam_team1',
    'jdam_team2',
])
_CAS_ORDNANCE_NAME_MARKERS = (
    'jdam',
    'mk82',
    'mk_82',
    'gbu',
    'hellfire',
    'maverick',
    'hydra',
    'napalm',
    'firebomb',
    'glu-1',
    'clusterbomb',
    'cluster_bomb',
)

# Fallback si realityconstants/realityvehicles (Py2) no importan en tests.
_FLYING_VEHICLE_MARKERS = ('_ahe_', '_the_', '_jet_', 'uav')
# Tanque / APC / IFV / AFV (canon principal exento de !ak; LMG no).
_ARMORED_VEHICLE_MARKERS = ('_tnk_', '_apc_', '_ifv_', '_atm_')
_KNOWN_LMG_TEMPLATES = frozenset([
    '50cal_bullets_vab',
    '50cal_gau16',
    '50cal_m2hb',
    '50cal_m2hb_crows',
    '50cal_m3m',
    'ammo_belt_50cal',
    'ammo_belt_7-62mm_long',
    'ammo_belt_7-62mm_long_gwagon',
])


def _weapon_template_name(weapon):
    """Nombre lower del template del arma, o '' si no hay."""
    if weapon is None:
        return ''
    # str (Py3) / str+unicode (Py2)
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
    """
    Variantes del template: el kill a veces trae el proyectil (*_projectile)
    y la lista de scoring usa el nombre base (at_mine).
    """
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


def _name_looks_like_c4(name):
    """C4 / dinamita / TNT colocados a mano (incluye carbomber)."""
    if not name:
        return False
    if name.startswith('c4_') or name.startswith('tnt'):
        return True
    if 'dynamite' in name:
        return True
    return False


def _name_looks_like_mine_or_ied(name):
    """Heuristica por nombre: minas, IED, claymore, trampas."""
    if not name:
        return False
    for variant in _weapon_name_variants(name):
        if variant in _TK_EXEMPT_WEAPON_TEMPLATES:
            return True
        # IED: exigir _ied / ied_ para evitar falsos positivos tipo "allied"
        if '_ied' in variant or variant.startswith('ied') or variant.endswith('_ied'):
            return True
        for marker in _TK_EXEMPT_NAME_MARKERS:
            if marker in variant:
                return True
    return False


def _vehicle_template_name(vehicle):
    """Nombre lower del template del vehiculo, o ''."""
    if vehicle is None:
        return ''
    try:
        return str(vehicle.templateName).lower()
    except Exception:
        return ''


def _vehicle_is_flying(vehicle):
    """True si el root del arma es jet/heli/UAV/turboprop."""
    if vehicle is None:
        return False
    if rvehicles is not None:
        try:
            return bool(rvehicles.isFlyingVehicle(vehicle))
        except Exception:
            pass
    if rconstants is not None:
        try:
            vt = rconstants.getVehicleType(vehicle.templateName)
            return vt in (
                rconstants.VEHICLE_TYPE_HELI,
                rconstants.VEHICLE_TYPE_HELIATTACK,
                rconstants.VEHICLE_TYPE_JET,
                rconstants.VEHICLE_TYPE_UAV,
                rconstants.VEHICLE_TYPE_TURBOPROP,
            )
        except Exception:
            pass
    vname = _vehicle_template_name(vehicle)
    for marker in _FLYING_VEHICLE_MARKERS:
        if marker in vname:
            return True
    return False


def _vehicle_is_armored_combat(vehicle):
    """True si es tanque / APC / IFV / AFV (canon principal)."""
    if vehicle is None:
        return False
    if rconstants is not None:
        try:
            vt = rconstants.getVehicleType(vehicle.templateName)
            return vt in (
                rconstants.VEHICLE_TYPE_ARMOR,
                rconstants.VEHICLE_TYPE_APC,
                rconstants.VEHICLE_TYPE_IFV,
                rconstants.VEHICLE_TYPE_AFV,
            )
        except Exception:
            pass
    vname = _vehicle_template_name(vehicle)
    for marker in _ARMORED_VEHICLE_MARKERS:
        if marker in vname:
            return True
    return False


def _weapon_is_lmg(name):
    """True si el arma es ametralladora (cuenta TK aunque sea desde aire/blindado)."""
    if not name:
        return False
    if name in _KNOWN_LMG_TEMPLATES or name.startswith('50cal_'):
        return True
    if name.startswith('coaxial_'):
        return True
    if rconstants is None:
        return False
    try:
        return rconstants.getWeaponType(name) == rconstants.WEAPON_TYPE_LMG
    except Exception:
        return False


def _resolve_weapon_root(weapon):
    """Root parent del arma via bf2, o None offline."""
    if weapon is None or not _IN_GAME or bf2 is None:
        return None
    try:
        return bf2.objectManager.getRootParent(weapon)
    except Exception:
        return None


def _resolve_attacker_vehicle_root(attacker):
    """
    Root del vehiculo del atacante.
    Util cuando el 'weapon' del PlayerKilled es el proyectil y no tiene
    al tanque/APC como parent (caso tipico del canon).
    """
    if attacker is None or not _IN_GAME or bf2 is None:
        return None
    try:
        veh = attacker.getVehicle()
    except Exception:
        return None
    if veh is None:
        return None
    try:
        return bf2.objectManager.getRootParent(veh)
    except Exception:
        return veh


def _is_mine_c4_or_ied_name(name):
    """True si el template es mina/IED/claymore/C4/dinamita por nombre."""
    if not name:
        return False
    return _name_looks_like_c4(name) or _name_looks_like_mine_or_ied(name)


def _is_exempt_projectile_or_weapon_type(name):
    """True si realityconstants tipa el template como mina/C4/obus de tanque."""
    if not name or rconstants is None:
        return False
    try:
        for variant in _weapon_name_variants(name):
            wtype = rconstants.getWeaponType(variant)
            if wtype in (
                rconstants.WEAPON_TYPE_ATMINE,
                rconstants.WEAPON_TYPE_CLAYMORE,
                rconstants.WEAPON_TYPE_C4,
            ):
                return True
            ptype = rconstants.getProjectileType(variant)
            if ptype in (
                rconstants.PROJECTILE_TYPE_MINE_VICTIM_AT,
                rconstants.PROJECTILE_TYPE_MINE_VICTIM_AP,
                rconstants.PROJECTILE_TYPE_MINE_REMOTE_AT,
                rconstants.PROJECTILE_TYPE_MINE_REMOTE_AP,
                rconstants.PROJECTILE_TYPE_C4_SMALL,
                rconstants.PROJECTILE_TYPE_C4_LARGE,
                getattr(rconstants, 'PROJECTILE_TYPE_TANKSHELL', -1),
            ):
                return True
    except Exception:
        return False
    return False


def _is_tank_shell_name(name):
    """Heuristica por nombre de obus/canon de tanque (tnk_120_heat_r, etc.)."""
    if not name:
        return False
    if not name.startswith('tnk_'):
        return False
    for marker in ('heat', 'hesh', 'apfsds', 'frag', 'smoke'):
        if marker in name:
            return True
    return False


def _is_cas_ordnance_name(name):
    """
    True si el template parece bomba/misil de CAS o artilleria aerea (JDAM, etc.).
    No incluye ametralladoras ni canones de avion tipados como LMG.
    """
    if not name:
        return False
    for variant in _weapon_name_variants(name):
        if variant in _CAS_ORDNANCE_TEMPLATES:
            return True
        for marker in _CAS_ORDNANCE_NAME_MARKERS:
            if marker in variant:
                return True
    return False


def _resolve_combat_root(weapon, root_vehicle=None, attacker=None):
    """
    Root del vehiculo combatiente.
    Primero parent del arma; si el proyectil no tiene parent util
    (caso tipico de bombas CAS y obuses), usa el vehiculo del atacante.
    """
    root = root_vehicle
    if root is None:
        root = _resolve_weapon_root(weapon)
    if _vehicle_is_flying(root) or _vehicle_is_armored_combat(root):
        return root
    attacker_root = _resolve_attacker_vehicle_root(attacker)
    if attacker_root is not None:
        return attacker_root
    return root


def is_auto_tk_exempt(weapon, root_vehicle=None, attacker=None, obj=None):
    """
    True si este TK no debe contar para !ak.
    Minas/IED/claymore, C4/dinamita, carbomber, bombas/misiles CAS desde aire,
    canon de tanque/APC/IFV (no ametralladoras).
    root_vehicle/attacker/obj: opcionales para resolver proyectiles y blindados.
    """
    name = _weapon_template_name(weapon)
    obj_name = _weapon_template_name(obj)
    # PlayerKilled a veces trae el proyectil/mina en obj y weapon vacio o raro.
    if not name:
        name = obj_name

    # Minas/IED/C4: revisar weapon Y obj (a veces el arma reportada no es la mina).
    if _is_mine_c4_or_ied_name(name) or _is_mine_c4_or_ied_name(obj_name):
        return True
    if _is_exempt_projectile_or_weapon_type(name):
        return True
    if obj_name and obj_name != name and _is_exempt_projectile_or_weapon_type(obj_name):
        return True
    if _is_tank_shell_name(name) or _is_tank_shell_name(obj_name):
        return True
    # Bombas/misiles CAS y JDAM/artilleria (aunque el proyectil no tenga parent).
    if _is_cas_ordnance_name(name) or _is_cas_ordnance_name(obj_name):
        return True

    if not name:
        # Sin nombre: no podemos distinguir coax vs canon en blindado/aire.
        return False

    # Parent del proyectil suele faltar: usar vehiculo del atacante (CAS y tanque).
    root = _resolve_combat_root(weapon, root_vehicle=root_vehicle, attacker=attacker)

    # Ordnance aereo: jet/heli/UAV + no LMG (salvo lista AIR_GUN que fuerza conteo)
    if _vehicle_is_flying(root):
        if name in _AIR_GUN_TEMPLATES:
            return False
        if _weapon_is_lmg(name):
            return False
        return True

    # Canon de tanque / APC / IFV / AFV: no LMG (coax/.50 siguen contando).
    if _vehicle_is_armored_combat(root):
        if _weapon_is_lmg(name):
            return False
        return True

    return False


def clear_round_tk_counts():
    """Limpia contadores de TK y cancela timers de decay. Retorna cuantos hashes habia."""
    global _tk_decay_timers
    for timer in list(_tk_decay_timers.values()):
        try:
            if timer is not None:
                if hasattr(timer, 'destroy'):
                    timer.destroy()
                elif hasattr(timer, 'cancel'):
                    timer.cancel()
        except Exception:
            pass
    _tk_decay_timers.clear()
    count = len(_tk_counts)
    _tk_counts.clear()
    return count


def get_tk_kick_expire_sec():
    """Segundos entre cada -1 TK del contador (default 5 min)."""
    if ras is not None:
        try:
            return max(1, int(getattr(ras, 'adm_autoTkKickExpireSec', _DEFAULT_TK_KICK_EXPIRE_SEC)))
        except Exception:
            pass
    return _DEFAULT_TK_KICK_EXPIRE_SEC


def _tk_entry_count(raw):
    """Lee el conteo desde dict nuevo, lista legacy o int legacy."""
    if raw is None:
        return 0
    if isinstance(raw, dict):
        try:
            return max(0, int(raw.get('count', 0)))
        except Exception:
            return 0
    if isinstance(raw, (list, tuple)):
        return len(raw)
    try:
        return max(0, int(raw))
    except Exception:
        return 0


def _tk_entry_last_change(raw, now):
    """last_change del entry, o now si no hay."""
    if isinstance(raw, dict):
        try:
            return float(raw.get('last_change', now))
        except Exception:
            return float(now)
    return float(now)


def _cancel_tk_decay_timer(attacker_hash):
    """Cancela el timer de -1 TK para este hash."""
    global _tk_decay_timers
    timer = _tk_decay_timers.pop(attacker_hash, None)
    if timer is None:
        return
    try:
        if hasattr(timer, 'destroy'):
            timer.destroy()
        elif hasattr(timer, 'cancel'):
            timer.cancel()
    except Exception:
        pass


def _schedule_tk_decay(attacker_hash):
    """Programa -1 TK automaticamente tras ExpireSec (si sigue habiendo conteo)."""
    global _tk_decay_timers
    _cancel_tk_decay_timer(attacker_hash)
    if not attacker_hash:
        return
    if _tk_entry_count(_tk_counts.get(attacker_hash)) <= 0:
        return
    if not _IN_GAME or rtimer is None:
        return
    delay = float(get_tk_kick_expire_sec())
    try:
        timer = rtimer.fireOnce(
            lambda data=None, h=attacker_hash: _on_tk_decay_timer(h),
            delay,
        )
        _tk_decay_timers[attacker_hash] = timer
    except Exception:
        _tk_decay_timers.pop(attacker_hash, None)


def _on_tk_decay_timer(attacker_hash):
    """Callback: resta 1 TK y reprograma si quedan."""
    _tk_decay_timers.pop(attacker_hash, None)
    apply_tk_decay(attacker_hash, force_one=True)
    if tk_count_for(attacker_hash) > 0:
        _schedule_tk_decay(attacker_hash)


def apply_tk_decay(attacker_hash, now=None, force_one=False):
    """
    Resta TK segun el tiempo: -1 por cada ExpireSec desde last_change.
    Si force_one=True (timer), resta exactamente 1 aunque el reloj falle.
    Retorna el conteo restante.
    """
    if not attacker_hash:
        return 0
    if now is None:
        now = time.time()
    raw = _tk_counts.get(attacker_hash)
    if raw is None:
        return 0
    count = _tk_entry_count(raw)
    if count <= 0:
        _tk_counts.pop(attacker_hash, None)
        _cancel_tk_decay_timer(attacker_hash)
        return 0
    last = _tk_entry_last_change(raw, now)
    ttl = float(get_tk_kick_expire_sec())
    if force_one:
        periods = 1
    else:
        elapsed = float(now) - float(last)
        if elapsed < ttl:
            # Normalizar a dict si venia legacy.
            _tk_counts[attacker_hash] = {'count': count, 'last_change': last}
            return count
        periods = int(elapsed // ttl)
        if periods <= 0:
            return count
    count = max(0, count - periods)
    if count <= 0:
        _tk_counts.pop(attacker_hash, None)
        _cancel_tk_decay_timer(attacker_hash)
        return 0
    # Avanzar last_change por los periodos aplicados.
    new_last = float(last) + float(periods) * ttl
    if force_one:
        new_last = float(now)
    _tk_counts[attacker_hash] = {'count': count, 'last_change': new_last}
    return count


def kit_type_token(template_name):
    """
    Token de kit desde template (us_sniper -> sniper, us_riflemanat -> riflemanat).
    Retorna None si no se puede parsear.
    """
    if template_name is None:
        return None
    name = str(template_name).strip().lower()
    if not name:
        return None
    parts = name.split('_')
    if len(parts) < 2:
        return None
    return parts[1]


def is_protected_kit(template_name):
    """True si el kit es Heavy AT / Sniper / Marksman / AA (no riflemanat)."""
    token = kit_type_token(template_name)
    if token is None:
        return False
    # Light AT no cuenta como Heavy AT.
    if token == 'riflemanat':
        return False
    return token in _PROTECTED_KIT_TOKENS


def _kit_template_name(kit):
    """templateName del kit, o ''."""
    if kit is None:
        return ''
    try:
        return str(kit.templateName or '').strip().lower()
    except Exception:
        return ''


def _kit_object_id(kit):
    """id() del objeto kit para matching, o None."""
    if kit is None:
        return None
    try:
        return id(kit)
    except Exception:
        return None


def clear_round_kit_steal_state():
    """Limpia marcas de robo y castigos activos de la ronda."""
    global _stolen_kit_marks, _kit_steal_punish, _kit_steal_timers
    for timer in list(_kit_steal_timers.values()):
        try:
            if timer is not None:
                if hasattr(timer, 'destroy'):
                    timer.destroy()
                elif hasattr(timer, 'cancel'):
                    timer.cancel()
        except Exception:
            pass
    _kit_steal_timers.clear()
    marks = len(_stolen_kit_marks)
    _stolen_kit_marks.clear()
    _kit_steal_punish.clear()
    return marks


def _prune_expired_stolen_marks(attacker_hash=None, now=None):
    """
    Quita marcas vencidas (TTL). Si attacker_hash es None, limpia todas.
    Retorna cuantas marcas se eliminaron.
    """
    if now is None:
        now = time.time()
    removed = 0
    if attacker_hash is None:
        hashes = list(_stolen_kit_marks.keys())
    else:
        hashes = [attacker_hash]
    for h in hashes:
        marks = _stolen_kit_marks.get(h) or []
        if not marks:
            _stolen_kit_marks.pop(h, None)
            continue
        kept = []
        for mark in marks:
            expires = mark.get('expires_at')
            # Marcas viejas sin expires_at: tratar como vigentes hasta fin de ronda.
            if expires is not None and float(expires) <= float(now):
                removed += 1
                continue
            kept.append(mark)
        if kept:
            _stolen_kit_marks[h] = kept
        else:
            _stolen_kit_marks.pop(h, None)
    return removed


def mark_stolen_kit(attacker_hash, kit_template, kit=None, now=None):
    """
    Marca un kit protegido como no tomable por el atacante durante
    TK_KIT_STEAL_MARK_TTL_SEC (o hasta fin de ronda / otro lo tome).
    Retorna True si se marco.
    """
    if not attacker_hash:
        return False
    template = str(kit_template or '').strip().lower()
    if not is_protected_kit(template):
        return False
    if now is None:
        now = time.time()
    marks = _stolen_kit_marks.get(attacker_hash)
    if marks is None:
        marks = []
        _stolen_kit_marks[attacker_hash] = marks
    marks.append({
        'template': template,
        'kit_id': _kit_object_id(kit),
        'token': kit_type_token(template),
        'expires_at': float(now) + float(TK_KIT_STEAL_MARK_TTL_SEC),
    })
    return True


def clear_stolen_marks_for_kit(kit, except_hash=None):
    """
    Quita marcas que apunten a este kit (u mismo template) cuando lo agarra otro.
    except_hash: no limpiar marcas de este atacante (el que lo esta robando).
    """
    _prune_expired_stolen_marks()
    template = _kit_template_name(kit)
    kit_id = _kit_object_id(kit)
    if not template and kit_id is None:
        return 0
    removed = 0
    for attacker_hash in list(_stolen_kit_marks.keys()):
        if except_hash is not None and attacker_hash == except_hash:
            continue
        marks = _stolen_kit_marks.get(attacker_hash) or []
        kept = []
        for mark in marks:
            same_obj = (
                kit_id is not None
                and mark.get('kit_id') is not None
                and mark.get('kit_id') == kit_id
            )
            same_tpl = mark.get('template') == template
            if same_obj or same_tpl:
                removed += 1
                continue
            kept.append(mark)
        if kept:
            _stolen_kit_marks[attacker_hash] = kept
        else:
            _stolen_kit_marks.pop(attacker_hash, None)
    return removed


def match_stolen_kit_pickup(attacker_hash, kit, now=None):
    """
    True si este pickup corresponde a una marca vigente del atacante.
    NO consume la marca: soltar y volver a agarrar sigue castigando
    hasta que caduque (TTL), fin de ronda, o hasta que otro tome el kit.
    """
    if not attacker_hash:
        return False
    _prune_expired_stolen_marks(attacker_hash, now=now)
    marks = _stolen_kit_marks.get(attacker_hash) or []
    if not marks:
        return False
    template = _kit_template_name(kit)
    kit_id = _kit_object_id(kit)
    if not is_protected_kit(template):
        return False
    for mark in marks:
        same_obj = (
            kit_id is not None
            and mark.get('kit_id') is not None
            and mark.get('kit_id') == kit_id
        )
        same_tpl = mark.get('template') == template
        if same_obj or same_tpl:
            return True
    return False


def cancel_kit_steal_punish(player_hash):
    """Cancela daño/timer de castigo por robo de kit."""
    timer = _kit_steal_timers.pop(player_hash, None)
    if timer is not None:
        try:
            if hasattr(timer, 'destroy'):
                timer.destroy()
            elif hasattr(timer, 'cancel'):
                timer.cancel()
        except Exception:
            pass
    _kit_steal_punish.pop(player_hash, None)


def _apply_soldier_damage(player, damage_value):
    """Baja HP del soldado (setDamage absoluto)."""
    if player is None:
        return False
    try:
        soldier = player.getDefaultVehicle()
    except Exception:
        return False
    if soldier is None:
        return False
    try:
        if damage_value <= 0:
            damage_value = 1e-07
        soldier.setDamage(float(damage_value))
        return True
    except Exception:
        return False


def _kit_steal_damage_tick(player_hash):
    """
    Tick periodico: aviso siempre; dano lineal tras TK_KIT_STEAL_GRACE_SEC
    hasta 0 en TK_KIT_STEAL_DURATION_SEC.
    """
    state = _kit_steal_punish.get(player_hash)
    if state is None:
        cancel_kit_steal_punish(player_hash)
        return
    player = state.get('player')
    try:
        if player is None or not player.isValid():
            cancel_kit_steal_punish(player_hash)
            return
    except Exception:
        cancel_kit_steal_punish(player_hash)
        return

    now = time.time()
    start = float(state.get('start') or now)
    ticks = int(state.get('ticks') or 0) + 1
    state['ticks'] = ticks
    # Reavisar cada 2 s (mismo ritmo que asset control en realitybouncer).
    if ticks % 2 == 0:
        _warn_kit_steal_hud(player)

    # Gracia: solo aviso, sin bajar vida.
    grace = float(TK_KIT_STEAL_GRACE_SEC)
    if (now - start) < grace:
        return

    # Arranque de dano: fija HP base al terminar la gracia.
    if not state.get('damage_started'):
        state['damage_started'] = True
        state['damage_start'] = now
        start_hp = 100.0
        try:
            soldier = player.getDefaultVehicle()
            if soldier is not None:
                start_hp = float(soldier.getDamage())
        except Exception:
            start_hp = 100.0
        if start_hp <= 0:
            start_hp = 100.0
        state['start_hp'] = start_hp

    damage_start = float(state.get('damage_start') or now)
    start_hp = float(state.get('start_hp') or 100.0)
    elapsed = now - damage_start
    if elapsed >= float(TK_KIT_STEAL_DURATION_SEC):
        _apply_soldier_damage(player, 1e-07)
        cancel_kit_steal_punish(player_hash)
        return

    frac = elapsed / float(TK_KIT_STEAL_DURATION_SEC)
    new_hp = start_hp * (1.0 - frac)
    if new_hp < 1e-07:
        new_hp = 1e-07
    _apply_soldier_damage(player, new_hp)


def _warn_kit_steal_hud(player):
    """DEJA DE HACER ESO! + aviso HUD explicando que debe soltar el kit."""
    if player is None:
        return
    # Misma var HUD que bouncer/assetban: texto personalizado con timer.
    if rmemory is not None:
        try:
            rmemory.HudVarWriteEventWstringWithTimedShowvar(
                player,
                'PythonGameWarning',
                MSG_TK_KIT_STEAL_HUD,
                MSG_TK_KIT_STEAL_HUD_SEC,
            )
            return
        except Exception:
            pass
    if rcore is not None:
        try:
            # Fallback: helper central (tambien fuerza español).
            if hasattr(rcore, 'sendDejaDeHacerEso') and rcore.sendDejaDeHacerEso(player):
                return
            rcore.sendMessageToPlayer(player, getattr(rcore, 'MSG_STOP_DOING_THAT_ID', 1220104), 1)
            return
        except Exception:
            pass
    if radmin is not None:
        try:
            radmin.sendRhooksAdminWarnEventWrapper(
                player,
                MSG_TK_KIT_STEAL_FALLBACK,
                history=False,
                longDisplay=True,
            )
        except Exception:
            try:
                radmin.personalMessage(MSG_TK_KIT_STEAL_FALLBACK, player)
            except Exception:
                pass


def start_kit_steal_punish(player):
    """
    Inicia aviso + gracia TK_KIT_STEAL_GRACE_SEC + dano ~30s si no suelta.
    Retorna True si arranco.
    """
    if player is None:
        return False
    player_hash = _player_hash(player)
    if player_hash is None:
        return False

    cancel_kit_steal_punish(player_hash)

    _kit_steal_punish[player_hash] = {
        'player': player,
        'start': time.time(),
        'start_hp': 100.0,
        'ticks': 0,
        'damage_started': False,
        'damage_start': None,
    }

    _warn_kit_steal_hud(player)

    if radmin is not None:
        try:
            radmin.adminPM(
                'Anti-kit-steal: %s debe soltar kit especial (TK).'
                % player.getName(),
                None,
                history=False,
                toPrism=False,
            )
        except Exception:
            pass

    if _IN_GAME and rtimer is not None:
        try:
            timer = rtimer.repeatingTask(
                lambda data=None, h=player_hash: _kit_steal_damage_tick(h),
                TK_KIT_STEAL_TICK_SEC,
            )
            _kit_steal_timers[player_hash] = timer
        except Exception:
            _kit_steal_timers.pop(player_hash, None)
    return True


def try_mark_tk_stolen_kit(victim, attacker, weapon, obj=None):
    """
    Si es TK no-exempt y el kit de la victima es protegido, marca el kit.
    Independiente de !ak on/off. Retorna True si marco.
    """
    if victim is None or attacker is None:
        return False
    try:
        if victim == attacker:
            return False
        if victim.getTeam() != attacker.getTeam():
            return False
    except Exception:
        return False
    try:
        # Pasar attacker/obj: sin eso no filtra canon de blindado ni minas raras.
        if is_auto_tk_exempt(weapon, attacker=attacker, obj=obj):
            return False
    except Exception:
        pass

    kit = None
    template = ''
    try:
        kit = victim.getKit()
        template = _kit_template_name(kit)
    except Exception:
        kit = None
        template = ''
    if not is_protected_kit(template):
        return False

    attacker_hash = _player_hash(attacker)
    if attacker_hash is None:
        return False
    return mark_stolen_kit(attacker_hash, template, kit)


def get_tk_kick_limit():
    """Limite de TK en la ventana de tiempo antes del autokick."""
    if ras is not None:
        try:
            return max(1, int(getattr(ras, 'adm_autoTkKickLimit', _DEFAULT_TK_KICK_LIMIT)))
        except Exception:
            pass
    return _DEFAULT_TK_KICK_LIMIT


def set_auto_tk_kick_enabled(enabled):
    """Activa o desactiva el kick por TK en runtime. No toca sv.tkPunishEnabled."""
    global _auto_tk_kick_active
    _auto_tk_kick_active = bool(enabled)
    return _auto_tk_kick_active


def is_auto_tk_kick_enabled():
    """
    True si el kick por TK esta activo.
    Independiente de !aa / sv.tkPunishEnabled.
    """
    # Master switch en config: si esta False, el feature queda muerto.
    if ras is not None and not getattr(ras, 'adm_autoTkKick', True):
        return False
    return bool(_auto_tk_kick_active)


def register_teamkill(attacker_hash, limit=None, now=None):
    """
    Suma un TK al atacante. Antes aplica decay (-1 cada ExpireSec).
    Retorna (count, should_kick). No cuenta si attacker_hash es vacio.
    """
    if not attacker_hash:
        return (0, False)
    if limit is None:
        limit = get_tk_kick_limit()
    if now is None:
        now = time.time()
    # Aplicar -1 pendientes por tiempo antes de sumar el nuevo TK.
    count = apply_tk_decay(attacker_hash, now=now)
    count = int(count) + 1
    _tk_counts[attacker_hash] = {
        'count': count,
        'last_change': float(now),
    }
    # Reinicia el timer: en ExpireSec se resta 1.
    _schedule_tk_decay(attacker_hash)
    return (count, count >= limit)


def tk_count_for(attacker_hash, now=None):
    """Cantidad de TK vigentes (despues de aplicar decay) para el hash."""
    if not attacker_hash:
        return 0
    return int(apply_tk_decay(attacker_hash, now=now))


def command_ak(args, admin):
    """
    !ak [on|off] - controla el kick por TK (sistema Python).
    No modifica !aa ni sv.tkPunishEnabled.
    """
    args = [a for a in list(args or []) if a]
    if len(args) > 0 and str(args[0]).lower() not in ('on', 'off'):
        radmin.personalMessage(
            'Uso: !ak [on|off]  (kick por teamkills)',
            admin,
        )
        return False

    if len(args) == 0:
        state = 'enabled' if is_auto_tk_kick_enabled() else 'disabled'
        limit = get_tk_kick_limit()
        expire = get_tk_kick_expire_sec()
        radmin.personalMessage(
            'Auto TK kick is %s (limite %d TK; -1 cada %d s).'
            % (state, limit, expire),
            admin,
        )
        return True

    if ras is not None and not getattr(ras, 'adm_autoTkKick', True):
        radmin.personalMessage(
            'Auto TK kick esta deshabilitado en realityconfig_admin (adm_autoTkKick=False).',
            admin,
        )
        return False

    turning_on = str(args[0]).lower() == 'on'
    set_auto_tk_kick_enabled(turning_on)
    if turning_on:
        radmin.adminPM('Auto TK kick ha sido activado (!ak).', admin)
    else:
        # Al apagar, limpiar contadores para no kickear al reactivar con restos.
        clear_round_tk_counts()
        radmin.adminPM('Auto TK kick ha sido desactivado (!ak).', admin)
    radmin.logAdmin('!ak', admin.getName(), '', 'on' if turning_on else 'off')
    return True


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


def _player_by_hash(player_hash):
    if not player_hash or bf2 is None:
        return None
    try:
        for player in bf2.playerManager.getPlayers():
            if _player_hash(player) == player_hash:
                return player
    except Exception:
        pass
    return None


def _is_spectator_camera(vehicle):
    if vehicle is None:
        return False
    try:
        return str(vehicle.templateName).lower().startswith('spectator_camera')
    except Exception:
        return False


def _spec_camera_pose(target):
    """Posicion atras/arriba del target para la camara espectador."""
    if rcore is None or target is None:
        return None
    try:
        if not target.isValid() or not target.isAlive() or target.isManDown():
            return None
    except Exception:
        return None
    try:
        behind = rcore.getPositionFromPlayer(target, -_SPEC_CAM_BACK)
        return (
            float(behind[0]),
            float(behind[1]) + _SPEC_CAM_HEIGHT,
            float(behind[2]),
        )
    except Exception:
        return None


def _destroy_spec_camera(cam_id):
    if not cam_id or rcore is None:
        return
    try:
        rcore.deleteObjectId(cam_id)
    except Exception:
        pass


def _end_spec_for_admin(admin, message=''):
    ph = _player_hash(admin)
    if not ph:
        return False
    sess = _spec_sessions.pop(ph, None)
    if sess is None:
        if message:
            radmin.personalMessage(message, admin)
        return False
    try:
        veh = admin.getVehicle()
        if _is_spectator_camera(veh) and rmemory is not None:
            rmemory.sendPlayerButtonClickEvent(admin, rmemory.PI_USE)
    except Exception:
        pass
    _destroy_spec_camera(sess.get('cam_id'))
    if message:
        radmin.personalMessage(message, admin)
    return True


def _clear_all_spec():
    global _spec_sessions
    for ph, sess in list(_spec_sessions.items()):
        _destroy_spec_camera(sess.get('cam_id'))
    _spec_sessions = {}


def _update_spec_follow(args=None):
    if not _spec_sessions or rcore is None:
        return
    for admin_hash, sess in list(_spec_sessions.items()):
        target = _player_by_hash(sess.get('target_hash'))
        cam_id = sess.get('cam_id')
        if not cam_id:
            continue
        if target is None:
            admin = _player_by_hash(admin_hash)
            if admin is not None:
                _end_spec_for_admin(admin, 'Espectador detenido: el jugador se desconecto.')
            else:
                _spec_sessions.pop(admin_hash, None)
                _destroy_spec_camera(cam_id)
            continue
        pos = _spec_camera_pose(target)
        if pos is None:
            continue
        try:
            rcore.editObject(cam_id, pos, None)
        except Exception:
            pass


def _ensure_spec_follow_task():
    global _spec_follow_task
    if not _IN_GAME or rtimer is None:
        return
    if _spec_follow_task is not None:
        return
    _spec_follow_task = rtimer.repeatingTask(_update_spec_follow, _SPEC_FOLLOW_SEC)


def command_spec(args, admin):
    """!spec JUGADOR - camara espectador PR que sigue al target."""
    args = [str(a) for a in list(args or []) if a is not None and str(a).strip()]
    if len(args) < 1:
        radmin.personalMessage('Uso: !spec JUGADOR', admin)
        return False
    if rcore is None:
        radmin.personalMessage('Espectador no disponible (realitycore).', admin)
        return False
    try:
        if not admin.isValid() or not admin.isAlive() or admin.isManDown():
            radmin.personalMessage('Debes estar vivo y a pie para espectear.', admin)
            return False
    except Exception:
        return False

    found = radmin.findPlayer(args[0], admin)
    if not found:
        return False
    target = found[0]
    if target == admin:
        radmin.personalMessage('No puedes espectearte a ti mismo.', admin)
        return False
    try:
        if not target.isAlive() or target.isManDown():
            radmin.personalMessage('%s no esta vivo a pie.' % target.getName(), admin)
            return False
    except Exception:
        return False

    _end_spec_for_admin(admin)

    pos = _spec_camera_pose(target)
    if pos is None:
        radmin.personalMessage('No se pudo calcular posicion para %s.' % target.getName(), admin)
        return False

    cam_id = rcore.createObject('spectator_camera', pos, (0.0, 0.0, 0.0))
    if not cam_id:
        radmin.personalMessage(
            'No se pudo spawnear spectator_camera. Proba consola: prbot',
            admin,
        )
        return False

    admin_pos = (pos[0], pos[1] - 2.0, pos[2])
    if not radmin.teleportPlayer(admin, admin_pos[0], admin_pos[1], admin_pos[2]):
        _destroy_spec_camera(cam_id)
        radmin.personalMessage('No se pudo teletransportarte a la camara.', admin)
        return False

    admin_hash = _player_hash(admin)
    target_hash = _player_hash(target)
    if not admin_hash:
        _destroy_spec_camera(cam_id)
        return False

    _spec_sessions[admin_hash] = {
        'cam_id': cam_id,
        'target_hash': target_hash,
        'target_name': target.getName(),
    }
    _ensure_spec_follow_task()
    radmin.personalMessage(
        'Espectando a %s. Usa E en la camara flotante (o acercate y subi). '
        'Salir: USE de nuevo o !unspec. No es POV del jugador, es camara libre.'
        % target.getName(),
        admin,
    )
    radmin.logAdmin('!spec', admin.getName(), target.getName(), target_hash[:16])
    return True


def command_unspec(args, admin):
    """!unspec - termina espectador admin."""
    if _end_spec_for_admin(admin, 'Espectador desactivado.'):
        radmin.logAdmin('!unspec', admin.getName(), '', '')
        return True
    radmin.personalMessage('No tenias espectador activo.', admin)
    return False


def on_player_killed(victim, attacker, weapon, assists, obj):
    """
    Contador de teamkills + autokick cuando !ak esta activo.
    Tambien marca kit especial protegido para anti-robo (independiente de !ak).
    Ignora suicidios, enemigos y armas exempt (minas/IED/C4/aire/canon blindado).
    """
    if victim is None or attacker is None:
        return
    try:
        if victim == attacker:
            return
        if victim.getTeam() != attacker.getTeam():
            return
    except Exception:
        return

    # Anti-robo de kit especial: marca aunque !ak este off.
    try:
        try_mark_tk_stolen_kit(victim, attacker, weapon, obj)
    except Exception:
        pass

    # Si el atacante estaba siendo castigado por robo y muere, cancelar.
    try:
        victim_hash = _player_hash(victim)
        if victim_hash is not None:
            cancel_kit_steal_punish(victim_hash)
    except Exception:
        pass

    if not is_auto_tk_kick_enabled():
        return

    # Minas, IED, C4, aire, canon de blindado: no cuentan para !ak
    try:
        if is_auto_tk_exempt(weapon, attacker=attacker, obj=obj):
            return
    except Exception:
        pass

    attacker_hash = _player_hash(attacker)
    if attacker_hash is None:
        return

    limit = get_tk_kick_limit()
    count, should_kick = register_teamkill(attacker_hash, limit)

    try:
        radmin.personalMessage(
            'Teamkill %d/%d (Auto TK; -1 cada %ds). Al llegar al limite seras kickeado.'
            % (count, limit, get_tk_kick_expire_sec()),
            attacker,
        )
        radmin.adminPM(
            'Auto TK: %s -> %s (%d/%d)'
            % (attacker.getName(), victim.getName(), count, limit),
            None,
            history=False,
            toPrism=False,
        )
    except Exception:
        pass

    if not should_kick:
        return

    # Limpiar contador antes del kick para no re-kickear en el mismo evento.
    _cancel_tk_decay_timer(attacker_hash)
    _tk_counts.pop(attacker_hash, None)
    try:
        radmin.globalMessage(
            '%s kickeado por demasiados teamkills (%d) - [Auto TK]'
            % (attacker.getName(), limit),
        )
        radmin.logAdmin(
            '!k', '[Auto TK]', attacker.getName(),
            'Teamkills (%d)' % limit,
        )
        radmin.kickPlayer(
            attacker,
            'Demasiados teamkills (%d)' % limit,
            False,
        )
    except Exception:
        pass


def on_pickup_kit(player, kit):
    """Si el TK agarra el kit marcado de su victima → castigo estilo kit enemigo."""
    if player is None or kit is None:
        return
    try:
        if player.isAIPlayer():
            return
    except Exception:
        pass

    player_hash = _player_hash(player)
    if player_hash is None:
        return

    # Primero: si es el ladron con marca activa → castigo (marca se conserva).
    if match_stolen_kit_pickup(player_hash, kit):
        start_kit_steal_punish(player)
        return

    # Otro jugador agarro el kit marcado → ya no es robo del TK original.
    try:
        clear_stolen_marks_for_kit(kit, except_hash=None)
    except Exception:
        pass


def on_drop_kit(player, kit):
    """Si suelta el kit durante el castigo, cancelar dano (la marca sigue)."""
    if player is None:
        return
    player_hash = _player_hash(player)
    if player_hash is None:
        return
    if player_hash in _kit_steal_punish:
        cancel_kit_steal_punish(player_hash)


def on_player_disconnect(player):
    """Limpia castigo/marcas del jugador que se desconecta."""
    if player is None:
        return
    player_hash = _player_hash(player)
    if not player_hash:
        return
    cancel_kit_steal_punish(player_hash)
    _stolen_kit_marks.pop(player_hash, None)
    if player_hash in _spec_sessions:
        sess = _spec_sessions.pop(player_hash)
        _destroy_spec_camera(sess.get('cam_id'))
    for admin_hash, sess in list(_spec_sessions.items()):
        if sess.get('target_hash') != player_hash:
            continue
        admin = _player_by_hash(admin_hash)
        if admin is not None:
            _end_spec_for_admin(admin, 'Espectador detenido: el jugador se desconecto.')
        else:
            _destroy_spec_camera(sess.get('cam_id'))
            _spec_sessions.pop(admin_hash, None)

def parse_mute_args(args):
    """
    Valida los argumentos de !mute: [jugador, alcance].
    Retorna (jugador, alcance_normalizado) o (None, None) si son invalidos.
    """
    args = [a for a in list(args or []) if a]
    if len(args) < 2:
        return (None, None)
    scope = _SCOPE_ALIASES.get(str(args[1]).strip().lower())
    if scope is None:
        return (None, None)
    return (str(args[0]), scope)


def scope_covers_channel(scopes, channel):
    """True si alguno de los alcances muteados cubre el canal del mensaje."""
    ch = str(channel or '').strip().lower()
    for scope in scopes:
        if ch in _SCOPE_CHANNELS.get(scope, ()):
            return True
    return False


def mute_player_hash(player_hash, scope):
    """Agrega un alcance de mute para el hash dado."""
    scopes = _muted.get(player_hash)
    if scopes is None:
        scopes = set()
        _muted[player_hash] = scopes
    scopes.add(scope)


def unmute_player_hash(player_hash):
    """Quita todos los mutes del hash. Retorna True si tenia alguno."""
    _warned.discard(player_hash)
    return _muted.pop(player_hash, None) is not None


def muted_scopes(player_hash):
    """Set de alcances muteados del hash (vacio si no esta muteado)."""
    return set(_muted.get(player_hash, ()))


def is_allchat_muted(player_hash):
    """True si el hash tiene mute de chat general."""
    return 'all' in _muted.get(player_hash, ())


def clear_round_mutes():
    """Limpia mutes, advertencias y cooldowns. Retorna cuántos mutes quitó."""
    count = len(_muted)
    _muted.clear()
    _warned.clear()
    _last_punish.clear()
    return count



def _scope_label(scope):
    return 'chat general' if scope == 'all' else 'chat de equipo'


def _player_hash(player):
    try:
        value = realityserver.getPlayerHash(player)
    except Exception:
        return None
    if value is None or value == '' or isinstance(value, bool):
        return None
    return value


def apply_allchat_hud(player, enabled):
    """
    Envia al cliente PythonAllChatEnabled (True/False).
    Retorna True si se envio, False si fallo (sin bf2 / sin rmemory).
    """
    if not _IN_GAME or rmemory is None or player is None:
        return False
    try:
        rmemory.sendHudVarWriteEventBool(
            player, 'PythonAllChatEnabled', 1 if enabled else 0,
        )
        return True
    except Exception:
        return False


def disable_allchat_for_player(player):
    """Bloqueo real de allchat para un jugador concreto."""
    return apply_allchat_hud(player, False)


def restore_allchat_for_player(player):
    """
    Restaura el estado normal de allchat del servidor para ese jugador
    (respeta disable_allchat global y umbrales por poblacion).
    """
    if not _IN_GAME or radmin is None:
        return False
    try:
        # Usa el original si ya lo envolviste, para no reaplicar mute a si mismo.
        if _orig_send_allchat_status is not None:
            _orig_send_allchat_status(player)
        else:
            radmin.sendAllChatStatus(player)
        return True
    except Exception:
        return False


def _reapply_mutes(data=None):
    """
    Tarea periodica: reenvia PythonAllChatEnabled=0 a todos los muteados en all.
    Asi el cliente nunca queda con el chat general rehabilitado.
    """
    if not _muted:
        return
    try:
        players = bf2.playerManager.getPlayers()
    except Exception:
        return
    for player in players:
        try:
            if player.isAIPlayer():
                continue
        except Exception:
            continue
        player_hash = _player_hash(player)
        if player_hash is not None and is_allchat_muted(player_hash):
            disable_allchat_for_player(player)


def _wrapped_send_allchat_status(player):
    """
    Tras el broadcast normal del servidor, vuelve a apagar allchat
    si el jugador tiene !mute all activo.
    """
    if _orig_send_allchat_status is not None:
        _orig_send_allchat_status(player)
    player_hash = _player_hash(player)
    if player_hash is not None and is_allchat_muted(player_hash):
        disable_allchat_for_player(player)


def command_mute(args, admin):
    """!mute <jugador> <all|team>"""
    args = [a for a in list(args or []) if a]
    target, scope = parse_mute_args(args)
    if target is None:
        radmin.personalMessage(
            'Uso: !mute <jugador> <all|team> (all = chat general, team = chat de equipo)',
            admin,
        )
        return False

    found = radmin.findPlayer(target, admin)
    if len(found) == 0:
        return False

    for player in found:
        player_hash = _player_hash(player)
        if player_hash is None:
            radmin.personalMessage(
                'No se pudo obtener el ID de %s' % player.getName(), admin,
            )
            continue
        mute_player_hash(player_hash, scope)

        # Mute all: intento de bloqueo real por HUD (mismo mecanismo que disable_allchat).
        if scope == 'all':
            if disable_allchat_for_player(player):
                radmin.personalMessage(
                    'Fuiste silenciado en el chat general (bloqueo de cliente).',
                    player,
                )
            else:
                radmin.personalMessage(
                    'Fuiste silenciado en el chat general por un administrador.',
                    player,
                )
        else:
            radmin.personalMessage(
                'Fuiste silenciado en el %s por un administrador.' % _scope_label(scope),
                player,
            )

        radmin.adminPM(
            '%s silenciado en %s por %s.'
            % (player.getName(), _scope_label(scope), admin.getName()),
        )
        radmin.logAdmin('!mute', admin.getName(), player.getName(), scope)

    return True


def command_unmute(args, admin):
    """!unmute <jugador>"""
    args = [a for a in list(args or []) if a]
    if len(args) < 1:
        radmin.personalMessage('Uso: !unmute <jugador>', admin)
        return False

    found = radmin.findPlayer(args[0], admin)
    if len(found) == 0:
        return False

    for player in found:
        player_hash = _player_hash(player)
        if player_hash is None or not unmute_player_hash(player_hash):
            radmin.personalMessage(
                '%s no estaba silenciado.' % player.getName(), admin,
            )
            continue
        # Quitar mute all: devolver el estado global de allchat al cliente.
        restore_allchat_for_player(player)
        radmin.personalMessage('Ya no estas silenciado.', player)
        radmin.adminPM(
            '%s ya no esta silenciado (por %s).'
            % (player.getName(), admin.getName()),
        )
        radmin.logAdmin('!unmute', admin.getName(), player.getName(), '')

    return True



def on_chat_message(player_id, msg_text, channel, flags):
    """Respaldo: castiga al muteado que igual logro hablar en canal restringido."""
    if player_id == -1 or not _muted:
        return

    try:
        player = bf2.playerManager.getPlayerByIndex(player_id)
    except Exception:
        return
    if player is None:
        return

    player_hash = _player_hash(player)
    if player_hash is None:
        return

    scopes = _muted.get(player_hash)
    if not scopes or not scope_covers_channel(scopes, channel):
        return

    # Si tenia mute all y hablo en global, reafirmar el HUD (por si el cliente lo ignoro).
    if 'all' in scopes and str(channel or '').strip().lower() == 'global':
        disable_allchat_for_player(player)

    now = time.time()
    if now - _last_punish.get(player_hash, 0) < _PUNISH_COOLDOWN_SEC:
        return
    _last_punish[player_hash] = now

    try:
        radmin.personalMessage(
            'Estas silenciado: no puedes hablar en este chat. Si insistes seras penalizado con autokick.',
            player,
        )
        # Primera infraccion: solo advertencia. Si insiste, autokick.
        if player_hash in _warned:
            radmin.kickPlayer(
                player,
                'Insistir en hablar mientras estaba silenciado.',
                True,
            )
        else:
            _warned.add(player_hash)
    except Exception:
        pass



# Mensaje al bloquear switch al equipo de bots en coop.
_MSG_COOP_BOT_TEAM = (
    'En mapas coop no podes pasarte al equipo de los bots.'
)
_MSG_COOP_BOT_TEAM_HUD = (
    'Advertencia:\nEn mapas coop no podes pasarte al equipo de los bots.'
)
_MSG_COOP_BOT_TEAM_HUD_SEC = 8
# Delay tras RoundStart: los bots a veces spawnean despues de los humanos.
_COOP_BOT_TEAM_SWEEP_DELAY_SEC = 5.0


def _is_coop_map():
    """True solo en gamemode coop (gpm_coop)."""
    if rcore is None:
        return False
    try:
        return str(rcore.getGameMode()).lower() == 'coop'
    except Exception:
        return False


def _count_humans_and_bots():
    """Cuenta humanos y AI por equipo. Retorna (h1, h2, b1, b2)."""
    h1 = h2 = b1 = b2 = 0
    if bf2 is None:
        return h1, h2, b1, b2
    try:
        players = bf2.playerManager.getPlayers()
    except Exception:
        return h1, h2, b1, b2
    for player in players:
        try:
            if not player.isValid():
                continue
            team = int(player.getTeam())
            if player.isAIPlayer():
                if team == 1:
                    b1 += 1
                elif team == 2:
                    b2 += 1
            else:
                if team == 1:
                    h1 += 1
                elif team == 2:
                    h2 += 1
        except Exception:
            continue
    return h1, h2, b1, b2


def _coop_bots_team():
    """
    Equipo considerado 'de bots' en coop.
    Prioridad: mas AI; si empate, el de menos humanos; 0 si no se puede decidir.
    """
    h1, h2, b1, b2 = _count_humans_and_bots()
    if b1 == 0 and b2 == 0:
        return 0
    if b1 > b2:
        return 1
    if b2 > b1:
        return 2
    if h1 < h2:
        return 1
    if h2 < h1:
        return 2
    return 0


def _warn_coop_bot_team(player):
    """Aviso HUD + PM al jugador que intento ir al equipo de bots."""
    if rmemory is not None:
        try:
            rmemory.HudVarWriteEventWstringWithTimedShowvar(
                player,
                'PythonGameWarning',
                _MSG_COOP_BOT_TEAM_HUD,
                _MSG_COOP_BOT_TEAM_HUD_SEC,
            )
        except Exception:
            pass
    if radmin is not None:
        try:
            radmin.personalMessage(_MSG_COOP_BOT_TEAM, player)
        except Exception:
            pass


def _bounce_human_off_bots_team(player, warn=True):
    """
    Si el humano esta en el equipo de bots en coop, lo manda al otro.
    Los admins pueden saltarse el bloqueo.
    Retorna True si hizo el bounce.
    """
    if not _is_coop_map():
        return False
    if player is None:
        return False
    try:
        if not player.isValid() or player.isAIPlayer():
            return False
    except Exception:
        return False
    # Admins (hash en adm_adminHashes / lite) pueden ir al equipo de bots.
    if getattr(player, 'isAdmin', False):
        return False

    bots_team = _coop_bots_team()
    if bots_team not in (1, 2):
        return False

    try:
        current = int(player.getTeam())
    except Exception:
        return False
    if current != bots_team:
        return False

    other = 2 if bots_team == 1 else 1
    if rcore is not None and hasattr(rcore, 'getOtherTeam'):
        try:
            other = int(rcore.getOtherTeam(bots_team))
        except Exception:
            pass

    try:
        player.setTeam(other)
    except Exception:
        return False

    if warn:
        _warn_coop_bot_team(player)
    return True


def _sweep_humans_off_bots_team():
    """Revisa todos los humanos y los saca del equipo de bots si hace falta."""
    if not _is_coop_map() or bf2 is None:
        return
    try:
        players = bf2.playerManager.getPlayers()
    except Exception:
        return
    for player in players:
        try:
            _bounce_human_off_bots_team(player, warn=True)
        except Exception:
            continue


def on_player_change_teams_coop(player, human_has_spawned):
    """Bloquea pasar al equipo de bots en mapas coop."""
    _bounce_human_off_bots_team(player, warn=True)


def on_round_start():
    """Al comenzar una ronda nueva, quita mutes, TK counts y marcas anti-robo."""
    _clear_all_spec()
    removed = clear_round_mutes()
    clear_round_tk_counts()
    clear_round_kit_steal_state()

    # Coop: barrido tardio por si los bots spawnean despues del RoundStart.
    if _is_coop_map() and rtimer is not None:
        try:
            rtimer.fireOnce(
                _sweep_humans_off_bots_team,
                _COOP_BOT_TEAM_SWEEP_DELAY_SEC,
            )
        except Exception:
            pass

    if removed == 0:
        return

    # Restaurar el estado normal de allchat a quienes siguen conectados.
    try:
        players = bf2.playerManager.getPlayers()
    except Exception:
        players = []
    for player in players:
        try:
            if not player.isAIPlayer():
                restore_allchat_for_player(player)
        except Exception:
            continue

    radmin.adminPM(
        'Se quitaron %d mute(s) al comenzar la nueva ronda.' % removed,
    )


def init():
    """Registra comandos, wrap de allchat y handlers al iniciar el mod."""
    global _orig_send_allchat_status
    global _auto_tk_kick_active
    if not _IN_GAME:
        return

    # Estado inicial del kick por TK (independiente de !aa).
    if ras is not None:
        _auto_tk_kick_active = bool(getattr(ras, 'adm_autoTkKick', True))
    else:
        _auto_tk_kick_active = True

    # Nivel desde adm_adminPowerLevels (fallback si falta la clave en config).
    # 0 Dueño | 1 Administrador | 2 Moderador | 777 Everyone
    def _power(name, default):
        if ras is None:
            return default
        return ras.adm_adminPowerLevels.get(name, default)

    radmin.addCommand('mute', command_mute, _power('mute', 1))
    radmin.addCommand('unmute', command_unmute, _power('unmute', 1))
    radmin.addCommand('ak', command_ak, _power('ak', 1))
    radmin.addCommand('spec', command_spec, _power('spec', 1))
    radmin.addCommand('unspec', command_unspec, _power('unspec', 1))
    host.registerHandler('ChatMessage', on_chat_message, 1)
    host.registerHandler('RoundStart', on_round_start, 1)
    # Mismo evento que usa el logger de TEAMKILL en realityadmin.
    host.registerHandler('PlayerKilled', on_player_killed, 1)
    # Anti-robo kit especial tras TK.
    host.registerHandler('PickupKit', on_pickup_kit, 1)
    host.registerHandler('DropKit', on_drop_kit, 1)
    host.registerHandler('PlayerDisconnect', on_player_disconnect, 1)
    # Coop: no permitir humanos en el equipo de bots.
    host.registerHandler('PlayerChangeTeams', on_player_change_teams_coop, 1)
    # Evitar que broadcasts del servidor reactiven allchat a muteados.
    if _orig_send_allchat_status is None and hasattr(radmin, 'sendAllChatStatus'):
        _orig_send_allchat_status = radmin.sendAllChatStatus
        radmin.sendAllChatStatus = _wrapped_send_allchat_status

    # Refuerzo periodico del bloqueo HUD (cierra la ventana del bypass).
    rtimer.repeatingTask(_reapply_mutes, _REAPPLY_INTERVAL_SEC)


if _IN_GAME:
    init()
