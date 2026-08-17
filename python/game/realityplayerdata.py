import ctypes
import json
import socket
import sys
import time
import bf2
import host
import realityadmin as radmin
import realityconfig_admin
import realitycore as rcore
import realitydebug as rdebug
import realityevents as revents
import realitylogger as rlogger
import realitymemory as rmemory
import realityserver as rserver
import realitytimer as rtimer
RETRY_INTERVAL = 20.0
RETRY_MAX = 3
gPlayerDataManager = None
config = {}

# Kick cuando el proxy reporta hash desconocido (!proxy on|off).
_proxy_kick_unknown = True


def is_proxy_kick_unknown_enabled():
    """True si se kickean jugadores con hash desconocido en el proxy."""
    return bool(_proxy_kick_unknown)


def set_proxy_kick_unknown_enabled(enabled):
    """Activa o desactiva el kick por hash desconocido en runtime."""
    global _proxy_kick_unknown
    _proxy_kick_unknown = bool(enabled)
    return _proxy_kick_unknown


def command_proxy(args, admin):
    """
    !proxy [on|off] - controla el kick cuando el proxy no conoce el hash.
    """
    args = [a for a in list(args or []) if a]
    if len(args) > 0 and str(args[0]).lower() not in ('on', 'off'):
        radmin.personalMessage(
            'Uso: !proxy [on|off]  (kick por hash desconocido del proxy)',
            admin,
        )
        return False

    if len(args) == 0:
        state = 'on' if is_proxy_kick_unknown_enabled() else 'off'
        radmin.personalMessage(
            'Proxy kick (hash desconocido): %s' % state,
            admin,
        )
        return True

    turning_on = str(args[0]).lower() == 'on'
    set_proxy_kick_unknown_enabled(turning_on)
    if turning_on:
        radmin.adminPM('Proxy kick (hash desconocido) activado (!proxy).', admin)
    else:
        radmin.adminPM('Proxy kick (hash desconocido) desactivado (!proxy).', admin)
    radmin.logAdmin('!proxy', admin.getName(), '', 'on' if turning_on else 'off')
    return True


def init():
    global config
    global gPlayerDataManager
    global _proxy_kick_unknown
    if not rserver.isInternetServer():
        return
    config['ec_allowVacBanned'] = realityconfig_admin.ec_allowVacBanned
    config['ec_minimumTrust'] = realityconfig_admin.ec_minimumTrust
    _proxy_kick_unknown = bool(getattr(realityconfig_admin, 'ec_proxyKickUnknownHash', True))
    rlogger.createLogger('playerdataerrors', 'admin/logs', 'playerdataerrors.log', True)
    rlogger.createLogger('playerprofiles', 'admin/logs', 'playerprofiles.log', True)
    rlogger.createLogger('joinlog', 'admin/logs', 'joinlog.log', True)
    gPlayerDataManager = PlayerDataManager()
    # Admin cmd: !proxy on|off
    try:
        radmin.addCommand('proxy', command_proxy, 1)
    except Exception:
        rdebug.errorMessage()


def isPlayerVerified(player):
    return hasattr(player, '_playerdata_profileData') and player._playerdata_profileData is not None


def getPlayerTrustLevel(player):
    if not isPlayerVerified(player):
        return 0
    return player._playerdata_profileData.get('trustLevel', 0)


def isVacBanned(player):
    if not isPlayerVerified(player):
        return False
    return player._playerdata_profileData.get('vacBanned', False)


def isPlayerWhitelisted(player):
    if not isPlayerVerified(player):
        return False
    return player._playerdata_profileData.get('whitelisted', False)


def getPlayerRelatedKeys(player):
    if not isPlayerVerified(player):
        raise Exception('Player is not verified')
    return player._playerdata_profileData.get('relatedKeys', [])


def getPlayerAccountCreationDate(player):
    if not isPlayerVerified(player):
        return ''
    epoch = player._playerdata_profileData.get('createdAt', 0)
    time.strftime('%Y-%m-%d', time.localtime(epoch))
    return time.strftime('%Y-%m-%d', time.localtime(epoch))


def getPlayerProfileIsLegacy(player):
    if not isPlayerVerified(player):
        return False
    return player._playerdata_profileData.get('legacy', False)


def getPRMSProxyIP():
    addr = 7933872 if 'win' in sys.platform else 12264748
    if ctypes.c_int32.from_address(addr).value == 1633906540:
        return '127.0.0.1'
    else:
        return 'PRMSProxy'


class PlayerDataManager():

    def __init__(self):
        self._pendingVerifications = {}
        self.proxy = (getPRMSProxyIP(), 29910)
        self.deniedPlayers = []
        try:
            self._sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
            self._sock.setblocking(0)
            interfaceIP = host.rcon_invoke('sv.interfaceIP').strip()
            if len(interfaceIP) == 0:
                self._sock.bind(('127.0.0.1', 0))
            else:
                self._sock.bind((interfaceIP, 0))
        except:
            host.rcon_invoke('echo "Initializing name verification manager failed: could not create socket." ')
            return

        try:
            f = open('%s/license.key' % host.sgl_getModDirectory().lower(), 'rb')
            self.licenseKey = f.read().strip()
            f.close()
        except:
            host.rcon_invoke('echo "Error reading license file."')
            host.rcon_invoke('echo "Please make sure its at BF2Root/mods/pr/license.key"')
            self.licenseKey = ''

        self.gamespyport = host.rcon_invoke('sv.gamespyport').strip()
        self.serverIp = host.rcon_invoke('sv.serverIp').strip()
        host.registerHandler('PlayerConnect', self.onPlayerConnect, 1)
        host.registerHandler('PlayerDisconnect', self.onPlayerDisconnect, 1)
        host.registerGameStatusHandler(self.onGameStatusChanged)
        rtimer.Timer(self.printUnverifiedPlayers, 120.0, 1).setRecurring(120.0)
        rtimer.Timer(self.checkSession, 40.0, 1).setRecurring(40.0)
        rtimer.Timer(self._refresh, 1.0, 1).setRecurring(3.0)
        rtimer.Timer(self._refreshConfiguration, 30.0, 1).setRecurring(30.0)
        self._refreshConfiguration()
        rtimer.repeatingTask(self._refreshPlayerList, 15.0)

    def onGameStatusChanged(self, status):
        self.deniedPlayers = []

    def sendJoinDeniedListToPlayer(self, p):
        radmin.personalMessage('Recently denied players:', p)
        for index, data in enumerate(self.deniedPlayers):
            radmin.personalMessage('!ec whitelist %s: %s lvl:%s (%s)' % (index,
             data['name'],
             data['trustLevel'],
             data['keyHash']), p)

    def addIndexToWhitelist(self, index, requestingPlayer):
        try:
            index = int(index)
        except:
            radmin.personalMessage('bad index', requestingPlayer)
            return

        if index < 0 or index >= len(self.deniedPlayers):
            radmin.personalMessage('bad index', requestingPlayer)
            return
        else:
            data = self.deniedPlayers[index]
            hash = data['keyHash']
            self._sock.sendto('\\addwhitelist\\\\%s' % hash, self.proxy)
            radmin.personalMessage('Added %s to whitelist' % data['name'], requestingPlayer)
            radmin.logAdmin('!ec whitelist', requestingPlayer.getName(), None, '%s: %s' % (data['keyHash'], data['name']))
            return

    def getMinimumToJoin(self):
        return config['ec_minimumTrust']

    def setMinimumToJoin(self, level, requestingPlayer):
        try:
            level = int(level)
        except:
            return radmin.personalMessage('bad syntax', requestingPlayer)

        if level < 0 or level > 2:
            return radmin.personalMessage('levels: 0,1,2', requestingPlayer)
        else:
            config['ec_minimumTrust'] = level
            self._refreshConfiguration()
            radmin.personalMessage('Minimum trust set to %s' % level, requestingPlayer)
            radmin.logAdmin('!ec minimumtrust', requestingPlayer.getName(), None, level)
            return

    def checkSession(self, args = None):
        if host.sgl_getModDirectory().lower() != 'mods/pr' and host.sgl_getModDirectory().lower() != 'mods/pr_repo':
            return
        now = time.time()
        for player in bf2.playerManager.getPlayers():
            if player.isAIPlayer():
                continue
            if not isPlayerVerified(player):
                self.newVerification(player)
                continue
            if not player.isAlive():
                continue
            if radmin.AFKDetection.estimateAFKNess(player) > 10:
                continue
            if not hasattr(player, 's'):
                continue
            if not hasattr(player, 'lastf') or player.f != player.lastf:
                player.lastf = player.f
                player.lastftime = now
                continue
            if rcore.now() - player.lastSpawn < 30:
                continue
            if player.f > 0 and now - player.lastftime > 60:
                rdebug.debugMessage('SessionERR %s' % player.getName())
                radmin.logAdmin('SessionErr', 'SERVER', player.getName(), 'Invalid session %s, %s' % (player.f, now - player.lastftime))

    def printUnverifiedPlayers(self, args = None):
        unverified = set()
        for player in bf2.playerManager.getPlayers():
            if player.isAIPlayer():
                continue
            if isPlayerVerified(player):
                continue
            if rserver.getPlayerHash(player) in self._pendingVerifications:
                continue
            unverified.add(player)

        if len(unverified) > 0:
            radmin.adminPM('Error verificando a los siguientes jugadores', p=None, target=None, big=False, color=True)
            for player in unverified:
                radmin.adminPM(player.getName(), p=None, target=None, big=False, color=True)

        return

    def onPlayerConnect(self, p):
        if p.isAIPlayer():
            return
        else:
            p._playerdata_profileData = None
            rtimer.fireNextTick(self.newVerification, p)
            return

    def onPlayerDisconnect(self, p):
        hash = rserver.getPlayerHash(p)
        if hash in self._pendingVerifications:
            del self._pendingVerifications[hash]

    def newVerification(self, player):
        if not player.isValid():
            return
        hash = rserver.getPlayerHash(player)
        if not hash:
            raise Exception('Player %s has no hash' % player.getName())
        if hash in self._pendingVerifications:
            return
        verification = self.__class__._DataRequest(player, hash)
        self._pendingVerifications[hash] = verification
        self._sendVerificationRequest(verification)

    class _DataRequest:

        def __init__(self, player, hash):
            self.player = player
            self.name = player.getName().split(' ')[1]
            self.pid = player.getProfileId()
            self.addr = player.getAddress()
            self.hash = hash
            self.packet = '\\playerdata\\\\' + str(self.hash)
            self.tryCount = 0
            self.lastRetry = 0

    def _refreshPlayerList(self, args = None):
        players = []
        for player in bf2.playerManager.getPlayers():
            players.append({'Name': player.getName(),
             'Score': host.pmgr_getScore(player.index, 'score'),
             'Ping': player.getPing(),
             'Team': player.getTeam(),
             'Deaths': host.pmgr_getScore(player.index, 'deaths'),
             'Kills': host.pmgr_getScore(player.index, 'kills'),
             'IsAI': player.isAIPlayer()})

        message = '\\playerlist\\\\%s\\%s' % (self.gamespyport, json.dumps(players).replace('\\', '.'))
        self._sock.sendto(message, self.proxy)

    def _refreshConfiguration(self, args = None):
        mumbleIp = host.rcon_invoke('sv.voipServerRemoteIP').strip()
        config['MumbleIPPort'] = mumbleIp
        config['version'] = rserver.getVersion().strip()
        config['mod'] = host.sgl_getModDirectory().lower().strip()
        config['countryFlag'] = realityconfig_admin.sv_countryflag
        if len(realityconfig_admin.sv_externalIP) > 0:
            self.serverIp = realityconfig_admin.sv_externalIP
        message = '\\configuration\\\\%s\\%s\\%s\\%s' % (self.gamespyport,
         self.serverIp,
         self.licenseKey,
         json.dumps(config))
        self._sock.sendto(message, self.proxy)

    def _refresh(self, args = None):
        now = time.time()
        while True:
            try:
                packet = self._sock.recv(8192)
            except:
                break

            self._handlePacket(packet)

        timedOutTooMuch = filter(lambda v: now > v.lastRetry + RETRY_INTERVAL and v.tryCount >= RETRY_MAX, self._pendingVerifications.values())
        for v in timedOutTooMuch:
            del self._pendingVerifications[v.hash]
            radmin.adminPM('Error verificando a %s, no hay respuesta del Masterserver.' % v.name)
            logNameVerError(v, 'Response timed out, giving up')

        for verification in self._pendingVerifications.values():
            if now > verification.lastRetry + RETRY_INTERVAL:
                self._sendVerificationRequest(verification)
                logNameVerError(verification, 'Response timed out, retry %s' % verification.tryCount)

    def _handlePacket(self, packet):
        if packet.startswith('\\playerdata\\\\'):
            self._handlePlayerDataPacket(packet)
        if packet.startswith('\\denied\\\\'):
            self._handleJoinDeniedReportPacket(packet)

    def _handleJoinDeniedReportPacket(self, packet):
        packet = packet[len('\\denied\\\\'):]
        try:
            data = json.loads(packet)
            rdebug.debugMessage('Player %s denied: %s' % (data['name'], data['denyReason']))
            radmin.adminPM('Jugador %s denegado: %s' % (data['name'], data['denyReason']))
            if any(map(lambda d: d['keyHash'] == data['keyHash'], self.deniedPlayers)):
                return
            logPlayerProfile(data)
            self.deniedPlayers.append(data)
        except:
            rdebug.errorMessage()

    def _handlePlayerDataPacket(self, packet):
        packet = packet[len('\\playerdata\\\\'):]
        try:
            data = json.loads(packet)
            hash = data['keyHash']
            if hash not in self._pendingVerifications:
                return
            v = self._pendingVerifications[hash]
            if data['known'] is False:
                radmin.adminPM('Error verificando a %s, el proxy reporta un hash desconocido.' % v.name)
                if is_proxy_kick_unknown_enabled():
                    kickPlayer(v.player)
                else:
                    radmin.adminPM(
                        'Kick omitido para %s (!proxy off).' % v.name,
                        history=False,
                    )
                logNameVerError(v, 'Proxy does not know about this hash')
                del self._pendingVerifications[hash]
                return
            if data['unexpectedErrorVerifying'] is True:
                radmin.adminPM('Error verificando a %s, error al conectar con el Masterserver.' % v.name)
                logNameVerError(v, 'Could not connect to MS or MS returned unexpected error')
                del self._pendingVerifications[hash]
                return
            if v.name != data['name']:
                radmin.adminPM("El masterserver esta en desacuerdo con el nombre de %s! Kickeando..." % v.name)
                kickPlayer(v.player)
                logNameVerError(v, 'KICKED: Fake name!')
                del self._pendingVerifications[hash]
                return
            v.player._playerdata_profileData = data
            del self._pendingVerifications[hash]
            logPlayerProfile(data)
            logJoin(data, ip=v.addr, name=v.player.getName())
            event = revents.getEvents('PlayerVerified')
            revents.sendToHandlers(event, v.player)
            rdebug.debugMessage('Player %s verified!' % v.player.getName(), 'admin')
        except:
            rdebug.errorMessage()

    def _sendVerificationRequest(self, verification):
        verification.tryCount += 1
        verification.lastRetry = time.time()
        self._sock.sendto(verification.packet, self.proxy)


def kickPlayer(p):
    rmemory.setPBKickstring('Server Error. Please try again.')
    if p.isValid():
        host.rcon_invoke('admin.kickPlayer %d' % p.index)


def logPlayerProfile(data):
    key = '\t%s\t%s\t%s' % (data['keyHash'], data['trustLevel'], data['name'])
    if rlogger.RealityLogger['playerprofiles'].contains(key):
        return
    rlogger.RealityLogger['playerprofiles'].logLine('[%s]\t%s\t%s\t%s' % (time.strftime('%Y-%m-%d %H:%M:%S'),
     data['keyHash'],
     data['trustLevel'],
     data['name']))
    radmin.adminPM('Nuevo jugador/hash se ha unido: %s (lvl %s): %s' % (data['name'], data['trustLevel'], data['keyHash']), history=False)


def logJoin(data, ip, name):
    status = ''
    if data.get('legacy', False):
        status += '(LEGACY)'
    if data.get('whitelisted', False):
        status += '(WHITELISTED)'
    if data.get('vacBanned', False):
        status += '(VAC BANNED)'
    rlogger.RealityLogger['joinlog'].logLine('[%s]\t%s\t%s\t%s\t%s\t%s\t%s' % (time.strftime('%Y-%m-%d %H:%M:%S'),
     data['keyHash'],
     data['trustLevel'],
     name,
     time.strftime('%Y-%m-%d', time.localtime(data['createdAt'])),
     ip,
     status))


def logNameVerError(v, message):
    rlogger.RealityLogger['playerdataerrors'].logLine('[%s]%s: %s' % (time.strftime('%Y-%m-%d %H:%M:%S'), '%s\t%s\t%s' % (v.hash, v.name, v.addr), message))
    rdebug.debugMessage('%s,%s,%s: %s' % (v.hash,
     v.name,
     v.addr,
     message))