import bf2
import host
import realityconstants as CONSTANTS
import realitycore as rcore
import realitydebug as rdebug
import realityserver
import realityvehicles_settings as rvehicles_settings
SCORE_KILL = 4
SCORE_TEAMKILL = -8
SCORE_SUICIDE = -8
SCORE_REVIVE = 16
SCORE_REPAIR = 12
SCORE_RESUPPLY = 12
SCORE_HEAL = 12
SCORE_TEAMDAMAGE = -4
SCORE_TEAMVEHICLEDAMAGE = -8
SCORE_ASSETS = 75
SCORE_ASSIST_COMMANDER = 0.25
SCORE_ASSIST_SQUADLEADER = 0.25
SCORE_ASSIST_SQUAD = 0.25
SCORE_ASSIST_VEHICLE = 0.5
REPAIR_POINT_LIMIT = 100
HEAL_POINT_LIMIT = 50
AMMO_POINT_LIMIT = 50
TEAMDAMAGE_POINT_LIMIT = 50
TEAMVEHICLEDAMAGE_POINT_LIMIT = 50
SCORE_DRIVER = 2
SCORE_DRIVER_INTERVAL = 10
SCORE_CAPTURE = 50
SCORE_NEUTRALIZE = 50
SCORE_DEFEND = 10
SCORE_DEFEND_ASSET = 8
SCORE_NORMAL = 0
SCORE_SKILL = 1
SCORE_TEAMWORK = 2
SCORE_COMMAND = 3
TOTAL_SCORE = 0
TOTAL_KILLS = 0
TOTAL_DEATHS = 0
WORTHSCHEMA = {'vehicles': {CONSTANTS.VEHICLE_TYPE_JET: 20,
              CONSTANTS.VEHICLE_TYPE_ARMOR: 10,
              CONSTANTS.VEHICLE_TYPE_HELIATTACK: 10,
              CONSTANTS.VEHICLE_TYPE_IFV: 10,
              CONSTANTS.VEHICLE_TYPE_AAV: 8,
              CONSTANTS.VEHICLE_TYPE_APC: 8,
              CONSTANTS.VEHICLE_TYPE_HELI: 6,
              CONSTANTS.VEHICLE_TYPE_RECON: 6,
              CONSTANTS.VEHICLE_TYPE_TRANSPORT: 4,
              CONSTANTS.VEHICLE_TYPE_STATIC: 2,
              CONSTANTS.VEHICLE_TYPE_ASSET: 20,
              CONSTANTS.VEHICLE_TYPE_AFV: 4,
              CONSTANTS.VEHICLE_TYPE_ALC: 4},
 'kits': {CONSTANTS.KIT_TYPE_AT: 10,
          CONSTANTS.KIT_TYPE_ASSAULT: 0,
          CONSTANTS.KIT_TYPE_ENGINEER: 0,
          CONSTANTS.KIT_TYPE_MEDIC: 0,
          CONSTANTS.KIT_TYPE_SPECOPS: 2,
          CONSTANTS.KIT_TYPE_SUPPORT: 2,
          CONSTANTS.KIT_TYPE_SNIPER: 10}}
WORTH_GRUNT = 0
WORTH_SQUADLEADER = 5
WORTH_COMMANDER = 10
SURVIVAL_RATING_RESTRAINT = 3
VEHICLE_FACTOR = 4
SOLDIER_FACTOR = 1
WEAPONS_NO_PUNISH = ['at_mine',
 'at_mine_linked',
 'at_mine_tm35',
 'argmin_fmk1',
 'argmin_fmk1_linked',
 'argmin_fmk3',
 'germin_smine',
 'germin_smine_q1',
 'germin_smine_q2',
 'insgr_hgr_trap',
 'insgr_hgr_trap_q1',
 'insgr_hgr_trap_soviet',
 'insgr_hgr_trap_soviet_q4',
 'insrg_watercontainer_ied',
 'insrg_watercontainer_ied_idx6',
 'rumin_tm35',
 'rumin_pomz',
 'tm62m_mine',
 'usmin_m1a1',
 'usmin_m2a3',
 'usmin_m2a3_idx7_q2',
 'usmin_m2a3_q1',
 'vnhgr_betty',
 'vnhgr_betty_idx7',
 'vnhgr_betty_idx7_q2',
 'vnhgr_betty_q1',
 'ars_d30',
 'artillery_coop',
 'artillery_m2a1_team2',
 'artillery_nw41_team1',
 'artillery_team1',
 'artillery_team2',
 'jdam_team1',
 'jdam_team2',
 'mortar_team1',
 'mortar_team2',
 'usart_lw155']
g_score_cache = {}

def addScore(player, points, subScore = SCORE_NORMAL, bonuses = True):
    if str(rcore.getMapName()) == 'test_airfield':
        zeroScoreTestMap(player)
    else:
        points = int(points)
        if subScore == SCORE_NORMAL and realityserver.C('SCORING_GENERAL') == 0:
            return 0
        if subScore == SCORE_SKILL and realityserver.C('SCORING_KILLS') == 0:
            return 0
        if subScore == SCORE_COMMAND and realityserver.C('SCORING_TEAMWORK') == 0:
            return 0
        if subScore == SCORE_TEAMWORK and realityserver.C('SCORING_TEAMWORK') == 0:
            return 0
        if points == 0:
            return 0
        playerTeam = player.getTeam()
        playerName = player.getName()
        playerSquad = player.getSquadId()
        if not player.isCommander() or subScore == SCORE_COMMAND or points < 0:
            if points > 0:
                commander = rcore.getCommander(playerTeam)
                if commander and not commander.killed and rcore.isClose(player, commander):
                    bonus = int(SCORE_ASSIST_COMMANDER * points)
                    if realityserver.C('SCORING_GENERAL') == 1:
                        if rdebug.isDebugEnabled('points'):
                            rdebug.debugMessage(playerName + ' ' + str(bonus) + ' bonus points - 50m close to commander', 'points')
                        points += bonus
                    if realityserver.C('SCORING_GENERAL') == 1:
                        if rdebug.isDebugEnabled('points'):
                            rdebug.debugMessage(commander.getName() + ' ' + str(bonus) + ' bonus points for command cohesion', 'points')
                        commander.score.score += bonus
                        addTotalScore(bonus)
                        if realityserver.C('SCORING_TEAMWORK') == 1:
                            commander.score.cmdScore += bonus
                squadLeader = rcore.getSquadLeader(playerTeam, playerSquad)
                if squadLeader and not squadLeader.killed and rcore.isClose(player, squadLeader):
                    bonus = int(SCORE_ASSIST_SQUADLEADER * points)
                    if realityserver.C('SCORING_GENERAL') == 1:
                        if rdebug.isDebugEnabled('points'):
                            rdebug.debugMessage(playerName + ' ' + str(bonus) + ' bonus points - 50m close to squad leader', 'points')
                        points += bonus
                    if realityserver.C('SCORING_GENERAL') == 1:
                        if rdebug.isDebugEnabled('points'):
                            rdebug.debugMessage(squadLeader.getName() + ' ' + str(bonus) + ' bonus points for squad cohesion', 'points')
                        squadLeader.score.score += bonus
                        addTotalScore(bonus)
                        if realityserver.C('SCORING_TEAMWORK') == 1:
                            squadLeader.score.rplScore += bonus
            if realityserver.C('SCORING_GENERAL') == 1:
                if player.score.score + points < 0:
                    addTotalScore(player.score.score * -1)
                    player.score.score = 0
                else:
                    addTotalScore(points)
                    player.score.score += points
            if subScore == SCORE_TEAMWORK and realityserver.C('SCORING_TEAMWORK') == 1:
                if rdebug.isDebugEnabled('points'):
                    rdebug.debugMessage(playerName + ' ' + str(points) + ' teamwork points', 'points')
                player.score.rplScore += points
            elif subScore == SCORE_SKILL and realityserver.C('SCORING_KILLS') == 1:
                if rdebug.isDebugEnabled('points'):
                    rdebug.debugMessage(playerName + ' ' + str(points) + ' skill points', 'points')
                player.score.skillScore += points
            elif subScore == SCORE_COMMAND and realityserver.C('SCORING_TEAMWORK') == 1:
                if rdebug.isDebugEnabled('points'):
                    rdebug.debugMessage(playerName + ' ' + str(points) + ' command points', 'points')
                player.score.cmdScore += points
            elif subScore == SCORE_NORMAL and realityserver.C('SCORING_GENERAL') == 1:
                if rdebug.isDebugEnabled('points'):
                    rdebug.debugMessage(playerName + ' ' + str(points) + ' normal points', 'points')
            if points > 0 and playerSquad > 0 and bonuses:
                vehicle = player.getVehicle()
                crew = []
                if not rcore.isSoldier(vehicle):
                    bonus = int(SCORE_ASSIST_VEHICLE * points)
                    rootVehicle = bf2.objectManager.getRootParent(vehicle)
                    crew = rootVehicle.getOccupyingPlayers()
                    for index, p in enumerate(crew):
                        if p.getSquadId() != playerSquad or p == player:
                            continue
                        if index == 0:
                            p.score.driverAssists += 1
                        else:
                            p.score.passengerAssists += 1
                        if realityserver.C('SCORING_GENERAL') == 1:
                            if rdebug.isDebugEnabled('points'):
                                rdebug.debugMessage(p.getName() + ' ' + str(bonus) + ' bonus points as crew of ' + playerName + ' vehicle', 'points')
                            p.score.score += bonus
                            addTotalScore(bonus)
                            if realityserver.C('SCORING_TEAMWORK') == 1:
                                p.score.rplScore += bonus

                if realityserver.C('SCORING_GENERAL') == 1:
                    bonus = int(SCORE_ASSIST_SQUAD * points)
                    for p in rcore.getPlayersInSquad(player, False):
                        if p in crew or not rcore.isClose(player, p):
                            continue
                        if rdebug.isDebugEnabled('points'):
                            rdebug.debugMessage(p.getName() + ' ' + str(bonus) + ' bonus points as close-by member of ' + playerName + ' squad', 'points')
                        p.score.score += bonus
                        addTotalScore(bonus)

        commander = rcore.getCommander(playerTeam)
        if not commander:
            return points
        if subScore == SCORE_COMMAND or player == commander or points <= 0:
            return points
        numPlayers = bf2.playerManager.getNumberOfAlivePlayersInTeam(playerTeam)
        if numPlayers > 0:
            bonus = int(float(points) / numPlayers)
            if realityserver.C('SCORING_GENERAL') == 1:
                if rdebug.isDebugEnabled('points'):
                    rdebug.debugMessage(commander.getName() + ' ' + str(bonus) + ' commander points', 'points')
                commander.score.score += bonus
                addTotalScore(bonus)
                if realityserver.C('SCORING_TEAMWORK') == 1:
                    commander.score.cmdScore += bonus
        return points


def zeroScore(player):
    if player.score.score > 0 and realityserver.C('SCORING_GENERAL') == 1:
        player.score.score = 0
    if player.score.skillScore > 0 and realityserver.C('SCORING_KILLS') == 1:
        player.score.skillScore = 0
    if player.score.cmdScore > 0 and realityserver.C('SCORING_TEAMWORK') == 1:
        player.score.cmdScore = 0
    if player.score.rplScore > 0 and realityserver.C('SCORING_TEAMWORK') == 1:
        player.score.rplScore = 0
    if rdebug.isDebugEnabled('points'):
        rdebug.debugMessage(player.getName() + ' score zeroed', 'points')

def zeroScoreTestMap(player):
    player.score.ammos = 0
    player.score.cmdScore = 0
    player.score.deaths = 0
    player.score.heals = 0
    player.score.kills = 0
    player.score.repairs = 0
    player.score.rplScore = 0
    player.score.score = 0
    player.score.skillScore = 0
    player.score.teamDamages = 0
    player.score.teamVehicleDamages = 0        


def getTotalScore():
    global TOTAL_SCORE
    return TOTAL_SCORE


def getTotalKills():
    global TOTAL_KILLS
    return TOTAL_KILLS


def getTotalDeaths():
    global TOTAL_DEATHS
    return TOTAL_DEATHS


def addTotalScore(points):
    global TOTAL_SCORE
    TOTAL_SCORE += points


def addTotalKills(kills = 1):
    global TOTAL_KILLS
    TOTAL_KILLS += kills


def addTotalDeaths(deaths = 1):
    global TOTAL_DEATHS
    TOTAL_DEATHS += deaths


def cacheScore(player):
    global g_score_cache
    try:
        playerName = player.getName().split(' ')[1]
        g_score_cache[playerName] = [player.score.ammos,
         player.score.cmdScore,
         player.score.deaths,
         player.score.heals,
         player.score.kills,
         player.score.repairs,
         player.score.rplScore,
         player.score.score,
         player.score.skillScore,
         player.score.teamDamages,
         player.score.teamVehicleDamages]
    except:
        rdebug.errorMessage()


def restoreScore(player):
    try:
        playerName = player.getName().split(' ')[1]
        if playerName in g_score_cache:
            oldScore = g_score_cache[playerName]
            player.score.ammos = oldScore[0]
            player.score.cmdScore = oldScore[1]
            player.score.deaths = oldScore[2]
            player.score.heals = oldScore[3]
            player.score.kills = oldScore[4]
            player.score.repairs = oldScore[5]
            player.score.rplScore = oldScore[6]
            player.score.score = oldScore[7]
            player.score.skillScore = oldScore[8]
            player.score.teamDamages = oldScore[9]
            player.score.teamVehicleDamages = oldScore[10]
            del g_score_cache[playerName]
    except:
        rdebug.errorMessage()


def init():
    bf2.gameLogic.setHealPointLimit(HEAL_POINT_LIMIT)
    bf2.gameLogic.setRepairPointLimit(REPAIR_POINT_LIMIT)
    bf2.gameLogic.setGiveAmmoPointLimit(AMMO_POINT_LIMIT)
    bf2.gameLogic.setTeamDamagePointLimit(TEAMDAMAGE_POINT_LIMIT)
    bf2.gameLogic.setTeamVehicleDamagePointLimit(TEAMVEHICLEDAMAGE_POINT_LIMIT)
    host.registerGameStatusHandler(onGameStatusChanged)
    host.registerHandler('ControlPointNeutralized', onCPNeutralized)
    host.registerHandler('ControlPointCaptured', onCPCaptured)
    host.registerHandler('PositionDefended', onPositionDefended)
    host.registerHandler('AssetDefended', onAssetDefended)
    host.registerHandler('AssetDeployed', onAssetDeployed)
    host.registerHandler('PlayerEnemyKilled', onPlayerEnemyKilled)
    host.registerHandler('PlayerSuicided', onPlayerSuicided)
    host.registerHandler('PlayerTeamKilled', onPlayerTeamKilled)
    host.registerHandler('PlayerPunished', onPlayerPunished)
    host.registerHandler('PlayerDeath', onPlayerDeath)
    host.registerHandler('PlayerRevived', onPlayerRevived)
    host.registerHandler('PlayerHealPoint', onPlayerHealPoint)
    host.registerHandler('PlayerRepairPoint', onPlayerRepairPoint)
    host.registerHandler('PlayerGiveAmmoPoint', onPlayerGiveAmmoPoint)
    host.registerHandler('PlayerTeamDamagePoint', onPlayerTeamDamagePoint)
    host.registerHandler('TeamVehicleDestroyed', onTeamVehicleDestroyed)
    host.registerHandler('EnemyVehicleDestroyed', onEnemyVehicleDestroyed)
    host.registerHandler('EnterVehicle', onEnterVehicle)
    host.registerHandler('ExitVehicle', onExitVehicle)
    host.registerHandler('RemoteCommandPoints', onRemotePointsCommand)
    host.registerHandler('PlayerSpawn', onPlayerSpawn)
    host.registerHandler('PlayerConnect', onPlayerConnect, 1)
    host.registerHandler('PlayerDisconnect', onPlayerDisconnect, 1)
    host.registerHandler('RoundEnd', onRoundEnd, 1)
    print 'realityscoring.py initialized'


def onRoundEnd(winner):
    for player in rcore.getPlayers():
        updateKillerCount(player)

    calculateSurvivalRatingBonus()
    giveCommanderEndScore(rcore.getCommander(1), winner)
    giveCommanderEndScore(rcore.getCommander(2), winner)


def onGameStatusChanged(status):
    global TOTAL_SCORE
    global TOTAL_DEATHS
    global TOTAL_KILLS
    if status == bf2.GameStatus.EndGame:
        host.gl_sendEndOfRoundData('\\')
    g_score_cache.clear()
    TOTAL_SCORE = 0
    TOTAL_KILLS = 0
    TOTAL_DEATHS = 0


def onPlayerConnect(player):
    restoreScore(player)


def onPlayerDisconnect(player):
    updateKillerCount(player)
    cacheScore(player)


def onPlayerSpawn(player, soldier):
    updateKillerCount(player)


def updateKillerCount(player):
    if hasattr(player, 'killer') and player.killer is not None and player.killer.isValid() and hasattr(player, 'killerName') and player.killerName == player.killer.getName():
        try:
            if realityserver.C('SCORING_KILLS') == 1:
                player.killer.score.kills += 1
            addTotalKills()
            addScore(player.killer, player.killerPoints, SCORE_SKILL)
        except:
            pass

    player.killer = None
    player.killerPoints = 0
    return


def giveCommanderEndScore(player, winningTeam):
    if player is None:
        return
    elif player.getTeam() != winningTeam:
        return
    else:
        bonus = int(player.score.score + player.score.fracScore - player.score.cmdScore + player.score.cmdScore * 2)
        if realityserver.C('SCORING_GENERAL') == 1:
            player.score.score = bonus
        if realityserver.C('SCORING_TEAMWORK') == 1:
            player.score.cmdScore = int(player.score.cmdScore * 2)
        return


def onPlayerSuicided(victim, weapon):
    points = -getPlayerWorth(victim, True, True) + SCORE_SUICIDE
    if points >= 0:
        return
    if rdebug.isDebugEnabled('points'):
        rdebug.debugMessage(victim.getName() + ' suicided', 'points')
    victim.score.suicides += 1
    addScore(victim, points, SCORE_TEAMWORK, False)


def onPlayerTeamKilled(victim, attacker, weapon, assists, obj):
    wreck = False
    try:
        if obj is not None and obj.getIsWreck():
            wreck = True
    except:
        pass

    try:
        if weapon:
            if weapon.templateName.lower() in WEAPONS_NO_PUNISH:
                return
            attackerVehicle = bf2.objectManager.getRootParent(weapon)
            if attackerVehicle.getIsRemoteControlled():
                return
    except:
        pass

    if wreck:
        return
    else:
        points = -getPlayerWorth(victim, True) + SCORE_TEAMKILL
        if points >= 0:
            return
        if rdebug.isDebugEnabled('points'):
            rdebug.debugMessage(attacker.getName() + ' teamkilled', 'points')
        attacker.score.TKs += 1
        addScore(attacker, points, SCORE_TEAMWORK, False)
        return


def onPlayerPunished(player):
    if not player.teamkiller:
        return
    if player.teamkiller.teamkilled <= 0:
        return
    if player.teamkiller.teamkilled % 2 == 0:
        if rdebug.isDebugEnabled('points'):
            rdebug.debugMessage(player.teamkiller.getName() + ' punished 2 times for teamkill', 'points')
        zeroScore(player.teamkiller)


def isIgnoredRcWeapon(weapon):
    if not weapon:
        return False
    attackerVehicle = bf2.objectManager.getRootParent(weapon)
    if not attackerVehicle:
        return False
    try:
        if not attackerVehicle.getIsRemoteControlled():
            return False
    except:
        return False

    isRandomCode = filter(lambda c: c.templateName == 'RandomCode', attackerVehicle.getChildren())
    if isRandomCode:
        return False
    return True


def onPlayerEnemyKilled(victim, attacker, weapon, assists, obj):
    if attacker.isCommander():
        return
    isIgnoredRc = isIgnoredRcWeapon(weapon)
    if isIgnoredRc:
        return
    victim.killer = attacker
    victim.killerName = attacker.getName()
    victim.killerPoints = calculateThreatAndWorth(attacker, victim)
    for a in assists:
        assister = a[0]
        assistType = a[1]
        if assister and assister.isValid() and assister.getTeam() != victim.getTeam():
            if assistType == 0:
                assister.score.passengerAssists += 1
            elif assistType == 1:
                assister.score.targetAssists += 1
            elif assistType == 2:
                assister.score.damageAssists += 1
            elif assistType == 3:
                assister.score.driverAssists += 1


def onPlayerDeath(victim, vehicle):
    if victim.teamkiller or victim.forgave:
        return
    if rdebug.isDebugEnabled('points'):
        rdebug.debugMessage(victim.getName() + ' died', 'points')
    if realityserver.C('SCORING_DEATHS') == 1:
        victim.score.deaths += 1
    addTotalDeaths()


def onPlayerRevived(victim, attacker):
    if attacker is None or victim is None or attacker.getTeam() != victim.getTeam():
        return
    else:
        if rdebug.isDebugEnabled('points'):
            rdebug.debugMessage(victim.getName() + ' revived by ' + attacker.getName(), 'points')
        victim.killer = None
        victim.killerPoints = 0
        attacker.score.revives += 1
        addScore(attacker, SCORE_REVIVE, SCORE_TEAMWORK)
        return


def onCPNeutralized(cp, team, players):
    for p in players:
        p.score.cpNeutralizes += 1
        if rdebug.isDebugEnabled('points'):
            rdebug.debugMessage(p.getName() + ' neutralize points', 'points')
        addScore(p, SCORE_NEUTRALIZE, SCORE_TEAMWORK, False)
        bf2.gameLogic.sendGameEvent(p, 12, 3)


def onCPCaptured(cp, team, players):
    for p in players:
        p.score.cpCaptures += 1
        if rdebug.isDebugEnabled('points'):
            rdebug.debugMessage(p.getName() + ' capture points', 'points')
        addScore(p, SCORE_CAPTURE, SCORE_TEAMWORK, False)
        bf2.gameLogic.sendGameEvent(p, 12, 0)


def onAssetDeployed(assetType, player):
    if not player.isValid():
        return
    if assetType not in realityserver.C('ASSET_POINTS_BUILD') or not player:
        return
    if hasattr(player, 'lastAssetScore') and rcore.now() - player.lastAssetScore < realityserver.C('ASSET_POINTS_INTERVAL'):
        return
    if rdebug.isDebugEnabled('points'):
        rdebug.debugMessage(player.getName() + ' asset deployment', 'points')
    player.lastAssetScore = rcore.now()
    if player.isCommander():
        addScore(player, SCORE_ASSETS, SCORE_COMMAND)
        rcore.setSpawnPenalty(player, realityserver.C('SPAWN_PENALTY_BUILD'), 'asset deployment')
    else:
        for p in rcore.getPlayersInSquad(player):
            addScore(p, SCORE_ASSETS, SCORE_TEAMWORK)
            rcore.setSpawnPenalty(p, realityserver.C('SPAWN_PENALTY_BUILD'), 'asset deployment')


def onAssetDefended(team, player):
    if rdebug.isDebugEnabled('points'):
        rdebug.debugMessage(player.getName() + ' defend asset points', 'points')
    addScore(player, SCORE_DEFEND_ASSET, SCORE_TEAMWORK)
    rcore.setSpawnPenalty(player, realityserver.C('SPAWN_PENALTY_DEFEND'), 'asset defense')
    bf2.gameLogic.sendGameEvent(player, 12, 1)


def onPositionDefended(team, player):
    if rdebug.isDebugEnabled('points'):
        rdebug.debugMessage(player.getName() + ' defend points', 'points')
    addScore(player, SCORE_DEFEND, SCORE_TEAMWORK)
    rcore.setSpawnPenalty(player, realityserver.C('SPAWN_PENALTY_DEFEND'), 'defense')
    bf2.gameLogic.sendGameEvent(player, 12, 1)


def onPlayerHealPoint(player, obj):
    if rdebug.isDebugEnabled('points'):
        rdebug.debugMessage(player.getName() + ' heal point', 'points')
    player.score.heals += 1
    addScore(player, SCORE_HEAL, SCORE_TEAMWORK)


def onPlayerRepairPoint(player, obj):
    if rdebug.isDebugEnabled('points'):
        rdebug.debugMessage(player.getName() + ' repair point', 'points')
    player.score.repairs += 1
    addScore(player, SCORE_REPAIR, SCORE_TEAMWORK)


def onPlayerGiveAmmoPoint(player, obj):
    if rdebug.isDebugEnabled('points'):
        rdebug.debugMessage(player.getName() + ' ammo point', 'points')
    player.score.ammos += 1
    addScore(player, SCORE_RESUPPLY, SCORE_TEAMWORK)


def onPlayerTeamDamagePoint(player, obj):
    try:
        if obj is not None and obj.getIsWreck():
            return
    except:
        pass

    if rcore.isSoldier(obj):
        if rdebug.isDebugEnabled('points'):
            rdebug.debugMessage(player.getName() + ' team damage point', 'points')
        player.score.teamDamages += 1
        addScore(player, SCORE_TEAMDAMAGE, SCORE_TEAMWORK, False)
    else:
        try:
            players = obj.getOccupyingPlayers()
        except:
            players = []

        if len(players) == 0:
            return
        if rdebug.isDebugEnabled('points'):
            rdebug.debugMessage(player.getName() + ' team vehicle damage point', 'points')
        player.score.teamVehicleDamages += 1
        addScore(player, SCORE_TEAMVEHICLEDAMAGE, SCORE_TEAMWORK, False)
    return


def onEnemyVehicleDestroyed(vehicle, attacker):
    worth = getVehicleWorth(vehicle)
    if worth <= 0:
        return
    if CONSTANTS.getVehicleType(vehicle.templateName) in [CONSTANTS.VEHICLE_TYPE_ASSET]:
        bf2.gameLogic.sendGameEvent(attacker, 10, 5)
    if rdebug.isDebugEnabled('points'):
        rdebug.debugMessage(attacker.getName() + ' destroyed worthy enemy vehicle', 'points')
    addScore(attacker, VEHICLE_FACTOR * worth, False)


def onTeamVehicleDestroyed(vehicle, attacker):
    worth = getVehicleWorth(vehicle)
    if worth <= 0:
        return
    if rdebug.isDebugEnabled('points'):
        rdebug.debugMessage(attacker.getName() + ' destroyed worthy friendly vehicle', 'points')
    attacker.score.teamVehicleDamages += 1
    addScore(attacker, -VEHICLE_FACTOR * worth, SCORE_TEAMWORK, False)


def onEnterVehicle(player, vehicle, freeSoldier = False):
    checkDriverPoints(player, vehicle, 1)


def onExitVehicle(player, vehicle):
    checkDriverPoints(player, vehicle, 0)


def checkDriverPoints(player, vehicle, enter = 1):
    vehicleTemplate = vehicle.templateName.lower()
    rootVehicle = bf2.objectManager.getRootParent(vehicle)
    rootVehicleTemplate = rootVehicle.templateName.lower()
    times = rcore.now()
    if not hasattr(rootVehicle, 'passengers'):
        rootVehicle.passengers = {}
    if rootVehicleTemplate == vehicleTemplate:
        if enter:
            if rdebug.isDebugEnabled('points'):
                rdebug.debugMessage('driver ' + player.getName() + ' entering ' + vehicleTemplate + ' - resetting passengers list', 'points')
            rootVehicle.passengers.clear()
            for passenger in rootVehicle.getOccupyingPlayers():
                if passenger != player:
                    rootVehicle.passengers[passenger.index] = times

        else:
            if rdebug.isDebugEnabled('points'):
                rdebug.debugMessage('driver ' + player.getName() + ' exiting ' + vehicleTemplate, 'points')
            points = 0
            for ptime in rootVehicle.passengers.values():
                delta = times - ptime
                if delta < SCORE_DRIVER_INTERVAL:
                    continue
                points += int(delta / SCORE_DRIVER_INTERVAL * SCORE_DRIVER)

            if points > 0:
                if rdebug.isDebugEnabled('points'):
                    rdebug.debugMessage(player.getName() + ' ' + str(points) + ' driver points', 'points')
                addScore(player, points, SCORE_TEAMWORK)
            rootVehicle.passengers.clear()
    else:
        playerId = player.index
        if enter:
            rootVehicle.passengers[playerId] = times
            if rdebug.isDebugEnabled('points'):
                rdebug.debugMessage('passenger ' + player.getName() + ' entering ' + rootVehicleTemplate, 'points')
        else:
            if rdebug.isDebugEnabled('points'):
                rdebug.debugMessage('passenger ' + player.getName() + ' exiting ' + rootVehicleTemplate, 'points')
            passengers = rootVehicle.getOccupyingPlayers()
            if len(passengers) == 0:
                return
            driver = passengers[0]
            if player == driver or playerId not in rootVehicle.passengers:
                return
            delta = times - rootVehicle.passengers[playerId]
            try:
                if playerId in rootVehicle.passengers:
                    del rootVehicle.passengers[playerId]
            except:
                return

            if delta < SCORE_DRIVER_INTERVAL:
                return
            points = int(delta / SCORE_DRIVER_INTERVAL * SCORE_DRIVER)
            if rdebug.isDebugEnabled('points'):
                rdebug.debugMessage(driver.getName() + ' ' + str(points) + ' driver points', 'points')
            addScore(driver, points, SCORE_TEAMWORK)


def addSniperBonus(playerVehicle, victimVehicle, points):
    if not playerVehicle or not victimVehicle:
        return 0
    try:
        dist = rcore.getVectorDistance(playerVehicle.getPosition(), victimVehicle.getPosition())
        return int(dist / 600 * points)
    except:
        return 0


def calculateSurvivalRatingBonus():
    for p in rcore.getPlayers():
        if not p.isValid():
            continue
        survivalRating = getPlayerSurvivalRating(p)
        if survivalRating > 0:
            points = int((p.score.kills - p.score.deaths) * survivalRating / SURVIVAL_RATING_RESTRAINT)
            if realityserver.C('SCORING_GENERAL') == 1:
                if rdebug.isDebugEnabled('points'):
                    rdebug.debugMessage(p.getName() + ' ' + str(points) + ' survival rating points', 'points')
                p.score.score += points


def getPlayerSurvivalRating(player):
    kills = float(player.score.kills + 1)
    deaths = float(player.score.deaths + 1)
    return round(kills / deaths, 2)


def calculateThreatAndWorth(attacker, victim):
    points = SCORE_KILL
    if rdebug.isDebugEnabled('points'):
        rdebug.debugMessage(attacker.getName() + ' kill ' + victim.getName() + ' ' + str(SCORE_KILL) + ' points', 'points')
    victimWorth = getPlayerWorth(victim)
    attackerWorth = getPlayerWorth(attacker)
    victimVehicle = None
    victimVehicleWorth = 0
    victimSoldier = True
    try:
        victimVehicle = victim.getVehicle()
        victimVehicleWorth = getVehicleWorth(victimVehicle)
        victimSoldier = rcore.isSoldier(victimVehicle)
    except:
        pass

    attackerVehicle = None
    attackerVehicleWorth = 0
    attackerSoldier = True
    try:
        attackerVehicle = attacker.getVehicle()
        attackerVehicleWorth = getVehicleWorth(attackerVehicle)
        attackerSoldier = rcore.isSoldier(attackerVehicle)
    except:
        pass

    victimKit = None
    victimKitWorth = 0
    if victimSoldier:
        try:
            victimKit = victim.getKit()
            victimKitWorth = getKitWorth(victimKit)
        except:
            pass

    attackerKit = None
    attackerKitWorth = 0
    if attackerSoldier:
        try:
            attackerKit = attacker.getKit()
            attackerKitWorth = getKitWorth(attackerKit)
        except:
            pass

    if victimSoldier and victimKitWorth > 0:
        if rdebug.isDebugEnabled('points'):
            rdebug.debugMessage(victim.getName() + ' lost worthy kit %s points' % (SOLDIER_FACTOR * victimKitWorth), 'points')
        addScore(victim, -SOLDIER_FACTOR * victimKitWorth, SCORE_TEAMWORK, False)
    if not victimSoldier and victimVehicleWorth > 0:
        if rdebug.isDebugEnabled('points'):
            rdebug.debugMessage(victim.getName() + ' lost worthy vehicle %s points' % (VEHICLE_FACTOR * victimVehicleWorth), 'points')
        addScore(victim, -VEHICLE_FACTOR * victimVehicleWorth, SCORE_TEAMWORK, False)
    bonus = victimWorth + victimKitWorth + victimVehicleWorth
    if bonus > 0:
        points += bonus
        if rdebug.isDebugEnabled('points'):
            rdebug.debugMessage(attacker.getName() + ' ' + str(bonus) + ' bonus victim worth points', 'points')
    if victimSoldier:
        vw = SOLDIER_FACTOR * victimWorth
    else:
        vw = VEHICLE_FACTOR * victimWorth
    if attackerSoldier:
        aw = SOLDIER_FACTOR * attackerWorth
    else:
        aw = VEHICLE_FACTOR * attackerWorth
    bonus = vw - aw
    if bonus > 0:
        points += bonus
        if rdebug.isDebugEnabled('points'):
            rdebug.debugMessage(attacker.getName() + ' ' + str(bonus) + ' bonus worth comparison points', 'points')
    attackerThreatRating = getPlayerThreatRating(attacker)
    victimThreatRating = getPlayerThreatRating(victim)
    if rdebug.isDebugEnabled('points'):
        rdebug.debugMessage(attacker.getName() + ' attacker threat %s' % attackerThreatRating, 'points')
        rdebug.debugMessage(victim.getName() + ' victim threat %s' % victimThreatRating, 'points')
    threatRatingFactor = 0
    if attackerThreatRating != 0:
        threatRatingFactor = round(victimThreatRating / attackerThreatRating, 3)
    if threatRatingFactor < 0.125:
        threatRatingFactor = 0
    elif threatRatingFactor < 0.25:
        threatRatingFactor = 0.125
    elif threatRatingFactor < 0.5:
        threatRatingFactor = 0.25
    elif threatRatingFactor < 0.75:
        threatRatingFactor = 0.5
    elif threatRatingFactor < 1.5:
        threatRatingFactor = 1
    elif threatRatingFactor < 2:
        threatRatingFactor = 1.5
    else:
        threatRatingFactor = 2
    bonus = int(threatRatingFactor * points)
    if bonus > 0:
        points += bonus
        if rdebug.isDebugEnabled('points'):
            rdebug.debugMessage(attacker.getName() + ' ' + str(bonus) + ' bonus threat points ' + str(threatRatingFactor), 'points')
    if victimVehicle and attackerVehicle and attackerKit:
        try:
            attackerKitType = CONSTANTS.getKitType(attackerKit.templateName)
        except:
            attackerKitType = None

        if attackerSoldier and attackerKitType == CONSTANTS.KIT_TYPE_SNIPER:
            bonus = addSniperBonus(attackerVehicle, victimVehicle, points)
            if bonus > 0:
                points += bonus
                if rdebug.isDebugEnabled('points'):
                    rdebug.debugMessage(attacker.getName() + ' ' + str(bonus) + ' bonus sniper range points', 'points')
    if rdebug.isDebugEnabled('points'):
        rdebug.debugMessage(attacker.getName() + ' total threat and worth ' + str(points) + ' points', 'points')
    return points


def getKitWorth(kit):
    kitType = CONSTANTS.getKitType(kit.templateName)
    if kitType not in WORTHSCHEMA['kits']:
        return 0
    try:
        return WORTHSCHEMA['kits'][kitType]
    except:
        return 0


def getVehicleWorth(vehicle):
    rootVehicle = CONSTANTS.getRootParent(vehicle)
    rootTemplate = rootVehicle.templateName.lower()
    vehicleType = CONSTANTS.getVehicleType(rootTemplate)
    if vehicleType not in WORTHSCHEMA['vehicles']:
        return 0
    else:
        vehicleSettings = rvehicles_settings.getVehicleSettings(rootVehicle)
        if vehicleSettings and vehicleSettings.isRestrictedSeat(vehicle):
            return WORTHSCHEMA['vehicles'][vehicleType]
        return 0


def getPlayerWorth(player, kit = False, vehicle = False):
    if player.isCommander():
        worth = WORTH_COMMANDER
        if rdebug.isDebugEnabled('points'):
            rdebug.debugMessage(player.getName() + ' commander worth %s' % worth, 'points')
    elif player.isSquadLeader():
        worth = WORTH_SQUADLEADER
        if rdebug.isDebugEnabled('points'):
            rdebug.debugMessage(player.getName() + ' squad leader worth %s' % worth, 'points')
    else:
        worth = WORTH_GRUNT
        if rdebug.isDebugEnabled('points'):
            rdebug.debugMessage(player.getName() + ' grunt worth %s' % worth, 'points')
    if not kit and not vehicle:
        return worth
    else:
        try:
            v = player.getVehicle()
        except:
            v = None

        soldier = rcore.isSoldier(v)
        try:
            if kit and soldier:
                worth += getKitWorth(player.getKit())
        except:
            pass

        try:
            if vehicle and not soldier:
                worth += getVehicleWorth(v)
        except:
            pass

        return worth


def getPlayerThreatRating(player):
    players = bf2.playerManager.getNumberOfPlayers()
    if players == 0:
        return 0
    try:
        score = getTotalScore()
        kills = getTotalKills()
        deaths = getTotalDeaths()
    except:
        return 0

    avgScore = float(score) / players
    avgKills = float(kills) / players
    avgDeaths = float(deaths) / players
    if avgScore == 0:
        avgScore = 1
    if avgKills == 0:
        avgKills = 1
    if avgDeaths == 0:
        avgDeaths = 1
    if player.score.score <= 0:
        scoreFactor = 1 / avgScore
    else:
        scoreFactor = float(player.score.score) / avgScore
    if player.score.kills <= 0:
        killsFactor = 1 / avgKills
    else:
        killsFactor = float(player.score.kills) / avgKills
    if player.score.deaths <= 0:
        deathsFactor = avgDeaths / 1
    else:
        deathsFactor = avgDeaths / float(player.score.deaths)
    threatRating = round(killsFactor * deathsFactor * scoreFactor, 3)
    return threatRating


def onRemotePointsCommand(player, cmd, args):
    count = len(args)
    if count == 0:
        return
    players = []
    points = 0
    if count >= 2:
        players = rcore.getPlayersByName(args[1])
    if count >= 1:
        try:
            points = int(args[0])
        except:
            return

    if len(players) == 0:
        players = [player]
    for p in players:
        addScore(p, points, SCORE_TEAMWORK)


def getMedalEntry(key):
    return None