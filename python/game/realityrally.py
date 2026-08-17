# Embedded file name: realityrally.py
import bf2
import host
import realityassets as rassets
import realityconstants as CONSTANTS
import realitycore as rcore
import realitydebug as rdebug
import realityevents as revents
import realitykits as rkits
import realitymemory as rmemory
import realityserver
import realityspawner as rspawner
import realitytimer as rtimer
import realitytriggers as rtriggers
import realityvehicles as rvehicles
g_rally_limit = {}
g_rallies = {1: [],
 2: []}
g_rallySpawnGroups = {}

def init():
    host.registerGameStatusHandler(onGameStatusChanged)
    host.registerHandler('RemoteCommandRallyRequest', onRemoteRallyRequestCommand)
    host.registerHandler('PlayerSpawn', onPlayerSpawn)
    host.registerHandler('ChangedCommander', onChangedCommander)
    host.registerHandler('VehicleDestroyedFiltered', onRallyDestroyed)
    host.registerHandler('SquadCreated', onSquadCreated)
    host.registerHandler('SquadRemoved', onSquadRemoved)
    host.registerHandler('RoundEnd', onRoundEnd)
    for team in [1, 2]:
        for squad in range(0, 10):
            g_rallies[team].append(Rally(team, squad))

    rtimer.repeatingTask(tryToRearmRallypoints, 9)
    rtimer.repeatingTask(onCheckCommanderRally, 17)
    NoExpireRallyHandler.init()
    revents.registerObjectSpawnedCallback(onSquadRallySpawn)


def onGameStatusChanged(status):
    global g_rally_limit
    if status == bf2.GameStatus.Playing:
        for team in [1, 2]:
            g_rally_limit[team] = []
            for squad in range(0, 10):
                g_rallies[team][squad].reset()

        g_rallySpawnGroups.clear()
        rtimer.fireOnce(onDestroyMapperRallyTimer, realityserver.C('STARTDELAY') + realityserver.C('RALLY_MAPPER_EXPIRATION'), '')
        rtimer.fireOnce(onDestroyRandomRallyTimer, 21, '')
        rtimer.fireOnce(onDestroyLimitedRallyTimer, 25, '')
        rtimer.fireOnce(onDestroyPickupRallyTimer, 28, '')
        for team in realityserver.C('TEAM_NAME').keys():
            for squad in range(0, 10):
                revents.registerObjectSpawnedTemplate('rallypoint_' + str(team) + '_' + str(squad))

        if rcore.getMapArea() in [CONSTANTS.INSANE, CONSTANTS.HUGE]:
            Rally.overrunRadius = realityserver.C('RALLY_AREA_HUGE')
        elif rcore.getMapArea() in [CONSTANTS.BIG]:
            Rally.overrunRadius = realityserver.C('RALLY_AREA_BIG')
        else:
            Rally.overrunRadius = realityserver.C('RALLY_AREA_SMALL')
        if rcore.getMapArea() in [CONSTANTS.INSANE, CONSTANTS.HUGE]:
            Rally.supportRadiusSquared = realityserver.C('RALLY_SUPPORT_AREA_HUGE')
        elif rcore.getMapArea() in [CONSTANTS.BIG]:
            Rally.supportRadiusSquared = realityserver.C('RALLY_SUPPORT_AREA_BIG')
        else:
            Rally.supportRadiusSquared = realityserver.C('RALLY_SUPPORT_AREA_SMALL')
        Rally.supportRadiusSquared = Rally.supportRadiusSquared ** 2
        Rally.rearmInterval = realityserver.C('RALLY_INTERVAL')
        Rally.rearmIntervalOverrun = realityserver.C('RALLY_OVERRUN_INTERVAL')
    else:
        g_rally_limit.clear()


def onRoundEnd(winner):
    for team in [1, 2]:
        for squad in range(0, 10):
            g_rallies[team][squad].deleteRally()


def onPlayerSpawn(player, soldier):
    playerTeam = player.getTeam()
    playerSquad = player.getSquadId()
    playerPos = soldier.getPosition()
    for rally in rcore.cleanListOfObjects(g_rally_limit[playerTeam]):
        if rcore.getSquareHorizDistance(rally.getPosition(), playerPos) < CONSTANTS.DISTANCE_SPAWN ** 2:
            if player.isSquadLeader() or player.isCommander():
                handler = g_rallies[playerTeam][playerSquad]
                handler.rearmTimer.start(Rally.rearmInterval)
                if rdebug.isDebugEnabled('rally'):
                    rdebug.debugMessage('team %s squad %s last request reset because officer spawned at expiring mapper rally' % (playerTeam, playerSquad), 'rally')
            rally.totalSpawns += 1
            if rally.totalSpawns >= realityserver.C('RALLY_MAPPER_LIMITED'):
                rcore.deleteObject(rally)
            return


def wrapToNewSpawn(player, asset):
    rdebug.debugMessage('wrong rp for ' + player.getName() + ' - moving to nearby spawn', 'rally')
    try:
        player.getDefaultVehicle().setPosition(rcore.getPositionFromObject(asset, 5))
        rcore.sendMessageToPlayer(player, 1190304, 3)
    except:
        return False

    return True


import re

class NoExpireRallyHandler():
    rallies = set()
    refreshRate = 3.5
    lastRefresh = 0.0

    @classmethod
    def init(cls):
        host.registerGameStatusHandler(cls.onGameStatusChanged)
        rtimer.repeatingTask(cls.refresh, cls.refreshRate)
        host.registerHandler('VehicleDestroyedFiltered', cls.onNoExpireRallyDestroyed)
        revents.registerObjectSpawnedCallback(cls.onSpawn)

    @classmethod
    def onSpawn(cls, rally):
        if not rally.templateName.lower().endswith('_placeable_noexpire'):
            return
        else:
            handler = rcore.findClosestPosCustom(rally.getPosition(), cls.rallies, lambda handler: handler.pos)
            if handler is not None:
                handler.loadObject(rally)
            return

    @classmethod
    def onNoExpireRallyDestroyed(cls, rally, p):
        if not rally.templateName.lower().startswith('rallypoint_'):
            return
        for rallyHandler in cls.rallies:
            if rallyHandler.rallyObj is rally:
                rallyHandler.onDestroyed()

    @classmethod
    def refresh(cls, args = None):
        now = host.timer_getWallTime()
        if cls.lastRefresh is None:
            cls.lastRefresh = now
            return
        else:
            timeSinceLastRefresh = now - cls.lastRefresh
            cls.lastRefresh = now
            for rally in cls.rallies:
                rally.refresh(timeSinceLastRefresh)

            return

    @classmethod
    def onGameStatusChanged(cls, status):
        if status == bf2.GameStatus.Loaded:
            for team in realityserver.C('TEAM_NAME').keys():
                revents.registerObjectSpawnedTemplate('rallypoint_%s_placeable_noexpire' % team)

            cls.rallies.clear()
            cls.lastRefresh = None
            pattern = re.compile('dmy_noexrally_(\\d)_(\\d+)_(\\d+)_([01]).*')
            deprecatedTemplate = re.compile('rallypoint_[^_]*_placeable_noexpire')
            for spawner in bf2.objectManager.getObjectsOfType('dice.hfe.world.ObjectTemplate.ObjectSpawner'):
                match = pattern.match(spawner.templateName)
                if match:
                    rally = cls.NoExpireRally(spawner, match.groups())
                    cls.rallies.add(rally)
                    continue
                template = spawner.getTemplateProperty('objectTemplate').strip()
                if deprecatedTemplate.match(template):
                    rdebug.debugMessage('Found deprecated noexpire rally %s, converting to new' % spawner.templateName, 'rally')
                    rally = cls.NoExpireRally(spawner, (None,
                     CONSTANTS.DISTANCE_CLOSE,
                     None,
                     0))
                    cls.rallies.add(rally)

        return

    class NoExpireRally:

        def __init__(self, spawner, groups):
            team, radius, maxSpawnDelay, kitsRequestable = groups
            self.radius = float(radius)
            self.kitsRequstable = kitsRequestable
            host.rcon_invoke('objectTemplate.active %s' % spawner.templateName)
            if team is None:
                try:
                    self.team = int(host.rcon_invoke('objectTemplate.team').strip())
                except:
                    rdebug.debugMessage('Invalid team for rally %s' % spawner.templateName)

            else:
                self.team = int(team)
            if maxSpawnDelay is None:
                try:
                    self.maxRespawnTime = float(host.rcon_invoke('objectTemplate.maxSpawnDelay').strip())
                except:
                    rdebug.debugMessage('Invalid maxSpawnDelay for rally %s' % spawner.templateName)
                    self.maxRespawnTime = 5.0

            else:
                self.maxRespawnTime = float(maxSpawnDelay)
            spawnDelayAtStart = host.rcon_invoke('objectTemplate.spawnDelayAtStart').strip() == '1'
            try:
                delayAtStart = float(host.rcon_invoke('objectTemplate.minSpawnDelay').strip()) + realityserver.C('STARTDELAY')
            except:
                rdebug.debugMessage('Invalid minSpawnDelay for rally %s' % spawner.templateName)
                delayAtStart = 0.0

            if spawnDelayAtStart:
                self.respawnTimeLeft = delayAtStart
            else:
                self.respawnTimeLeft = 0.0
            try:
                host.rcon_invoke('Object.active id' + str(rcore.getObjectId(spawner)))
                self.cpid = int(host.rcon_invoke('object.getControlPointId').strip())
                if self.cpid == -1:
                    self.cpid = None
            except:
                self.cpid = None

            self.spawnerObj = spawner
            self.currentTeam = self.team
            templates = spawner.getTemplateProperty('objectTemplate').strip().split('\n')
            if len(templates) > 1:
                if len(templates[0]) > 1 and len(templates[1]) > 1:
                    self.team = 0
            self.template1 = None
            self.template2 = None
            if self.team == 0 or self.team == 1:
                self.template1 = 'rallypoint_%s_placeable_noexpire' % rcore.getTeamName(1).lower()
            if self.team == 0 or self.team == 2:
                self.template2 = 'rallypoint_%s_placeable_noexpire' % rcore.getTeamName(2).lower()
            self.pos = spawner.getPosition()
            self.rot = spawner.getRotation()
            triggerTeam = 0
            if self.template1 is not None:
                triggerTeam |= 2
            if self.template2 is not None:
                triggerTeam |= 1
            self.trigger = rtriggers.createTrigger(obj=self.spawnerObj, callback=None, radius=self.radius, team=triggerTeam, ignoreFlyingVehicles=True)
            rdebug.debugMessage('-----Creating noexpire rally %s' % spawner.templateName, 'rally')
            rdebug.debugMessage('rally template 1 %s' % self.template1, 'rally')
            rdebug.debugMessage('rally template 2 %s' % self.template2, 'rally')
            rdebug.debugMessage('cpid %s, triggerTeam %s' % (self.cpid, triggerTeam), 'rally')
            rdebug.debugMessage('delay %s, respawn %s' % (self.respawnTimeLeft, self.maxRespawnTime), 'rally')
            rdebug.debugMessage('at pos %s' % str(self.pos), 'rally')
            self.rallyObj = None
            host.rcon_invoke('objectTemplate.active %s' % spawner.templateName)
            host.rcon_invoke('objectTemplate.setObjectTemplate 1 ""')
            host.rcon_invoke('objectTemplate.setObjectTemplate 2 ""')
            host.rcon_invoke('objectTemplate.objectTemplate ""')
            host.rcon_invoke('objectTemplate.minSpawnDelay 99999')
            host.rcon_invoke('objectTemplate.maxSpawnDelay 99999')
            return

        def getIsRallyUp(self):
            return self.rallyObj is not None and self.rallyObj is not False

        def getIsRallyDown(self):
            return self.rallyObj is None

        def getIsRallyLoading(self):
            return self.rallyObj is False

        def onDestroyed(self):
            rdebug.debugMessage('Rally destroyed: %s' % self.spawnerObj.templateName, 'rally')
            self.rallyObj = None
            self.respawnTimeLeft = self.maxRespawnTime
            return

        def destroyRallyIfNeeded(self):
            if self.getIsRallyUp():
                rdebug.debugMessage('destroyed noexpire rally for %s' % self.spawnerObj.templateName, 'rally')
                if self.rallyObj.isValid():
                    rcore.deleteObject(self.rallyObj)
                self.onDestroyed()

        def spawnRallyIfNeeded(self):
            if self.getIsRallyLoading() or self.getIsRallyUp():
                return
            else:
                team = self.currentTeam
                if team == 1:
                    template = self.template1
                elif team == 2:
                    template = self.template2
                else:
                    return
                if template is None:
                    return
                rspawner.createSpawner(template + '_spawner', {'team': team,
                 'position': self.pos,
                 'rotation': self.rot})
                self.rallyObj = False
                if rmemory.isWindowsListenServer:
                    rtimer.task(self.loadObject, rcore.LOAD_OBJECT_DELAY)
                rdebug.debugMessage('Spawned noexpire rally for %s' % self.spawnerObj.templateName, 'rally')
                return

        def loadObject(self, obj = None):
            if obj is None:
                if self.currentTeam == 1:
                    template = self.template1
                else:
                    template = self.template2
                rallyList = rcore.getObjectsOfTemplate(template, 'dice.hfe.world.ObjectTemplate.PlayerControlObject')
                rallyList = filter(lambda x: not hasattr(x, 'found'), rcore.cleanListOfObjects(rallyList))
                obj = rcore.findClosestPosCustom(self.pos, rallyList, lambda obj: obj.getPosition())
            if obj is None:
                rdebug.debugMessage('Could not find a spawned noexpire rally')
                self.rallyObj = None
                return
            else:
                rdebug.debugMessage('Loaded rally for %s' % self.spawnerObj.templateName, 'rally')
                obj.found = True
                self.rallyObj = obj
                if self.kitsRequstable == 1:
                    pass
                return

        def refresh(self, time):
            if self.cpid is not None:
                cps = filter(lambda cp: cp.getTemplateProperty('ControlPointID') == str(self.cpid), rcore.getControlPoints())
                cp = None
                if len(cps) == 1:
                    cp = cps[0]
                if cp is None:
                    rdebug.debugMessage('Warning: Could not find CP id %s for rally %s' % (self.cpid, self.spawnerObj.templateName), 'rally')
                    return
                newTeam = int(cp.cp_getParam('team'))
                if newTeam != self.currentTeam:
                    self.currentTeam = newTeam
                    rdebug.debugMessage('Flag changed hands, destroying linked rally %s' % self.spawnerObj.templateName, 'rally')
                    self.destroyRallyIfNeeded()
                    return
            enemyTeam = 3 - self.currentTeam
            enemiesnearby = len(rtriggers.getPlayersInAreaofTeam(self.trigger, enemyTeam)) != 0
            if enemiesnearby:
                self.respawnTimeLeft = self.maxRespawnTime
                self.destroyRallyIfNeeded()
            else:
                self.respawnTimeLeft -= time
                if self.respawnTimeLeft <= 0:
                    self.spawnRallyIfNeeded()
            return


def onDestroyMapperRallyTimer(data = ''):
    for teamName in rcore.getTeamNames():
        rcore.deleteObjectsOfTemplate('rallypoint_' + teamName + '_placeable')


def onDestroyLimitedRallyTimer(data = ''):
    for team in [1, 2]:
        teamName = rcore.getTeamName(team)
        for obj in rcore.cleanListOfObjects(rcore.getObjectsOfTemplate('rallypoint_' + teamName + '_placeable', 'dice.hfe.world.ObjectTemplate.PlayerControlObject')):
            obj.totalSpawns = 0
            g_rally_limit[team].append(obj)


def onDestroyRandomRallyTimer(data = ''):
    maximum = rspawner.getRandomSpawnerProperty('gpm_rallypoint_random')
    objects = {1: [],
     2: []}
    for team in [1, 2]:
        teamName = rcore.getTeamName(team)
        for obj in rcore.cleanListOfObjects(rcore.getObjectsOfTemplate('rallypoint_' + teamName + '_placeable_random', 'dice.hfe.world.ObjectTemplate.PlayerControlObject')):
            objects[team].append(obj)

        for obj in rcore.cleanListOfObjects(rcore.getObjectsOfTemplate('rallypoint_' + teamName + '_placeable_noexpire_random', 'dice.hfe.world.ObjectTemplate.PlayerControlObject')):
            objects[team].append(obj)

        total = len(objects[team])
        if not maximum:
            _max = int(float(total) / float(realityserver.C('RALLY_RANDOM')))
        else:
            _max = int(maximum)
        if total == 0 or total < _max:
            continue
        rdebug.debugMessage('random team ' + str(team) + ' total ' + str(total) + ' keep ' + str(_max), 'rally')
        rcore.random.shuffle(objects[team])
        removed = rcore.random.sample(objects[team], int(total - _max))
        for obj in objects[team]:
            remove = False
            for rem in removed:
                if obj.index == rem.index:
                    rcore.deleteObject(obj)
                    remove = True
                    break

            if remove:
                continue
            pos = obj.getPosition()
            rot = obj.getRotation()
            template = obj.templateName.lower()
            expire = False
            if template != 'rallypoint_' + teamName + '_placeable_noexpire_random':
                expire = True
            rcore.deleteObject(obj)
            properties = {'team': team,
             'position': pos,
             'rotation': rot}
            if not expire:
                properties['delay'] = 900
            rspawner.createSpawner(template.replace('_random', '_spawner'), properties, expire, True, True)
            rdebug.debugMessage('random team ' + str(team) + ' expire ' + str(expire), 'rally')


def onDestroyPickupRallyTimer(data = ''):
    for team in [1, 2]:
        teamName = rcore.getTeamName(team)
        if teamName not in realityserver.C('RALLY_RANDOM_PICKUP'):
            continue
        curr = 0
        for obj in rcore.cleanListOfObjects(rcore.getObjectsOfTemplate('rallypoint_' + teamName + '_placeable_noexpire'), 'dice.hfe.world.ObjectTemplate.PlayerControlObject'):
            if curr == len(realityserver.C('RALLY_RANDOM_PICKUP')[teamName]):
                curr = 0
            template = realityserver.C('RALLY_RANDOM_PICKUP')[teamName][curr]
            spawn = realityserver.C('KIT_PICKUP_DELAY')[rkits.getKitTypeString(template)]
            curr += 1
            pos = obj.getPosition()
            properties = {'template': template,
             'delay': spawn,
             'team': team,
             'position': (pos[0] + 1.0, pos[1] + 0.1, pos[2]),
             'rotation': obj.getRotation()}
            rspawner.createSpawner('gpm_rally_pickup_' + str(rcore.getObjectId(obj)), properties, False)
            rdebug.debugMessage('pickup team ' + str(team) + ' template ' + str(template), 'rally')


def onSquadCreated(player, team, squad, name):
    if not rcore.roundStarted():
        return
    g_rallies[team][squad].lastRequestTime = rcore.now()


def onSquadRemoved(team, squad):
    g_rallies[team][squad].deleteRally()


def tryToRearmRallypoints(arg):
    if not rcore.roundStarted():
        return
    for team in [1, 2]:
        playerPositions = {}
        objectPositions = []
        for squad in range(0, 10):
            if squad == 0:
                sl = rcore.getCommander(team)
            else:
                sl = rcore.getSquadLeader(team, squad)
            if not sl:
                continue
            if sl.dead:
                continue
            if g_rallies[team][squad].isRearmed():
                continue
            try:
                position = sl.getDefaultVehicle().getPosition()
            except:
                continue

            playerPositions[squad] = position

        if len(playerPositions) == 0:
            continue
        for outpost in rassets.getAssetsOfType('outpost', team):
            if rassets.isOutpostDisabled(outpost):
                continue
            try:
                position = outpost.getPosition()
            except:
                continue

            objectPositions.append(position)

        cmdPost = rcore.getCommandPost(team)
        if cmdPost:
            try:
                position = cmdPost.getPosition()
                objectPositions.append(position)
            except:
                pass

        depot = rcore.getVehicleDepot(team)
        if depot:
            try:
                position = depot.getPosition()
                objectPositions.append(position)
            except:
                pass

        if len(objectPositions) == 0:
            continue
        for squad, position in playerPositions.items():
            for pos in objectPositions:
                if rcore.getSquareVectorDistance(position, pos) <= CONSTANTS.DISTANCE_CLOSE ** 2:
                    g_rallies[team][squad].rearmRally()
                    rdebug.debugMessage('team %s squad %s rearmed because officer is close to rearm location' % (team, squad), 'rally')
                    break


def onChangedCommander(team, oldCmd, newCmd):
    if oldCmd or newCmd:
        rdebug.debugMessage('team %s deleted commander rally because commander changed' % team, 'rally')
        g_rallies[team][0].deleteRally()


def onCheckCommanderRally(data = ''):
    if not rcore.roundStarted():
        return
    for team in [1, 2]:
        rally = getRallyPoint(team, 0)
        if not rally:
            continue
        cmdr = rcore.getCommander(team)
        if not cmdr or not cmdr.isAlive() or cmdr.isManDown():
            rdebug.debugMessage('cmdr rally team %s deleted because he is down' % team, 'rally')
            g_rallies[team][0].deleteRally()
            continue
        v = cmdr.getDefaultVehicle()
        if not v:
            continue
        cmdrPos = v.getPosition()
        rallyPos = rally.getPosition()
        if rcore.getSquareVectorDistance(cmdrPos, rallyPos) > CONSTANTS.DISTANCE_AREA ** 2:
            rdebug.debugMessage('cmdr rally team %s deleted because he is too far' % team, 'rally')
            g_rallies[team][0].deleteRally()
            continue


def enoughPlayersNearPosForCommanderRally(pos, team):
    if realityserver.C('RALLY_CLOSE_COMMANDER') >= 1 or realityserver.C('RALLY_CLOSE_COMMANDER_SL') >= 1:
        num = realityserver.C('RALLY_CLOSE_COMMANDER')
        num_sl = realityserver.C('RALLY_CLOSE_COMMANDER_SL')
        if num_sl > num:
            num = num_sl
        if num > 32:
            num = 32
        if num_sl > 9:
            num_sl = 9
        if num > 0:
            count = 0
            count_sl = 0
            for p in rcore.getPlayers(team):
                if p.killed:
                    continue
                try:
                    pPos = p.getDefaultVehicle().getPosition()
                except:
                    continue

                distance = rcore.getSquareHorizDistance(pPos, pos)
                if distance <= (CONSTANTS.DISTANCE_CLOSE / 2) ** 2:
                    count += 1
                    if p.isSquadLeader():
                        count_sl += 1
                    if count >= num and count_sl >= num_sl:
                        return True

        return False
    else:
        return True


def enoughPlayersNearPosForSquadRally(pos, team, squad):
    if realityserver.C('RALLY_CLOSE_SQUAD') >= 1:
        num = realityserver.C('RALLY_CLOSE_SQUAD')
        if num > realityserver.C('RALLY_LIMIT_SQUAD'):
            num = realityserver.C('RALLY_LIMIT_SQUAD') - 1
        if num > 0:
            count = 0
            for p in rcore.getPlayersOfSquad(team, squad):
                if p.killed:
                    continue
                if p.isSquadLeader():
                    continue
                distance = rcore.getSquareHorizDistance(p.getDefaultVehicle().getPosition(), pos)
                if distance <= (CONSTANTS.DISTANCE_CLOSE / 2) ** 2:
                    count += 1
                    if count == num:
                        return True

        return False
    else:
        return True


def onRemoteRallyRequestCommand(player, cmd, args):
    rtimer.task(onRemoteRallyRequestCommand_task, -1000.0, (player, cmd, args))


def onRemoteRallyRequestCommand_task(args):
    player, cmd, args = args
    if not player.isValid():
        return
    if not player.isAlive():
        return
    if rcore.isInsideVehicle(player) or rcore.isClimbing(player):
        return
    isCommander = player.isCommander()
    if not isCommander and not player.isSquadLeader():
        return
    v = player.getDefaultVehicle()
    if not v:
        return
    kit = player.getKit()
    if not kit:
        return
    playerPos = v.getPosition()
    playerTeam = player.getTeam()
    playerSquad = player.getSquadId()
    playerKitName = kit.templateName
    if not g_rallies[playerTeam][playerSquad].isRearmed():
        rdebug.debugMessage('blocked due to not rearmed', 'rally')
        return rcore.sendMessageToPlayer(player, 2190318)
    if rkits.getKitTypeString(playerKitName) not in ('officer',):
        return rcore.sendMessageToPlayer(player, 3190409)
    if rkits.getKitTeam(playerKitName) != playerTeam and realityserver.C('KIT_FACTION_LOCKED') == 1:
        return rcore.sendMessageToPlayer(player, 3190409)
    if not isPosFarEnoughFromFob(playerPos, playerTeam):
        return rcore.sendMessageToPlayer(player, 1031113, 1)
    playerTeamName = rcore.getTeamName(playerTeam)
    if isCommander:
        if playerTeamName not in realityserver.C('RALLY_TEAMS_COMMANDER'):
            return rcore.sendMessageToPlayer(player, 3240703)
        if bf2.playerManager.getNumberOfPlayersInTeam(playerTeam) < realityserver.C('RALLY_LIMIT_COMMANDER'):
            return rcore.sendMessageToPlayer(player, 2190318)
        if not enoughPlayersNearPosForCommanderRally(playerPos, playerTeam):
            return rcore.sendMessageToPlayer(player, 2190318)
        badAttemptCooldown = realityserver.C('RALLY_EXPIRATION_COMMANDER')
    else:
        if playerTeamName not in realityserver.C('RALLY_TEAMS'):
            return rcore.sendMessageToPlayer(player, 3240703)
        if rcore.numPlayersInSquad(player) < realityserver.C('RALLY_LIMIT_SQUAD'):
            return rcore.sendSquadRequirementMessageToPlayer(player, realityserver.C('RALLY_LIMIT_SQUAD'))
        if not enoughPlayersNearPosForSquadRally(playerPos, playerTeam, playerSquad):
            return rcore.sendNearSquadRequirementMessageToPlayer(player, realityserver.C('RALLY_CLOSE_SQUAD'))
        badAttemptCooldown = realityserver.C('RALLY_EXPIRATION')
    rallyHandler = g_rallies[playerTeam][playerSquad]
    rallyHandler.deleteRally()
    if rcore.now() - rallyHandler.lastRequestTime < badAttemptCooldown:
        rdebug.debugMessage('blocked due to not enough time since last request or squad start', 'rally')
        return rcore.sendMessageToPlayer(player, 2190318)
    rallyHandler.lastRequestTime = rcore.now()
    if areEnemiesNearby(playerPos, playerTeam):
        rdebug.debugMessage('blocked due to enemy presence', 'rally')
        return rcore.sendMessageToPlayer(player, 2190318)
    rallyHandler.createRally(playerPos)


def isPosFarEnoughFromFob(pos, team):
    for fob in rassets.getAssetsOfType('outpost', team, wreck=True):
        if rcore.getSquareHorizDistance(pos, fob.getPosition()) < 180:
            return False

    return True


def areEnemiesNearby(pos, team):
    area = rcore.getMapArea()
    if area in [CONSTANTS.INSANE, CONSTANTS.HUGE]:
        presenceRadius = realityserver.C('RALLY_AREA_HUGE')
    elif area in [CONSTANTS.BIG]:
        presenceRadius = realityserver.C('RALLY_AREA_BIG')
    else:
        presenceRadius = realityserver.C('RALLY_AREA_SMALL')
    presenceRadius = int(presenceRadius * realityserver.C('RALLY_SET_MULTIPLIER'))
    presenceRadiusSquared = presenceRadius ** 2
    for enemyPlayer in rcore.getPlayers(3 - team):
        enemyV = enemyPlayer.getDefaultVehicle()
        if not enemyV:
            continue
        if enemyPlayer.isManDown():
            continue
        if rvehicles.isFlyingVehicle(enemyV):
            continue
        if rcore.getSquareVectorDistance(enemyV.getPosition(), pos) < presenceRadiusSquared:
            return True

    return False


def isSupporting(asset, pos):
    assetID = rcore.getObjectId(asset)
    if not assetID:
        rdebug.debugMessage('could not check support from ' + str(asset.templateName) + ' because it has no objectID', 'rally')
        return
    if rcore.getSquareHorizDistance(asset.getPosition(), pos) > Rally.supportRadiusSquared:
        return False
    rdebug.debugMessage(str(asset.templateName) + ' (' + str(assetID) + ') is supporting a rally', 'rally')
    return True


def posHasOutpostSupport(pos, team):
    for outpost in rassets.getAssetsOfType('outpost', team):
        if rassets.isOutpostDisabled(outpost):
            continue
        if isSupporting(outpost, pos):
            return True

    return False


def posHasControlPointSupport(pos, team):
    for cp in rcore.getControlPoints(team):
        if isSupporting(cp, pos):
            return True

    return False


def posHasVehicleSupport(pos, team):
    for player in rcore.getAlivePlayers(team):
        if not rcore.isInsideVehicle(player):
            continue
        vehicle = player.getVehicle()
        if not vehicle:
            continue
        split = vehicle.templateName.lower().split('_')
        if len(split) < 2:
            continue
        typeName = split[1]
        teamName = rcore.getTeamName(team)
        if typeName not in realityserver.C('RALLY_SUPPORT_VEHICLE_TYPES') or vehicle.templateName not in realityserver.C('KIT_SUPPLY_OBJECTS_VEHICLES')[teamName]:
            continue
        if isSupporting(vehicle, pos):
            return True

    return False


def onRallyDestroyed(rally, attacker):
    templateName = rally.templateName.lower()
    if not templateName.startswith('rallypoint'):
        return
    arr = templateName.split('_')
    if len(arr) < 3:
        return
    if not arr[2].isdigit():
        return
    team = rcore.getTeamNumber(arr[1])
    squad = int(arr[2])
    rdebug.debugMessage('t:%s, s:%s was physically destroyed' % (team, squad), 'rally')
    rallyHandler = g_rallies[team][squad]
    rallyHandler.deleteRally()
    rallyHandler.rearmTimer.start(Rally.rearmIntervalOverrun)


def getRallyPoint(team, squad):
    rallyHandler = g_rallies[team][squad]
    rallypoint = rallyHandler.engineObject
    if rallypoint and rallypoint.isValid() and rallypoint.getPosition() != (0, 0, 0):
        return rallypoint
    else:
        return None


squadRallyRegex = re.compile('rallypoint_.*_\\d', re.IGNORECASE)

def onSquadRallySpawn(obj):
    if not squadRallyRegex.match(obj.templateName):
        return
    template = obj.templateName
    team = template.split('_')[1]
    squad = int(template.split('_')[2])
    if rcore.getTeamName(1).lower() == team:
        g_rallies[1][squad].loadObject(obj)
    else:
        g_rallies[2][squad].loadObject(obj)


def getRallyFromSpawngroup(spawngroup):
    return g_rallySpawnGroups.get(spawngroup, None)


class Rally(object):
    overrunRadius = 1
    supportRadiusSquared = 1
    rearmInterval = 1
    rearmIntervalOverrun = 1

    def __init__(self, team, squad):
        self.team = team
        self.squad = squad
        self.engineObject = None
        self.isEngineObjectLoading = False
        self.spawnGroup = None
        self.trigger = 0
        self.lastRequestTime = 0
        self.rearmTimer = rtimer.coolDown(self.rearmRally)
        self.expireTimer = None
        self.reset()
        return

    def reset(self):
        if self.squad == 0:
            self.expireTime = realityserver.C('RALLY_EXPIRATION_COMMANDER')
        else:
            self.expireTime = realityserver.C('RALLY_EXPIRATION')
        self.engineObject = None
        self.isEngineObjectLoading = False
        self.spawnGroup = None
        self.destroyAreaTrigger()
        self.lastRequestTime = 0
        self.destroyExpirationTimer()
        self.rearmTimer.reset()
        return

    def createRally(self, pos):
        rdebug.debugMessage('Creating rally for for t:%s, s:%s' % (self.team, self.squad), 'rally')
        templateName = 'rallypoint_' + rcore.getTeamName(self.team) + '_' + str(self.squad)
        rspawner.createSpawner(templateName + '_spawner', {'team': self.team,
         'position': (pos[0], pos[1] - 1.0, pos[2]),
         'rotation': (0, 0, 0)})
        self.isEngineObjectLoading = True
        if rmemory.isWindowsListenServer:
            rtimer.task(self.loadObject, rcore.LOAD_OBJECT_DELAY)
        self.startExpirationTimer()
        self.rearmTimer.start(Rally.rearmInterval)
        event = revents.getEvents('RallyCreated')
        revents.sendToHandlers(event, self.team, self.squad, pos)

    def loadObject(self, obj = None):
        if obj is None:
            if not self.isEngineObjectLoading:
                return
            rallyList = rcore.getObjectsOfTemplate('rallypoint_' + rcore.getTeamName(self.team) + '_' + str(self.squad), 'dice.hfe.world.ObjectTemplate.PlayerControlObject')
            rallyList = list(rcore.cleanListOfObjects(rallyList))
            if len(rallyList) == 0:
                rdebug.debugMessage('Error: Found 0 rallies', 'rally')
                return
            if len(rallyList) > 1:
                rdebug.debugMessage('Error: Found more than 1 rally', 'rally')
                return
            rdebug.debugMessage('Rally object loaded succesfully for t:%s, s:%s' % (self.team, self.squad), 'rally')
            obj = rallyList[0]
        self.engineObject = obj
        self.isEngineObjectLoading = False
        spawnpoint = rcore.getFirstChild(obj, lambda child: 'spawnpoint' in child.templateName)
        self.spawnGroup = rmemory.getSpawnPointSpawnGroup(spawnpoint)
        g_rallySpawnGroups[self.spawnGroup] = self
        rdebug.debugMessage('Rally spawn group %d' % self.spawnGroup, 'rally')
        self.createTrigger()
        return

    def deleteRally(self):
        rdebug.debugMessage('Rally delete t:%s, s:%s' % (self.team, self.squad), 'rally')
        rcore.deleteObjectsOfTemplate('rallypoint_' + rcore.getTeamName(self.team) + '_' + str(self.squad))
        if not self.isDeployed():
            return
        else:
            self.isEngineObjectLoading = False
            self.engineObject = None
            if self.spawnGroup in g_rallySpawnGroups:
                del g_rallySpawnGroups[self.spawnGroup]
            self.spawnGroup = None
            self.destroyAreaTrigger()
            self.destroyExpirationTimer()
            event = revents.getEvents('RallyDelete')
            revents.sendToHandlers(event, self.team, self.squad)
            return

    def isDeployed(self):
        return bool(self.engineObject) or bool(self.isEngineObjectLoading)

    def startExpirationTimer(self):
        """
        Rally expiration. Check every expire time if rally is being supported, and destroy it if not.
        :return:
        """
        self.destroyExpirationTimer()
        self.expireTimer = rtimer.Timer(self.checkExpire, self.expireTime, 1)
        self.expireTimer.setRecurring(self.expireTime)

    def checkExpire(self, data = None):
        if not self.isRallySupported():
            rdebug.debugMessage('Rally expired t:%s, s:%s' % (self.team, self.squad), 'rally')
            self.deleteRally()

    def isRallySupported(self):
        if not self.engineObject:
            return False
        pos = self.engineObject.getPosition()
        if posHasOutpostSupport(pos, self.team):
            return True
        if posHasVehicleSupport(pos, self.team):
            return True
        return False

    def destroyExpirationTimer(self):
        if self.expireTimer:
            self.expireTimer.destroy()
            self.expireTimer = None
        return

    def createTrigger(self):
        self.destroyAreaTrigger()
        self.trigger = rtriggers.createTrigger(self.engineObject, callback=self.onEnemyEnteredTrigger, radius=Rally.overrunRadius, team=3 - self.team, ignoreFlyingVehicles=True)
        rdebug.debugMessage('trigger created...: %s' % self.trigger, 'rally')

    def onEnemyEnteredTrigger(self, TriggerID, PlayerEntered, isEntering, Data):
        """
        When enemy enters rally radius
        """
        if not self.isDeployed():
            rdebug.debugMessage('Trigger %s fired but rally t:%s, s:%s is not deployed' % (TriggerID, self.team, self.squad), 'rally')
            return
        if realityserver.C('RALLY_CLOSE_DESTROY') == 0 or len(rtriggers.getPlayersInArea(TriggerID)) < realityserver.C('RALLY_CLOSE_DESTROY'):
            return
        rdebug.debugMessage('rally deleted, trigger overrun t:%s, s:%s' % (self.team, self.squad), 'rally')
        self.deleteRally()
        self.rearmTimer.start(Rally.rearmIntervalOverrun)

    def destroyAreaTrigger(self):
        if self.trigger != 0:
            rdebug.debugMessage('rally trigger %s destroyed, t:%s, s:%s' % (self.trigger, self.team, self.squad), 'rally')
            rtriggers.deleteTrigger(self.trigger)
            self.trigger = 0

    def rearmRally(self, data = None):
        if not self.isRearmed():
            self.rearmTimer.reset()
            player = rcore.getSquadLeader(self.team, self.squad)
            rcore.sendMessageToPlayer(player, 1220803, 2)
            rdebug.debugMessage('rally rearmed, t:%s, s:%s' % (self.team, self.squad), 'rally')

    def isRearmed(self):
        return not self.rearmTimer.isOnCoolDown()