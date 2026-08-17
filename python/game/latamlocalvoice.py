# -*- coding: utf-8 -*-
# latamlocalvoice.py - sv1 / latam1 / MuMo vanilla
# Lock de voz local (H) - solo briefing (unlink):
#   Suppress por carga: lo maneja MuMo via UserState.context (is_linked)
#   Playing: H libre hasta squad time; unlink en 2:00; unlock en 0:00 / RoundStart
# Comando admin: !ml on | !ml off
# Exentos en MuMo: SuperUser (userid 0) o ACL PermissionWrite en root.

import os
import time
import realityadmin as radmin

try:
    import bf2
    import host
    import realityconfig_admin as ras
    import realityevents as revents
    import realityserver
    import realitytimer as rtimer
    _IN_GAME = True
except ImportError:
    bf2 = None
    host = None
    ras = None
    revents = None
    realityserver = None
    rtimer = None
    _IN_GAME = False

try:
    import json
except ImportError:
    json = None

_STATE_FILE = r'C:\prbf2_murmur\modded\local_voice_lock_state_sv1.json'
_LOG_PATH = 'C:/prbf2_db/sv1/latamlocalvoice.log'

_lock_timer = None
_unlock_timer = None
_manual_hold = False
_playing_since = None


def _wall_now():
    try:
        return int(host.timer_getWallTime())
    except Exception:
        return int(time.time())


def _log(msg):
    try:
        folder = os.path.dirname(_LOG_PATH)
        if folder and not os.path.isdir(folder):
            try:
                os.makedirs(folder)
            except Exception:
                pass
        line = '[%s] %s\n' % (time.strftime('%Y-%m-%d %H:%M:%S'), msg)
        fp = open(_LOG_PATH, 'ab')
        try:
            fp.write(line)
        finally:
            fp.close()
    except Exception:
        pass


def _load_state():
    if json is None:
        return {'locked': False, 'channels': {}}
    if not os.path.isfile(_STATE_FILE):
        return {'locked': False, 'channels': {}}
    try:
        fp = open(_STATE_FILE, 'rb')
        try:
            data = json.load(fp)
        finally:
            fp.close()
        if not isinstance(data, dict):
            return {'locked': False, 'channels': {}}
        if 'channels' not in data:
            data['channels'] = {}
        return data
    except Exception, e:
        _log('ERROR read state: %s' % e)
        return {'locked': False, 'channels': {}}


def _save_state(data):
    if json is None:
        return False
    try:
        folder = os.path.dirname(_STATE_FILE)
        if folder and not os.path.isdir(folder):
            os.makedirs(folder)
        fp = open(_STATE_FILE, 'wb')
        try:
            json.dump(data, fp, indent=2, sort_keys=True)
            fp.write('\n')
        finally:
            fp.close()
        return True
    except Exception, e:
        _log('ERROR write state: %s' % e)
        return False


def _set_lock_state(locked, manual_hold=None):
    """Solo modo unlink (squad time / !ml). Sin map_load global."""
    data = _load_state()
    data['locked'] = bool(locked)
    data['map_load'] = False
    data.pop('map_load_since', None)
    if manual_hold is not None:
        data['manual_hold'] = bool(manual_hold)
    if not locked:
        data['manual_hold'] = False
    if _save_state(data):
        _log('state locked=%s manual_hold=%s' % (
            int(bool(data.get('locked'))),
            int(bool(data.get('manual_hold'))),
        ))


def _cancel_timers():
    global _lock_timer, _unlock_timer
    for t in (_lock_timer, _unlock_timer):
        if t is None:
            continue
        try:
            t.destroy()
        except Exception:
            try:
                if hasattr(t, 'cancel'):
                    t.cancel()
            except Exception:
                pass
    _lock_timer = None
    _unlock_timer = None


def _briefing_remaining():
    global _playing_since
    try:
        start_delay = int(realityserver.C('STARTDELAY') or 0)
    except Exception:
        start_delay = 0
    if start_delay <= 0 or _playing_since is None:
        return None
    left = start_delay - (_wall_now() - int(_playing_since))
    return left


def _do_lock(data=None, announce=True):
    global _manual_hold
    remaining = _briefing_remaining()
    _log('lock request manual=%s announce=%s remaining=%s' % (
        int(bool(_manual_hold)),
        int(bool(announce)),
        remaining if remaining is not None else '?',
    ))
    _set_lock_state(True, manual_hold=_manual_hold)
    if announce:
        try:
            radmin.globalMessage('SQUAD TIME...', True, False)
        except Exception:
            pass


def _do_unlock(data=None):
    global _manual_hold
    _log('unlock request')
    _set_lock_state(False, manual_hold=False)


def _squad_time_lock(data=None):
    if _manual_hold:
        return
    _log('squad time -> lock (unlink)')
    _do_lock(announce=True)


def _schedule_for_playing():
    """
    Playing (briefing): H libre hasta squad time; unlink a los 2:00; unlock a 0:00.
    Suppress por carga lo hace MuMo segun context del cliente.
    """
    global _lock_timer, _unlock_timer, _playing_since
    _cancel_timers()

    if _manual_hold:
        return

    _playing_since = _wall_now()
    _do_unlock()

    try:
        start_delay = int(realityserver.C('STARTDELAY') or 0)
    except Exception:
        start_delay = 0
    try:
        no_before = int(getattr(ras, 'sqd_noSquadsBefore', 0) or 0)
    except Exception:
        no_before = 0

    if start_delay <= 0 or no_before <= 0:
        _log('Playing -> no schedule (STARTDELAY=%s noSquadsBefore=%s)' % (
            start_delay, no_before,
        ))
        return

    lock_at = max(0, start_delay - no_before)
    _log('Playing -> schedule lock_at=%ss unlock_at=%ss (briefing)' % (
        lock_at, start_delay,
    ))

    if lock_at == 0:
        _lock_timer = rtimer.Timer(_squad_time_lock, 0.5, 1, None)
    else:
        _lock_timer = rtimer.Timer(_squad_time_lock, float(lock_at), 1, None)

    _unlock_timer = rtimer.Timer(_do_unlock, float(start_delay), 1, None)


def _status_label(status):
    for name in ('Loading', 'Loaded', 'Playing', 'EndGame'):
        try:
            if status == getattr(bf2.GameStatus, name):
                return name
        except Exception:
            pass
    try:
        return str(int(status))
    except Exception:
        return '?'


def _sync_state_on_init():
    try:
        state = revents.g_gameState
    except Exception:
        state = None
    if state == bf2.GameStatus.Playing:
        _log('init state=Playing -> schedule briefing')
        _schedule_for_playing()
    else:
        _log('init state=%s -> unlock (suppress por context en MuMo)' % _status_label(state))
        _do_unlock()


def on_game_status_changed(status):
    global _manual_hold, _playing_since
    try:
        if status == bf2.GameStatus.Playing:
            _schedule_for_playing()
        else:
            # Loading/Loaded/EndGame/otros: sin map_load global.
            _log('status %s -> unlock (briefing off)' % _status_label(status))
            _manual_hold = False
            _playing_since = None
            _cancel_timers()
            _do_unlock()
    except Exception, e:
        _log('ERROR on_game_status_changed: %s' % e)


def on_round_start(safe=None):
    global _playing_since
    try:
        if _manual_hold:
            return
        _log('RoundStart -> unlock')
        _playing_since = None
        _cancel_timers()
        _do_unlock()
    except Exception, e:
        _log('ERROR on_round_start: %s' % e)


def command_ml(args, admin):
    global _manual_hold
    args = [str(a).lower() for a in list(args or []) if a]
    if len(args) != 1 or args[0] not in ('on', 'off'):
        radmin.personalMessage('Uso: !ml on|off', admin)
        return False

    _cancel_timers()
    if args[0] == 'on':
        _manual_hold = True
        _do_lock(announce=True)
        radmin.adminPM('Mumble local lock ON (!ml on).', admin)
        _log('!ml on by %s' % admin.getName())
    else:
        _manual_hold = False
        _do_unlock()
        radmin.adminPM('Mumble local lock OFF (!ml off).', admin)
        _log('!ml off by %s' % admin.getName())

    try:
        radmin.logAdmin('!ml', admin.getName(), '', args[0])
    except Exception:
        pass
    return True


def init():
    if not _IN_GAME:
        return
    try:
        host.registerGameStatusHandler(on_game_status_changed)
    except Exception, e:
        _log('ERROR registerGameStatusHandler: %s' % e)
    try:
        host.registerHandler('RoundStart', on_round_start, 1)
    except Exception, e:
        _log('ERROR register RoundStart: %s' % e)
    try:
        power = 1
        if ras is not None:
            power = ras.adm_adminPowerLevels.get('ml', 1)
        radmin.addCommand('ml', command_ml, power)
    except Exception, e:
        _log('ERROR register !ml: %s' % e)
    _sync_state_on_init()
    _log('latamlocalvoice init OK (sv1) - briefing only (suppress via MuMo context)')


if _IN_GAME:
    init()
