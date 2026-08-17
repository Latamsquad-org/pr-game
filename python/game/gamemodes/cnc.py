import bf2
import game.realityassets as rassets
import game.realitycore as rcore
import game.realitydebug as rdebug
import game.realityflags as rflag
import game.realitygamemode as rgamemode
import game.realitylocalization as rlocalization
import game.realityserver as realityserver
import game.realitytimer as rtimer
import host

def init():
    rgamemode.setCurrentGameMode(PRCnC())
    print 'gpm_cnc.py initialized'


def deinit():
    rgamemode.setCurrentGameMode()
    print 'gpm_cnc.py uninitialized'


class PRCnC(rflag.PRFlags):

    def __init__(self):
        rflag.PRFlags.__init__(self)
        self.g_start = None
        self.g_timer = None
        self.g_destroyed = {}
        return

    def registerHandlers(self):
        rflag.PRFlags.registerHandlers(self)
        host.registerHandler('VehicleDestroyedFiltered', self.onOutpostDestroyed)

    def unregisterHandlers(self):
        rflag.PRFlags.unregisterHandlers(self)
        host.unregisterHandler(self.onOutpostDestroyed)

    def onGameStatusChanged(self, status):
        rflag.PRFlags.onGameStatusChanged(self, status)
        if status == bf2.GameStatus.Playing:
            host.sh_setEnableCommander(realityserver.C('CNC_COMMANDER'))
            rassets.setAssetMapMaximum('outpost', realityserver.C('CNC_OUTPOSTS_MAX'))
            rassets.setAssetMapMaximum('mortar', 0)
            m = int(realityserver.C('CNC_DEFENSES_MULTIPLIER'))
            realityserver.C('ASSET_MAX_STATIC_DEFENSES', m * int(realityserver.C('ASSET_MAX_STATIC_DEFENSES')))
            realityserver.C('ASSET_MAX_HEAVY_DEFENSES', m * int(realityserver.C('ASSET_MAX_HEAVY_DEFENSES')))
            realityserver.C('ASSET_MAX_MEDIUM_DEFENSES', m * int(realityserver.C('ASSET_MAX_MEDIUM_DEFENSES')))
            realityserver.C('ASSET_MAX_LIGHT_DEFENSES', m * int(realityserver.C('ASSET_MAX_LIGHT_DEFENSES')))
            realityserver.C('ASSET_OUTPOST_DISTANCE', int(realityserver.C('CNC_OUTPOST_DISTANCE')))
            realityserver.C('ASSET_DEPOT_DISTANCE', int(realityserver.C('CNC_DEPOT_DISTANCE')))
            realityserver.C('ASSET_COMMANDPOST_DISTANCE', int(realityserver.C('CNC_COMMANDPOST_DISTANCE')))
            realityserver.C('ASSET_EDGE_DISTANCE', int(realityserver.C('CNC_EDGE_DISTANCE')))
            self.g_destroyed[1] = rcore.now()
            self.g_destroyed[2] = rcore.now()
            self.g_timer = rtimer.Timer(self.updateObjectives, realityserver.C('STARTDELAY'), 1)
            self.g_timer.setRecurring(30)
        else:
            try:
                if self.g_timer:
                    self.g_timer.destroy()
                    self.g_timer = None
            except:
                pass

            self.g_start = None
            self.g_destroyed.clear()
        return

    def onOutpostDestroyed(self, asset, attacker):
        team = asset.getTeam()
        teamName = rcore.getTeamName(team)
        template = asset.templateName.lower()
        if team in (1, 2) and rassets.getAssetTypeFromTemplate(template, team) != 'outpost':
            return
        self.g_destroyed[team] = rcore.now()
        if rcore.now() - self.g_destroyed[team] < realityserver.C('CNC_DESTROYED_INTERVAL'):
            if rdebug.isDebugEnabled('gamemode'):
                rdebug.debugMessage('cnc: outpost destroyed team %s, no ticket loss because is too soon' % teamName, 'gamemode')
            return
        if rdebug.isDebugEnabled('gamemode'):
            rdebug.debugMessage('cnc: outpost destroyed team %s = %s ticket loss' % (teamName, realityserver.C('CNC_OUTPOST_TICKETS')), 'gamemode')
        self.addTickets(team, -realityserver.C('CNC_OUTPOST_TICKETS'), 'outpost %s destroyed' % teamName)

    def updateObjectives(self, data):
        if self.g_start is None:
            rcore.sendMessageToAll(rcore.BIGCOLOREDTEXT + rlocalization.t('cnc_start'))
            self.g_start = rcore.now()
        self.updateTicketLoss()
        return

    def getDistanceMultiplier(self, team):
        distance = 999999
        try:
            for outpost in rassets.getAssetsOfType('outpost', team):
                dis = rcore.getVectorHorizDistance(outpost.getPosition(), (0.0, 0.0, 0.0))
                if dis < distance:
                    distance = dis

            if distance <= 250:
                m = 25
            elif distance <= 500:
                m = 20
            elif distance <= 1000:
                m = 15
            elif distance <= 1500:
                m = 10
            else:
                m = 1
        except:
            m = 1

        if rdebug.isDebugEnabled('gamemode'):
            rdebug.debugMessage('cnc: ticket bleed distance %s multiplier for %s = %s' % (distance, rcore.getTeamName(team), m), 'gamemode')
        return m

    def updateTicketLoss(self):
        if not self.g_start or self.g_start and rcore.now() - self.g_start < realityserver.C('CNC_START'):
            return
        team1 = len(rassets.getAssetsOfType('outpost', 1))
        team2 = len(rassets.getAssetsOfType('outpost', 2))
        team1n = rcore.getTeamName(1)
        team2n = rcore.getTeamName(2)
        team1d = int(rcore.now() - self.g_destroyed[1])
        team2d = int(rcore.now() - self.g_destroyed[2])
        if rdebug.isDebugEnabled('gamemode'):
            rdebug.debugMessage('cnc: %s outposts = %s | %s outposts = %s' % (team1n,
             team1,
             team2n,
             team2), 'gamemode')
        if team1 >= realityserver.C('CNC_OUTPOSTS_MAX') and team2 == realityserver.C('CNC_OUTPOSTS_MIN'):
            bleed = realityserver.C('CNC_BLEED_TICKETS')
            if team2d >= realityserver.C('CNC_DESTROYED_INTERVAL'):
                bleed *= self.getDistanceMultiplier(1)
            bf2.gameLogic.setTicketChangePerSecond(2, bleed)
            bf2.gameLogic.setTicketChangePerSecond(1, 0)
            if rdebug.isDebugEnabled('gamemode'):
                rdebug.debugMessage('cnc: ticket bleed on %s = %s tickets per second' % (team2n, bleed), 'gamemode')
        elif team2 >= realityserver.C('CNC_OUTPOSTS_MAX') and team1 == realityserver.C('CNC_OUTPOSTS_MIN'):
            bleed = realityserver.C('CNC_BLEED_TICKETS')
            if team1d >= realityserver.C('CNC_DESTROYED_INTERVAL'):
                bleed *= self.getDistanceMultiplier(2)
            bf2.gameLogic.setTicketChangePerSecond(1, bleed)
            bf2.gameLogic.setTicketChangePerSecond(2, 0)
            if rdebug.isDebugEnabled('gamemode'):
                rdebug.debugMessage('cnc: ticket bleed on %s = %s tickets per second' % (team1n, bleed), 'gamemode')
        else:
            bf2.gameLogic.setTicketChangePerSecond(2, 0)
            bf2.gameLogic.setTicketChangePerSecond(1, 0)
            if rdebug.isDebugEnabled('gamemode'):
                rdebug.debugMessage('cnc: no ticket bleed', 'gamemode')

    def getType(self):
        return 'cnc'

    def getBf2Type(self):
        return 'gpm_cnc'