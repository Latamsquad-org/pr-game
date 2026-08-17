# -*- coding: utf-8 -*-
# latamassetban.py - bans de assets (cas/tank/apc/trans) en SQLite
import os
import re
import shutil
import bf2
import host
import sqlite3
import realityadmin as radmin
import realitydebug as rdebug
import realityconstants as rconstants
import realitycore as rcore
import realityserver
import realitymemory as rmemory
import realitytimer as rtimer

# Instancia PR (1..4). Debe coincidir con el sufijo de STATS_SERVER_ID
# (pr-N). Cada servidor usa su propia SQLite:
#   C:/prbf2_db/assetbans1.sqlite3, assetbans2.sqlite3, ...
ASSETBANS_SERVER_NUM = 1


def server_num_from_stats_id(server_id):
    """Extrae N de pr-N (o legacy latamsquad-N). Si no matchea, usa ASSETBANS_SERVER_NUM."""
    text = str(server_id or '').strip()
    match = re.search(r'-(\d+)\s*$', text)
    if match:
        return int(match.group(1))
    return int(ASSETBANS_SERVER_NUM)


def assetban_db_path(server_num=None):
    """Ruta SQLite de assetbans para la instancia N (1..4)."""
    num = ASSETBANS_SERVER_NUM if server_num is None else int(server_num)
    return 'C:/prbf2_db/assetbans%d.sqlite3' % num


ASSETBANS_DB_PATH = assetban_db_path(ASSETBANS_SERVER_NUM)

# Esquema v3: nombre legible en 2da columna + hash para buscar.
ASSETBANS_TABLE_SQL = (
    'CREATE TABLE IF NOT EXISTS assetbans ('
    'ban_id INTEGER PRIMARY KEY NOT NULL, '
    'player_name TEXT DEFAULT \'\', '
    'player_id TEXT, '
    'cas INTEGER NOT NULL, '
    'tank INTEGER NOT NULL, '
    'apc INTEGER NOT NULL, '
    'trans INTEGER NOT NULL)'
)


def init():
    # Hereda bans del archivo compartido legacy solo en la instancia 1.
    _adopt_legacy_shared_db_if_needed()
    AssetBanSystem()


def _adopt_legacy_shared_db_if_needed():
    """Migracion one-shot: assetbans.sqlite3 compartido -> assetbans1.sqlite3.
    Instancias 2+ arrancan vacias (no copian el legacy).
    """
    target = assetban_db_path(ASSETBANS_SERVER_NUM)
    legacy = 'C:/prbf2_db/assetbans.sqlite3'
    if ASSETBANS_SERVER_NUM != 1:
        return
    if os.path.isfile(target):
        return
    if not os.path.isfile(legacy):
        return
    try:
        parent = os.path.dirname(target)
        if parent and not os.path.isdir(parent):
            os.makedirs(parent)
        shutil.copy2(legacy, target)
    except Exception:
        pass


def _table_columns(cur, table_name):
    """Lista de nombres de columna de una tabla SQLite."""
    cur.execute('PRAGMA table_info(%s)' % table_name)
    return [row[1] for row in cur.fetchall()]


def ensure_assetbans_schema(con):
    """
    Crea o migra la tabla assetbans a:
    ban_id, player_name, player_id, cas, tank, apc, trans
    """
    cur = con.cursor()
    cur.execute(
        "SELECT name FROM sqlite_master WHERE type='table' AND name='assetbans'"
    )
    exists = cur.fetchone() is not None
    if not exists:
        cur.execute(ASSETBANS_TABLE_SQL)
        con.commit()
        return

    cols = _table_columns(cur, 'assetbans')
    # Ya en esquema nuevo (nombre en 2da posiciÃ³n).
    if cols == [
        'ban_id', 'player_name', 'player_id', 'cas', 'tank', 'apc', 'trans',
    ]:
        return

    # MigraciÃ³n: reconstruir para poner player_name como 2da columna.
    cur.execute(
        'CREATE TABLE IF NOT EXISTS assetbans_v3 ('
        'ban_id INTEGER PRIMARY KEY NOT NULL, '
        'player_name TEXT DEFAULT \'\', '
        'player_id TEXT, '
        'cas INTEGER NOT NULL, '
        'tank INTEGER NOT NULL, '
        'apc INTEGER NOT NULL, '
        'trans INTEGER NOT NULL)'
    )
    if 'player_name' in cols:
        # TenÃ­a nombre pero en otro orden: copiar columnas por nombre.
        cur.execute(
            'INSERT OR REPLACE INTO assetbans_v3 '
            '(ban_id, player_name, player_id, cas, tank, apc, trans) '
            'SELECT ban_id, '
            "COALESCE(player_name, ''), "
            'player_id, cas, tank, apc, trans FROM assetbans'
        )
    else:
        # Esquema viejo sin nombre.
        cur.execute(
            'INSERT OR REPLACE INTO assetbans_v3 '
            '(ban_id, player_name, player_id, cas, tank, apc, trans) '
            "SELECT ban_id, '', player_id, cas, tank, apc, trans FROM assetbans"
        )
    cur.execute('DROP TABLE assetbans')
    cur.execute('ALTER TABLE assetbans_v3 RENAME TO assetbans')
    con.commit()


def _player_display_name(player):
    """Nombre visible del jugador, o '' si falla."""
    try:
        return str(player.getName() or '')
    except Exception:
        return ''


class AssetBanSystem():
    def __init__(self):
        self.db_path = ASSETBANS_DB_PATH
        self.con = sqlite3.connect(self.db_path)
        ensure_assetbans_schema(self.con)
        self.cur = self.con.cursor()


def assetBan(args, p):
    if len(args) != 2:
        radmin.personalMessage(
            'Por favor especifica un jugador y el tipo de asset a banear.(cas/tank/apc/trans)',
            p,
        )
        return False
    db_path = ASSETBANS_DB_PATH
    foundPlayers = radmin.findPlayer(args[0], p)
    if args[1] == 'cas' or args[1] == 'tank' or args[1] == 'apc' or args[1] == 'trans':
        for player in foundPlayers:
            playerHash = realityserver.getPlayerHash(player)
            playerName = _player_display_name(player)
            if playerHash is not True and playerHash != '':
                con = sqlite3.connect(db_path)
                ensure_assetbans_schema(con)
                cur = con.cursor()
                query = (
                    'SELECT ban_id, player_name, player_id, cas, tank, apc, trans '
                    'FROM assetbans WHERE player_id == ?'
                )
                asban = 'REPLACE INTO assetbans VALUES (?, ?, ?, ?, ?, ?, ?)'
                try:
                    cur.execute(query, (playerHash,))
                    row = cur.fetchone()
                    if row and len(row) == 7:
                        ban_id, _old_name, player_id, cas, tank, apc, trans = row
                        # Actualizar nombre al banear de nuevo.
                        if args[1] == 'cas' and cas != 1:
                            cur.execute(
                                asban,
                                (ban_id, playerName, player_id, 1, tank, apc, trans),
                            )
                            con.commit()
                            radmin.globalMessage(
                                'El jugador ' + player.getName()
                                + ' ha sido baneado de usar cas.'
                            )
                            return True
                        elif args[1] == 'tank' and tank != 1:
                            cur.execute(
                                asban,
                                (ban_id, playerName, player_id, cas, 1, apc, trans),
                            )
                            con.commit()
                            radmin.globalMessage(
                                'El jugador ' + player.getName()
                                + ' ha sido baneado de usar tank.'
                            )
                            return True
                        elif args[1] == 'apc' and apc != 1:
                            cur.execute(
                                asban,
                                (ban_id, playerName, player_id, cas, tank, 1, trans),
                            )
                            con.commit()
                            radmin.globalMessage(
                                'El jugador ' + player.getName()
                                + ' ha sido baneado de usar apc/ifv/aav.'
                            )
                            return True
                        elif args[1] == 'trans' and trans != 1:
                            cur.execute(
                                asban,
                                (ban_id, playerName, player_id, cas, tank, apc, 1),
                            )
                            con.commit()
                            radmin.globalMessage(
                                'El jugador ' + player.getName()
                                + ' ha sido baneado de usar trans.'
                            )
                            return True
                        else:
                            radmin.personalMessage(
                                'El jugador ' + player.getName()
                                + ' ya se encuentra baneado en este tipo de asset.',
                                p,
                            )
                            return False

                except sqlite3.Error:
                    rdebug.errorMessage()
                    return False
                except ValueError:
                    rdebug.errorMessage()
                    return False

                try:
                    select = 'SELECT player_id FROM assetbans WHERE player_id == ?'
                    ban = 'INSERT INTO assetbans VALUES (?, ?, ?, ?, ?, ?, ?)'
                    banvalues = (None, playerName, playerHash, False, False, False, False)
                    cur.execute(select, (playerHash,))
                    if args[1] == 'cas':
                        banvalues = (None, playerName, playerHash, 1, False, False, False)
                    elif args[1] == 'tank':
                        banvalues = (None, playerName, playerHash, False, 1, False, False)
                    elif args[1] == 'apc':
                        banvalues = (None, playerName, playerHash, False, False, 1, False)
                    elif args[1] == 'trans':
                        banvalues = (None, playerName, playerHash, False, False, False, 1)

                    if cur.fetchone():
                        return
                    else:
                        cur.execute(ban, banvalues)
                        con.commit()
                        radmin.globalMessage(
                            'El jugador ' + player.getName()
                            + ' ha sido baneado de usar ' + str(args[1]) + '.'
                        )
                        return True
                except sqlite3.IntegrityError:
                    raise
                except sqlite3.Error:
                    rdebug.errorMessage()
                    return False


def assetUnban(args, p):
    if len(args) != 2:
        radmin.personalMessage(
            'Por favor especifica un jugador y el tipo de asset a desbanear.(cas/tank/apc/trans)',
            p,
        )
        return False
    db_path = ASSETBANS_DB_PATH
    foundPlayers = radmin.findPlayer(args[0], p)
    if args[1] == 'cas' or args[1] == 'tank' or args[1] == 'apc' or args[1] == 'trans':
        for player in foundPlayers:
            playerHash = realityserver.getPlayerHash(player)
            playerName = _player_display_name(player)
            if playerHash is not True and playerHash != '':
                con = sqlite3.connect(db_path)
                ensure_assetbans_schema(con)
                cur = con.cursor()
                query = (
                    'SELECT ban_id, player_name, player_id, cas, tank, apc, trans '
                    'FROM assetbans WHERE player_id == ?'
                )
                asuban = 'REPLACE INTO assetbans VALUES (?, ?, ?, ?, ?, ?, ?)'
                try:
                    cur.execute(query, (playerHash,))
                    row = cur.fetchone()
                    if row and len(row) == 7:
                        ban_id, _old_name, player_id, cas, tank, apc, trans = row
                        if args[1] == 'cas' and cas != 0:
                            cur.execute(
                                asuban,
                                (ban_id, playerName, player_id, 0, tank, apc, trans),
                            )
                            con.commit()
                            radmin.globalMessage(
                                'El jugador ' + player.getName()
                                + ' ha sido desbaneado de usar cas.'
                            )
                            return True
                        elif args[1] == 'tank' and tank != 0:
                            cur.execute(
                                asuban,
                                (ban_id, playerName, player_id, cas, 0, apc, trans),
                            )
                            con.commit()
                            radmin.globalMessage(
                                'El jugador ' + player.getName()
                                + ' ha sido desbaneado de usar tank.'
                            )
                            return True
                        elif args[1] == 'apc' and apc != 0:
                            cur.execute(
                                asuban,
                                (ban_id, playerName, player_id, cas, tank, 0, trans),
                            )
                            con.commit()
                            radmin.globalMessage(
                                'El jugador ' + player.getName()
                                + ' ha sido desbaneado de usar apc/ifv/aav.'
                            )
                            return True
                        elif args[1] == 'trans' and trans != 0:
                            cur.execute(
                                asuban,
                                (ban_id, playerName, player_id, cas, tank, apc, 0),
                            )
                            con.commit()
                            radmin.globalMessage(
                                'El jugador ' + player.getName()
                                + ' ha sido desbaneado de usar trans.'
                            )
                            return True
                        else:
                            radmin.personalMessage(
                                'El jugador ' + player.getName()
                                + ' ya se encuentra desbaneado en este tipo de asset.',
                                p,
                            )
                            return False

                except sqlite3.Error:
                    rdebug.errorMessage()
                    return False
                except ValueError:
                    rdebug.errorMessage()
                    return False


def isPlayerAssetBanned(player, asset):
    playerId = realityserver.getPlayerHash(player)
    if not playerId:
        return None
    else:
        return isPlayerIdAssetBanned(playerId, asset)


def isPlayerIdAssetBanned(playerId, asset):
    """
    CAS 5
    TANK 1
    APC 4
    TRANS 6
    AAV 2
    IFV 3
    BOAT 18
    JEEP 8
    PROPELLER CAS 14

    VEHICLE_TYPE_TNK = 0
    VEHICLE_TYPE_IFV = 1
    VEHICLE_TYPE_APC = 2
    VEHICLE_TYPE_ATM = 3
    VEHICLE_TYPE_AAV = 4
    VEHICLE_TYPE_JEP = 5
    VEHICLE_TYPE_TRK = 6
    VEHICLE_TYPE_UAV = 7
    VEHICLE_TYPE_JET = 8
    VEHICLE_TYPE_AHE = 9
    VEHICLE_TYPE_THE = 10
    """
    db_path = ASSETBANS_DB_PATH
    flags = get_assetban_flags(playerId, db_path)
    if asset == 5 and flags['ban_cas'] == 1:
        return True
    elif asset == 7 and flags['ban_cas'] == 1:
        return True
    elif asset == 14 and flags['ban_cas'] == 1:
        return True
    elif asset == 1 and flags['ban_tank'] == 1:
        return True
    elif asset == 4 and flags['ban_apc'] == 1:
        return True
    elif asset == 6 and flags['ban_trans'] == 1:
        return True
    elif asset == 2 and flags['ban_apc'] == 1:
        return True
    elif asset == 3 and flags['ban_apc'] == 1:
        return True
    else:
        return False


def get_assetban_flags(player_id, db_path=None):
    """
    Flags 0/1 para upload web / checks.
    Retorna siempre: ban_cas, ban_tank, ban_apc, ban_trans.
    """
    empty = {
        'ban_cas': 0,
        'ban_tank': 0,
        'ban_apc': 0,
        'ban_trans': 0,
    }
    if not player_id or player_id is True:
        return empty
    path = db_path if db_path else ASSETBANS_DB_PATH
    try:
        con = sqlite3.connect(path)
        ensure_assetbans_schema(con)
        cur = con.cursor()
        cur.execute(
            'SELECT cas, tank, apc, trans FROM assetbans WHERE player_id == ?',
            (player_id,),
        )
        row = cur.fetchone()
        con.close()
    except Exception:
        return empty
    if not row or len(row) < 4:
        return empty
    return {
        'ban_cas': 1 if int(row[0] or 0) == 1 else 0,
        'ban_tank': 1 if int(row[1] or 0) == 1 else 0,
        'ban_apc': 1 if int(row[2] or 0) == 1 else 0,
        'ban_trans': 1 if int(row[3] or 0) == 1 else 0,
    }
