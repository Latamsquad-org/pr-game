# Embedded file name: realitygameplay.py
import bf2
import host
import realityconfig_common as rconfig_common
import realityconstants as CONSTANTS
import realitycore as rcore
import realitydebug as rdebug
import realityevents as revents
import realitykits as rkits
import realitylaser as rlaser
import realitymarkers as rmarkers
import realitymemory as rmemory
import realityserver
import realityspawner as rspawner
import realitytimer as rtimer
GAMEPLAY_ATTACK_EXPIRATION = 1800
GAMEPLAY_PARADROP_EXPIRATION = 120
GAMEPLAY_PARACRATE_EXPIRATION = 300
GAMEPLAY_PARACRATE_TEMPLATE = 'para_supply_crate'
GAMEPLAY_TARGET_EXPIRATION = 60
GAMEPLAY_MAX_LZ = 7
GAMEPLAY_MAX_MINES = 3
GAMEPLAY_MAX_SPOTTED = 3
GAMEPLAY_TEMPLATES = ['marker_spotted',
 'marker_lz',
 'marker_extract',
 'marker_extract_apc',
 'marker_mines',
 'marker_extract_helo',
 'marker_supply',
 'marker_repair',
 'marker_target']
GAMEPLAY_SPOTTED = ['outpost',
 'tank',
 'apc',
 'aav',
 'atm',
 'aa',
 'at',
 'truck',
 'jeep',
 'rally',
 'spotter',
 'bridge',
 'destroyedbridge',
 'supply',
 'supplyallied',
 'stationarymortar_allied_commander',
 'request_demolition',
 'request_recon',
 'request_sniper',
 'ifv',
 'mine',
 'objective',
 'razorwire',
 'sniper',
 'saboteur',
 'squad1',
 'squad2',
 'squad3',
 'squad4',
 'squad5',
 'squad6',
 'squad7',
 'squad8',
 'squad9',
 'buildfob',
 'buildminefield',
 'buildmortar',
 'stationaryaa',
 'stationaryat',
 'stationaryatallied',
 'stationarymg',
 'stationarymortar',
 'infantry',
 'stationarymortar_commander',
 'outpost_commander',
 'objective_commander']
GAMEPLAY_REQUEST = {'cas': 20,
 'mortar': 180}
for index in range(1, GAMEPLAY_MAX_LZ + 1):
    GAMEPLAY_TEMPLATES.append('marker_lz_' + str(index))

for index in GAMEPLAY_SPOTTED:
    GAMEPLAY_TEMPLATES.append('marker_spotted_' + str(index))

for index in GAMEPLAY_REQUEST.keys():
    GAMEPLAY_TEMPLATES.append('marker_' + str(index))

GAMEPLAY_ATTACK = {'jdam': 40,
 'artillery': None,
 'mortar': None}
GAMEPLAY_EXTRACT_MODES = ['helo', 'apc', 'jeep']
GAMEPLAY_SUPPORT_MODES = ['armor',
 'cas',
 'jeep',
 'bombcar']
GAMEPLAY_STATUS_MODES = ['attack',
 'observe',
 'build',
 'destroy',
 'move',
 'defend']
GAMEPLAY_BRIDGES_DISTANCE = 20
GAMEPLAY_BRIDGES_TEMPLATES = ['deployable_csb_no10',
 'deployable_csb_no10_dds',
 'deployable_csb_no10_sds',
 'deployable_csb_no10_trestle',
 'deployable_csb_no10_trestle_sds',
 'deployable_csb_no11',
 'deployable_csb_no11_dds',
 'deployable_csb_no11_sds',
 'deployable_csb_no10_built',
 'deployable_csb_no10_dds_built',
 'deployable_csb_no10_sds_built',
 'deployable_csb_no10_trestle_built',
 'deployable_csb_no10_trestle_sds_built',
 'deployable_csb_no11_built',
 'deployable_csb_no11_dds_built',
 'deployable_csb_no11_sds_built']
g_attack = {}
g_distance = {}
g_spotted = {}
g_mutiny = {}
g_mutiny_last = {}
g_target = {}
g_target_last = {}
g_reload = {}
g_check_arty_firing_timer = None
g_last_target_marker = {}
g_lz = {}
g_bridges = {}
g_informants = {}
g_informants_timer = None
g_paradrop_timer_expire = None
g_paradrop_squad = {}
g_paradrop_markers = []
g_paradrop_spawners = []
g_paradrop_time = 0
g_delayed_spawners = []
g_delayed_spawners_timer = None

def init():
    host.registerGameStatusHandler(onGameStatusChanged)
    host.registerHandler('RemoteCommandGameplayRequest', onCustomGameplayRequest)
    host.registerHandler('AttackRequest', onAttackRequest)
    host.registerHandler('ExtractRequest', onExtractRequest)
    host.registerHandler('SupplyRequest', onSupplyRequest)
    host.registerHandler('AmmoRequest', onAmmoRequest)
    host.registerHandler('RepairRequest', onRepairRequest)
    host.registerHandler('MedicRequest', onMedicRequest)
    host.registerHandler('MineRequest', onMineRequest)
    host.registerHandler('SupportRequest', onSupportRequest)
    host.registerHandler('FireRequest', onFireRequest)
    host.registerHandler('MutinyRequest', onMutinyRequest)
    host.registerHandler('StatusRequest', onStatusRequest)
    host.registerHandler('ChangedCommander', onChangedCommander)
    host.registerHandler('ChangedCommander', onChangedCommanderDeleteConstantMarkers)
    host.registerHandler('RemoteCommandDistance', onDistanceDefined)
    host.registerHandler('RemoteCommandRequestMark', onRequestOrSpottedMarkDefined)
    host.registerHandler('RemoteCommandSpottedMark', onRequestOrSpottedMarkDefined)
    host.registerHandler('RemoteCommandGameplayMark', onGameplayMarkCreated)
    host.registerHandler('VehicleSpawned', onVehicleSpawned)
    host.registerHandler('VehicleDestroyed', onCsbCrateDropped)
    host.registerHandler('VehicleDestroyed', onNapalmBombExploded)
    host.registerHandler('PositionMarked', onMarkedSpotted)
    host.registerHandler('PositionMarked', onMarkedDelete)
    host.registerHandler('PositionMarked', onMarkedCAS)
    host.registerHandler('PositionMarked', onMarkedLandingZone)
    host.registerHandler('PositionMarked', onMarkedMortar)
    host.registerHandler('PositionMarked', onMarkedMinefield)
    host.registerHandler('PositionsUpdated', onPositionsUpdated)
    host.registerHandler('ExitVehicle', onExitSpectatorCamera)
    host.registerHandler('RemoteCommandCheat', onRemoteCheatCommand)
    host.registerHandler('RemoteCommandClosest', onRemoteClosestCommand)
    host.registerHandler('RemoteCommandSpectator', onRemoteSpectatorCommand)
    print 'realitygameplay.py initialized'


def onGameStatusChanged(status):
    global g_paradrop_time
    global g_lz
    global g_target
    global g_paradrop_markers
    global g_bridges
    global g_mutiny
    global g_paradrop_timer_expire
    global g_delayed_spawners
    global g_mutiny_last
    global g_paradrop_squad
    global g_delayed_spawners_timer
    global g_informants
    global g_check_arty_firing_timer
    global g_attack
    global g_reload
    global g_last_target_marker
    global g_spotted
    global g_target_last
    global g_paradrop_spawners
    global g_informants_timer
    if status == bf2.GameStatus.Playing:
        for team in [1, 2]:
            g_attack[team] = None
            g_reload[team] = None
            g_target[team] = bf2.objectManager.getObjectsOfType('dice.hfe.world.ObjectTemplate.TargetObject')[team - 1]
            g_target_last[team] = (0.0, 0.0, 0.0)
            g_mutiny[team] = None
            g_mutiny_last[team] = None
            g_paradrop_squad[team] = {}
            for squad in range(1, 10):
                g_paradrop_squad[team][squad] = None

            g_lz[team] = {}
            g_informants[team] = {}

        rtimer.fireOnce(setupBridges, 13, '')
        g_check_arty_firing_timer = rtimer.Timer(onCheckArtyFiring, 5, 1, '')
        g_check_arty_firing_timer.setRecurring(5)
        if rcore.getTeamName(1) in realityserver.C('INFORMANTS_TEAMS') or rcore.getTeamName(2) in realityserver.C('INFORMANTS_TEAMS'):
            g_informants_timer = rtimer.Timer(checkInformants, realityserver.C('STARTDELAY') + realityserver.C('INFORMANTS_MOVEMENT_DELAY'), 1, '')
            g_informants_timer.setRecurring(30)
        g_paradrop_time = 0
        g_paradrop_spawners = []
        g_delayed_spawners = []
        hasPara = False
        spawners = rcore.cleanListOfObjects(revents.getOnPlayingObjectSpawners())
        for spawner in spawners:
            try:
                template = spawner.templateName
                if 'paradrop' in template:
                    _id = rcore.getObjectId(spawner)
                    hasPara = True
                    if _id:
                        host.rcon_invoke('Object.active id' + str(_id))
                        cpId = host.rcon_invoke('Object.getControlPointId').replace('\n', '')
                        layer = host.rcon_invoke('Object.layer').replace('\n', '')
                        pos = spawner.getPosition()
                        rot = spawner.getRotation()
                        team = int(spawner.getTemplateProperty('team'))
                        if team == 0:
                            team = 2
                        nrSpawned = int(spawner.getTemplateProperty('maxNrOfObjectSpawned'))
                        time = float(spawner.getTemplateProperty('minSpawnDelay'))
                        if time < 99999.0 and nrSpawned > 1:
                            if g_paradrop_time < nrSpawned * time:
                                g_paradrop_time = nrSpawned * time
                        distance = float(spawner.getTemplateProperty('distance'))
                        endPos = rcore.getPositionFromPositionAndRotation(pos, rot, distance)
                        g_paradrop_markers.append(rmarkers.markerParadropStart(team, pos, 'paradrop_start'))
                        g_paradrop_markers.append(rmarkers.markerParadropEnd(team, endPos, 'paradrop_end'))
                        g_paradrop_spawners.append(template)
                        g_delayed_spawners.append((template,
                         pos,
                         rot,
                         layer,
                         cpId))
                        rcore.deleteObjectId(_id)
                elif int(spawner.getTemplateProperty('spawnDelayAtStart')) == 1:
                    _id = rcore.getObjectId(spawner)
                    if _id:
                        host.rcon_invoke('Object.active id' + str(_id))
                        cpId = host.rcon_invoke('Object.getControlPointId').replace('\n', '')
                        layer = host.rcon_invoke('Object.layer').replace('\n', '')
                        pos = spawner.getPosition()
                        rot = spawner.getRotation()
                        maxDelay = float(spawner.getTemplateProperty('maxSpawnDelay'))
                        g_delayed_spawners.append((template,
                         pos,
                         rot,
                         layer,
                         cpId,
                         maxDelay))
                        rcore.deleteObjectId(_id)
            except:
                continue

        if len(g_delayed_spawners):
            g_delayed_spawners_timer = rtimer.Timer(createDelayedSpawners, realityserver.C('STARTDELAY'), 1, '')
        if hasPara:
            g_paradrop_timer_expire = rtimer.Timer(destroyParadrops, 1, 1, '')
    else:
        for team in [1, 2]:
            destroyReloadTimer(team)

        destroyParadropExpireTimer()
        destroyInformantsTimer()
        destroyDelayedSpawnersTimer()
        destroyCheckArtyFiringTimer()
        g_bridges.clear()
        g_attack.clear()
        g_reload.clear()
        g_target_last.clear()
        g_target.clear()
        g_last_target_marker.clear()
        g_lz.clear()
        g_informants.clear()
        g_spotted.clear()
        g_mutiny.clear()
        g_mutiny_last.clear()
        g_paradrop_squad.clear()
        del g_paradrop_spawners[:]
        del g_paradrop_markers[:]
        del g_delayed_spawners[:]
    return


def onRemoteSpectatorCommand(player, cmd, args):
    if player.killed:
        return
    if cmd == 'prbot':
        tmp = 'spectator_camera_spawner'
    elif cmd == 'prbot2':
        tmp = 'spectator_camera_2_spawner'
    elif cmd == 'prbot3':
        tmp = 'spectator_camera_3_spawner'
    elif cmd == 'prbot4':
        tmp = 'spectator_camera_4_spawner'
    elif cmd == 'prbot_alt':
        tmp = 'spectator_camera_alt_spawner'
    else:
        return
    if cmd == 'prbot_alt':
        rspawner.createSpawner(tmp, {'team': player.getTeam(),
         'position': rcore.getPositionFromPlayer(player, 5),
         'teamonvehicle': 1,
         'rotation': (0, 0, 0)})
    else:
        rspawner.createSpawner(tmp, {'team': player.getTeam(),
         'position': rcore.getPositionFromPlayer(player, 5),
         'teamonvehicle': 1})


def onExitSpectatorCamera(player, vehicle):
    if vehicle.templateName.lower().startswith('spectator_camera'):
        try:
            rootVehicle = CONSTANTS.getRootParent(vehicle)
            if len(rootVehicle.getOccupyingPlayers()) == 0:
                rcore.deleteObject(rootVehicle)
        except:
            pass


def onRemoteClosestCommand(player, cmd, args):
    if player.killed:
        return
    else:
        if not realityserver.C('PRDEBUG_ALL') and not rdebug.isDebugEnabled():
            if not rkits.isNinja(player):
                return
        friendly = True
        try:
            if int(args[0].strip()) != 0:
                friendly = False
        except:
            pass

        team = player.getTeam()
        if not friendly:
            team = rcore.getOtherTeam(team)
        try:
            pos = player.getDefaultVehicle().getPosition()
        except:
            return

        distance = 999999999
        closest = None
        for p in rcore.getAlivePlayers(team):
            if rkits.isNinja(p):
                continue
            try:
                dis = rcore.getSquareVectorDistance(p.getDefaultVehicle().getPosition(), pos)
            except:
                continue

            if dis <= CONSTANTS.DISTANCE_CLOSE ** 2 or dis > distance:
                continue
            distance = rcore.copy(dis)
            closest = p

        if not closest:
            return
        player.getDefaultVehicle().setPosition(rcore.getPositionFromPlayer(closest, -5))
        return


def onRemoteCheatCommand(player, cmd, args):
    if cmd == 'teleport':
        if player.killed:
            return
        try:
            distance = int(args[0].strip())
        except:
            distance = 10

        try:
            altitude = int(args[1].strip())
        except:
            altitude = 0

        pos = rcore.getPositionFromPlayer(player, distance)
        player.getDefaultVehicle().setPosition((pos[0], pos[1], pos[2]))
    elif cmd == 'ready':
        if player.isManDown():
            rcore.setPlayerDamage(player, 0)
        player.setTimeToSpawn(0)
    elif cmd == 'arty':
        for spawner in bf2.objectManager.getObjectsOfType('dice.hfe.world.ObjectTemplate.ObjectSpawner'):
            try:
                team = int(spawner.getTemplateProperty('team').replace('\n', ''))
                template = spawner.getTemplateProperty('objectTemplate').replace('\n', '')
                pos = spawner.getPosition()
                rot = spawner.getRotation()
                if template in ('artillery_team1', 'artillery_team2', 'mortar_team1', 'mortar_team2', 'jdam_team1', 'jdam_team2'):
                    rspawner.createSpawner('arty_team_%s' % team, {'team': team,
                     'template': template,
                     'position': pos,
                     'rotation': rot})
            except:
                pass


def createDelayedSpawners(data = ''):
    destroyDelayedSpawnersTimer()
    ids = []
    for _tuple in g_delayed_spawners:
        try:
            res = host.rcon_invoke('Object.create ' + str(_tuple[0])).replace('\n', '')
            if res.find('Unauthorised method!') != -1:
                continue
            pos = _tuple[1]
            rot = _tuple[2]
            layer = int(_tuple[3])
            cpId = _tuple[4]
            if cpId not in ids:
                ids.append(cpId)
            host.rcon_invoke('Object.absolutePosition %s/%s/%s' % (pos[0], pos[1], pos[2]))
            host.rcon_invoke('Object.rotation %s/%s/%s' % (rot[0], rot[1], rot[2]))
            host.rcon_invoke('Object.layer ' + str(layer))
            host.rcon_invoke('Object.setControlPointId ' + str(cpId))
        except:
            continue

    for cp in rcore.getControlPoints():
        if cp.getTemplateProperty('controlPointID') in ids:
            team = cp.cp_getParam('team')
            cp.cp_setParam('team', team)

    for _tuple in g_delayed_spawners:
        if len(_tuple) != 6:
            continue
        template = _tuple[0]
        respawn = _tuple[5]
        rcore.setTemplateProperties(template, {'maxSpawnDelay': respawn,
         'minSpawnDelay': respawn})

    del g_delayed_spawners[:]


def destroyDelayedSpawnersTimer():
    global g_delayed_spawners_timer
    try:
        if g_delayed_spawners_timer:
            g_delayed_spawners_timer.destroy()
            g_delayed_spawners_timer = None
    except:
        pass

    return


def destroyParadropExpireTimer():
    global g_paradrop_timer_expire
    try:
        if g_paradrop_timer_expire:
            g_paradrop_timer_expire.destroy()
            g_paradrop_timer_expire = None
    except:
        pass

    return


def destroyCheckArtyFiringTimer():
    global g_check_arty_firing_timer
    try:
        if g_check_arty_firing_timer:
            g_check_arty_firing_timer.destroy()
            g_check_arty_firing_timer = None
    except:
        pass

    return


def destroyParadrops(data = ''):
    global g_paradrop_timer_expire
    destroyParadropExpireTimer()
    rcore.deleteObjectsOfTemplate('paradrop')
    if g_paradrop_time:
        g_paradrop_timer_expire = rtimer.Timer(disableParadrops, realityserver.C('STARTDELAY') + g_paradrop_time, 1, '')
    else:
        g_paradrop_timer_expire = rtimer.Timer(checkParadrops, realityserver.C('STARTDELAY'), 1, '')
        g_paradrop_timer_expire.setRecurring(10)


def disableParadrops(data = ''):
    global g_paradrop_timer_expire
    destroyParadropExpireTimer()
    for template in g_paradrop_spawners:
        for spawner in rcore.getObjectsOfTemplate(template):
            _id = rcore.getObjectId(spawner)
            host.rcon_invoke('Object.active id' + str(_id))
            host.rcon_invoke('Object.setTeam 0')

    g_paradrop_timer_expire = rtimer.Timer(checkParadrops, 10, 1, '')
    g_paradrop_timer_expire.setRecurring(10)


def checkParadrops(data = ''):
    if len(list(rcore.cleanListOfObjects(rcore.getObjectsOfTemplate('paradrop')))) == 0:
        for marker in g_paradrop_markers:
            rmarkers.deleteMarker(marker)

        for template in g_paradrop_spawners:
            rcore.deleteObjectsOfTemplate(template)

        del g_paradrop_spawners[:]
        del g_paradrop_markers[:]
        destroyParadropExpireTimer()


def setupBridges(data = ''):
    for template in GAMEPLAY_BRIDGES_TEMPLATES:
        for bridge in rcore.cleanListOfObjects(bf2.objectManager.getObjectsOfTemplate(template), True):
            g_bridges[bridge.getPosition()] = bridge
            if rdebug.isDebugEnabled('bridge'):
                rdebug.debugMessage('%s ' % template, 'bridge')

    if len(g_bridges) == 0:
        if rdebug.isDebugEnabled('bridge'):
            rdebug.debugMessage('no bridges found', 'bridge')
        return


def onDistanceDefined(player, cmd, args):
    global g_distance
    try:
        distance = int(args[0])
    except:
        return

    if distance == 0:
        return
    g_distance[player.index] = [distance, rcore.now()]
    if rdebug.isDebugEnabled('gameplay'):
        rdebug.debugMessage('distance %s set by player %s' % (distance, player.index), 'gameplay')


spottingWeapons = {'insrg_phone',
 'insrg_phone_idx2',
 'radio',
 'radio_fsa',
 'radio_insurgent',
 'radio_insurgent_spotter',
 'radio_militia',
 'radio_militia_spotter',
 'radio_militia90',
 'radio_militia90_spotter',
 'radio_spotter',
 'radio_vnnva',
 'radio_ww2rus',
 'radio_ww2rus_spotter',
 'simrad'}

def isSpottingWeapon(weapon):
    if weapon is None:
        return False
    elif weapon.templateName.lower() not in spottingWeapons:
        return False
    else:
        return True


def onRequestOrSpottedMarkDefined(player, cmd, args):
    if player.killed:
        return
    else:
        try:
            mark = str(args[0])
        except:
            return

        if cmd == 'request' and mark not in GAMEPLAY_REQUEST:
            return
        if cmd == 'mark' and mark not in GAMEPLAY_SPOTTED:
            return
        pos = None
        if rmemory.isWindowsListenServer:
            host.rcon_invoke('game.sayall "Placing marks not supported on create local"')
            return
        if cmd == 'request' and rlaser.isPlayerLasing(player):
            pos = rlaser.getPlayerLasePosition(player)
        elif player.isSquadLeader():
            order = rmemory.getSLOrder(player.getTeam(), player.getSquadId())
            if not rcore.isPlayerLookingAtPoint(player, order, 10.0):
                rcore.sendMessageToPlayer(player, 1222016, 2)
                return
            pos = order
        if not pos:
            rcore.sendMessageToPlayer(player, 1222016, 2)
            return
        if player.index not in g_spotted:
            g_spotted[player.index] = []
        if len(g_spotted[player.index]) >= GAMEPLAY_MAX_SPOTTED:
            rmarkers.deleteMarker(g_spotted[player.index].pop(0))
        if not isSpottingWeapon(player.getPrimaryWeapon()):
            return
        if cmd == 'mark':
            _index = rmarkers.markerSpotted(player.getTeam(), pos, 'spotted_' + mark)
        else:
            _index = rmarkers.createMarker('marker_' + mark, player.getTeam(), pos, 'request_%s_%s' % (mark, player.index), None, 150, GAMEPLAY_REQUEST[mark], False)
        g_spotted[player.index].append(_index)
        return


def onGameplayMarkCreated(player, cmd, args):
    if not player.isCommander() or not player.isAlive():
        return
    team = player.getTeam()
    position = (float(args[0]), 3000, float(args[1]))
    mark = args[2]
    markArgs = args[3:]
    if rdebug.isDebugEnabled('gameplay'):
        rdebug.debugMessage('mark ' + str(cmd) + ' team ' + str(team) + ' args ' + str(args) + ' markArgs ' + str(markArgs), 'gameplay')
    event = revents.getEvents('PositionMarked')
    revents.sendToHandlers(event, mark, team, position, markArgs)


def onCsbCrateDropped(vehicle, attacker):
    if vehicle.templateName.lower() == 'csb_crate':
        try:
            crate_pos = vehicle.getPosition()
        except:
            return

        closestBridge = None
        closestBridgeDistance = None
        for bridge_pos, bridge in g_bridges.items():
            distance = rcore.getSquareVectorDistance(bridge_pos, crate_pos)
            if distance > GAMEPLAY_BRIDGES_DISTANCE ** 2:
                continue
            damage = bridge.getDamage()
            if damage is None:
                rdebug.debugMessage('Bridge returned None damage', 'bridge')
                continue
            if rdebug.isDebugEnabled('bridge'):
                rdebug.debugMessage('close to %s damage %s distance %s' % (bridge.templateName, damage, distance), 'bridge')
            if damage > 500:
                continue
            if closestBridgeDistance is None or distance < closestBridgeDistance:
                closestBridge = bridge
                closestBridgeDistance = distance

        if closestBridge:
            closestBridge.setDamage(1000)
            if rdebug.isDebugEnabled('bridge'):
                rdebug.debugMessage('deploying %s' % closestBridge.templateName, 'bridge')
    return


def onNapalmBombExploded(vehicle, attacker):
    if vehicle.templateName != 'glu-1_firebomb':
        return
    if rdebug.isDebugEnabled('gameplay'):
        rdebug.debugMessage('napalm bomb exploded', 'gameplay')
    try:
        vpos = vehicle.getPosition()
    except:
        return

    rspawner.createSpawner('glu-1_firebomb_fire_spawner', {'team': 2,
     'position': vpos})


def destroyReloadTimer(team):
    try:
        if g_reload[team]:
            g_reload[team].destroy()
            g_reload[team] = None
    except:
        pass

    return


def onCheckArtyFiring(data = ''):
    for team in (1, 2):
        checkArtyFiring(team)


def isTeamAreaAttacking(team):
    return team in g_reload and g_reload[team]


def onAttackRequest(player):
    if not player.isCommander() or not player.isAlive():
        return
    team = player.getTeam()
    checkArtyFiring(team)


def checkArtyFiring(team):
    if isTeamAreaAttacking(team):
        return
    try:
        pos = g_target[team].getPosition()
    except:
        return

    if team in g_target_last:
        if g_target_last[team] != pos:
            destroyReloadTimer(team)
            g_reload[team] = rtimer.Timer(onAttackReload, 60, 1, team)
            g_target_last[team] = pos
            rdebug.debugMessage('Team %s launching area attack' % team, 'gameplay')


def onAttackReload(team):
    destroyReloadTimer(team)
    g_attack[team] = None
    for gun in ['artillery_team%s', 'mortar_team%s', 'jdam_team%s']:
        rcore.deleteObjectsOfTemplate(gun % team)

    disableAttack(team)
    if rdebug.isDebugEnabled('gameplay'):
        rdebug.debugMessage('attack reload team ' + str(team), 'gameplay')
    return


def enableAttack(team):
    if not rcore.reallyPlaying():
        return
    if True:
        return
    if not isAttackEnabled(team):
        host.rcon_invoke('objecttemplate.active ' + getAttackTemplate(team))
        host.rcon_invoke('objecttemplate.rctype RCArtillery')
        if rdebug.isDebugEnabled('gameplay'):
            rdebug.debugMessage('Area attack activated, team ' + str(team), 'gameplay')


def disableAttack(team):
    if True:
        return
    if isAttackEnabled(team):
        host.rcon_invoke('objecttemplate.active ' + getAttackTemplate(team))
        host.rcon_invoke('objecttemplate.rctype RCNone')
        if rdebug.isDebugEnabled('gameplay'):
            rdebug.debugMessage('Area attack deactivated, team ' + str(team), 'gameplay')


def isAttackEnabled(team):
    host.rcon_invoke('objecttemplate.active ' + getAttackTemplate(team))
    return str(host.rcon_invoke('objecttemplate.rctype')).replace('\n', '').lower() == 'rcartillery'


def getAttackTemplate(team):
    if team == 2:
        return 'ArtilleryControlObjectUS'
    else:
        return 'ArtilleryControlObjectMEC'


def onVehicleSpawned(vehicle):
    if not rcore.reallyPlaying():
        return
    rdebug.debugMessage('Vehicle Spawned', 'gameplay')
    template = vehicle.templateName.lower()
    if template[:template.find('_')] in GAMEPLAY_ATTACK:
        rdebug.debugMessage('Artillery Spawned', 'gameplay')
        enableAttack(vehicle.getTeam())


def onExtractRequest(player, mode = ''):
    team = player.getTeam()
    if mode in GAMEPLAY_EXTRACT_MODES:
        _index = 'extract_' + str(mode) + '_' + str(player.index)
    else:
        _index = 'extract_' + str(player.index)
    rmarkers.markerExtraction(team, rcore.getPositionFromPlayer(player, 15), _index)
    if rdebug.isDebugEnabled('gameplay'):
        rdebug.debugMessage('extract team ' + str(team) + ' player ' + str(player.index) + ' mode ' + str(mode), 'gameplay')


def onRepairRequest(player):
    team = player.getTeam()
    rmarkers.markerRepair(team, rcore.getPositionFromPlayer(player, 15), 'repair_' + str(player.index))
    if rdebug.isDebugEnabled('gameplay'):
        rdebug.debugMessage('repair team ' + str(team) + ' player ' + str(player.index), 'gameplay')


def onMedicRequest(player):
    team = player.getTeam()
    rmarkers.markerMedic(team, rcore.getPositionFromPlayer(player, 15), 'medic_' + str(player.index))
    if rdebug.isDebugEnabled('gameplay'):
        rdebug.debugMessage('medic team ' + str(team) + ' player ' + str(player.index), 'gameplay')


def onSupplyRequest(player):
    team = player.getTeam()
    rmarkers.markerSupply(team, rcore.getPositionFromPlayer(player, 15), 'supply_' + str(player.index))
    if rdebug.isDebugEnabled('gameplay'):
        rdebug.debugMessage('supply team ' + str(team) + ' player ' + str(player.index), 'gameplay')


def onAmmoRequest(player):
    team = player.getTeam()
    rmarkers.markerAmmo(team, rcore.getPositionFromPlayer(player, 15), 'ammo_' + str(player.index))
    if rdebug.isDebugEnabled('gameplay'):
        rdebug.debugMessage('ammo team ' + str(team) + ' player ' + str(player.index), 'gameplay')


def onSupportRequest(player, mode = ''):
    team = player.getTeam()
    if mode in GAMEPLAY_SUPPORT_MODES:
        _index = 'support_' + str(mode) + '_' + str(player.index)
    else:
        _index = 'support_' + str(player.index)
    rmarkers.markerSupport(team, rcore.getPositionFromPlayer(player, 15), _index)
    if rdebug.isDebugEnabled('gameplay'):
        rdebug.debugMessage('support team ' + str(team) + ' player ' + str(player.index) + ' mode ' + str(mode), 'gameplay')


def onFireRequest(player):
    team = player.getTeam()
    rmarkers.markerCloseAirSupport(team, rcore.getPositionFromPlayer(player, 15), 'fire_' + str(player.index))
    if rdebug.isDebugEnabled('gameplay'):
        rdebug.debugMessage('fire team ' + str(team) + ' player ' + str(player.index), 'gameplay')


def onMutinyRequest(player):
    if rconfig_common.PRMUTINY != 1:
        return
    elif not player.isSquadLeader():
        return
    else:
        team = player.getTeam()
        cmdr = rcore.getCommander(team)
        if not cmdr:
            return
        elif player.changedSquad and rcore.now() - player.changedSquad <= realityserver.C('MUTINY_INTERVAL'):
            if rdebug.isDebugEnabled('gameplay'):
                rdebug.debugMessage('too soon for %s to start a mutiny on team %s - squad leader is new' % (player.getName(), team), 'gameplay')
            return rcore.sendMessageToPlayer(player, 1031406, 3)
        diff = None
        if g_mutiny_last[team]:
            diff = rcore.now() - g_mutiny_last[team]
        if diff and realityserver.C('MUTINY_VOTING') < diff <= realityserver.C('MUTINY_INTERVAL'):
            if rdebug.isDebugEnabled('gameplay'):
                rdebug.debugMessage('too soon for a mutiny on team %s - time restrictions' % team, 'gameplay')
            return rcore.sendMessageToPlayer(player, 1031406, 3)
        if not diff or diff > realityserver.C('MUTINY_INTERVAL'):
            if rdebug.isDebugEnabled('gameplay'):
                rdebug.debugMessage('%s started mutiny vote of %s on team %s' % (player.getName(), cmdr.getName(), team), 'gameplay')
            g_mutiny[team] = {'voters': [player.index],
             'voted': [player.index]}
            g_mutiny_last[team] = rcore.now()
            rcore.sendMessageToPlayer(player, 1031119, 3)
            for squad in range(1, 10):
                sl = rcore.getSquadLeader(team, squad)
                if not sl or sl.index == player.index:
                    continue
                if not sl.changedSquad or rcore.now() - sl.changedSquad > realityserver.C('MUTINY_INTERVAL'):
                    g_mutiny[team]['voters'].append(sl.index)
                    rcore.sendMessageToPlayer(sl, 1031619, 3)

            if rdebug.isDebugEnabled('gameplay'):
                rdebug.debugMessage('%s mutiny voters allowed = %s' % (cmdr.getName(), rcore.getPlayersNames(rcore.getPlayersByIndex(g_mutiny[team]['voters']))), 'gameplay')
        else:
            if player.index not in g_mutiny[team]['voters'] or player.index in g_mutiny[team]['voted']:
                return
            g_mutiny[team]['voted'].append(player.index)
            needed = len(g_mutiny[team]['voters'])
            voted = len(g_mutiny[team]['voted'])
            if rdebug.isDebugEnabled('gameplay'):
                rdebug.debugMessage('%s voted in favor for mutiny on team %s - %s out of %s' % (player.getName(),
                 team,
                 voted,
                 needed), 'gameplay')
            rcore.sendMessageToPlayer(player, 1031119, 3)
            if float(voted) / float(needed) > realityserver.C('MUTINY_PERCENTAGE'):
                if rdebug.isDebugEnabled('gameplay'):
                    rdebug.debugMessage('mutiny votes %s out of %s - %s removed as commander of team %s' % (voted,
                     needed,
                     cmdr.getName(),
                     team), 'gameplay')
                cmdr.setTeam(rcore.getOtherTeam(team))
                cmdr.setTeam(team)
                g_mutiny[team] = {}
                g_mutiny_last[team] = None
                rcore.sendMessageToPlayer(cmdr, 1031120, 3)
                for squad in range(1, 10):
                    sl = rcore.getSquadLeader(team, squad)
                    if sl:
                        rcore.sendMessageToPlayer(sl, 1031120, 3)

        return


def onChangedCommander(team, oldCmd, newCmd):
    if newCmd:
        team = newCmd.getTeam()
        g_mutiny[team] = {}
        g_mutiny_last[team] = None
        if rdebug.isDebugEnabled('gameplay'):
            rdebug.debugMessage('mutiny vote time reset on team %s' % team, 'gameplay')
    return


deleteOldCommanderMarkersTimer = {1: None,
 2: None}

def onChangedCommanderDeleteConstantMarkers(team, oldCmd, newCmd):
    teamTimer = deleteOldCommanderMarkersTimer[team]
    if teamTimer:
        teamTimer.destroy()
    if newCmd is None:
        deleteOldCommanderMarkersTimer[team] = rtimer.fireOnce(deleteOldCommanderMarkers, 600, team)
        if rdebug.isDebugEnabled('gameplay'):
            rdebug.debugMessage('commander markers delete timer set team %s' % team, 'gameplay')
    return


def deleteOldCommanderMarkers(team):
    for marker in rmarkers.getMarkers(team):
        if 'commander' in marker.template:
            marker.delete()


def onStatusRequest(player, mode = ''):
    team = player.getTeam()
    if mode in GAMEPLAY_STATUS_MODES:
        _index = 'status_' + str(mode) + '_' + str(player.index)
    else:
        _index = 'status_' + str(player.index)
    rmarkers.markerStatus(team, rcore.getPositionFromPlayer(player, 15), _index)
    if rdebug.isDebugEnabled('gameplay'):
        rdebug.debugMessage('status team ' + str(team) + ' player ' + str(player.index) + ' mode ' + str(mode), 'gameplay')


def onMineRequest(player):
    if not hasattr(player, 'lastMineMarker'):
        player.lastMineMarker = 0
    if player.lastMineMarker >= GAMEPLAY_MAX_MINES:
        player.lastMineMarker = 1
    else:
        player.lastMineMarker += 1
    _index = 'mine_%s_%s' % (player.index, player.lastMineMarker)
    for team in [1, 2]:
        rmarkers.deleteMarker(_index, team)

    try:
        playerPos = player.getDefaultVehicle().getPosition()
    except:
        return

    rmarkers.markerMines(player.getTeam(), playerPos, _index)
    if rdebug.isDebugEnabled('gameplay'):
        rdebug.debugMessage('mine team ' + str(player.getTeam()) + ' index ' + str(_index), 'gameplay')


def onMarkedMinefield(mark, team, position, args):
    if mark != 'minefield':
        return
    try:
        if int(args[0]) == 1:
            for marker in rmarkers.getMarkers(team):
                if marker.template == 'marker_mines':
                    rmarkers.deleteMarker(marker.index)

    except:
        pass

    rmarkers.markerMinefield(team, position, 'minefield')
    if rdebug.isDebugEnabled('gameplay'):
        rdebug.debugMessage('minefield team ' + str(team), 'gameplay')


def onMarkedSpotted(mark, team, position, args):
    if mark != 'spotted':
        return
    try:
        if args[0] in GAMEPLAY_SPOTTED:
            mark = mark + '_' + args[0]
    except:
        pass

    try:
        if int(args[1]) == 1:
            for marker in rmarkers.getMarkers(team):
                if marker.template == 'marker_' + mark:
                    rmarkers.deleteMarker(marker.index)

    except:
        pass

    rmarkers.markerSpotted(team, position, mark)
    if rdebug.isDebugEnabled('gameplay'):
        rdebug.debugMessage('spotted team ' + str(team) + ' ' + mark, 'gameplay')


def onMarkedDelete(mark, team, position, args):
    if mark != 'delete':
        return
    _all = False
    try:
        if int(args[0]) == 1:
            _all = True
    except:
        pass

    zoomed = False
    try:
        if args[0] == 'zoomed':
            zoomed = True
    except:
        pass

    if _all:
        markers = rmarkers.getMarkers(team)
    elif rcore.getMapArea() in [CONSTANTS.HUGE, CONSTANTS.INSANE]:
        if zoomed:
            markers = rmarkers.getMarkersClose(position, CONSTANTS.DISTANCE_AREA_HUGE * CONSTANTS.DISTANCE_AREA_ZOOM_FACTOR, team)
        else:
            markers = rmarkers.getMarkersClose(position, CONSTANTS.DISTANCE_AREA_HUGE, team)
    elif rcore.getMapArea() in [CONSTANTS.BIG]:
        if zoomed:
            markers = rmarkers.getMarkersClose(position, CONSTANTS.DISTANCE_AREA_BIG * CONSTANTS.DISTANCE_AREA_ZOOM_FACTOR, team)
        else:
            markers = rmarkers.getMarkersClose(position, CONSTANTS.DISTANCE_AREA_BIG, team)
    elif rcore.getMapArea() in [CONSTANTS.MEDIUM, CONSTANTS.SMALL, CONSTANTS.TINY]:
        if zoomed:
            markers = rmarkers.getMarkersClose(position, CONSTANTS.DISTANCE_AREA_SMALL * CONSTANTS.DISTANCE_AREA_ZOOM_FACTOR, team)
        else:
            markers = rmarkers.getMarkersClose(position, CONSTANTS.DISTANCE_AREA_SMALL, team)
    else:
        markers = rmarkers.getMarkersClose(position, CONSTANTS.DISTANCE_AREA, team)
    for marker in markers:
        if marker.template not in GAMEPLAY_TEMPLATES:
            continue
        if marker.index.find('lz_') != -1:
            try:
                if marker.index in g_lz[team]:
                    del g_lz[team][marker.index]
            except:
                pass

        rmarkers.deleteMarker(marker.index)


def onMarkedTarget(mark, team, position, args):
    if mark != 'target':
        return
    if team in g_last_target_marker and rcore.now() - g_last_target_marker[team] <= GAMEPLAY_TARGET_EXPIRATION:
        return
    g_last_target_marker[team] = rcore.now()
    rspawner.createSpawner('mark_laser_spawner', {'team': rcore.getOtherTeam(team),
     'position': position})
    rmarkers.markerTarget(team, position, 'target')
    if rdebug.isDebugEnabled('gameplay'):
        rdebug.debugMessage('target team ' + str(team), 'gameplay')


def onMarkedMortar(mark, team, position, args):
    if mark != 'mortar':
        return
    rmarkers.markerMortar(team, position, 'mortar')
    if rdebug.isDebugEnabled('gameplay'):
        rdebug.debugMessage('mortar team ' + str(team), 'gameplay')


def onMarkedCAS(mark, team, position, args):
    if mark != 'cas':
        return
    rmarkers.markerCloseAirSupport(team, position, 'cas')
    if rdebug.isDebugEnabled('gameplay'):
        rdebug.debugMessage('cas team ' + str(team), 'gameplay')


def onMarkedLandingZone(mark, team, position, args):
    if mark != 'lz':
        return
    if len(g_lz[team]) >= GAMEPLAY_MAX_LZ:
        return
    for key in range(1, GAMEPLAY_MAX_LZ + 1):
        _index = str(team) + '_lz_' + str(key)
        if _index in g_lz[team]:
            continue
        rmarkers.markerLandingZone(team, position, 'lz_' + str(key), key)
        g_lz[team][_index] = rcore.now()
        if rdebug.isDebugEnabled('gameplay'):
            rdebug.debugMessage('lz team ' + str(team) + ' num ' + str(key), 'gameplay')
        break


def onPositionsUpdated(positions):
    if realityserver.C('INFORMANTS_CLOSE_DISABLE') == 0:
        return
    for team in [1, 2]:
        if rcore.getTeamName(team) not in realityserver.C('INFORMANTS_TEAMS'):
            continue
        if not rcore.getCommander(team):
            continue
        playerPositions = positions[rcore.getOtherTeam(team)]
        objectPositions = {}
        for _index, times in g_lz[team].items():
            if rcore.now() - realityserver.C('INFORMANTS_MOVEMENT_DELAY') < times:
                continue
            marker = rmarkers.getMarker(_index)
            try:
                position = marker.position()
            except:
                continue

            objectPositions[_index] = position

        for _index, count in rcore.getCloseProximity(playerPositions, objectPositions, realityserver.C('INFORMANTS_CLOSE_DISABLE'), CONSTANTS.DISTANCE_AREA, True, True, True, True).items():
            if _index in g_informants[team]:
                continue
            if rdebug.isDebugEnabled('gameplay'):
                rdebug.debugMessage('informant %s reports %s enemies are close' % (_index, count), 'gameplay')
            g_informants[team][_index] = rcore.now()


def destroyInformantsTimer():
    global g_informants_timer
    try:
        if g_informants_timer:
            g_informants_timer.destroy()
            g_informants_timer = None
    except:
        pass

    return


def checkInformants(data = ''):
    for team in [1, 2]:
        cmdr = rcore.getCommander(team)
        if not cmdr:
            continue
        if rcore.getTeamName(team) not in realityserver.C('INFORMANTS_TEAMS'):
            continue
        for _index, times in g_informants[team].items():
            if rcore.now() - realityserver.C('INFORMANTS_REPORT_DELAY') < times:
                continue
            if times in range(0, 6):
                if times == 5:
                    try:
                        if _index in g_informants[team]:
                            del g_informants[team][_index]
                    except:
                        pass

                else:
                    g_informants[team][_index] += 1
                continue
            else:
                g_informants[team][_index] = 0
            if rdebug.isDebugEnabled('gameplay'):
                rdebug.debugMessage('informant %s intel received by %s' % (_index, cmdr.getName()), 'gameplay')
            for key in range(1, GAMEPLAY_MAX_LZ + 1):
                if _index != '%s_lz_%s' % (team, key):
                    continue
                if key == 1:
                    msg = 1031406
                elif key == 2:
                    msg = 1031619
                elif key == 3:
                    msg = 1031119
                elif key == 4:
                    msg = 1031120
                elif key == 5:
                    msg = 1031109
                elif key == 6:
                    msg = 1031115
                elif key == 7:
                    msg = 1031121
                else:
                    continue
                rcore.sendMessageToPlayer(cmdr, msg, 2)
                break


def onCustomGameplayRequest(player, cmd, args):
    mode = ''
    officer = True
    if cmd == 'attack':
        customEvent = 'AttackRequest'
    elif cmd == 'extract':
        customEvent = 'ExtractRequest'
        try:
            mode = args[0]
        except:
            pass

    elif cmd == 'support':
        customEvent = 'SupportRequest'
        try:
            mode = args[0]
        except:
            pass

    elif cmd == 'supply':
        customEvent = 'SupplyRequest'
    elif cmd == 'repair':
        customEvent = 'RepairRequest'
    elif cmd == 'ammo':
        customEvent = 'AmmoRequest'
    elif cmd == 'medic':
        customEvent = 'MedicRequest'
    elif cmd == 'fire':
        customEvent = 'FireRequest'
    elif cmd == 'mutiny':
        customEvent = 'MutinyRequest'
    elif cmd == 'status':
        customEvent = 'StatusRequest'
        try:
            mode = args[0]
        except:
            pass

    elif cmd == 'mine':
        customEvent = 'MineRequest'
        officer = False
    else:
        return
    if officer and not player.isSquadLeader() and not player.isCommander():
        return
    event = revents.getEvents(customEvent)
    if mode:
        revents.sendToHandlers(event, player, mode)
    else:
        revents.sendToHandlers(event, player)