import bf2
import host
import realitycore as rcore
import realitykits as rkits


def pilotKit(player,team):
    if player.killed:
        return
    try:
        playerPos = player.getDefaultVehicle().getPosition()
    except:
        return
    if str(rcore.getMapName()) == 'test_airfield':
        if team == 1:
            rkits.spawnerKit(player, playerPos, 'ch_pilot', player.getTeam())
            return True
        elif team == 2:
            rkits.spawnerKit(player, playerPos, 'gb_pilot', player.getTeam())
            return True
    else:
        return False