import math
import random
import bf2
import host
import realityconstants as rconstants
import realitycore as rcore
import realitydebug as rdebug
import realityevents as revents
import realitykits as rkits
import realitymemory as rmemory
import realityserver
import realitytimer as rtimer
import realityvehicles_settings as rvehicles_settings
import realityzones as rzones
_invalid_seat_timers = {}
VEHICLE_CHECK_INTERVAL = 1.0
CYCLE_SEAT_COOLDOWN = 0.5
UPSIDE_DOWN_INTERVAL = 5.0
UPSIDE_DOWN_DAMAGE_PER_INTERVAL = 0.2
MIN_DAMAGE = 0.05
MAX_DISABLE_HP = 0.65
VEHICLE_REPAIR_HP = 0.1
HELICOPTER_EXIT_DAMAGE_DISTANCE_MOD = 1.0
GLOBAL_VEHICLE_EXIT_DAMAGE_MOD = 1.0
GLOBAL_VEHICLE_EXIT_VELOCITY_MOD = 1.0
NO_DAMAGE_WHEN_LEAVING = ['static_uav',
 'deployable',
 'spectator_camera',
 'us_air_c47_para']
_activeVehicles = set()
_knownVehicles = set()
_vehicleProperties = {}
playersInJets = set()
VEHICLE_TYPE_UNKNOWN = -1
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
invalidSeatEnforcer = None

def init():
    global invalidSeatEnforcer
    host.registerGameStatusHandler(onGameStatusChanged)
    host.registerHandler('EnterVehicle', onEnterVehicle)
    host.registerHandler('ExitVehicle', onExitVehicle)
    host.registerHandler('EnterVehicle', onEnterVehicleInitialize)
    host.registerHandler('EnterVehicle', onEnterVehicleActive, 1)
    host.registerHandler('ExitVehicle', onExitVehicleActive, 1)
    host.registerHandler('ExitVehicle', onExitVehicleDamage)
    host.registerHandler('VehicleDestroyed', onCustomVehicleDestroyed)
    host.registerHandler('PlayerChangedSquad', onPlayerChangedSquad)
    parachute.init()
    vehicleDODBleed.init()
    rtimer.repeatingTask(checkActiveVehicles, VEHICLE_CHECK_INTERVAL)
    host.registerHandler('RemoteCommandVehicles', onRemoteVehiclesCommand)
    invalidSeatEnforcer = InvalidSeatEnforcer()
    if host.sgl_getIsAIGame():
        rtimer.repeatingTask(refreshActiveVehicles, 1.0)


def onEnterVehicleInitialize(player, seatVehicle, freeSoldier = False):
    if seatVehicle.getParent() is not None:
        return
    elif hasattr(seatVehicle, '_seats'):
        return
    else:
        seats = []

        def getSeats(object, seats):
            typ = rcore.getObjectType(object.templateName).lower()
            if typ == 'playercontrolobject':
                object.pcoid = rmemory.getVehiclePCOID(object)
                seats.append(object)
            for child in object.getChildren():
                getSeats(child, seats)

        getSeats(seatVehicle, seats)
        seats = sorted(seats, key=lambda obj: obj.pcoid)
        seatVehicle._seats = seats
        if rmemory.getObjectHasDynamicPhysics(seatVehicle):
            settings = rvehicles_settings.getVehicleSettings(seatVehicle)
            if hasattr(settings, 'sleepinessMax'):
                rmemory.setObjectSleepinessMax(seatVehicle, settings.sleepinessMax)
            else:
                rmemory.setObjectSleepinessMax(seatVehicle, rvehicles_settings.SLEEPINESS_MAX_DEFAULT)
        return


getFirstEmptySeatAntiSpam = {}

def _resolveSeatIndex(vehicle, seats):
    # Prefer the PCO id assigned on enter. If the current object is not a seat
    # (child part, turret, etc), walk parents and match against known seats.
    if vehicle is None or not seats:
        return None
    if hasattr(vehicle, 'pcoid'):
        try:
            return int(vehicle.pcoid)
        except:
            pass
    cursor = vehicle
    while cursor is not None:
        for i in range(len(seats)):
            if seats[i] is cursor:
                return i
        try:
            cursor = cursor.getParent()
        except:
            return None
    return None


def getFirstEmptySeat(playerid):
    try:
        debug_templateName = 'TEMPLATE NAME NOT FOUND'
        now = host.timer_getWallTime()
        if playerid in getFirstEmptySeatAntiSpam and getFirstEmptySeatAntiSpam[playerid][0] + CYCLE_SEAT_COOLDOWN > now:
            return getFirstEmptySeatAntiSpam[playerid][1]
        player = bf2.playerManager.getPlayerByIndex(playerid)
        if player is None:
            return 0
        if player.isAIPlayer():
            return 7
        vehicle = player.getVehicle()
        if vehicle is None:
            return 0
        if hasattr(vehicle, 'templateName'):
            debug_templateName = vehicle.templateName
        root = getRoot(vehicle)
        if root is None or not hasattr(root, '_seats') or not root._seats:
            return 0
        seats = root._seats
        myindex = _resolveSeatIndex(vehicle, seats)
        if myindex is None:
            return 0
        seatCount = len(seats)
        for index in range(myindex + 1, myindex + seatCount):
            index = index % seatCount
            seat = seats[index]
            if not hasattr(seat, 'currentPlayer') or seat.currentPlayer is None:
                rdebug.debugMessage('Selected Seat %s' % index)
                getFirstEmptySeatAntiSpam[playerid] = (now, index)
                return index

        return 0
    except:
        rdebug.errorMessage()
        radmin.adminPM('rvehicles getFirstEmptySeat vehicle no pcoid debug %s' % debug_templateName)
        rdebug.debugMessage('rvehicles getFirstEmptySeat vehicle no pcoid debug %s' % debug_templateName)
        for qa in rdebug.PRDEBUG_QAs_ONLINE:
            radmin.personalMessage('rvehicles getFirstEmptySeat vehicle no pcoid debug %s' % debug_templateName, qa)

        return 0

    return


def onGameStatusChanged(status):
    global _invalid_seat_timers
    playersInJets.clear()
    for vehicle in list(_activeVehicles):
        if not vehicle.isValid() or len(vehicle.getOccupyingPlayers()) == 0:
            _activeVehicles.remove(vehicle)

    for vehicle in list(_knownVehicles):
        if not vehicle.isValid() == 0:
            _knownVehicles.remove(vehicle)

    if status == bf2.GameStatus.Loaded:
        rtimer.fireOnce(findVehiclesOnMap, 2, '')
        _vehicleProperties.clear()
    elif status == bf2.GameStatus.EndGame:
        _invalid_seat_timers.clear()
        for player in bf2.playerManager.getPlayers():
            bf2.gameLogic.sendGameEvent(player, 10, 80)


def refreshActiveVehicles(arg = None):
    for vehicle in list(_activeVehicles):
        if not vehicle.isValid() or vehicle.getOccupyingPlayers() == 0:
            _activeVehicles.discard(vehicle)


def onEnterVehicle(player, seatVehicle, freeSoldier = False):
    vehicle = getRoot(seatVehicle)
    cacheWeapons(seatVehicle)
    for function in getAppliedDisableFunctions(vehicle):
        function.reapplyOverheat(vehicle)

    seat = getSeat(seatVehicle)
    sendDisabledWeapons(vehicle, seat, player)
    recheckPlayer(player, seatVehicle, blackscreenOnFailure=True)
    addStartDelay(vehicle, seatVehicle)
    checkDamage(vehicle)


def onExitVehicle(player, seatVehicle):
    if not isPlayerInValidSeat(player):
        rtimer.fireNextTick(checkSeatAfterExit, player)
    bf2.gameLogic.sendGameEvent(player, 10, 80)
    vehicle = getRoot(seatVehicle)
    removeStartDelay(vehicle, seatVehicle)


def onPlayerChangedSquad(player, oldSquad, newSquad):
    if player.isAIPlayer():
        return
    if not rcore.isInsideVehicle(player):
        return
    seatVehicle = player.getVehicle()
    recheckPlayer(player, seatVehicle, blackscreenOnFailure=False)


def recheckPlayer(player, seatVehicle, blackscreenOnFailure):
    vehicle = getRoot(seatVehicle)
    if isSeatValid(player, vehicle, seatVehicle, silent=False):
        invalidSeatEnforcer.clearInvalidSeat(player)
        for passenger in vehicle.getOccupyingPlayers():
            if passenger == player:
                continue
            if isSeatValid(passenger, vehicle, passenger.getVehicle(), silent=True):
                invalidSeatEnforcer.clearInvalidSeat(passenger)

    else:
        invalidSeatEnforcer.setInvalidSeat(player, blackscreen=blackscreenOnFailure)


def onExitVehicleDamage(player, seatVehicle):
    if player.isAIPlayer():
        return
    elif player.killed or rcore.isClimbing(player):
        return
    elif not realityserver.C('VEHICLES_EXIT_DAMAGE_SPEED') and not realityserver.C('VEHICLES_EXIT_DAMAGE_CRITICAL'):
        return
    else:
        template = seatVehicle.templateName.lower()
        kit = player.getKit()
        if kit:
            kit = rkits.getKitTypeFast(kit.templateName)
            if isFlyingVehicle(seatVehicle) and kit in ('pilot',):
                return
        for prefix in NO_DAMAGE_WHEN_LEAVING:
            if template.startswith(prefix):
                return

        vehicle = getRoot(seatVehicle)
        damage = 0.0
        if realityserver.C('VEHICLES_EXIT_DAMAGE_CRITICAL'):
            vehicleDamage = vehicle.getDamage()
            if vehicleDamage is not None:
                criticalDamage = getVehicleProperties(vehicle)['criticalDamage']
                if vehicleDamage <= criticalDamage:
                    damage = 0.5
        if rmemory.getObjectHasDynamicPhysics(vehicle):
            velocity = rcore.getVectorDistance(rmemory.getVelocity(vehicle), (0, 0, 0))
        else:
            velocity = 0.0
        velocity *= GLOBAL_VEHICLE_EXIT_VELOCITY_MOD
        isTransHelicopter = '_the_' in vehicle.templateName
        if isTransHelicopter:
            velocity *= HELICOPTER_EXIT_DAMAGE_DISTANCE_MOD
        if velocity >= 16:
            damage += 1.0
        elif velocity >= 14:
            damage += 0.9
        elif velocity >= 12:
            damage += 0.8
        elif velocity >= 10:
            damage += 0.7
        elif velocity >= 9:
            damage += 0.6
        if damage > 0.0:
            rtimer.fireNextTick(damageOnExitVehicle, (player,
             damage * GLOBAL_VEHICLE_EXIT_DAMAGE_MOD,
             template,
             velocity))
        return


def damageOnExitVehicle(args):
    player = args[0]
    damage = args[1]
    vehicle = args[2]
    velocity = args[3]
    if not player.isValid():
        return
    if player.killed or rcore.isInsideVehicle(player) or rcore.isClimbing(player):
        return
    rdebug.debugMessage('damageOnExitVehicle: Damaging player %s for %s exiting %s (%s m/s)' % (player.index,
     damage,
     vehicle,
     velocity), 'vehicles')
    rcore.damagePlayer(player, damage)


def onEnterVehicleActive(player, seatVehicle, freeSoldier):
    seatVehicle.currentPlayer = player
    vehicle = getRoot(seatVehicle)
    _knownVehicles.add(vehicle)
    _activeVehicles.add(vehicle)
    if '_jet_' in seatVehicle.templateName.lower():
        playersInJets.add(player)


def onExitVehicleActive(player, seatVehicle):
    if '_jet_' in seatVehicle.templateName.lower():
        playersInJets.discard(player)
    seatVehicle.currentPlayer = None
    vehicle = getRoot(seatVehicle)
    if vehicle == seatVehicle:
        vehicle.lastDrivingPlayerIndex = player.index
        vehicle.lastDrivingPlayerName = player.getName()
    if len(vehicle.getOccupyingPlayers()) == 0:
        _activeVehicles.discard(vehicle)
    return


def onCustomVehicleDestroyed(vehicleObject, attackerObject):
    if rcore.isSoldier(vehicleObject):
        return
    else:
        if not attackerObject:
            if vehicleObject is not None:
                if hasattr(vehicleObject, 'lastDrivingPlayerIndex'):
                    try:
                        attackerObject = rcore.getPlayerByIndex(vehicleObject.lastDrivingPlayerIndex)
                    except:
                        pass

        event = revents.getEvents('VehicleDestroyedFiltered')
        revents.sendToHandlers(event, vehicleObject, attackerObject)
        if not attackerObject:
            return
        try:
            vehicleTeam = vehicleObject.getTeam()
        except:
            return

        if attackerObject.getTeam() == vehicleTeam:
            event = revents.getEvents('TeamVehicleDestroyed')
            revents.sendToHandlers(event, vehicleObject, attackerObject)
            return
        event = revents.getEvents('EnemyVehicleDestroyed')
        revents.sendToHandlers(event, vehicleObject, attackerObject)
        return


def findVehiclesOnMap(data = ''):
    cacheVehiclesOnMap()


def removeStartDelayCallback(seatVehicle = None):
    if not seatVehicle.isValid():
        return
    vehicle = getRoot(seatVehicle)
    removeStartDelay(vehicle, seatVehicle)


def checkSeatAfterExit(player):
    if not player.isValid():
        return
    if isPlayerInValidSeat(player):
        return
    seatVehicle = player.getVehicle()
    vehicle = getRoot(seatVehicle)
    if isSeatValid(player, vehicle, seatVehicle, silent=True):
        invalidSeatEnforcer.clearInvalidSeat(player)


def checkActiveVehicles(data = ''):
    for vehicle in _activeVehicles:
        if checkUpsideDown(vehicle):
            rdebug.debugMessage('Upside-down check killed vehicle %s, no need to check further' % vehicle.templateName, 'vehicles')
            continue
        checkDamage(vehicle)


def isPlayerInValidSeat(player):
    if not hasattr(player, 'pr_veh_invalid'):
        return True
    return not player.pr_veh_invalid


def isSeatValid(player, vehicle, seatVehicle, silent):
    rdebug.debugMessage('Checking if seat is  valid for player %s' % player.getName(), 'vehicles')
    if not player.isValid():
        rdebug.debugMessage('Valid! Player is invalid', 'vehicles')
        return True
    if player.isAIPlayer():
        rdebug.debugMessage('Valid! Player is bot', 'vehicles')
        return True
    if not realityserver.C('VEHICLES_REQUIREMENTS'):
        rdebug.debugMessage('Valid! Requirements disabled', 'vehicles')
        return True
    template = vehicle.templateName.lower()
    if (template.endswith('_prsp') or template.endswith('_sp')) and not template.startswith('deployable_'):
        if not silent:
            rmemory.HudVarWriteEventWstringWithTimedShowvar(player, 'PythonGameWarning', 'Game warning:\nThis vehicle may only be operated by bots!', 8)
            if rmemory.isWindowsListenServer:
                rcore.sendMessageToPlayer(player, 1220118, 2)
        rdebug.debugMessage('Invalid! Bot vehicle', 'vehicles')
        return False
    vehicleSettings = rvehicles_settings.getVehicleSettings(vehicle)
    if not vehicleSettings:
        rdebug.debugMessage('No limted vehicle', 'vehicles')
        return True
    squad = player.getSquadId()
    if vehicleSettings.isRestrictedSeat(seatVehicle) and squad == 0:
        if not silent:
            rcore.sendMessageToPlayer(player, 3240301)
        rdebug.debugMessage('Invalid! No Squad', 'vehicles')
        return False
    seatKitsSettings = vehicleSettings.getSeatKitsSettings(seatVehicle)
    if not hasValidKit(player, seatKitsSettings, vehicle, silent):
        rdebug.debugMessage('Invalid! No valid kit', 'vehicles')
        return False
    seatSeatsSettings = vehicleSettings.getSeatSeatsSettings(seatVehicle)
    if not hasValidRequiredSeats(player, seatSeatsSettings, vehicle, silent):
        rdebug.debugMessage('Invalid! No valid required seats', 'vehicles')
        return False
    if not hasValidDependendSeats(player, vehicleSettings, vehicle, getSeat(seatVehicle), silent):
        rdebug.debugMessage('Invalid! No valid dependend seats', 'vehicles')
        return False
    return True


def hasValidKit(player, seatKitsSettings, vehicle, silent):
    kit = player.getKit().templateName
    kitType = rkits.getKitTypeFast(kit).lower()
    if seatKitsSettings and 'required' in seatKitsSettings:
        requiredKits = seatKitsSettings['required']
        if kitType not in requiredKits:
            if not silent:
                if len(requiredKits) == 1:
                    reqKit = requiredKits[0]
                    if reqKit == 'tanker':
                        rcore.sendMessageToPlayer(player, 2020913)
                    elif reqKit == 'pilot':
                        rcore.sendMessageToPlayer(player, 2020919)
                    else:
                        rcore.sendMessageToPlayer(player, 2021403)
                else:
                    rcore.sendMessageToPlayer(player, 2021403)
            rdebug.debugMessage('Invalid! Wrong kit', 'vehicles')
            return False
        rdebug.debugMessage('Valid! Right kit', 'vehicles')
        return True
    if kitType in ('pilot',):
        template = vehicle.templateName.lower()
        if '_ahe_' in template or '_the_' in template:
            if not silent:
                rcore.sendMessageToPlayer(player, 2021403)
            rdebug.debugMessage('Invalid! Pilot in non pilot seat', 'vehicles')
            return False
    rdebug.debugMessage('Valid! No kit required', 'vehicles')
    return True


def hasValidRequiredSeats(player, seatSeatsSettings, vehicle, silent):
    if not seatSeatsSettings or 'required' not in seatSeatsSettings:
        rdebug.debugMessage('Valid! No required seats', 'vehicles')
        return True
    requiredSeats = seatSeatsSettings['required']
    requiredSeatsCount = len(requiredSeats)
    requiredOccupiedSeats = 0
    if requiredSeatsCount == requiredOccupiedSeats:
        rdebug.debugMessage('Valid! No required seats', 'vehicles')
        return True
    squad = player.getSquadId()
    for passenger in vehicle.getOccupyingPlayers():
        passengerVehicle = passenger.getVehicle()
        passengerSeat = getSeat(passengerVehicle)
        if passengerSeat in requiredSeats:
            if passenger.getSquadId() != squad:
                if not silent:
                    rcore.sendMessageToPlayer(player, 3211305)
                rdebug.debugMessage('Invalid! Different squad then required seat', 'vehicles')
                return False
            if isPlayerInValidSeat(passenger):
                requiredOccupiedSeats += 1
        if requiredOccupiedSeats == requiredSeatsCount:
            rdebug.debugMessage('Valid! All required seats crewed', 'vehicles')
            return True

    if not silent:
        rcore.sendMessageToPlayer(player, 2020419)
    rdebug.debugMessage('Invalid! Not all required seats crewed', 'vehicles')
    return False


def getDependentSeatPlayers(player, vehicleSettings, vehicle, seat):
    for passenger in vehicle.getOccupyingPlayers():
        if passenger == player:
            continue
        seatVehicle = passenger.getVehicle()
        passengerSeatSeatsSettings = vehicleSettings.getSeatSeatsSettings(seatVehicle)
        if 'required' in passengerSeatSeatsSettings:
            if seat in passengerSeatSeatsSettings['required']:
                yield passenger


def hasValidDependendSeats(player, vehicleSettings, vehicle, seat, silent):
    squad = player.getSquadId()
    for passenger in getDependentSeatPlayers(player, vehicleSettings, vehicle, seat):
        if isPlayerInValidSeat(passenger):
            if passenger.getSquadId() != squad:
                if not silent:
                    rcore.sendMessageToPlayer(player, 3211305)
                rdebug.debugMessage('Invalid! Not same squad as valid dependend seat', 'vehicles')
                return False

    return True


class InvalidSeatEnforcer:

    def __init__(self):
        self.invalidSeatPlayerTimers = {}

    def _clearTimer(self, player):
        if player not in self.invalidSeatPlayerTimers:
            return
        self.invalidSeatPlayerTimers[player].destroy()
        del self.invalidSeatPlayerTimers[player]

    def setInvalidSeat(self, player, blackscreen = False):
        if player in self.invalidSeatPlayerTimers:
            return
        elif player.isAIPlayer():
            return
        elif not player.isValid():
            return
        else:
            player.pr_veh_invalid = True
            veh = player.getVehicle()
            isFlyingVehicle = veh is not None and ('_the_' in veh.templateName or '_jet_' in veh.templateName or '_ahe_' in veh.templateName)
            exitdelay = 25 if isFlyingVehicle else 8
            self.invalidSeatPlayerTimers[player] = rtimer.Timer(self._tryExit, exitdelay, 1, data=player)
            self.invalidSeatPlayerTimers[player].setRecurring(0.3)
            rdebug.debugMessage('seat enforcer: player %s in invalid seat' % player.getName(), 'vehicles')
            if blackscreen or rmemory.isWindowsListenServer:
                rcore.blackScreen(player, fast=True)
            return

    def _tryExit(self, player):
        if not player.isValid():
            self._clearTimer(player)
            return
        recheckPlayer(player, player.getVehicle(), blackscreenOnFailure=False)
        if player not in self.invalidSeatPlayerTimers:
            return
        rmemory.sendPlayerButtonClickEvent(player, rmemory.PI_USE)
        rdebug.debugMessage('seat enforcer: Trying to make player %s leave vehicle...' % player.getName(), 'vehicles')

    def clearInvalidSeat(self, player):
        if hasattr(player, 'pr_veh_invalid') and player.pr_veh_invalid is True:
            player.pr_veh_invalid = False
            self._clearTimer(player)
            rcore.clearScreen(player)
            rdebug.debugMessage('seat enforcer: player %s no longer in invalid seat' % player.getName(), 'vehicles')


def addStartDelay(vehicle, seatVehicle):
    if not realityserver.C('VEHICLES_START_DELAY'):
        return
    else:
        vehicleSettings = rvehicles_settings.getVehicleSettings(vehicle)
        if not vehicleSettings:
            return
        seatStartSettings = vehicleSettings.getSeatStartSettings(seatVehicle)
        if not seatStartSettings:
            return
        rdebug.debugMessage('Applying start delay to %s' % vehicle.templateName, 'vehicles')
        if not hasattr(vehicle, 'pr_veh_startDelay'):
            seatVehicle.pr_veh_startDelay = None
        elif seatVehicle.pr_veh_startDelay:
            seatVehicle.pr_veh_startDelay.destroy()
            seatVehicle.pr_veh_startDelay = None
        startFunc = seatStartSettings['function']
        startFunc.applyTo(vehicle)
        players = seatVehicle.getOccupyingPlayers()
        if players:
            sendDisabledWeapons(vehicle, getSeat(seatVehicle), players[0])
        startDelay = seatStartSettings['delay']
        seatVehicle.pr_veh_startDelay = rtimer.fireOnce(removeStartDelayCallback, startDelay, seatVehicle)
        return


def removeStartDelay(vehicle, seatVehicle):
    vehicleSettings = rvehicles_settings.getVehicleSettings(vehicle)
    if not vehicleSettings:
        return
    else:
        seatStartSettings = vehicleSettings.getSeatStartSettings(seatVehicle)
        if not seatStartSettings:
            return
        if not hasattr(vehicle, 'pr_veh_startDelay'):
            seatVehicle.pr_veh_startDelay = None
        rdebug.debugMessage('Removing start delay for %s' % seatVehicle.templateName, 'vehicles')
        startFunc = seatStartSettings['function']
        vehicle = getRoot(seatVehicle)
        startFunc.removeFrom(vehicle)
        if seatVehicle.pr_veh_startDelay:
            seatVehicle.pr_veh_startDelay.destroy()
            seatVehicle.pr_veh_startDelay = None
        return


def checkUpsideDown(vehicle):
    vehicleType = rconstants.getVehicleType(vehicle.templateName)
    if vehicleType in {rconstants.VEHICLE_TYPE_HELI, rconstants.VEHICLE_TYPE_HELIATTACK}:
        if not hasattr(vehicle, 'pr_veh_upsideDown'):
            vehicle.pr_veh_upsideDown = 0.0
        if isUpsideDown(vehicle):
            vehicle.pr_veh_upsideDown += VEHICLE_CHECK_INTERVAL
            rdebug.debugMessage('Vehicle %s upside-down for %s' % (vehicle.templateName, vehicle.pr_veh_upsideDown), 'vehicles')
        else:
            vehicle.pr_veh_upsideDown = 0.0
        if vehicle.pr_veh_upsideDown >= UPSIDE_DOWN_INTERVAL:
            rdebug.debugMessage('Damaging vehicle %s for being upside-down' % vehicle.templateName, 'vehicles')
            vehicle.pr_veh_upsideDown -= UPSIDE_DOWN_INTERVAL
            hp = vehicle.getDamage()
            if hp is None:
                return
            maxHp = getVehicleProperties(vehicle)['maxHitPoints']
            hp -= maxHp * UPSIDE_DOWN_DAMAGE_PER_INTERVAL
            if hp <= 0.001:
                hp = 0.001
            vehicle.setDamage(hp)
            return hp <= 0.001
    return False


def checkDamage(vehicle):
    vehicleSettings = rvehicles_settings.getVehicleSettings(vehicle)
    if not vehicleSettings:
        return
    else:
        damageSets = vehicleSettings.getDamageSettings()
        if not damageSets:
            return
        maxHp = getVehicleProperties(vehicle)['maxHitPoints']
        if not hasattr(vehicle, 'pr_veh_lastHp'):
            vehicle.pr_veh_lastHp = 1.0
        if not hasattr(vehicle, 'pr_veh_repairedHp'):
            vehicle.pr_veh_repairedHp = 0.0
        vehicle_damage = vehicle.getDamage()
        if vehicle_damage is None:
            msg = 'Missing ObjectTemplate.createComponent Armor in ' + str(vehicle.templateName)
            rdebug.debugMessage(msg)
            return
        hp = vehicle_damage / maxHp
        if hp is None:
            return
        lastHp = vehicle.pr_veh_lastHp
        damage = hp - lastHp
        vehicle.pr_veh_lastHp = hp
        if damage < 0:
            if hp >= MAX_DISABLE_HP:
                return
            damage = abs(damage)
            damage -= MIN_DAMAGE
            if damage <= 0.0:
                return
            vehicle.pr_veh_repairedHp = 0.0
            disableChance = getDamageDisableChance(lastHp, damage)
            rdebug.debugMessage('Vehicle %s took %s%% damage, checking if should be disabled. Chance %s%%' % (vehicle.templateName, (damage + MIN_DAMAGE) * 100, disableChance * 100), 'vehicles')
            for idx in range(0, len(damageSets)):
                damageSet = damageSets[idx]
                modifier = damageSet['modifier']
                rng = random.uniform(0.0, 1.0)
                if rng <= disableChance * modifier:
                    applyDamageSet(vehicle, damageSets, idx)

        elif damage > 0:
            if not isDamaged(vehicle):
                return
            vehicle.pr_veh_repairedHp += damage
            if hp >= 0.999:
                rdebug.debugMessage('Vehicle %s got fully reparied' % vehicle.templateName, 'vehicles')
                repairVehicle(vehicle, damageSets)
            elif vehicle.pr_veh_repairedHp >= VEHICLE_REPAIR_HP:
                rdebug.debugMessage('Vehicle %s got %s%% damage repaired, checking if should be repaired' % (vehicle.templateName, vehicle.pr_veh_repairedHp * 100), 'vehicles')
                rng = random.uniform(0.0, 1.0)
                if rng <= hp:
                    repairVehicle(vehicle, damageSets)
                vehicle.pr_veh_repairedHp = 0.0
        return


def getDamageDisableChance(lastHp, damagePercent):
    return 0.25 * (1 + math.erf((damagePercent / lastHp * 100.0 - 35.0) / 20.0))


def applyDamageSet(vehicle, damageSets, damageSetIdx):
    if not hasattr(vehicle, 'pr_veh_activeDamageSets'):
        vehicle.pr_veh_activeDamageSets = set()
    if damageSetIdx in vehicle.pr_veh_activeDamageSets:
        rdebug.debugMessage('Damageset %s already applied to vehicle %s' % (damageSetIdx, vehicle.templateName), 'vehicles')
        return
    vehicle.pr_veh_activeDamageSets.add(damageSetIdx)
    functions = damageSets[damageSetIdx]['functions']
    functionIdx = random.randint(0, len(functions) - 1)
    chosenFunction = functions[functionIdx]
    chosenFunction.applyTo(vehicle)
    for player in vehicle.getOccupyingPlayers():
        seat = getSeat(player.getVehicle())
        sendDisabledWeapons(vehicle, seat, player)

    rdebug.debugMessage('Applied function %s of damageset %s to vehicle %s' % (functionIdx, damageSetIdx, vehicle.templateName), 'vehicles')


def repairVehicle(vehicle, damageSets):
    if not hasattr(vehicle, 'pr_veh_activeDamageSets'):
        vehicle.pr_veh_activeDamageSets = set()
    for idx in vehicle.pr_veh_activeDamageSets:
        for function in damageSets[idx]['functions']:
            function.removeFrom(vehicle)

    vehicle.pr_veh_activeDamageSets.clear()
    for passenger in vehicle.getOccupyingPlayers():
        bf2.gameLogic.sendGameEvent(passenger, 10, 80)

    rdebug.debugMessage('Repaired vehicle %s' % vehicle.templateName, 'vehicles')


def isDamaged(vehicle):
    if not hasattr(vehicle, 'pr_veh_activeDamageSets'):
        vehicle.pr_veh_activeDamageSets = set()
    return bool(vehicle.pr_veh_activeDamageSets)


def sendDisabledWeapons(vehicle, seat, player):
    weapons = getWeapons(vehicle, seat)
    if weapons is None:
        return
    else:
        weaponsMask = 0
        for weapon in weapons:
            if hasattr(weapon, 'rv_disabled') and weapon.rv_disabled:
                weaponsMask |= _getWeaponMaskIndex(weapon.templateName)

        args = weaponsMask << 8 | 80
        bf2.gameLogic.sendGameEvent(player, 10, args)
        return


def _getWeaponMaskIndex(weaponTemplate):
    index = int(rcore.getTemplateProperty(weaponTemplate, 'itemIndex', 'GenericFirearm'))
    fireInput = rcore.getTemplateProperty(weaponTemplate, 'fire.fireInput', 'GenericFirearm')
    if fireInput and fireInput.lower() == 'pialtfire':
        if index <= 0:
            return 1048576
        return 1 << 10 + index
    elif index <= 0:
        return 1024
    else:
        return 1 << index


def cacheWeapons(seatVehicle):
    vehicle = getRoot(seatVehicle)
    if not hasattr(vehicle, 'pr_veh_seat_weapons'):
        vehicle.pr_veh_seat_weapons = {}
    seat = getSeat(seatVehicle)
    if seat in vehicle.pr_veh_seat_weapons:
        return
    weapons = []
    findWeapons(seatVehicle, weapons)
    vehicle.pr_veh_seat_weapons[seat] = weapons


def findWeapons(physicalObject, outWeapons):
    children = physicalObject.getChildren()
    for child in children:
        childType = rcore.getObjectType(child.templateName).lower()
        if childType in ('genericfirearm',):
            outWeapons.append(child)
            rmemory.setWeaponHeat(child, 0.0)
            continue
        if childType in ('playercontrolobject', 'soldier'):
            continue
        findWeapons(child, outWeapons)


def getWeapons(vehicle, seat):
    if not hasattr(vehicle, 'pr_veh_seat_weapons'):
        vehicle.pr_veh_seat_weapons = {}
    if seat in vehicle.pr_veh_seat_weapons:
        return vehicle.pr_veh_seat_weapons[seat]
    else:
        return None


def getAppliedDisableFunctions(vehicle):
    if not hasattr(vehicle, 'pr_veh_functions'):
        vehicle.pr_veh_functions = []
    return vehicle.pr_veh_functions


def getSeat(vehicle):
    root = getRoot(vehicle)
    template = vehicle.templateName
    rootTemplate = root.templateName
    return getPart(rootTemplate, template)


def getPart(rootTemplate, template):
    template = template.lower()
    rootTemplate = rootTemplate.lower()
    if not template.startswith(rootTemplate):
        return template
    else:
        seat = template[len(rootTemplate) + 1:]
        if not seat:
            return 'root'
        return seat.lower()


def getRoot(vehicle):
    parent = vehicle.getParent()
    if parent is None:
        return vehicle
    else:
        return getRoot(parent)


def getActiveVehicles():
    return _activeVehicles


def getKnownVehicles():
    return filter(lambda v: v.isValid(), _knownVehicles)


def isFlyingVehicle(vehicle):
    flyingVehicleSet = {rconstants.VEHICLE_TYPE_HELI,
     rconstants.VEHICLE_TYPE_HELIATTACK,
     rconstants.VEHICLE_TYPE_JET,
     rconstants.VEHICLE_TYPE_UAV,
     rconstants.VEHICLE_TYPE_TURBOPROP}
    return rconstants.getVehicleType(vehicle.templateName) in flyingVehicleSet


def isUpsideDown(vehicle):
    try:
        rot = vehicle.getRotation()
        pitch = rcore.math.fabs(rot[1])
        if pitch > 180.0:
            pitch = (pitch - 360.0) * -1
        roll = rcore.math.fabs(rot[2])
        if roll > 180.0:
            roll = (roll - 360.0) * -1
        if roll >= 100.0 or pitch >= 100.0:
            return True
        return False
    except:
        return False


def getVehicleProperties(vehicle):
    maxHealth = 0
    criHealth = 0
    vehicleTemplate = vehicle.templateName
    if vehicleTemplate in _vehicleProperties:
        return _vehicleProperties[vehicleTemplate]
    try:
        maxHealth = float(vehicle.getTemplateProperty('armor.maxHitPoints'))
        criHealth = float(vehicle.getTemplateProperty('armor.criticalDamage'))
    except:
        pass

    _vehicleProperties[vehicleTemplate] = {'maxHitPoints': maxHealth,
     'criticalDamage': criHealth}
    return _vehicleProperties[vehicleTemplate]


def getPositionInVehicle(vehicle):
    if not hasattr(vehicle, 'seattype'):
        tempLower = vehicle.templateName.lower()
        if '_uav_' in tempLower:
            vehicle.seattype = 1
        elif vehicle.getParent() == None:
            vehicle.seattype = 0
        elif 'gun' in tempLower or 'cupola' in tempLower:
            vehicle.seattype = 1
        else:
            vehicle.seattype = 2
    return vehicle.seattype


class parachute:

    @classmethod
    def init(cls):
        host.registerHandler('PlayerSpawn', cls.onPlayerSpawn, 1)
        host.registerHandler('EnterVehicle', cls.onEnterParachute)
        host.registerHandler('ExitVehicle', cls.onExitParachute)
        host.registerHandler('ExitVehicle', cls.onExitParadropVehicle)

    @classmethod
    def onEnterParachute(cls, player, vehicle, freeSoldier = False):
        if realityserver.isCoopServer():
            return
        elif player.killed or vehicle.templateName.lower() != 'parachute' or rkits.isNinja(player):
            return
        else:
            player.parachute_startTime = rcore.now()
            if hasattr(player, 'parachute_clickRetryTimer') and player.parachute_clickRetryTimer is not None:
                player.parachute_clickRetryTimer.destroy()
            return

    @classmethod
    def onExitParachute(cls, player, vehicle):
        if realityserver.isCoopServer():
            return
        elif player.killed or vehicle.templateName.lower() != 'parachute' or rkits.isNinja(player):
            return
        elif not hasattr(player, 'parachute_startTime') or player.parachute_startTime is None:
            return
        else:
            delta = int(rcore.now() - player.parachute_startTime)
            if delta >= 18.0:
                pass
            elif delta <= 8.0:
                rcore.killPlayer(player)
            else:
                damage = (18.0 - delta) / 18.0
                rcore.damagePlayer(player, damage)
                rdebug.debugMessage(player.getName() + ' parachuted for ' + str(delta) + ' seconds - ' + str(damage) + ' damage', 'vehicles')
            player.parachute_startTime = None
            return

    @classmethod
    def onExitParadropVehicle(cls, player, vehicle):
        if not vehicle.templateName.startswith('us_air_c47_para'):
            return
        cls.forceParachute(player, delay=1.5)

    @classmethod
    def onPlayerSpawn(cls, player, soldier):
        if not cls.isPlayerParatrooping(player, soldier):
            return
        cls.forceParachute(player)

    @classmethod
    def forceParachute(cls, player, delay = 3.0):
        if player.isAIPlayer():
            return
        rtimer.Timer(cls.click, delay, 1, data=player)

    @staticmethod
    def click(player):
        if not player.isValid():
            return
        rmemory.sendPlayerButtonClickEvent(player, rmemory.PI_WEAPONSELECT1 + 8)

    @staticmethod
    def isPlayerParatrooping(player, soldier):
        return soldier.getPosition()[1] > 300.0


import realityadmin as radmin

class vehicleDODBleed:
    BLEED_PERCENT = 0.08
    BLEED_TICK = 25
    BLEED_DELAY = 30
    BLEED_REFRESH = 15
    _vehiclesInDOD = {}

    @classmethod
    def init(cls):
        rtimer.repeatingTask(cls.findVehiclesInDod, cls.BLEED_REFRESH)

    @classmethod
    def findVehiclesInDod(cls, args = None):
        if not rzones.g_combat_areas.used:
            return
        for v in getKnownVehicles():
            if 'us_air_c47' in v.templateName:
                continue
            if v in _activeVehicles:
                continue
            team = v.getTeam()
            if team == 0:
                continue
            if rzones.getPointDODs(v.getPosition(), team, (rzones.ALL,)):
                cls.start(v)

    @classmethod
    def start(cls, v):
        if hasattr(v, 'dod_Timer') and v.dod_Timer is not None:
            return
        else:
            rdebug.debugMessage(v.templateName + ' in DOD.', 'zones')
            v.dod_Timer = rtimer.Timer(cls.tick, cls.BLEED_DELAY, 1, v)
            v.dod_Timer.setRecurring(cls.BLEED_TICK)
            cls._vehiclesInDOD[rcore.getObjectId(v)] = v
            return

    @classmethod
    def tick(cls, v):
        if not v.isValid() or v.getIsWreck() or v.getPosition() == (0.0, 0.0, 0.0) or v in _activeVehicles:
            return cls.stop(v)
        team = v.getTeam()
        if team == 0 or not rzones.getPointDODs(v.getPosition(), team, (rzones.ALL,)):
            rdebug.debugMessage(v.templateName + ' no longer in DOD.', 'zones')
            return cls.stop(v)
        radmin.adminPM('%s:%s is empty in DOD for more than 30 seconds. last driving player: %s' % (rcore.getObjectId(v), v.templateName, v.lastDrivingPlayerName))
        rdebug.debugMessage(v.templateName + ' in DOD, doing damage', 'zones')
        maxHealth = int(v.getTemplateProperty('armor.maxHitPoints'))
        damage = maxHealth * cls.BLEED_PERCENT
        newdmg = max(10.0, v.getDamage() - damage)
        v.setDamage(newdmg)

    @classmethod
    def stop(cls, v):
        v.dod_Timer.destroy()
        v.dod_Timer = None
        vehicleID = rcore.getObjectId(v)
        if vehicleID in cls._vehiclesInDOD:
            del cls._vehiclesInDOD[vehicleID]
        return

    @classmethod
    def list(cls, admin):
        cls.findVehiclesInDod()
        radmin.personalMessage('Vehicles in DOD:', admin)
        for vehicleID in cls._vehiclesInDOD:
            v = cls._vehiclesInDOD[vehicleID]
            radmin.personalMessage('%s:%s last driven by %s' % (vehicleID, v.templateName, v.lastDrivingPlayerName), admin)

    @classmethod
    def destroy(cls, admin, id):
        cls.findVehiclesInDod()
        if id not in cls._vehiclesInDOD:
            radmin.personalMessage('vehicle id %s not found or is not in DOD' % id, admin)
        else:
            targetv = cls._vehiclesInDOD[id]
            if len(targetv.getOccupyingPlayers()) != 0:
                radmin.personalMessage('vehicle id %s is not empty' % id, admin)
                return
            targetv.setDamage(10.0)
            return targetv

    @classmethod
    def teleport(cls, admin, id):
        cls.findVehiclesInDod()
        if id not in cls._vehiclesInDOD:
            radmin.personalMessage('vehicle id %s not found or is not in DOD' % id, admin)
        else:
            targetv = cls._vehiclesInDOD[id]
            if admin.getTeam() != targetv.getTeam():
                radmin.personalMessage('You must be in the same team of the vehicle to teleport it' % id, admin)
                return
            adminsol = admin.getDefaultVehicle()
            if adminsol is None:
                radmin.personalMessage('You must be alive in your DOD to teleport a vehicle' % id, admin)
                return
            adminpos = adminsol.getPosition()
            isEnemyDOD = len(rzones.getPointDODs(adminpos, rcore.getOtherTeam(admin.getTeam()), (rzones.ALL,))) == 0
            isFriendlyDOD = len(rzones.getPointDODs(adminpos, admin.getTeam(), (rzones.ALL,))) == 0
            if isEnemyDOD or not isFriendlyDOD:
                radmin.personalMessage('You must be in your mainbase DOD to teleport a vehicle', admin)
                return
            targetpos = rcore.getPositionFromPlayer(admin, 5)
            targetv.setPosition(targetpos)
            return targetv
        return


def cacheVehiclesOnMap():
    rvehicles_settings.g_vehicle_settings.clear()
    knownVehicles = set()
    vehicles = bf2.objectManager.getObjectsOfType('dice.hfe.world.ObjectTemplate.PlayerControlObject')
    for vehicle in vehicles:
        template = vehicle.templateName.lower()
        if template in knownVehicles:
            continue
        knownVehicles.add(template)
        vehicleSettings = rvehicles_settings.findSettings(template)
        if vehicleSettings is not None:
            settings = _createTemplateSettings(template, vehicleSettings)
            rvehicles_settings.g_vehicle_settings[template] = settings

    return


def _createTemplateSettings(template, vehicleSettings):
    settings_dict = {}
    if 'extends' in vehicleSettings:
        extends = rvehicles_settings.VEHICLE_SETTINGS[vehicleSettings['extends']]
        for setting in extends:
            settings_dict[setting] = extends[setting]

    for setting in vehicleSettings:
        settings_dict[setting] = vehicleSettings[setting]

    return VehicleTemplateSettings(template, settings_dict)


class VehicleTemplateSettings:

    def __init__(self, template, settingsDict):
        self._seatSettings = {}
        self._damageSettings = []
        self._partOffsets = {}
        self._template = template
        if 'seats' in settingsDict:
            for seat in settingsDict['seats']:
                newSettings = {}
                seatSettings = settingsDict['seats'][seat]
                if 'kits' in seatSettings:
                    newSettings['kits'] = seatSettings['kits']
                if 'seats' in seatSettings:
                    newSettings['seats'] = seatSettings['seats']
                if 'start' in seatSettings:
                    function = seatSettings['start']['function']
                    newSettings['start'] = {'delay': seatSettings['start']['delay'],
                     'function': VehicleDisableFunction(function[0], function[1])}
                self._seatSettings[seat] = newSettings

        if 'damage' in settingsDict:
            for damageSet in settingsDict['damage']:
                newSet = {'modifier': damageSet['modifier'],
                 'functions': []}
                for function in damageSet['functions']:
                    newSet['functions'].append(VehicleDisableFunction(function[0], function[1]))

                self._damageSettings.append(newSet)

    def getAllParts(self):
        parts = set()
        for seat in self._seatSettings:
            if 'start' in self._seatSettings[seat]:
                function = self._seatSettings[seat]['start']['function']
                for part in function.getParts():
                    parts.add(part)

        for damageSet in self._damageSettings:
            for function in damageSet['functions']:
                for part in function.getParts():
                    parts.add(part)

        return parts

    def findIdOffsets(self, vehicle, parts):
        foundParts = {}
        self.walkObject(vehicle, parts, foundParts)
        vehicleId = rcore.getObjectId(vehicle)
        for part, partId in foundParts.iteritems():
            idOffset = partId - vehicleId
            self._partOffsets[part] = idOffset

    def walkObject(self, object, parts, foundParts):
        objectId = rmemory.getObjectId(object)
        template = object.templateName.lower()
        objectType = rcore.getObjectType(template)
        for p in parts:
            partType = p[0]
            if objectType != partType:
                continue
            part = p[1]
            if template.endswith('_' + part):
                if part in foundParts:
                    try:
                        raise Exception('Found multiple objects for part %s on %s' % (part, template))
                    except:
                        rdebug.errorMessage()

                else:
                    foundParts[part] = objectId

        children = object.getChildren()
        for child in children:
            self.walkObject(child, parts, foundParts)

    def getTemplate(self):
        return self._template

    def isRestrictedSeat(self, seatVehicle):
        seat = getSeat(seatVehicle)
        if seat not in self._seatSettings:
            return False
        if 'kits' not in self._seatSettings[seat] and 'required' not in self._seatSettings[seat]:
            return False
        return True

    def getSeatKitsSettings(self, seatVehicle):
        seat = getSeat(seatVehicle)
        if seat not in self._seatSettings:
            return {}
        if 'kits' not in self._seatSettings[seat]:
            return {}
        return self._seatSettings[seat]['kits']

    def getSeatSeatsSettings(self, seatVehicle):
        seat = getSeat(seatVehicle)
        if seat not in self._seatSettings:
            return {}
        if 'seats' not in self._seatSettings[seat]:
            return {}
        return self._seatSettings[seat]['seats']

    def getSeatStartSettings(self, seatVehicle):
        seat = getSeat(seatVehicle)
        if seat not in self._seatSettings:
            return {}
        if 'start' not in self._seatSettings[seat]:
            return {}
        return self._seatSettings[seat]['start']

    def getDamageSettings(self):
        return self._damageSettings

    def getPartOffsets(self):
        return self._partOffsets

    def getRequiredKits(self):
        required = set()
        if not self._seatSettings:
            return required
        for seat in self._seatSettings:
            if 'kits' not in self._seatSettings[seat]:
                continue
            kitsSettings = self._seatSettings[seat]['kits']
            if 'required' not in kitsSettings:
                continue
            for kit in kitsSettings['required']:
                required.add(kit)

        return required


class VehicleDisableFunction:

    def __init__(self, functionType, params):
        self._type = functionType
        self._params = params

    def getType(self):
        return self._type

    def getParams(self):
        return self._params

    def applyTo(self, vehicle):
        if not vehicle.isValid():
            return
        if self.isAppliedTo(vehicle):
            return
        if self._type == 'disable':
            self._applyDisableTo(vehicle)
        elif self._type == 'overheat':
            self._applyOverheatTo(vehicle)
        vehicle.pr_veh_functions.append(self)

    def removeFrom(self, vehicle):
        if not vehicle.isValid():
            return
        if not self.isAppliedTo(vehicle):
            return
        vehicle.pr_veh_functions.remove(self)
        if self._type == 'disable':
            self._removeDisableFrom(vehicle)
        elif self._type == 'overheat':
            self._removeOverheatFrom(vehicle)

    def reapplyOverheat(self, vehicle):
        if not vehicle.isValid():
            return
        if not self.isAppliedTo(vehicle):
            return
        if self._type == 'overheat':
            self._applyOverheatTo(vehicle)

    def isAppliedTo(self, vehicle):
        return self in getAppliedDisableFunctions(vehicle)

    def getParts(self):
        parts = set()
        if self._type == 'disable':
            for paramType in self._params:
                for part in self._params[paramType]:
                    parts.add(part)

        return parts

    def _applyOverheatTo(self, vehicle):
        for passenger in vehicle.getOccupyingPlayers():
            seatVehicle = passenger.getVehicle()
            seat = getSeat(seatVehicle)
            if seat in self._params:
                weapons = getWeapons(vehicle, seat)
                if weapons is None:
                    continue
                for weapon in weapons:
                    weaponTemplate = weapon.templateName.lower()
                    if 'ignore' in self._params[seat] and any((weaponTemplate.endswith(p) for p in self._params[seat]['ignore'])):
                        continue
                    heatAdded = float(rcore.getTemplateProperty(weaponTemplate, 'heatAddWhenFire'))
                    if heatAdded == 0.0:
                        continue
                    rdebug.debugMessage('Overheated weapon %s ' % weapon.templateName, 'vehicles')
                    rmemory.setWeaponHeat(weapon, 19999.9)
                    weapon.rv_disabled = True

        return

    def _removeOverheatFrom(self, vehicle):
        for seat in self._params.keys():
            weapons = getWeapons(vehicle, seat)
            if weapons is None:
                continue
            for weapon in weapons:
                weaponTemplate = weapon.templateName.lower()
                if 'ignore' in self._params[seat] and any((weaponTemplate.endswith(p) for p in self._params[seat]['ignore'])):
                    continue
                heatAdded = float(rcore.getTemplateProperty(weaponTemplate, 'heatAddWhenFire'))
                if heatAdded == 0.0:
                    continue
                if self._overheatedByOtherFunction(vehicle, seat, weaponTemplate):
                    rdebug.debugMessage('Weapons %s still overheated by other function' % weaponTemplate, 'vehicles')
                    continue
                rdebug.debugMessage('Removed overheat on weapon %s ' % weaponTemplate, 'vehicles')
                rmemory.setWeaponHeat(weapon, 0.0)
                weapon.rv_disabled = False

        return

    def _overheatedByOtherFunction(self, vehicle, seat, weaponTemplate):
        for func in vehicle.pr_veh_functions:
            if func.getType() != self._type:
                continue
            otherParams = func.getParams()
            if seat not in otherParams:
                continue
            if 'ignore' in otherParams[seat] and any((weaponTemplate.endswith(p) for p in otherParams[seat]['ignore'])):
                continue
            return True

        return False

    def _applyDisableTo(self, vehicle):
        disable = []
        enable = []
        if 'disable' in self._params:
            disable = self._params['disable']
        if 'enable' in self._params:
            enable = self._params['enable']
        alreadyAppliedParts = set()
        for func in vehicle.pr_veh_functions:
            if func.getType() == 'disable':
                parts = func.getParts()
                for part in parts:
                    alreadyAppliedParts.add(part[1])

        for typedPart in disable:
            if typedPart[1] in alreadyAppliedParts:
                continue
            try:
                self._setVehiclePartEnablement(vehicle, typedPart, disabled=True)
            except:
                rdebug.errorMessage()

        for typedPart in enable:
            if typedPart[1] in alreadyAppliedParts:
                continue
            try:
                self._setVehiclePartEnablement(vehicle, typedPart, disabled=False)
            except:
                rdebug.errorMessage()

    def _removeDisableFrom(self, vehicle):
        disable = []
        if 'disable' in self._params:
            disable = self._params['disable']
        stillAppliedParts = set()
        for func in vehicle.pr_veh_functions:
            if func.getType() == 'disable':
                parts = func.getParts()
                for part in parts:
                    stillAppliedParts.add(part[1])

        for part in disable:
            if part in stillAppliedParts:
                continue
            try:
                self._setVehiclePartEnablement(vehicle, part, disabled=False)
            except:
                rdebug.errorMessage()

    def _setVehiclePartEnablement(self, vehicle, typedPart, disabled):
        vehicleSettings = rvehicles_settings.getVehicleSettings(vehicle)
        if not vehicleSettings:
            raise Exception('No settings for vehicle %s' % vehicle.templateName)
        part = typedPart[1]
        offsets = vehicleSettings.getPartOffsets()
        if part not in offsets:
            vehicleSettings.findIdOffsets(vehicle, self.getParts())
            offsets = vehicleSettings.getPartOffsets()
        if part not in offsets:
            raise Exception('No offset for part %s for vehicle %s' % (typedPart, vehicle.templateName))
        vehicleId = rcore.getObjectId(vehicle)
        partOffset = offsets[part]
        partId = vehicleId + partOffset
        host.rcon_invoke('object.active id%s' % partId)
        if disabled:
            host.rcon_invoke('object.setIsDisabledRecursive 1')
        else:
            host.rcon_invoke('object.setIsDisabledRecursive 0')
        partTemplate = host.rcon_invoke('object.templateName').rstrip('\n')
        rdebug.debugMessage('Set enablement %s on part %s' % (not disabled, partTemplate), 'vehicles')


def onRemoteVehiclesCommand(player, cmd, args):
    if cmd == 'oneman':
        if realityserver.C('VEHICLES_REQUIREMENTS') == 1:
            realityserver.C('VEHICLES_REQUIREMENTS', 0)
            rdebug.debugMessage('vehicles requirements system disabled...')
        else:
            realityserver.C('VEHICLES_REQUIREMENTS', 1)
            rdebug.debugMessage('vehicles requirements system enabled...')
    elif cmd == 'exit':
        if realityserver.C('VEHICLES_EXIT_DAMAGE_SPEED') == 1:
            realityserver.C('VEHICLES_EXIT_DAMAGE_SPEED', 0)
            rdebug.debugMessage('vehicles exit damage system disabled...')
        else:
            realityserver.C('VEHICLES_EXIT_DAMAGE_SPEED', 1)
            rdebug.debugMessage('vehicles exit damage system enabled...')
    elif cmd == 'critical':
        if realityserver.C('VEHICLES_EXIT_DAMAGE_CRITICAL') == 1:
            realityserver.C('VEHICLES_EXIT_DAMAGE_CRITICAL', 0)
            rdebug.debugMessage('vehicles critical damage system disabled...')
        else:
            realityserver.C('VEHICLES_EXIT_DAMAGE_CRITICAL', 1)
            rdebug.debugMessage('vehicles critical damage system enabled...')
    elif cmd == 'start':
        if realityserver.C('VEHICLES_START_DELAY') == 1:
            realityserver.C('VEHICLES_START_DELAY', 0)
            rdebug.debugMessage('vehicles start delay system disabled...')
        else:
            realityserver.C('VEHICLES_START_DELAY', 1)
            rdebug.debugMessage('vehicles start delay system enabled...')
    elif cmd == 'damage':
        if len(args) == 0:
            if realityserver.C('VEHICLES_DAMAGE') == 1:
                realityserver.C('VEHICLES_DAMAGE', 0)
                rdebug.debugMessage('vehicles damage system disabled...')
            else:
                realityserver.C('VEHICLES_DAMAGE', 1)
                rdebug.debugMessage('vehicles damage system enabled...')
        elif len(args) == 1:
            if args[0] == 'reload':
                reload(rvehicles_settings)
                cacheVehiclesOnMap()
                rdebug.debugMessage('Reloaded damage settings')
            elif args[0] == 'validate':
                rdebug.debugMessage('Checking damage settings for all vehicles...')
                validateVehicles()
            else:
                damage = float(args[0])
                seatVehicle = player.getVehicle()
                vehicle = getRoot(seatVehicle)
                properties = getVehicleProperties(vehicle)
                maxHealth = properties['maxHitPoints']
                vehicle.setDamage(float(maxHealth) * damage / 100)
                rdebug.debugMessage('Set damage to %s on vehicle %s driven by %s.' % (damage, vehicle.templateName, player.getName()))
        elif len(args) == 2:
            damageSetIdx = int(args[0])
            damageFunctionIdx = int(args[1])
            seatVehicle = player.getVehicle()
            vehicle = getRoot(seatVehicle)
            vehicleSettings = rvehicles_settings.getVehicleSettings(vehicle)
            if not vehicleSettings:
                rdebug.debugMessage('No damage settings for %s' % vehicle.templateName)
                return
            damageSettings = vehicleSettings.getDamageSettings()
            if not damageSettings:
                rdebug.debugMessage('No damage settings for %s' % vehicle.templateName)
                return
            damageSetIdx %= len(damageSettings)
            damageSet = damageSettings[damageSetIdx]
            damageFunctionIdx %= len(damageSet['functions'])
            damageFunction = damageSet['functions'][damageFunctionIdx]
            if damageFunction.isAppliedTo(vehicle):
                damageFunction.removeFrom(vehicle)
                rdebug.debugMessage('Removed disable function %s from damage set %s' % (damageFunctionIdx, damageSetIdx))
            else:
                damageFunction.applyTo(vehicle)
                rdebug.debugMessage('Applyed disable function %s from damage set %s' % (damageFunctionIdx, damageSetIdx))
            seat = getSeat(seatVehicle)
            sendDisabledWeapons(vehicle, seat, player)


def validateVehicles():
    vehicles = bf2.objectManager.getObjectsOfType('dice.hfe.world.ObjectTemplate.PlayerControlObject')
    for vehicle in vehicles:
        template = vehicle.templateName.lower()
        settings = rvehicles_settings.getVehicleSettings(vehicle)
        if not settings:
            continue
        parts = settings.getAllParts()
        settings.findIdOffsets(vehicle, parts)
        offsets = settings.getPartOffsets()
        for part in parts:
            if part[1] not in offsets:
                rdebug.debugMessage('No offset for part %s on vehicle %s' % (part, template))