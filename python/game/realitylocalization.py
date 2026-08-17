# Embedded file name: realitylocalization.py
import bf2
import host
import realityconfig_common as rconfig_common
import realitydebug as rdebug
import realitytimer as rtimer
g_loc_timer = None
g_loc_other = {}
g_loc_default = {}

def t(string, replace = None):
    global g_loc_default
    if not replace:
        replace = {}
    string = string.upper()
    if 'PYTHON_' + string in g_loc_default:
        text = str(g_loc_default['PYTHON_' + string])
        for key, value in replace.items():
            text = text.replace('#' + key.upper() + '#', str(value))

        return text
    return '%' + string + '%'


def parseLocalizationFile(prefix = None, filename = 'pr.utxt', language = None, remove_prefix = False):
    arr = {}
    if not language:
        language = rconfig_common.PRL10N.replace('/', '').lower()
    filename = filename.replace('/', '').lower()
    locDir = str(bf2.gameLogic.getModDir() + '/localization/')
    try:
        locFile = file(locDir + language + '/' + filename, 'r')
    except:
        locFile = file(locDir + 'english/' + filename, 'r')

    for line in locFile:
        line = line.strip()
        line = line.replace('\x00', '')
        line = line.replace('\xfe', '')
        line = line.replace('\xff', '')
        line = line.replace('\r', '')
        if prefix and line.find(prefix) == -1:
            continue
        pair = line.split('\x1b\x1b')
        if len(pair) > 1:
            key = str(pair[0])
            key = key.replace('\x1b\x1b', '')
            key = key.strip()
            value = str(pair[1])
            value = value.replace('\x1b\x1b', '')
            value = value.strip()
            if remove_prefix:
                key = key.replace(prefix, '')
            arr[key] = value

    locFile.close()
    return arr


def init():
    host.registerHandler('RemoteCommandLocalization', onRemoteLocalizationCommand)
    host.registerHandler('RemoteCommandLocalization', onRemoteCompareCommand)
    host.registerHandler('RemoteCommandLocalization', onRemotePrintCommand)
    setDefaultLocalization(rconfig_common.PRL10N)
    print 'realitylocalization.py initialized'


def loadLocalization(other, locfile = 'prmessages', default = 'english'):
    rdebug.debugMessage('localization: default ' + default + ' other ' + other)
    setDefaultLocalization(default, None, locfile)
    setOtherLocalization(other, None, locfile)
    return


def setDefaultLocalization(language = 'english', prefix = 'PYTHON_', locfile = 'prmessages'):
    global g_loc_default
    g_loc_default = parseLocalizationFile(prefix, locfile + '.utxt', language)


def setOtherLocalization(language = 'english', prefix = 'PYTHON_', locfile = 'prmessages'):
    global g_loc_other
    g_loc_other = parseLocalizationFile(prefix, locfile + '.utxt', language)


def onRemoteLocalizationCommand(player, cmd, args):
    setDefaultLocalization(args[0])
    rdebug.debugMessage('localization: changed to ' + args[0])


def onRemotePrintCommand(player, cmd, args):
    global g_loc_timer
    if args[0] != 'print':
        return
    elif g_loc_timer:
        g_loc_timer.destroy()
        g_loc_timer = None
        return
    else:
        try:
            other = args[1]
        except:
            return

        try:
            locfile = args[2]
        except:
            locfile = 'prmessages'

        loadLocalization(other, locfile)
        first = None
        for keyword in g_loc_other:
            if not first:
                first = keyword
                break

        g_loc_timer = rtimer.Timer(onTimer, 2, 1, first)
        return


def onRemoteCompareCommand(player, cmd, args):
    if args[0] != 'compare':
        return
    try:
        other = args[1]
    except:
        return

    try:
        locfile = args[2]
    except:
        locfile = 'prmessages'

    loadLocalization(other, locfile)
    found = False
    for keyword in g_loc_default:
        if keyword not in g_loc_other:
            rdebug.debugMessage('localization: keyword "' + keyword + '" missing in ' + other + ' ' + locfile + '.utxt')
            found = True

    if not found:
        rdebug.debugMessage('localization: no keywords missing in ' + other + ' ' + locfile + '.utxt')


def onTimer(data = None):
    global g_loc_timer
    if g_loc_timer:
        g_loc_timer.destroy()
        g_loc_timer = None
    if data is None:
        return
    else:
        if data in g_loc_other:
            host.rcon_invoke('game.sayAll "' + g_loc_other[data] + '"')
        found = False
        for keyword in g_loc_other:
            if found:
                data = keyword
                break
            if keyword == data:
                found = True

        if data is None:
            return
        g_loc_timer = rtimer.Timer(onTimer, 2, 1, data)
        return