# Embedded file name: realityspawner.py
import bf2
import host
import realitycore as rcore
import realitydebug as rdebug
g_spawners = {}
g_spawners_properties = {}
g_spawners_created = []
spawnerDefault = {'minspawndelay': 99999,
 'maxspawndelay': 99999,
 'maxnrobjectspawned': 1,
 'distance': 99999,
 'timetolive': 99999,
 'damagewhenlost': 0,
 'spawndelayatstart': '',
 'teamonvehicle': 1,
 'team': 1}

def init():
    host.registerGameStatusHandler(onGameStatusChanged)
    host.registerHandler('RemoteCommandSpawner', onRemoteSpawnerCommand)
    host.registerHandler('RoundEnd', onRoundEnd)
    print 'realityspawner.py initialized'


def onGameStatusChanged(status):
    global g_spawners_properties
    global g_spawners_created
    global g_spawners
    if status != bf2.GameStatus.Playing:
        g_spawners.clear()
        g_spawners_properties.clear()
        try:
            del g_spawners_created[:]
        except:
            pass


def onRoundEnd(winner):
    for name in g_spawners_created[:]:
        deleteSpawner(name)
        if rdebug.isDebugEnabled('spawner'):
            rdebug.debugMessage('deleting created spawner ' + name, 'spawner')


def getProperties(obj):
    properties = {}
    for p, v in spawnerDefault.items():
        value = obj.getTemplateProperty(p)
        try:
            value = value.replace('\n', '')
        except:
            pass

        if value:
            if value == 'Unknown object or method!':
                value = ''
            properties[p] = value

    templates = obj.getTemplateProperty('ObjectTemplate').split('\n')
    templates.pop()
    if len(templates) == 1:
        team = str(properties['team'])
        if team != '0':
            properties['setobjecttemplate ' + team] = templates[0].lower()
        else:
            properties['setobjecttemplate 1'] = templates[0].lower()
            properties['setobjecttemplate 2'] = templates[0].lower()
    elif len(templates) == 2:
        properties['setobjecttemplate 1'] = templates[0].lower()
        properties['setobjecttemplate 2'] = templates[1].lower()
    else:
        properties['setobjecttemplate 1'] = obj.templateName.replace('_spawner', '')
        properties['setobjecttemplate 2'] = obj.templateName.replace('_spawner', '')
    return properties


def filterProperties(properties = None):
    if not properties:
        properties = {}
    arr = {}
    for p, v in properties.items():
        arr[p.lower()] = v

    return arr


def createSpawner(name, properties = None, delete = True, reset = True, sufix = False):
    if not properties:
        properties = {}
    if delete or sufix:
        tempname = name + '_' + str(int(rcore.now())) + str(rcore.random.randint(0, 9999))
    else:
        tempname = name
    if spawnerExists(tempname):
        return
    properties = filterProperties(properties)
    defaults = {}
    for p, v in spawnerDefault.items():
        defaults[p] = v

    for p, v in properties.items():
        defaults[p] = v

    if 'setobjecttemplate 1' not in properties and 'setobjecttemplate 2' not in properties:
        if 'template' in properties:
            template = properties['template']
        else:
            template = name.replace('_spawner', '')
        defaults['setobjecttemplate 0'] = template
        defaults['setobjecttemplate 1'] = template
        defaults['setobjecttemplate 2'] = template
        try:
            host.rcon_invoke('ObjectTemplate.active %s' % template)
            if 'no object template' in host.rcon_invoke('ObjectTemplate.type').lower():
                raise Exception('Tried to spawn unknown template %s' % template)
        except:
            rdebug.errorMessage()

    if 'delay' in properties:
        defaults['minspawndelay'] = properties['delay']
        defaults['maxspawndelay'] = properties['delay']
    host.rcon_invoke('ObjectTemplate.create objectSpawner ' + tempname)
    if rdebug.isDebugEnabled('spawner'):
        rdebug.debugMessage('created ' + tempname, 'spawner')
    if not editSpawner(tempname, defaults, True):
        return
    if reset:
        g_spawners_created.append(tempname)
    if delete:
        deleteSpawner(tempname)
    return True


def editSpawner(name, properties = None, create = False):
    if not properties:
        properties = {}
    if not create and not spawnerExists(name):
        return
    else:
        properties = filterProperties(properties)
        if name not in g_spawners_properties:
            g_spawners_properties[name] = {}
        if 'position' not in properties:
            properties['position'] = None
        if 'rotation' not in properties:
            properties['rotation'] = None
        if not setSpawnerProperties(name, properties):
            return
        for p, v in properties.items():
            g_spawners_properties[name][p] = str(v)

        if not create:
            return rcore.editObject(g_spawners[name], properties['position'], properties['rotation'])
        index = rcore.createObject(name, properties['position'], properties['rotation'])
        if not index:
            return
        g_spawners[name] = index
        return True


def spawnerExists(name):
    if name in g_spawners:
        return True
    return False


def deleteSpawner(name):
    if not spawnerExists(name):
        return
    rcore.deleteObjectId(g_spawners[name])
    try:
        if name in g_spawners:
            del g_spawners[name]
    except:
        pass

    try:
        if name in g_spawners_properties:
            del g_spawners_properties[name]
    except:
        pass

    try:
        if name in g_spawners_created:
            g_spawners_created.remove(name)
    except:
        pass

    return True


def activateSpawner(name):
    return rcore.activateTemplate(name, 'objectSpawner')


def getSpawnerProperties(name, properties = None):
    if not properties:
        properties = []
    return rcore.getTemplateProperties(name, properties, 'objectSpawner')


def setSpawnerProperties(name, properties = None):
    if not properties:
        properties = {}
    return rcore.setTemplateProperties(name, properties, 'objectSpawner')


def getRandomSpawnerProperty(name):
    try:
        gpm = getSpawnerProperties(name, ['minspawndelay', 'maxspawndelay'])
        if gpm:
            return rcore.random.randint(int(gpm['minspawndelay']), int(gpm['maxspawndelay']))
    except:
        pass


def getTeamSpawnerProperty(name):
    try:
        gpm = getSpawnerProperties(name, ['team'])
        if gpm:
            return int(gpm['team'])
    except:
        pass


def onRemoteSpawnerCommand(player, cmd, args):
    if player.killed:
        return
    try:
        name = args[0] + '_spawner'
    except:
        return

    createSpawner(name, {'team': player.getTeam(),
     'position': rcore.getPositionFromPlayer(player, 4),
     'rotation': player.getDefaultVehicle().getRotation()})