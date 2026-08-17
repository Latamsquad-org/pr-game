# latamtrackersummary.py - agrega SquadName al JSON del Reality Tracker
# Motivo: CreateJson solo escribe Squad (numero); el nombre vive en RCON/cache.
# ASCII only (Python 2 / BF2).
import host
import realitycore as rcore
import realitytracker

# Cache propio: no se borra al vaciar la escuadra (g_squadNames si).
_squad_names = {1: {}, 2: {}}
_IN_GAME = False
try:
    import bf2
    _IN_GAME = True
except Exception:
    _IN_GAME = False


def _parse_list_squads_line(line):
    """Parsea una linea de squadManager.listSquads (mismo criterio que realitycore)."""
    try:
        squad = int(line[3])
        name = ' '.join(line.split(' ')[1:-2])
        if squad >= 1 and squad <= 9 and name:
            return (squad, name)
    except Exception:
        pass
    return (None, None)


def _refresh_names_from_rcon():
    """Actualiza nombres desde RCON (incluye renombres durante la ronda)."""
    for team in (1, 2):
        try:
            raw = host.rcon_invoke('squadManager.listSquads ' + str(team))
        except Exception:
            continue
        if not raw:
            continue
        lines = raw.split('\n')
        if lines and lines[-1] == '':
            lines = lines[:-1]
        for line in lines:
            squad, name = _parse_list_squads_line(line)
            if squad is not None:
                _squad_names[team][squad] = name


def _name_from_core_cache(team, squad):
    """Lee g_squadNames si sigue cargado (sin exigir jugadores vivos)."""
    try:
        cached = rcore.g_squadNames.get(team, {}).get(squad)
        if cached:
            return cached
    except Exception:
        pass
    return None


def get_tracked_squad_name(team, squad):
    """Devuelve el mejor nombre conocido para team/squad, o ''.ASCII."""
    try:
        team = int(team)
        squad = int(squad)
    except Exception:
        return ''
    if team not in (1, 2) or squad < 1 or squad > 9:
        return ''
    name = _squad_names.get(team, {}).get(squad)
    if name:
        return name
    name = _name_from_core_cache(team, squad)
    if name:
        _squad_names[team][squad] = name
        return name
    try:
        # Puede devolver '' si la escuadra ya esta vacia al fin de ronda.
        name = rcore.getSquadName(team, squad)
        if name:
            _squad_names[team][squad] = name
            return name
    except Exception:
        pass
    return ''


def on_squad_created(player, team, squad, name):
    """Guarda el nombre al crear escuadra (evento SquadCreated)."""
    try:
        team = int(team)
        squad = int(squad)
    except Exception:
        return
    if team not in (1, 2) or squad < 1 or squad > 9:
        return
    if name:
        _squad_names[team][squad] = str(name)


def on_round_start(safe=None):
    """Limpia cache al empezar ronda."""
    _squad_names[1] = {}
    _squad_names[2] = {}


# --- Monkey-patch JsonMaker (CreateJson llama cls.JsonOnePlayer en runtime) ---
_orig_json_one = realitytracker.JsonMaker.__dict__['JsonOnePlayer'].__func__
_orig_create_json = realitytracker.JsonMaker.__dict__['CreateJson'].__func__


@classmethod
def _json_one_player_with_name(cls, p, disconnected):
    out = _orig_json_one(cls, p, disconnected)
    if not isinstance(out, dict):
        return out
    try:
        squad = int(getattr(p, 'squad', 0) or 0)
        team = int(getattr(p, 'team', 0) or 0)
        if squad > 0 and team in (1, 2):
            sn = get_tracked_squad_name(team, squad)
            if sn:
                out['SquadName'] = sn
    except Exception:
        pass
    return out


@classmethod
def _create_json_with_names(cls):
    # Refresco RCON antes de serializar (nombres al cierre de ronda).
    try:
        _refresh_names_from_rcon()
    except Exception:
        pass
    return _orig_create_json(cls)


def init():
    """Registra hooks y aplica el parche al JSON del tracker."""
    realitytracker.JsonMaker.JsonOnePlayer = _json_one_player_with_name
    realitytracker.JsonMaker.CreateJson = _create_json_with_names
    try:
        host.registerHandler('SquadCreated', on_squad_created, 1)
    except Exception:
        pass
    try:
        host.registerHandler('RoundStart', on_round_start, 1)
    except Exception:
        pass


if _IN_GAME:
    init()
