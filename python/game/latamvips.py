# latamvips.py - slot reservado por hash y saludo VIP al spawn

import re

try:
    import bf2
    import host
    import realityserver
    _IN_GAME = True
except ImportError:
    bf2 = None
    host = None
    realityserver = None
    _IN_GAME = False

# reservedSlots.addHash "hash32hex" ["Mensaje opcional"] rem Nombre
_ADD_HASH_RE = re.compile(
    r'reservedSlots\.addHash\s+"([0-9a-fA-F]{32})"(?:\s+"([^"]*)")?',
    re.IGNORECASE,
)
# Quita comentario rem al final de la linea (solo para humanos, no para el motor).
_TRAILING_REM_RE = re.compile(r'\s+rem\s+.*$', re.IGNORECASE)

_vip_hashes = set()
_vip_messages = {}


def _hashes_path():
    return '%s/settings/reservedslots_hashes.con' % host.sgl_getModDirectory()


def _safe_comment_name(name):
    """Nombre limpio para comentario rem (ASCII printable, sin saltos)."""
    if name is None:
        return ''
    text = str(name).replace('\r', ' ').replace('\n', ' ').strip()
    cleaned = []
    for ch in text:
        o = ord(ch)
        if 32 <= o <= 126:
            cleaned.append(ch)
        else:
            cleaned.append('?')
    return ''.join(cleaned).strip()


def _build_hash_line(player_hash, message, player_name):
    """Arma la linea addHash con mensaje opcional y rem Nombre."""
    line = 'reservedSlots.addHash "%s"' % player_hash
    if message:
        line = '%s "%s"' % (line, message)
    comment_name = _safe_comment_name(player_name)
    if comment_name:
        line = '%s rem %s' % (line, comment_name)
    return line


def annotate_hash_name(player_hash, player_name):
    """
    Actualiza reservedslots_hashes.con poniendo rem Nombre en la linea del hash.
    Solo para consulta humana; el parser ignora el rem al final.
    """
    if not player_hash or not player_name:
        return False
    player_hash = str(player_hash).lower()
    path = _hashes_path()
    try:
        handle = open(path, 'r')
        raw_lines = handle.readlines()
        handle.close()
    except IOError:
        return False

    changed = False
    new_lines = []
    for raw in raw_lines:
        stripped = raw.strip()
        if not stripped or stripped.lower().startswith('rem'):
            new_lines.append(raw)
            continue
        match = _ADD_HASH_RE.search(stripped)
        if not match or match.group(1).lower() != player_hash:
            new_lines.append(raw)
            continue
        message = match.group(2)
        if message is not None:
            message = message.strip()
        else:
            message = ''
        new_content = _build_hash_line(player_hash, message, player_name)
        # Conserva salto de linea original si existia.
        if raw.endswith('\r\n'):
            ending = '\r\n'
        elif raw.endswith('\n'):
            ending = '\n'
        else:
            ending = ''
        if stripped != new_content:
            changed = True
        new_lines.append(new_content + ending)

    if not changed:
        return False
    try:
        handle = open(path, 'w')
        handle.writelines(new_lines)
        handle.close()
    except IOError:
        return False
    return True


def load_vip_hashes():
    """Lee hashes VIP y mensajes opcionales desde reservedslots_hashes.con."""
    global _vip_hashes
    global _vip_messages
    hashes = set()
    messages = {}
    try:
        handle = open(_hashes_path(), 'r')
    except IOError:
        _vip_hashes = hashes
        _vip_messages = messages
        return hashes, messages
    try:
        for raw_line in handle:
            line = raw_line.strip()
            if not line or line.lower().startswith('rem'):
                continue
            # Ignora rem Nombre al final de la linea addHash.
            line = _TRAILING_REM_RE.sub('', line).strip()
            match = _ADD_HASH_RE.search(line)
            if not match:
                continue
            player_hash = match.group(1).lower()
            hashes.add(player_hash)
            custom = match.group(2)
            if custom is not None and custom.strip():
                messages[player_hash] = custom.strip()
    finally:
        try:
            handle.close()
        except Exception:
            pass
    _vip_hashes = hashes
    _vip_messages = messages
    return hashes, messages


def _player_nick(player):
    """Nick sin tag (formato TAG nombre)."""
    try:
        parts = player.getName().split(' ', 1)
        if len(parts) == 2:
            return parts[1]
    except Exception:
        pass
    return player.getName()


def _player_hash(player):
    try:
        player_hash = realityserver.getPlayerHash(player)
    except Exception:
        return None
    if not player_hash or player_hash is True:
        return None
    return str(player_hash).lower()


def _is_vip_hash(player_hash):
    if not player_hash:
        return False
    return str(player_hash).lower() in _vip_hashes


def _open_slot_limit():
    """Cupos para no-VIP = maxPlayers - numReservedSlots (igual que el motor BF2)."""
    try:
        max_players = int(host.rcon_invoke('sv.maxPlayers').replace('\r\n', '').strip())
        reserved = int(host.rcon_invoke('sv.numReservedSlots').replace('\r\n', '').strip())
    except Exception:
        return 0
    if reserved < 0:
        reserved = 0
    return max(0, max_players - reserved)


def _register_engine_nick(player):
    """Registra el nick actual en el motor (addNick) como respaldo nativo."""
    nick = _player_nick(player)
    if not nick:
        return
    host.rcon_invoke('reservedSlots.addNick "%s"' % nick)


def _say_all(msg):
    text = '\xc2\xa7C1001' + str(msg)
    if len(text) > 240:
        text = text[:239]
    host.rcon_invoke('game.sayall "%s"' % text)


def on_player_connect(player):
    if player is None or player.isAIPlayer():
        return
    player.latamvip_welcomed = False
    load_vip_hashes()
    player_hash = _player_hash(player)
    if not player_hash:
        return
    if _is_vip_hash(player_hash):
        player.latamvip_reserved = True
        _register_engine_nick(player)
        # Anota el nombre en el .con (comentario rem) para consulta humana.
        try:
            annotate_hash_name(player_hash, player.getName())
        except Exception:
            pass
        return
    player.latamvip_reserved = False
    open_slots = _open_slot_limit()
    if open_slots <= 0:
        return
    try:
        n_players = bf2.playerManager.getNumberOfPlayers()
    except Exception:
        return
    if n_players > open_slots:
        host.rcon_invoke('admin.kickPlayer %d' % player.index)


def on_player_spawn(player, soldier):
    if player is None or player.isAIPlayer():
        return
    if getattr(player, 'latamvip_welcomed', False):
        return
    load_vip_hashes()
    player_hash = _player_hash(player)
    if not player_hash:
        return
    msg = _vip_messages.get(player_hash)
    if not msg:
        return
    player.latamvip_welcomed = True
    msg = msg.replace('[playername]', player.getName())
    _say_all(msg)


def init():
    if not _IN_GAME:
        return
    load_vip_hashes()
    host.registerHandler('PlayerConnect', on_player_connect, 2)
    host.registerHandler('PlayerSpawn', on_player_spawn, 1)


if _IN_GAME:
    init()
