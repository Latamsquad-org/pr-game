# -*- coding: utf-8 -*-
# latamlink.py - vincula Discord↔PR con !link en el chat

import json
import os
import subprocess
import tempfile
import time

try:
    import urllib2
except ImportError:
    import urllib.request as urllib2

try:
    import ssl
except ImportError:
    ssl = None

# Misma API key / server_id que latamstats (se importan si está disponible).
LINK_URL = 'https://stats.latamsquad.org/api/link.php'
LINK_TIMEOUT = 4
LINK_COOLDOWN_SEC = 15
LINK_LOG = 'C:/prbf2_db/latamlink.log'

try:
    import latamstats as _ls
    LINK_API_KEY = getattr(_ls, 'STATS_API_KEY', 'CHANGE_ME')
    LINK_SERVER_ID = getattr(_ls, 'STATS_SERVER_ID', 'pr-1')
except ImportError:
    LINK_API_KEY = 'CHANGE_ME'
    LINK_SERVER_ID = 'pr-1'

try:
    import bf2
    import host
    import realityserver
    import realitydebug as rdebug
    _IN_GAME = True
except ImportError:
    bf2 = None
    host = None
    realityserver = None
    rdebug = None
    _IN_GAME = False

# player_id (hash) -> timestamp último intento
_last_link_attempt = {}


def _log(message):
    """Escribe resultado a disco (visible aunque rdebug esté apagado)."""
    try:
        line = '%s %s\n' % (
            time.strftime('%Y-%m-%dT%H:%M:%SZ', time.gmtime()),
            message,
        )
        log_dir = os.path.dirname(LINK_LOG)
        if log_dir and not os.path.isdir(log_dir):
            os.makedirs(log_dir)
        with open(LINK_LOG, 'a') as handle:
            handle.write(line)
    except Exception:
        pass


def _encode_json_body(payload):
    body = json.dumps(payload)
    if not isinstance(body, type(b'')):
        try:
            body = body.encode('utf-8')
        except Exception:
            pass
    return body


def _post_link(body):
    """POST a api/link.php; urllib primero, curl.exe como fallback."""
    req = urllib2.Request(LINK_URL, data=body)
    req.add_header('Content-Type', 'application/json')
    req.add_header('X-API-Key', LINK_API_KEY)
    kwargs = {'timeout': LINK_TIMEOUT}
    if ssl is not None and hasattr(ssl, '_create_unverified_context'):
        kwargs['context'] = ssl._create_unverified_context()
    try:
        resp = urllib2.urlopen(req, **kwargs)
        raw = resp.read()
        code = getattr(resp, 'code', 200)
        if code >= 200 and code < 300:
            return (True, raw)
        return (False, 'http %s %s' % (code, raw))
    except Exception as exc:
        # Fallback curl (TLS moderno en Windows / Python embebido de PR).
        tmp_path = None
        try:
            fd, tmp_path = tempfile.mkstemp(suffix='.json')
            os.close(fd)
            with open(tmp_path, 'wb') as handle:
                handle.write(body)
            cmd = [
                'curl.exe', '-sS', '-X', 'POST', LINK_URL,
                '-H', 'Content-Type: application/json',
                '-H', 'X-API-Key: %s' % LINK_API_KEY,
                '--data-binary', '@%s' % tmp_path,
                '--max-time', str(LINK_TIMEOUT),
            ]
            proc = subprocess.Popen(
                cmd,
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE,
            )
            out, err = proc.communicate()
            out_text = out if isinstance(out, type('')) else out.decode('utf-8', 'replace')
            if proc.returncode == 0 and '"ok"' in out_text.replace(' ', ''):
                return (True, out_text)
            return (False, 'curl rc=%s out=%s err=%s prev=%s' % (
                proc.returncode, out, err, exc,
            ))
        except Exception as exc2:
            return (False, 'curl error: %s | urllib: %s' % (exc2, exc))
        finally:
            if tmp_path and os.path.isfile(tmp_path):
                try:
                    os.remove(tmp_path)
                except Exception:
                    pass


def parse_link_command(msg_text):
    """
    Detecta !link + código.
    Retorna el código normalizado (lower) o None.
    """
    if msg_text is None:
        return None
    text = str(msg_text).strip()
    # Quitar prefijos HUD del motor PR (mismo patrón que realityadmin).
    for prefix in (
        'HUD_TEXT_CHAT_TEAM',
        'HUD_TEXT_CHAT_SQUAD',
        'HUD_TEXT_CHAT_DEADPREFIX',
        'HUD_CHAT_DEADPREFIX',
        '* ',
    ):
        if text.startswith(prefix):
            text = text[len(prefix):].lstrip()
    if not text.startswith('!'):
        return None
    parts = text[1:].split()
    if len(parts) < 2:
        return None
    cmd = parts[0].lower()
    if cmd != 'link':
        return None
    code = parts[1].strip().lower()
    # 10 chars a-z0-9 (el server web valida con más rigor).
    if len(code) != 10:
        return None
    for ch in code:
        if not (('a' <= ch <= 'z') or ('0' <= ch <= '9')):
            return None
    return code


def request_link(player_id, code, server_id=None):
    """Llama a la API; retorna (linked:bool, message:str)."""
    if LINK_API_KEY == 'CHANGE_ME':
        return (False, 'Link deshabilitado (API key)')
    sid = server_id if server_id is not None else LINK_SERVER_ID
    payload = {
        'server_id': sid,
        'player_id': str(player_id),
        'code': str(code),
    }
    body = _encode_json_body(payload)
    ok, raw = _post_link(body)
    _log('player=%s code=%s ok=%s raw=%s' % (player_id, code, ok, raw))
    if not ok:
        return (False, 'No se pudo contactar latamstats')
    try:
        raw_text = raw if isinstance(raw, type('')) else raw.decode('utf-8', 'replace')
        data = json.loads(raw_text)
    except Exception:
        return (False, 'Respuesta inválida de latamstats')
    if not data.get('ok'):
        return (False, str(data.get('error') or 'Error de vínculo'))
    if data.get('linked'):
        return (True, 'Cuenta vinculada con Discord')
    return (False, str(data.get('error') or 'Código inválido o vencido'))


def _pm(player, msg):
    """Mensaje privado al jugador (mismo canal que personalMessage)."""
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


def on_chat_message(player_id, msg_text, channel, flags):
    """Handler ChatMessage: !link <codigo>."""
    if player_id == -1:
        return
    code = parse_link_command(msg_text)
    if code is None:
        return

    try:
        player = bf2.playerManager.getPlayerByIndex(player_id)
    except Exception:
        return
    if player is None:
        return

    try:
        player_hash = realityserver.getPlayerHash(player)
    except Exception:
        player_hash = None
    if player_hash is None or player_hash == '' or player_hash is True or player_hash is False:
        _pm(player, 'No se pudo obtener tu ID de jugador')
        return

    now = time.time()
    last = _last_link_attempt.get(player_hash, 0)
    if now - last < LINK_COOLDOWN_SEC:
        _pm(player, 'Espera unos segundos antes de reintentar')
        return
    _last_link_attempt[player_hash] = now

    linked, message = request_link(player_hash, code)
    _pm(player, message)
    if _IN_GAME and rdebug:
        try:
            rdebug.debugMessage(
                'latamlink linked=%s player=%s' % (linked, player_hash),
                'latamlink',
            )
        except Exception:
            pass


def init():
    if _IN_GAME:
        host.registerHandler('ChatMessage', on_chat_message, 1)


if _IN_GAME:
    init()
