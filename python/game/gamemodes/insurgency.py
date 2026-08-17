import json
import os
import random
import zipfile
import bf2
import game.realitycivilian as rcivilian
import game.realityconstants as CONSTANTS
import game.realitycore as rcore
import game.realitydebug as rdebug
import game.realityevents as revents
import game.realityflags as rflags
import game.realitygamemode as rgamemode
import game.realitykits as rkits
import game.realitylocalization as rlocalization
import game.realitymarkers as rmarkers
import game.realityscoring as rscoring
import game.realityserver as realityserver
import game.realityspawner as rspawner
import game.realitytimer as rtimer
import host

def init():
    rgamemode.setCurrentGameMode(PRInsurgency())
    print 'gpm_insurgency.py initialized'


def deinit():
    rgamemode.setCurrentGameMode()
    print 'gpm_insurgency.py uninitialized'


class PRInsurgency(rflags.PRFlags):

    def __init__(self):
        rflags.PRFlags.__init__(self)
        self.g_timer_message = None
        self.g_destroyed = 0
        self.g_max = 0
        self.g_min = 0
        self.g_intel = 0
        self.g_active = 0
        self.g_objectives = []
        self.g_insurgent = None
        self.g_attacker = None
        return

    def registerHandlers(self):
        rflags.PRFlags.registerHandlers(self)
        host.registerHandler('ControlPointNeutralized', self.onCPNeutralized)
        host.registerHandler('ControlPointCaptured', self.onCPCaptured)
        host.registerHandler('VehicleDestroyed', self.onObjectiveDestroyed)
        host.registerHandler('PlayerEnemyKilled', self.onInsurgentKilledIntel)
        host.registerHandler('PlayerEnemyKilled', self.onAttackerKilled)
        host.registerHandler('PositionsUpdated', self.onPositionsUpdated)
        host.registerHandler('ExitVehicle', self.onCivilianCarUse)
        host.registerHandler('VehicleDestroyed', self.onCivilianCarDestroyed)

    def unregisterHandlers(self):
        rflags.PRFlags.unregisterHandlers(self)
        host.unregisterHandler(self.onCPNeutralized)
        host.unregisterHandler(self.onCPCaptured)
        host.unregisterHandler(self.onObjectiveDestroyed)
        host.unregisterHandler(self.onInsurgentKilledIntel)
        host.unregisterHandler(self.onAttackerKilled)
        host.unregisterHandler(self.onPositionsUpdated)
        host.unregisterHandler(self.onCivilianCarUse)
        host.unregisterHandler(self.onCivilianCarDestroyed)

    def onGameStatusChanged(self, status):
        rflags.PRFlags.onGameStatusChanged(self, status)
        if status == bf2.GameStatus.Playing:
            self.setupObjectives()
            host.sh_setEnableCommander(realityserver.C('INSURGENCY_COMMANDER'))
            rcivilian.init(self)
            self.g_timer_message = rtimer.Timer(self.messageTeams, realityserver.C('STARTDELAY'), 1, '')
            self.g_timer_message.setRecurring(300)
            self.g_destroyed = 0
            self.g_intel = 0
            self.g_active = 0
            if self.g_max == 0:
                if bf2.gameLogic.getTickets(1) > 10:
                    self.g_max = realityserver.C('INSURGENCY_OBJECTIVES') + realityserver.C('INSURGENCY_ACTIVE') - 1
                    self.g_min = realityserver.C('INSURGENCY_OBJECTIVES')
                else:
                    self.g_max = bf2.gameLogic.getTickets(1) + realityserver.C('INSURGENCY_ACTIVE') - 1
                    self.g_min = bf2.gameLogic.getTickets(1)
                bf2.gameLogic.setTickets(self.g_attacker, int(bf2.gameLogic.getTickets(self.g_attacker)))
                bf2.gameLogic.setTickets(self.g_insurgent, int(self.g_min))
                self.g_objectives = self.g_objectives[0:self.g_max]
            rtimer.fireOnce(self.initialObjectives, realityserver.C('STARTDELAY') - 30)
        elif status == bf2.GameStatus.EndGame:
            rcivilian.deinit()
            for obj in self.g_objectives:
                obj.destroy()

            del self.g_objectives[:]
            self.destroyMessageTimer()

    def destroyMessageTimer(self):
        if self.g_timer_message:
            self.g_timer_message.destroy()
            self.g_timer_message = None
        return

    def setupObjectives(self):
        if len(self.g_objectives) != 0:
            return
        else:
            objectivePosRots = []
            try:
                zipfilepath = os.path.join(host.sgl_getModDirectory(), 'levels', host.sgl_getMapName(), 'server.zip')
                layer = rcore.getMapLayer()
                zFile = zipfile.ZipFile(zipfilepath, 'r')
                jsonpath = os.path.join('gamemodes', 'gpm_insurgency', str(layer), 'caches.json')
                jsonpath = jsonpath.replace('\\', '/')
                arrayOfCaches = json.loads(zFile.read(jsonpath))
                for cacheInfo in arrayOfCaches:
                    objectivePosRots.append((tuple(cacheInfo['position']), tuple(cacheInfo['rotation'])))

                zFile.close()
            except Exception as e:
                rdebug.debugMessage("Could not load map's cache list:", 'gamemode')
                rdebug.debugMessage('%s' % e, 'gamemode')

            spawners = rcore.cleanListOfObjects(revents.getOnPlayingObjectSpawners())
            for spawner in spawners:
                host.rcon_invoke('ObjectTemplate.active %s' % spawner.templateName)
                templates = host.rcon_invoke('ObjectTemplate.objectTemplate').split('\n')
                if 'ammocache' in templates:
                    objectivePosRots.append((spawner.getPosition(), spawner.getRotation()))
                    rcore.deleteObject(spawner)

            def deletedCachesDelayed(args = None):
                objectives = rcore.cleanListOfObjects(rcore.getObjectsOfTemplate('ammocache'), True, True)
                for obj in objectives:
                    rcore.deleteObject(obj)

            rtimer.fireOnce(deletedCachesDelayed, 0.5)
            self.g_insurgent = 1
            self.g_attacker = 2
            random.shuffle(objectivePosRots)
            final = []
            if len(objectivePosRots) > 10:
                distanceBetweenCaches = 200
                while len(final) < 10 and distanceBetweenCaches >= 0:
                    distance = rcore.getRelativeDistance(distanceBetweenCaches, True)
                    distanceBetweenCaches -= 50
                    for posRot in objectivePosRots:
                        bad = False
                        for fin in final:
                            if posRot == fin:
                                bad = True
                                break
                            if rcore.getSquareHorizDistance(posRot[0], fin[0]) <= distance:
                                bad = True
                                break

                        if bad:
                            continue
                        final.append(posRot)
                        if len(final) == 10:
                            break

            else:
                for posRot in objectivePosRots:
                    final.append(posRot)

                self.g_max = len(final)
                self.g_min = self.g_max - 1
            index = 0
            for posRot in final:
                self.g_objectives.append(PRInsurgency.PRObjective(index, posRot[0], posRot[1], self.g_insurgent))
                index += 1

            return

    def initialObjectives(self, data = ''):
        self.updateObjectives(True)
        self.updateMarkers()

    def updateObjectives(self, initial = False):
        while self.g_active < realityserver.C('INSURGENCY_ACTIVE'):
            objectives = [ o for o in self.g_objectives if not o.active ]
            objective = objectives[0]
            if initial:
                objective.setActive(True, True)
                initial = False
            else:
                objective.setActive(self.revealOnCreation())
            self.g_active += 1

    def updateMarkers(self):
        for cp in rcore.getControlPoints():
            if not self.isCPCapturable(cp):
                continue
            team1 = self.isCPCapturableByTeam(cp, 1)
            team2 = self.isCPCapturableByTeam(cp, 2)
            team = cp.cp_getParam('team')
            pos = cp.getPosition()
            if team == 0:
                if team1:
                    rmarkers.markerPointAttack(1, pos, cp.templateName)
                elif team2:
                    rmarkers.markerPointDefend(1, pos, cp.templateName)
                if team2:
                    rmarkers.markerPointAttack(2, pos, cp.templateName)
                elif team1:
                    rmarkers.markerPointDefend(2, pos, cp.templateName)
            elif team == 1:
                if team2:
                    rmarkers.markerPointAttack(2, pos, cp.templateName)
                    rmarkers.markerPointDefend(1, pos, cp.templateName)
                else:
                    rmarkers.deleteMarkerTeams(cp.templateName)
            elif team == 2:
                if team1:
                    rmarkers.markerPointAttack(1, pos, cp.templateName)
                    rmarkers.markerPointDefend(2, pos, cp.templateName)
                else:
                    rmarkers.deleteMarkerTeams(cp.templateName)

    def onTimeLimitReached(self, value):
        if self.g_destroyed < self.g_min:
            self.endGame(self.g_insurgent, 3)
        else:
            rflags.PRFlags.onTimeLimitReached(self, value)

    def onAttackerKilled(self, victim, attacker, weapon, assists, obj):
        if victim.getTeam() == self.g_insurgent or attacker.getTeam() == self.g_attacker:
            return
        found = False
        attackVehicle = attacker.getVehicle()
        if not attackVehicle:
            return
        attackPos = attackVehicle.getPosition()
        victimVehicle = victim.getVehicle()
        if not victimVehicle:
            return
        victimPos = victimVehicle.getPosition()
        for objective in self.g_objectives:
            if objective.isRevealed():
                if rcore.getSquareHorizDistance(attackPos, objective.pos) <= CONSTANTS.DISTANCE_AREA ** 2 or rcore.getSquareHorizDistance(victimPos, objective.pos) <= CONSTANTS.DISTANCE_AREA ** 2:
                    found = True
                    break

        if not found:
            return
        team = self.g_insurgent
        player = attacker
        event = revents.getEvents('PositionDefended')
        revents.sendToHandlers(event, team, player)

    def onInsurgentKilledIntel(self, victim, attacker, weapon, assists, obj):
        if victim.getTeam() != self.g_insurgent or attacker.getTeam() != self.g_attacker:
            return
        try:
            weaponName = weapon.templateName.lower()
        except:
            weaponName = 'vehicle'

        try:
            vehicleType = attacker.getVehicle().templateName.lower().split('_')[1]
        except:
            vehicleType = 'soldier'

        if not rcivilian.isCivilian(victim):
            if rcivilian.isArrestWeapon(weaponName):
                self.addIntelPoints(realityserver.C('INSURGENCY_INTEL_CAPTURE'), 'insurgent capture ' + victim.getName())
            elif vehicleType not in realityserver.C('INSURGENCY_INTEL_EXCLUDE_VEHICLES'):
                try:
                    vicPos = victim.getDefaultVehicle().getPosition()
                    attPos = attacker.getDefaultVehicle().getPosition()
                except:
                    vicPos = (0, 0, 0)
                    attPos = (0, 0, 0)

                if rcore.getSquareVectorDistance(vicPos, attPos) <= realityserver.C('INSURGENCY_INTEL_MAX_RANGE') ** 2:
                    self.addIntelPoints(realityserver.C('INSURGENCY_INTEL_KILL'), 'insurgent kill ' + victim.getName())

    def addIntelPoints(self, points, debug = ''):
        self.g_intel += points
        intel = realityserver.C('INSURGENCY_REVEAL_INTEL')
        if bf2.playerManager.getNumberOfPlayers() < 32:
            intel /= 2
        self.g_intel = max(min(intel, self.g_intel), -intel)
        if rdebug.isDebugEnabled('gamemode') and debug != '':
            rdebug.debugMessage(debug + ' intel points ' + str(points) + ' total ' + str(self.g_intel), 'gamemode')
        self.checkIntel()
        event = revents.getEvents('InsurgencyIntelChanged')
        revents.sendToHandlers(event, self.g_intel)

    def revealOnCreation(self):
        reqIntel = realityserver.C('INSURGENCY_REVEAL_INTEL')
        if bf2.playerManager.getNumberOfPlayers() < 32:
            reqIntel /= 2
        if self.g_intel < reqIntel:
            return False
        self.g_intel = 0
        event = revents.getEvents('InsurgencyIntelChanged')
        revents.sendToHandlers(event, self.g_intel)
        return True

    def checkIntel(self):
        notRevealed = [ o for o in self.g_objectives if o.active and not o.isRevealed() ]
        if len(notRevealed) == 0:
            return
        reqIntel = realityserver.C('INSURGENCY_REVEAL_INTEL')
        if bf2.playerManager.getNumberOfPlayers() < 32:
            reqIntel /= 2
        if self.g_intel < reqIntel:
            return
        notRevealed[0].setRevealed()
        self.g_intel = 0

    def messageTeams(self, data = ''):
        if self.g_max - self.g_destroyed == 0:
            return
        rcore.sendMessageToTeam(self.g_insurgent, rcore.BIGCOLOREDTEXT + rlocalization.t('insurgency_ins_total', {'num': self.g_max - self.g_destroyed}))
        if self.g_destroyed + 1 == self.g_min:
            rcore.sendMessageToTeam(self.g_insurgent, rcore.BIGCOLOREDTEXT + rlocalization.t('insurgency_ins_last'))
        else:
            rcore.sendMessageToTeam(self.g_insurgent, rcore.BIGCOLOREDTEXT + rlocalization.t('insurgency_ins_defend'))
        rcore.sendMessageToTeam(self.g_attacker, rcore.BIGCOLOREDTEXT + rlocalization.t('insurgency_coa_total', {'num': self.g_max - self.g_destroyed}))
        rcore.sendMessageToTeam(self.g_attacker, rcore.BIGCOLOREDTEXT + rlocalization.t('insurgency_coa_destroy', {'num': self.g_min - self.g_destroyed}))

    def onPositionsUpdated(self, positions):
        if realityserver.C('OUTPOST_CLOSE_DISABLE') == 0:
            return
        playerPositions = positions[rcore.getOtherTeam(self.g_insurgent)]
        objectPositions = {}
        enable = []
        for objective in self.g_objectives:
            if not objective.active:
                continue
            if not objective.isRevealed() or objective.isRevealedToAttacker():
                continue
            if objective.disabled and rcore.now() - objective.disabled >= realityserver.C('OUTPOST_LOST_INTERVAL'):
                enable.append(objective)
            objectPositions[objective] = objective.pos

        for objective, count in rcore.getCloseProximity(playerPositions, objectPositions, realityserver.C('OUTPOST_CLOSE_DISABLE')).items():
            if rdebug.isDebugEnabled('gamemode'):
                rdebug.debugMessage('disabling cache %s because %s enemies are close' % (objective.index, count), 'gamemode')
            objective.disableObjective()
            if objective in enable:
                enable.remove(objective)

        for objective in enable:
            objective.enableObjective()

    def onCPNeutralized(self, cp, team, players):
        self.updateMarkers()

    def onCPCaptured(self, cp, team, players):
        self.updateMarkers()

    def onObjectiveDestroyed(self, obj, attacker):
        if obj.templateName.lower() != 'ammocache':
            return
        else:
            foundObjective = None
            for objective in self.g_objectives:
                if objective.isRevealed() and rcore.getSquareHorizDistance(objective.pos, obj.getPosition()) <= 4:
                    foundObjective = objective
                    break

            if foundObjective is None:
                return
            foundObjective.destroy()
            self.g_objectives.remove(foundObjective)
            self.g_destroyed += 1
            self.g_active -= 1
            rcore.sendMessageToAll(rcore.BIGCOLOREDTEXT + rlocalization.t('insurgency_destroyed', {'num': self.g_destroyed,
             'total': self.g_min}))
            event = revents.getEvents('InsurgencyCacheDestroyed')
            revents.sendToHandlers(event, foundObjective)
            if attacker:
                attackerName = attacker.getName()
                attackerTeam = attacker.getTeam()
                if rdebug.isDebugEnabled('gamemode'):
                    rdebug.debugMessage('objective ' + str(foundObjective.index) + ' destroyed by ' + attackerName + ' team ' + str(attackerTeam), 'gamemode')
                if attackerTeam == self.g_attacker:
                    rscoring.addScore(attacker, realityserver.C('INSURGENCY_DESTROY_POINTS'), rscoring.SCORE_TEAMWORK)
                    for player in rcore.getPlayers(attackerTeam):
                        if player.isCommander() or player.getSquadId() != 0:
                            rcore.setSpawnPenalty(player, realityserver.C('SPAWN_PENALTY_OBJECTIVE'), 'objective destroyed')

                else:
                    rscoring.zeroScore(attacker)
                    rscoring.addScore(attacker, realityserver.C('INSURGENCY_TREASON_POINTS'), rscoring.SCORE_TEAMWORK, False)
                    rcore.setTemporarySpawnPenalty(attacker, realityserver.C('INSURGENCY_TREASON_PENALTY'), 'insurgency treason')
                    rcore.killPlayer(attacker)
                    rcore.sendMessageToTeam(attackerTeam, rcore.BIGCOLOREDTEXT + rlocalization.t('insurgency_traitor', {'name': attackerName}))
            self.addTickets(self.g_insurgent, -1, 'objective lost')
            if self.g_destroyed != self.g_min:
                self.addTickets(self.g_attacker, realityserver.C('INSURGENCY_DESTROY_TICKETS'), 'objective destroyed')
            else:
                self.endGame(self.g_attacker, 3)
                return
            self.updateObjectives()
            return

    def onCivilianCarUse(self, playerObject, vehicleObject):
        if playerObject.getTeam() != self.g_insurgent:
            return
        if vehicleObject.templateName.lower() not in realityserver.C('INSURGENCY_CIV_CARS'):
            return
        vehicleObject.lastUse = rcore.now()

    def onCivilianCarDestroyed(self, vehicleObject, attackerObject):
        if vehicleObject is None or attackerObject is None:
            return
        elif attackerObject.getTeam() == self.g_insurgent:
            return
        elif len(vehicleObject.getOccupyingPlayers()) != 0:
            return
        elif vehicleObject.templateName.lower() not in realityserver.C('INSURGENCY_CIV_CARS'):
            return
        elif hasattr(vehicleObject, 'lastUse') and rcore.now() - vehicleObject.lastUse <= realityserver.C('INSURGENCY_INTERVAL_CIV_CARS'):
            return
        else:
            tooCloseDist = realityserver.C('CIV_HELP_DISTANCE_XZ') ** 2
            vehiclePos = vehicleObject.getPosition()
            for p in rcore.getPlayers(self.g_insurgent):
                if not p.isAlive() or rcivilian.isCivilian(p):
                    continue
                try:
                    pPos = p.getDefaultVehicle().getPosition()
                except:
                    continue

                distance = (pPos[0] - vehiclePos[0]) ** 2
                if distance > tooCloseDist:
                    continue
                distance += (pPos[2] - vehiclePos[2]) ** 2
                if distance > tooCloseDist:
                    continue
                modifier = tooCloseDist / realityserver.C('CIV_HELP_DISTANCE_Y') ** 2
                distance += modifier * (pPos[1] - vehiclePos[1]) ** 2
                if distance <= tooCloseDist:
                    return

            self.addIntelPoints(realityserver.C('INSURGENCY_INTEL_CIV_CARS'), 'civilian car kill')
            rscoring.addScore(attackerObject, realityserver.C('INSURGENCY_DESTROY_CIV_CARS'), rscoring.SCORE_NORMAL)
            rcore.sendMessageToPlayer(attackerObject, 2020903)
            return

    def getCPTicketLoss(self, cp, team):
        return 0

    def onPlayerDeathTicket(self, victim, vehicle):
        if victim and victim.getTeam() != self.g_insurgent:
            rgamemode.PRGameMode.onPlayerDeathTicket(self, victim, vehicle)

    def onPlayerKilledTicket(self, victim, attacker, weapon, assists, soldier):
        if victim and victim.getTeam() != self.g_insurgent:
            rgamemode.PRGameMode.onPlayerKilledTicket(self, victim, attacker, weapon, assists, soldier)

    def onVehicleDestroyedTicket(self, vehicle, attacker):
        if vehicle and vehicle.getTeam() != self.g_insurgent:
            rgamemode.PRGameMode.onVehicleDestroyedTicket(self, vehicle, attacker)

    def getType(self):
        return 'insurgency'

    def getBf2Type(self):
        return 'gpm_insurgency'

    def checkAssetPlacementRestrictions(self, asset, position, player):
        if asset == 'mortar':
            if player.getTeam() == self.g_attacker:
                rcore.sendMessageToPlayer(player, 3240703)
                return False
        if asset.startswith('roadblock'):
            mindist = 121
        else:
            mindist = 49
        for obj in self.g_objectives:
            if obj.active:
                if rcore.getSquareVectorDistance(position, obj.pos) < mindist:
                    rcore.sendMessageToPlayer(player, 1031113, 1)
                    return False

        return True

    def isInsurgent(self, player):
        return player.getTeam() == self.g_insurgent

    class PRObjective(object):

        def __init__(self, index, position, rotation, team):
            self.index = index
            self.pos = position
            self.rot = rotation
            self.team = team
            self.active = False
            self.revealedPos = None
            self.revealTimer = None
            self.disabled = None
            self.defenseMarker = None
            self.attackMarker = None
            self.PICKUPKITS = {'meinsurgent': [{'template': 'meinsurgent_riflemanat_pickup',
                              'position': (0, 0.4, 0),
                              'rotation': (-90, 0, 0),
                              'distance': -0.3},
                             {'template': 'meinsurgent_riflemanat_pickup',
                              'position': (0, 0.3, 0),
                              'rotation': (-90, 0, 0),
                              'distance': 0.3},
                             {'template': 'meinsurgent_support_pickup',
                              'position': (0, 0.2, 0),
                              'rotation': (-90, 0, 0),
                              'distance': 0.8},
                             {'template': 'meinsurgent_support_alt_pickup',
                              'position': (0, 0.2, 0),
                              'rotation': (-90, 0, 0),
                              'distance': 1.4}]}
            return

        def destroy(self):
            self.deletePickupKits()
            self.disableObjective()
            self.destroyRevealTimer()
            if self.defenseMarker:
                rmarkers.deleteMarker(self.defenseMarker)
            if self.attackMarker:
                rmarkers.deleteMarker(self.attackMarker)
            self.active = False

        def isRevealed(self):
            return self.revealedPos is not None

        def isRevealedToAttacker(self):
            return self.isRevealed() and self.revealTimer is None

        def setActive(self, revealed, initial = False):
            self.active = True
            if revealed:
                self.setRevealed(initial)
            else:
                self.defenseMarker = rmarkers.markerPointDefend(self.team, self.pos, self.index)
            if rdebug.isDebugEnabled('gamemode'):
                rdebug.debugMessage('new objective created', 'gamemode')
            event = revents.getEvents('InsurgencyCacheAdded')
            revents.sendToHandlers(event, self)

        def setRevealed(self, initial = False):
            self.revealedPos = rcore.getAreaPositionFromPosition(self.pos, -60, 60)
            if rdebug.isDebugEnabled('gamemode'):
                rdebug.debugMessage('revealed objective ' + str(self.index), 'gamemode')
            revealTime = realityserver.C('INSURGENCY_REVEAL_INTERVAL')
            if initial:
                revealTime += 30
            else:
                rcore.sendMessageToTeam(self.team, rcore.BIGCOLOREDTEXT + rlocalization.t('insurgency_ins_intel'))
            self.defenseMarker = rmarkers.markerAreaDefendRevealed(self.team, self.pos, self.index)
            self.revealTimer = rtimer.Timer(self.revealObjectiveToAttacker, revealTime, 1)
            self.createObjective()

        def createObjective(self):
            rspawner.createSpawner('ammocache_spawner_temp_%s' % self.index, {'team': self.team,
             'template': 'ammocache',
             'position': self.pos,
             'rotation': self.rot})
            self.createPickupKits()
            self.enableObjective()

        def createPickupKits(self):
            teamName = rcore.getTeamName(self.team)
            if teamName not in self.PICKUPKITS:
                return
            for num, p in enumerate(self.PICKUPKITS[teamName]):
                rspawner.createSpawner('gpm_insurgency_pickup_%s_%s' % (self.index, num), {'template': p['template'],
                 'delay': realityserver.C('KIT_PICKUP_DELAY')[rkits.getKitTypeString(p['template'])],
                 'team': self.team,
                 'position': rcore.getPositionFromPositionAndRotation((self.pos[0] + p['position'][0], self.pos[1] + p['position'][1], self.pos[2] + p['position'][2]), (self.rot[0] + p['rotation'][0], self.rot[1] + p['rotation'][1], self.rot[2] + p['rotation'][2]), p['distance']),
                 'rotation': self.rot}, False)

        def deletePickupKits(self):
            teamName = rcore.getTeamName(self.team)
            if teamName not in self.PICKUPKITS:
                return
            for num, p in enumerate(self.PICKUPKITS[teamName]):
                rspawner.deleteSpawner('gpm_insurgency_pickup_%s_%s' % (self.index, num))

            if rdebug.isDebugEnabled('gamemode'):
                rdebug.debugMessage('deleted objective pickup kits ' + str(self.index), 'gamemode')

        def enableObjective(self):
            self.disabled = None
            rspawner.createSpawner('gpm_insurgency_spawn_spawner_%s' % self.index, {'team': self.team,
             'template': 'fixed_spawn_cache',
             'position': rcore.getPositionFromPositionAndRotation((self.pos[0], self.pos[1] + 1.5, self.pos[2]), self.rot, 1.0),
             'rotation': self.rot})
            if rdebug.isDebugEnabled('gamemode'):
                rdebug.debugMessage('cache spawn created %s' % self.index, 'gamemode')
            return

        def disableObjective(self):
            self.disabled = rcore.now()
            for spawn in rcore.cleanListOfObjects(rcore.getObjectsOfTemplate('fixed_spawn_cache')):
                if spawn.getTeam() != self.team:
                    continue
                if rcore.getSquareHorizDistance(spawn.getPosition(), self.pos) <= 100:
                    rcore.deleteObject(spawn)
                    if rdebug.isDebugEnabled('gamemode'):
                        rdebug.debugMessage('cache spawn deleted %s' % self.index, 'gamemode')

        def revealObjectiveToAttacker(self, data = ''):
            aTeam = rcore.getOtherTeam(self.team)
            rcore.sendMessageToTeam(aTeam, rcore.BIGCOLOREDTEXT + rlocalization.t('insurgency_coa_intel'))
            self.attackMarker = rmarkers.markerAreaAttackRevealed(aTeam, self.revealedPos, self.index)
            self.disableObjective()
            self.destroyRevealTimer()
            event = revents.getEvents('InsurgencyCacheRevealed')
            revents.sendToHandlers(event, self)

        def destroyRevealTimer(self):
            if self.revealTimer:
                self.revealTimer.destroy()
                self.revealTimer = None
            return