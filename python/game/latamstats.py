# -*- coding: utf-8 -*-
# latamstats.py - estadísticas PR → stats.latamsquad.org (helpers, GeoIP, upload, hooks)

import json
import re
import os
import sqlite3
import struct
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

try:
    from latamtreasures import TREASURE_XP_BONUS
except ImportError:
    TREASURE_XP_BONUS = 5000

# Config placeholders (ajustar en deploy del servidor)
STATS_DB_PATH = 'C:/prbf2_db/stats.sqlite3'
STATS_UPLOAD_URL = 'https://stats.latamsquad.org/api/upload.php'
STATS_API_KEY = 'xYUvckvpeeUW0MLTwAFcKZeyi5SYGBv8'
# Instancia fisica prbf2_1 = servidor #1 (tabla stats1).
STATS_SERVER_ID = 'pr-1'
STATS_UPLOAD_TIMEOUT = 8
STATS_UPLOAD_LOG = 'C:/prbf2_db/latamstats_upload.log'
# Cooldown de !stats por jugador (segundos).
STATS_CMD_COOLDOWN_SEC = 10
# Base GeoIP: IP2Location DB1 (.bin). Fallback CSV opcional.
STATS_GEOIP_PATH = 'C:/prbf2_db/geo_ip.bin'

# Tabla SQLite por servidor (stats.sqlite3 compartido, una tabla por instancia PR).
STATS_SERVER_TABLES = {
    'pr-1': 'stats1',
    'pr-2': 'stats2',
    'pr-3': 'stats3',
    'pr-4': 'stats4',
}
STATS_TABLE_NAMES = ('stats1', 'stats2', 'stats3', 'stats4')


# ------------------------------------------------------------------
# GeoIP: país ISO-2 por IPv4
# Prioridad: STATS_GEOIP_PATH (.bin IP2Location) -> CSV legacy opcional
# ------------------------------------------------------------------
DEFAULT_GEOIP_CSV = 'C:/prbf2_db/GeoIPCountryWhois.csv'

_CACHE = {
    'path': None,
    'mtime': None,
    'mode': None,
    'bin_meta': None,
    'ranges': None,
}

_IPV4_RE = re.compile(
    r'^(\d{1,3})\.(\d{1,3})\.(\d{1,3})\.(\d{1,3})$'
)


def normalize_ip_address(addr):
    """Extrae IPv4 de 'ip', 'ip:port' o vacío. IPv6 → ''."""
    if addr is None:
        return ''
    text = str(addr).strip()
    if text == '':
        return ''

    if text.count(':') == 1:
        text = text.split(':', 1)[0].strip()

    match = _IPV4_RE.match(text)
    if match is None:
        return ''

    parts = []
    for part in match.groups():
        value = int(part)
        if value < 0 or value > 255:
            return ''
        parts.append(value)

    return '%d.%d.%d.%d' % tuple(parts)


def ipv4_to_int(ip):
    """IPv4 dotted → entero 32-bit, o None."""
    ip = normalize_ip_address(ip)
    if ip == '':
        return None
    a, b, c, d = [int(x) for x in ip.split('.')]
    return (a << 24) + (b << 16) + (c << 8) + d


def _u8(data, off):
    value = data[off]
    if not isinstance(value, int):
        value = ord(value)
    return value


def _u32(data, off):
    return struct.unpack_from('<I', data, off)[0]


def _country_at(data, ptr):
    """Lee ISO-2 en puntero IP2Location (byte de longitud + letras)."""
    if ptr < 0 or ptr + 3 > len(data):
        return ''
    length = _u8(data, ptr)
    if length < 1 or length > 3:
        # Sin prefijo: intentar 2 letras directas
        c0 = _u8(data, ptr)
        c1 = _u8(data, ptr + 1)
        if 65 <= c0 <= 90 and 65 <= c1 <= 90:
            return chr(c0) + chr(c1)
        return ''
    start = ptr + 1
    if start + length > len(data):
        return ''
    chars = []
    for i in range(length):
        ch = _u8(data, start + i)
        if not (65 <= ch <= 90 or 97 <= ch <= 122):
            return ''
        chars.append(chr(ch))
    cc = ''.join(chars).upper()
    if len(cc) == 2:
        return cc
    return ''


def _load_ip2location_bin(path):
    """Carga IP2Location DB1 (.bin)."""
    handle = open(path, 'rb')
    try:
        data = handle.read()
    finally:
        handle.close()

    if len(data) < 32:
        return None

    cols = _u8(data, 1)
    if cols < 2:
        return None

    ipv4_count = _u32(data, 5)
    ipv4_addr = _u32(data, 9)   # base 1-based de filas IPv4
    ipv4_index = _u32(data, 21)  # índice IPv4 (offset 0-based en este BIN)
    col_size = cols * 4

    if ipv4_count <= 0 or ipv4_addr <= 0:
        return None

    return {
        'data': data,
        'cols': cols,
        'col_size': col_size,
        'ipv4_count': ipv4_count,
        'ipv4_addr': ipv4_addr,
        'ipv4_index': ipv4_index,
    }


def _lookup_ip2location(ip_int, meta):
    """Búsqueda IPv4 en IP2Location DB1 → código ISO-2."""
    data = meta['data']
    col_size = meta['col_size']
    count = meta['ipv4_count']
    base = meta['ipv4_addr']  # 1-based
    index_base = meta['ipv4_index']

    low = 0
    high = count

    # Índice por octeto alto (ip >> 16): 8 bytes (low, high) por entrada
    if index_base > 0:
        idx_off = index_base + ((ip_int >> 16) * 8)
        if idx_off + 8 <= len(data):
            i_low = _u32(data, idx_off)
            i_high = _u32(data, idx_off + 4)
            if 0 <= i_low <= i_high <= count:
                low = i_low
                high = i_high

    while low <= high:
        mid = (low + high) // 2
        row0 = (base - 1) + (mid * col_size)
        if row0 < 0 or row0 + 8 > len(data):
            return ''

        ip_from = _u32(data, row0)
        next0 = row0 + col_size
        if next0 + 4 <= len(data):
            ip_to = _u32(data, next0)
        else:
            ip_to = 0xFFFFFFFF

        if ip_int < ip_from:
            high = mid - 1
            continue
        if ip_int >= ip_to:
            low = mid + 1
            continue

        ptr = _u32(data, row0 + 4)
        return _country_at(data, ptr)

    return ''


def _parse_csv_line(line):
    line = line.strip()
    if line == '' or line.startswith('#'):
        return None

    raw = line.replace('"', '')
    parts = [p.strip() for p in raw.split(',')]
    if len(parts) < 3:
        return None

    if len(parts) >= 5:
        try:
            start = int(parts[2])
            end = int(parts[3])
            cc = parts[4].upper()
        except (TypeError, ValueError):
            return None
    else:
        try:
            start = int(parts[0])
            end = int(parts[1])
            cc = parts[2].upper()
        except (TypeError, ValueError):
            return None

    if len(cc) != 2 or not cc.isalpha():
        return None
    if start < 0 or end < start:
        return None

    return (start, end, cc)


def load_geoip_ranges(csv_path):
    if not csv_path or not os.path.isfile(csv_path):
        return []

    ranges = []
    try:
        handle = open(csv_path, 'r')
        try:
            for line in handle:
                parsed = _parse_csv_line(line)
                if parsed is not None:
                    ranges.append(parsed)
        finally:
            handle.close()
    except Exception:
        return []

    ranges.sort(key=lambda item: item[0])
    return ranges


def _resolve_geoip_path(explicit_path=None):
    candidates = []
    if explicit_path:
        candidates.append(explicit_path)
    candidates.append(STATS_GEOIP_PATH)
    candidates.append(DEFAULT_GEOIP_CSV)

    for path in candidates:
        if path and os.path.isfile(path):
            return path
    return None


def _get_db(explicit_path=None):
    path = _resolve_geoip_path(explicit_path)
    if path is None:
        reset_geoip_cache()
        return None

    mtime = None
    try:
        mtime = os.path.getmtime(path)
    except Exception:
        mtime = None

    if (
        _CACHE['path'] == path
        and _CACHE['mtime'] == mtime
        and _CACHE['mode'] is not None
    ):
        return _CACHE

    lower = path.lower()
    if lower.endswith('.bin'):
        meta = _load_ip2location_bin(path)
        _CACHE['path'] = path
        _CACHE['mtime'] = mtime
        _CACHE['mode'] = 'bin' if meta else None
        _CACHE['bin_meta'] = meta
        _CACHE['ranges'] = None
    else:
        ranges = load_geoip_ranges(path)
        _CACHE['path'] = path
        _CACHE['mtime'] = mtime
        _CACHE['mode'] = 'csv' if ranges else None
        _CACHE['bin_meta'] = None
        _CACHE['ranges'] = ranges

    return _CACHE


def _lookup_csv(ip_int, ranges):
    if not ranges:
        return ''
    lo = 0
    hi = len(ranges) - 1
    best = None
    while lo <= hi:
        mid = (lo + hi) // 2
        start, end, cc = ranges[mid]
        if start <= ip_int:
            best = mid
            lo = mid + 1
        else:
            hi = mid - 1
    if best is None:
        return ''
    start, end, cc = ranges[best]
    if start <= ip_int <= end:
        return cc
    return ''


def lookup_country_code(ip, db_path=None):
    """Devuelve código ISO-2 (ej. AR) o ''."""
    ip_int = ipv4_to_int(ip)
    if ip_int is None:
        return ''

    cache = _get_db(db_path)
    if cache is None or cache.get('mode') is None:
        return ''

    if cache['mode'] == 'bin' and cache.get('bin_meta'):
        try:
            return _lookup_ip2location(ip_int, cache['bin_meta']) or ''
        except Exception:
            return ''

    if cache['mode'] == 'csv':
        return _lookup_csv(ip_int, cache.get('ranges') or [])

    return ''


def reset_geoip_cache():
    """Limpia cache GeoIP (útil al recargar el BIN)."""
    _CACHE['path'] = None
    _CACHE['mtime'] = None
    _CACHE['mode'] = None
    _CACHE['bin_meta'] = None
    _CACHE['ranges'] = None



def _encode_json_body(payload):
    """Serializa JSON como bytes/str apto para urllib2 (Py2) y urllib (Py3)."""
    body = json.dumps(payload)
    # Py2: unicode -> str utf-8; Py3: str -> bytes
    if not isinstance(body, type(b'')):
        try:
            body = body.encode('utf-8')
        except Exception:
            pass
    return body


def _log_upload(message):
    """Escribe resultado de upload a disco (visible aunque rdebug esté apagado)."""
    try:
        line = '%s %s\n' % (
            time.strftime('%Y-%m-%dT%H:%M:%SZ', time.gmtime()),
            message,
        )
        log_dir = os.path.dirname(STATS_UPLOAD_LOG)
        if log_dir and not os.path.isdir(log_dir):
            os.makedirs(log_dir)
        with open(STATS_UPLOAD_LOG, 'a') as handle:
            handle.write(line)
    except Exception:
        pass


def _upload_via_urllib(body):
    """POST con urllib2; usa SSL sin verificación si el runtime lo permite."""
    req = urllib2.Request(STATS_UPLOAD_URL, data=body)
    req.add_header('Content-Type', 'application/json')
    req.add_header('X-API-Key', STATS_API_KEY)
    kwargs = {'timeout': STATS_UPLOAD_TIMEOUT}
    if ssl is not None and hasattr(ssl, '_create_unverified_context'):
        kwargs['context'] = ssl._create_unverified_context()
    resp = urllib2.urlopen(req, **kwargs)
    code = getattr(resp, 'code', 200)
    raw = resp.read()
    if code >= 200 and code < 300:
        return (True, raw)
    return (False, 'http %s %s' % (code, raw))


def _upload_via_curl(body):
    """Fallback Windows: curl.exe (mejor HTTPS/TLS que el Python embebido de PR)."""
    tmp_path = None
    try:
        fd, tmp_path = tempfile.mkstemp(suffix='.json')
        os.close(fd)
        with open(tmp_path, 'wb') as handle:
            handle.write(body)
        cmd = [
            'curl.exe', '-sS', '-X', 'POST', STATS_UPLOAD_URL,
            '-H', 'Content-Type: application/json',
            '-H', 'X-API-Key: %s' % STATS_API_KEY,
            '--data-binary', '@%s' % tmp_path,
            '--max-time', str(STATS_UPLOAD_TIMEOUT),
        ]
        proc = subprocess.Popen(
            cmd,
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
        )
        out, err = proc.communicate()
        out_text = out if isinstance(out, type('')) else out.decode('utf-8', 'replace')
        compact = out_text.replace(' ', '').replace('\n', '')
        if proc.returncode == 0 and '"ok":true' in compact:
            return (True, out_text)
        return (False, 'curl rc=%s out=%s err=%s' % (proc.returncode, out, err))
    finally:
        if tmp_path and os.path.isfile(tmp_path):
            try:
                os.remove(tmp_path)
            except Exception:
                pass


def upload_stats_payload(payload):
    """POST JSON a stats.latamsquad.org; nunca lanza hacia el game loop."""
    if not STATS_UPLOAD_URL or STATS_API_KEY == 'CHANGE_ME':
        msg = 'upload disabled or api key placeholder'
        _log_upload(msg)
        return (False, msg)
    body = _encode_json_body(payload)
    # 1) Intento urllib (native)
    try:
        ok, msg = _upload_via_urllib(body)
        _log_upload('urllib ok=%s msg=%s' % (ok, msg))
        if ok:
            return (ok, msg)
    except Exception as exc:
        msg = 'urllib error: %s' % exc
        _log_upload(msg)
        ok, msg = False, msg
    # 2) Fallback curl.exe (TLS moderno en Windows)
    try:
        ok2, msg2 = _upload_via_curl(body)
        _log_upload('curl ok=%s msg=%s' % (ok2, msg2))
        return (ok2, msg2)
    except Exception as exc2:
        msg2 = 'curl error: %s | previous=%s' % (exc2, msg)
        _log_upload(msg2)
        return (False, msg2)


def parse_player_name(full_name):
    """Separa clan (primer token) y nombre del jugador."""
    if full_name is None:
        return ('', '')
    text = full_name.strip()
    if not text:
        return ('', '')
    parts = text.split(' ')
    if len(parts) == 1:
        return ('', parts[0])
    return (parts[0], ' '.join(parts[1:]))


def kd_ratio(kills, deaths):
    """K/D: si deaths==0 devuelve kills como float; si no kills/deaths."""
    k = int(kills or 0)
    d = int(deaths or 0)
    if d == 0:
        return float(k)
    return k / float(d)


def compute_xp(score, kills, deaths, treasures=0):
    """
    XP = (score*3 + kills - deaths*2) * (1 + K/D*0.25) + treasures*TREASURE_XP_BONUS
    Misma fórmula que latamstats-web/includes/ranks.php, más bonus por tesoros.
    """
    s = int(score or 0)
    k = int(kills or 0)
    d = int(deaths or 0)
    t = int(treasures or 0)
    kd = k / float(d if d > 0 else 1)
    base = (s * 3) + k - (d * 2)
    bonus = t * TREASURE_XP_BONUS
    return base * (1.0 + (kd * 0.25)) + bonus


def format_int_es(n):
    """Formato 1.234.567 (punto como separador de miles)."""
    text = str(int(n))
    neg = text.startswith('-')
    if neg:
        text = text[1:]
    parts = []
    while text:
        parts.append(text[-3:])
        text = text[:-3]
    out = '.'.join(reversed(parts))
    return ('-' + out) if neg else out


def format_stats_message(player_row, position):
    """Arma el texto privado de !stats."""
    score = int(player_row.get('score') or 0)
    kills = int(player_row.get('kills') or 0)
    deaths = int(player_row.get('deaths') or 0)
    rounds = int(player_row.get('rounds') or 0)
    treasures = int(player_row.get('treasures') or 0)
    xp = int(round(compute_xp(score, kills, deaths, treasures)))
    kd = kd_ratio(kills, deaths)
    return (
        '#%s | XP %s | Score %s | K %s | D %s | K/D %.2f | Rondas %s'
        % (
            int(position),
            format_int_es(xp),
            format_int_es(score),
            format_int_es(kills),
            format_int_es(deaths),
            kd,
            format_int_es(rounds),
        )
    )



def strip_chat_hud_prefix(msg_text):
    """Quita prefijos HUD del motor PR antes de parsear comandos."""
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


def is_stats_command(msg_text):
    """True si el mensaje es exactamente !stats (sin argumentos)."""
    text = strip_chat_hud_prefix(msg_text)
    if not text.startswith('!'):
        return False
    parts = text[1:].split()
    if len(parts) != 1:
        return False
    return parts[0].lower() == 'stats'


def rank_position_by_xp(players, player_id):
    """
    Posición 1-based ordenando por XP descendente.
    Retorna None si el jugador no está en la lista.
    """
    scored = []
    for row in players:
        if not isinstance(row, dict):
            continue
        pid = row.get('player_id')
        if pid is None or pid == '':
            continue
        xp = compute_xp(
            row.get('score'),
            row.get('kills'),
            row.get('deaths'),
            row.get('treasures', 0),
        )
        scored.append((xp, str(pid), row))
    # XP desc; empate: player_id asc (estable y determinista)
    scored.sort(key=lambda item: (-item[0], item[1]))
    target = str(player_id)
    for idx, (_xp, pid, _row) in enumerate(scored):
        if pid == target:
            return idx + 1
    return None


def merge_round_into_totals(totals_row, round_delta):
    """Suma score/kills/deaths/rounds y actualiza name/clan/country desde el delta."""
    out = dict(totals_row)
    out['score'] = int(totals_row.get('score', 0)) + int(round_delta.get('score', 0))
    out['kills'] = int(totals_row.get('kills', 0)) + int(round_delta.get('kills', 0))
    out['deaths'] = int(totals_row.get('deaths', 0)) + int(round_delta.get('deaths', 0))
    out['rounds'] = int(totals_row.get('rounds', 0)) + int(round_delta.get('rounds', 0))
    out['treasures'] = int(totals_row.get('treasures', 0)) + int(round_delta.get('treasures', 0))
    out['player_name'] = round_delta.get('player_name', totals_row.get('player_name', ''))
    out['player_clan'] = round_delta.get('player_clan', totals_row.get('player_clan', ''))
    out['player_id'] = round_delta.get('player_id', totals_row.get('player_id'))
    # Conservar país previo si el delta no trae uno nuevo.
    new_country = str(round_delta.get('player_country') or '').strip().upper()
    old_country = str(totals_row.get('player_country') or '').strip().upper()
    out['player_country'] = new_country if new_country else old_country
    return out


def build_upload_payload(server_id, timestamp, players_list):
    """Arma el dict listo para json.dumps y POST a la API."""
    return {
        'server_id': server_id,
        'timestamp': timestamp,
        'players': list(players_list),
    }


def enrich_players_with_assetbans(players_list, server_id=None):
    """
    Añade ban_cas/tank/apc/trans (0/1) a cada jugador del upload.
    Lee la SQLite de assetban de ESTA instancia (assetbansN.sqlite3),
    alineada con STATS_SERVER_ID / server_id del payload web.
    No modifica la SQLite de stats; solo el payload hacia la web.
    """
    sid = server_id if server_id is not None else STATS_SERVER_ID
    ban_db = None
    if latassban is not None:
        try:
            ban_db = latassban.assetban_db_path(
                latassban.server_num_from_stats_id(sid)
            )
        except Exception:
            ban_db = None
    enriched = []
    for row in list(players_list or []):
        player = dict(row)
        flags = {
            'ban_cas': 0,
            'ban_tank': 0,
            'ban_apc': 0,
            'ban_trans': 0,
        }
        if latassban is not None:
            try:
                flags = latassban.get_assetban_flags(
                    player.get('player_id'), ban_db
                )
            except Exception:
                pass
        player['ban_cas'] = int(flags.get('ban_cas') or 0)
        player['ban_tank'] = int(flags.get('ban_tank') or 0)
        player['ban_apc'] = int(flags.get('ban_apc') or 0)
        player['ban_trans'] = int(flags.get('ban_trans') or 0)
        enriched.append(player)
    return enriched


_STATS_SCHEMA_TEMPLATE = """
CREATE TABLE IF NOT EXISTS {table_name} (
  log_id INTEGER PRIMARY KEY NOT NULL,
  player_id TEXT NOT NULL UNIQUE,
  player_clan TEXT,
  player_name TEXT,
  player_country TEXT DEFAULT '',
  score INTEGER NOT NULL,
  kills INTEGER NOT NULL,
  deaths INTEGER NOT NULL,
  rounds INTEGER NOT NULL,
  treasures INTEGER NOT NULL DEFAULT 0,
  created TEXT,
  seen TEXT
);
"""

# Columnas expuestas por get_player / list_all_players (sin log_id interno)
_STATS_PLAYER_COLUMNS = (
    'player_id', 'player_clan', 'player_name', 'player_country',
    'score', 'kills', 'deaths', 'rounds', 'treasures', 'created', 'seen',
)


def server_table_name(server_id=None):
    """Nombre de tabla SQLite para un server_id (stats1..stats4)."""
    sid = server_id if server_id is not None else STATS_SERVER_ID
    return STATS_SERVER_TABLES.get(sid, 'stats1')


def _validate_stats_table_name(table_name):
    """Solo permite tablas stats1..stats4 (evita inyección SQL)."""
    if table_name not in STATS_TABLE_NAMES:
        raise ValueError('invalid stats table: %s' % table_name)
    return table_name


def _create_stats_table_sql(table_name):
    return _STATS_SCHEMA_TEMPLATE.format(
        table_name=_validate_stats_table_name(table_name),
    )


def _ensure_treasures_column(conn, table_name):
    """Migración suave: añade treasures si la tabla ya existía sin la columna."""
    table_name = _validate_stats_table_name(table_name)
    cur = conn.execute('PRAGMA table_info(%s)' % table_name)
    cols = [row[1] for row in cur.fetchall()]
    if 'treasures' not in cols:
        conn.execute(
            'ALTER TABLE %s ADD COLUMN treasures INTEGER NOT NULL DEFAULT 0'
            % table_name
        )


def _stats_row_to_dict(row):
    """Convierte sqlite3.Row o tupla nombrada a dict de jugador."""
    if row is None:
        return None
    data = {}
    for col in _STATS_PLAYER_COLUMNS:
        try:
            data[col] = row[col]
        except (IndexError, KeyError):
            data[col] = '' if col == 'player_country' else None
    if data.get('player_country') is None:
        data['player_country'] = ''
    return data


class StatsStore(object):
    """Persistencia SQLite: una tabla por servidor (stats1..stats4) en el mismo .sqlite3."""

    def __init__(self, db_path, server_id=None):
        self.db_path = db_path
        self.server_id = server_id if server_id is not None else STATS_SERVER_ID
        self.table_name = _validate_stats_table_name(server_table_name(self.server_id))

    def _connect(self):
        return sqlite3.connect(self.db_path, timeout=5.0)

    def _migrate_legacy_stats_table(self, conn):
        """Renombra la tabla antigua stats → stats1 si aún no existe stats1."""
        cur = conn.execute(
            "SELECT name FROM sqlite_master WHERE type='table' AND name='stats'"
        )
        if cur.fetchone() is None:
            return

        cur = conn.execute(
            "SELECT name FROM sqlite_master WHERE type='table' AND name='stats1'"
        )
        if cur.fetchone() is None:
            conn.execute('ALTER TABLE stats RENAME TO stats1')

    def _ensure_country_column(self, conn, table_name):
        """Agrega player_country a tablas ya existentes (migración suave)."""
        table_name = _validate_stats_table_name(table_name)
        cur = conn.execute('PRAGMA table_info(%s)' % table_name)
        cols = [row[1] for row in cur.fetchall()]
        if 'player_country' not in cols:
            conn.execute(
                "ALTER TABLE %s ADD COLUMN player_country TEXT DEFAULT ''"
                % table_name
            )

    def ensure_schema(self):
        """Crea stats1..stats4, migra stats → stats1, country y treasures."""
        conn = self._connect()
        try:
            self._migrate_legacy_stats_table(conn)
            for table_name in STATS_TABLE_NAMES:
                conn.executescript(_create_stats_table_sql(table_name))
                self._ensure_country_column(conn, table_name)
                _ensure_treasures_column(conn, table_name)
            conn.commit()
        finally:
            conn.close()

    def get_player(self, player_id):
        """Devuelve dict del jugador o None si no está en la BD."""
        conn = self._connect()
        try:
            conn.row_factory = sqlite3.Row
            sql = (
                'SELECT player_id, player_clan, player_name, player_country, '
                'score, kills, deaths, rounds, treasures, created, seen '
                'FROM %s WHERE player_id = ?'
            ) % self.table_name
            cur = conn.execute(sql, (player_id,))
            return _stats_row_to_dict(cur.fetchone())
        finally:
            conn.close()

    def upsert_round_delta(self, delta):
        """Inserta jugador nuevo o suma stats vía merge_round_into_totals."""
        player_id = delta['player_id']
        existing = self.get_player(player_id)
        country = str(delta.get('player_country') or '').strip().upper()
        conn = self._connect()
        try:
            if existing is None:
                sql = (
                    'INSERT INTO %s (player_id, player_clan, player_name, '
                    'player_country, score, kills, deaths, rounds, treasures, created, seen) '
                    'VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)'
                ) % self.table_name
                conn.execute(
                    sql,
                    (
                        player_id,
                        delta.get('player_clan'),
                        delta.get('player_name'),
                        country,
                        int(delta.get('score', 0)),
                        int(delta.get('kills', 0)),
                        int(delta.get('deaths', 0)),
                        int(delta.get('rounds', 0)),
                        int(delta.get('treasures', 0)),
                        delta.get('created'),
                        delta.get('seen'),
                    ),
                )
            else:
                merged = merge_round_into_totals(existing, delta)
                sql = (
                    'UPDATE %s SET player_clan = ?, player_name = ?, '
                    'player_country = ?, score = ?, kills = ?, deaths = ?, '
                    'rounds = ?, treasures = ?, seen = ? WHERE player_id = ?'
                ) % self.table_name
                conn.execute(
                    sql,
                    (
                        merged['player_clan'],
                        merged['player_name'],
                        merged.get('player_country') or '',
                        merged['score'],
                        merged['kills'],
                        merged['deaths'],
                        merged['rounds'],
                        merged['treasures'],
                        delta.get('seen'),
                        player_id,
                    ),
                )
            conn.commit()
        finally:
            conn.close()

    def list_all_players(self):
        """Lista todos los jugadores de la tabla del servidor activo."""
        conn = self._connect()
        try:
            conn.row_factory = sqlite3.Row
            sql = (
                'SELECT player_id, player_clan, player_name, player_country, '
                'score, kills, deaths, rounds, treasures, created, seen '
                'FROM %s ORDER BY player_id'
            ) % self.table_name
            cur = conn.execute(sql)
            return [_stats_row_to_dict(row) for row in cur.fetchall()]
        finally:
            conn.close()


# Imports del motor PR: protegidos para que tests/CI importen sin bf2
try:
    import bf2
    import host
    import realityserver
    import realitycore as rcore
    import realitydebug as rdebug
    _IN_GAME = True
except ImportError:
    bf2 = None
    host = None
    realityserver = None
    rcore = None
    rdebug = None
    _IN_GAME = False

try:
    import latamassetban as latassban
except Exception:
    latassban = None

def init():
    """Registra el sistema de estadísticas al iniciar el mod."""
    if _IN_GAME:
        StatsSystem()


class StatsSystem(object):
    """Captura una ronda en memoria y la persiste una sola vez al terminar."""

    def __init__(self):
        self.store = StatsStore(STATS_DB_PATH, STATS_SERVER_ID)
        self.store.ensure_schema()
        self.round_snapshots = {}
        # player_hash -> timestamp del último !stats
        self._stats_cmd_cooldown = {}
        host.registerGameStatusHandler(self.on_game_status_changed)
        host.registerHandler('PlayerDisconnect', self.on_player_disconnect, 1)
        host.registerHandler('ChatMessage', self.on_chat_message, 1)

    @staticmethod
    def _merge_round_snapshots(memory_snapshots, endgame_snapshots):
        """Une snapshots; el valor leído en EndGame tiene prioridad."""
        merged = dict(memory_snapshots)
        merged.update(endgame_snapshots)
        return merged

    @staticmethod
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

    def on_chat_message(self, player_id, msg_text, channel, flags):
        """Handler ChatMessage: !stats consulta SQLite local."""
        if player_id == -1:
            return
        if not is_stats_command(msg_text):
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
        if not self._valid_player_id(player_hash):
            self._pm(player, 'No se pudo obtener tu ID de jugador')
            return

        now = time.time()
        last = self._stats_cmd_cooldown.get(player_hash, 0)
        if now - last < STATS_CMD_COOLDOWN_SEC:
            self._pm(player, 'Espera unos segundos antes de usar !stats')
            return
        self._stats_cmd_cooldown[player_hash] = now

        try:
            row = self.store.get_player(player_hash)
            if row is None:
                self._pm(player, 'Sin stats registradas en este servidor')
                return
            players = self.store.list_all_players()
            position = rank_position_by_xp(players, player_hash)
            if position is None:
                position = 1
            self._pm(player, format_stats_message(row, position))
        except Exception as exc:
            self._pm(player, 'Error al leer tus stats')
            if rdebug:
                try:
                    rdebug.debugMessage(
                        'latamstats !stats error: %s' % exc,
                        'latamstats',
                    )
                except Exception:
                    pass

    @staticmethod
    def _read_score_tuple(player):
        """Lee score, bajas y muertes sin interrumpir el handler si fallan."""
        try:
            return (
                int(player.score.score),
                int(player.score.kills),
                int(player.score.deaths),
            )
        except Exception:
            return (0, 0, 0)

    @staticmethod
    def _valid_player_id(player_id):
        """Descarta valores que el motor devuelve cuando no hay hash válido."""
        if isinstance(player_id, bool):
            return False
        return player_id is not None and player_id != ''

    @staticmethod
    def _player_ip(player):
        """IPv4 del jugador (sin puerto) o ''."""
        try:
            addr = player.getAddress()
        except Exception:
            return ''
        return normalize_ip_address(addr)

    @staticmethod
    def _player_country(player):
        """Código ISO-2 vía GeoIP local, o ''."""
        ip = StatsSystem._player_ip(player)
        if ip == '':
            return ''
        try:
            return lookup_country_code(ip, STATS_GEOIP_PATH) or ''
        except Exception:
            return ''

    def _snapshot_player(self, player):
        """Construye el delta completo de la ronda para un jugador."""
        player_id = realityserver.getPlayerHash(player)
        if not self._valid_player_id(player_id):
            return None

        clan, name = parse_player_name(player.getName())
        score, kills, deaths = self._read_score_tuple(player)
        timestamp = time.strftime('%Y-%m-%dT%H:%M:%SZ', time.gmtime())
        return {
            'player_id': player_id,
            'player_clan': clan,
            'player_name': name,
            'player_country': self._player_country(player),
            'score': score,
            'kills': kills,
            'deaths': deaths,
            'rounds': 1,
            'treasures': 0,
            'created': timestamp,
            'seen': timestamp,
        }

    def on_player_disconnect(self, player):
        """Conserva el último estado del jugador sin escribir aún en SQLite."""
        snapshot = self._snapshot_player(player)
        if snapshot is not None:
            self.round_snapshots[snapshot['player_id']] = snapshot

    def on_game_status_changed(self, status):
        """Persiste la ronda cuando el motor informa EndGame."""
        if status == bf2.GameStatus.EndGame:
            self._flush_round_and_upload()

    def _flush_round_and_upload(self):
        """Prioriza jugadores conectados, persiste y sube stats a la API."""
        try:
            endgame_snapshots = {}
            for player in rcore.getPlayers():
                snapshot = self._snapshot_player(player)
                if snapshot is not None:
                    endgame_snapshots[snapshot['player_id']] = snapshot

            snapshots = self._merge_round_snapshots(
                self.round_snapshots,
                endgame_snapshots,
            )

            pending = {}
            try:
                import latamtreasures as lt
                pending = lt.take_pending_treasures()
            except Exception:
                pending = {}

            timestamp = time.strftime('%Y-%m-%dT%H:%M:%SZ', time.gmtime())

            for player_id in snapshots:
                snap = snapshots[player_id]
                snap['treasures'] = int(pending.get(str(player_id), 0))
                self.store.upsert_round_delta(snap)

            # Crédito de tesoros a jugadores que se desconectaron antes del flush
            for player_id, treasure_count in pending.items():
                pid = str(player_id)
                if pid in snapshots:
                    continue
                treasures = int(treasure_count or 0)
                if treasures <= 0:
                    continue
                # Jugador ya en BD: omitir name/clan para no pisarlos con ''.
                orphan_delta = {
                    'player_id': pid,
                    'score': 0,
                    'kills': 0,
                    'deaths': 0,
                    'rounds': 0,
                    'treasures': treasures,
                    'created': timestamp,
                    'seen': timestamp,
                }
                if self.store.get_player(pid) is None:
                    orphan_delta['player_clan'] = ''
                    orphan_delta['player_name'] = ''
                self.store.upsert_round_delta(orphan_delta)

            # Flags desde assetbansN.sqlite3 (mismo N que STATS_SERVER_ID).
            players = enrich_players_with_assetbans(
                self.store.list_all_players(), STATS_SERVER_ID
            )
            payload = build_upload_payload(STATS_SERVER_ID, timestamp, players)
            ok, msg = upload_stats_payload(payload)
            if _IN_GAME and rdebug:
                rdebug.debugMessage(
                    'latamstats upload ok=%s msg=%s' % (ok, msg),
                    'latamstats',
                )
            self.round_snapshots.clear()
        except Exception as exc:
            if _IN_GAME and rdebug:
                rdebug.debugMessage(
                    'latamstats flush error: %s' % exc,
                    'latamstats',
                )
            else:
                print('latamstats flush error: %s' % exc)


# Arrancar al importar el módulo en el servidor PR.
# Solo "import latamstats" en __init__.py no alcanza: hay que llamar init().
if _IN_GAME:
    init()
