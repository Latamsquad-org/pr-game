# -*- coding: utf-8 -*-
# latamfiles.py - mueve demos/json al fin de ronda y renombra auto*/tracker*

import os
import re
import struct
import zlib
import shutil
import time
import json

try:
    import host
except ImportError:
    host = None

# Rutas de este servidor (prbf2_1 / sv1)
SOURCE_2D = 'C:/prbf2_1/demos/'
DEST_2D = 'C:/prbf2_db/sv1/demos2d/'

SOURCE_JSON = 'C:/prbf2_1/json/'
DEST_JSON = 'C:/prbf2_db/sv1/json/'

SOURCE_3D = 'C:/prbf2_1/mods/pr/demos/'
DEST_3D = 'C:/prbf2_db/sv1/demos3d/'

# Log de fallos (RoundStart no debe tumbar el servidor)
_FILES_LOG = 'C:/prbf2_db/sv1/latamfiles.log'

# Solo hace falta la cabecera zlib del .bf2demo (no cargar 100MB+ en RAM).
_HEADER_READ_BYTES = 256 * 1024

# Caracteres no validos en nombres de archivo en Windows.
_INVALID_WIN_CHARS = re.compile(r'[<>:"/\\|?*]')

# tracker_YYYY_MM_DD_HH_MM_SS_... o tracker_DD_MM_YYYY_HH_MM_SS_...
_TRACKER_DT = re.compile(
    r'^tracker_(\d{4}_\d{2}_\d{2}_\d{2}_\d{2}_\d{2}|\d{2}_\d{2}_\d{4}_\d{2}_\d{2}_\d{2})_',
    re.IGNORECASE
)
# tracker_DT_map_gpm_*_layer.ext (YMD o DMY)
_TRACKER_FULL = re.compile(
    r'^tracker_(\d{4}_\d{2}_\d{2}_\d{2}_\d{2}_\d{2}|\d{2}_\d{2}_\d{4}_\d{2}_\d{2}_\d{2})_(.+)_(gpm_[A-Za-z0-9_]+)_(\d+)(?:_\d+)?\.(prdemo|json)$',
    re.IGNORECASE
)

# Fecha canonica en nombres finales: dia_mes_ano_hora_min_seg
_YMD_DT = re.compile(r'^(\d{4})_(\d{2})_(\d{2})_(\d{2})_(\d{2})_(\d{2})$')
_DMY_DT = re.compile(r'^(\d{2})_(\d{2})_(\d{4})_(\d{2})_(\d{2})_(\d{2})$')
# map_YYYY_MM_DD_HH_MM_SS.ext o map_YYYY_MM_DD_HH_MM_SS_2.ext (conflicto)
_NAME_YMD_TAIL = re.compile(
    r'^(.*_)(\d{4})_(\d{2})_(\d{2})_(\d{2})_(\d{2})_(\d{2})(_\d+)?(\.[^.]+)$',
    re.IGNORECASE
)
# auto_YYYY_MM_DD_HH_MM_SS.ext
_AUTO_YMD = re.compile(
    r'^auto_(\d{4}_\d{2}_\d{2}_\d{2}_\d{2}_\d{2})(\.[^.]+)$',
    re.IGNORECASE
)
# Nombre corto roto: map_DMY.ext (sin modo/layer)
_MAP_DMY_ONLY = re.compile(
    r'^(.+)_(\d{2}_\d{2}_\d{4}_\d{2}_\d{2}_\d{2})(_\d+)?\.(json|prdemo)$',
    re.IGNORECASE
)
# Nombre tracker ya correcto con DMY
_TRACKER_DMY_OK = re.compile(
    r'^tracker_\d{2}_\d{2}_\d{4}_\d{2}_\d{2}_\d{2}_.+_gpm_[A-Za-z0-9_]+_\d+(?:_\d+)?\.(json|prdemo)$',
    re.IGNORECASE
)


def _log(message):
    """Escribe una linea de diagnostico; nunca propaga errores."""
    try:
        line = '%s %s\n' % (time.strftime('%Y-%m-%d %H:%M:%S'), message)
        with open(_FILES_LOG, 'a') as handle:
            handle.write(line)
    except Exception:
        pass


def _has_ext(name, ext):
    """Comparacion de extension case-insensitive (ej. .JSON / .PRdemo)."""
    if not name or not ext:
        return False
    low = name.lower()
    ext_low = ext.lower()
    if not ext_low.startswith('.'):
        ext_low = '.' + ext_low
    return low.endswith(ext_low)


def moveFiles3D():
    """Mueve .bf2demo no vacios desde demos del mod al almacenamiento 3D."""
    if not os.path.isdir(SOURCE_3D):
        _log('moveFiles3D: source missing %s' % SOURCE_3D)
        return
    try:
        ListOfFiles = os.listdir(SOURCE_3D)
    except Exception as exc:
        _log('moveFiles3D: listdir failed: %s' % exc)
        return

    if not os.path.isdir(DEST_3D):
        try:
            os.makedirs(DEST_3D)
        except Exception as exc:
            _log('moveFiles3D: cannot create dest: %s' % exc)
            return

    moved = 0
    for files in ListOfFiles:
        src_path = os.path.join(SOURCE_3D, files)
        try:
            if not _has_ext(files, '.bf2demo'):
                continue
            if not os.path.isfile(src_path):
                continue
            if os.path.getsize(src_path) == 0:
                continue
            dest_path = _unique_destination(DEST_3D, files)
            shutil.move(src_path, dest_path)
            moved += 1
            if os.path.basename(dest_path) != files:
                _log('moveFiles3D: conflict renamed %s -> %s' % (files, os.path.basename(dest_path)))
        except Exception as exc:
            # Un archivo bloqueado no debe abortar el resto.
            _log('moveFiles3D: %s -> %s' % (files, exc))
    _log('moveFiles3D: moved %s files' % moved)


def _read_string32(data, offset):
    """Lee un string con longitud uint32 little-endian y avanza el offset."""
    if offset + 4 > len(data):
        raise ValueError('cabecera truncada al leer longitud de string')
    length = struct.unpack_from('<I', data, offset)[0]
    offset += 4
    if length > 1024 * 1024:
        raise ValueError('longitud de string invalida: %s' % length)
    if offset + length > len(data):
        raise ValueError('cabecera truncada al leer contenido de string')
    raw = data[offset:offset + length]
    offset += length
    # Py2: raw es str; Py3: bytes. Quitar nulls finales.
    if isinstance(raw, type(b'')):
        raw = raw.split(b'\x00', 1)[0]
        text = raw.decode('utf-8', 'replace')
    else:
        raw = raw.split('\x00', 1)[0]
        text = raw.decode('utf-8', 'replace') if hasattr(raw, 'decode') else raw
    return text, offset


def _extract_map_name(path):
    """
    Descomprime (parcialmente) el .bf2demo y obtiene el MapName de la cabecera.
    Layout tras zlib: 4 bytes skip | server (str32) | start_time (str32) | map_name (str32)
    Solo lee los primeros _HEADER_READ_BYTES del archivo.
    """
    with open(path, 'rb') as handle:
        compressed = handle.read(_HEADER_READ_BYTES)

    if not compressed:
        raise ValueError('archivo vacio')

    decompressor = zlib.decompressobj()
    decompressed = decompressor.decompress(compressed)
    # Si hace falta mas salida, intentar finish (cabecera corta).
    try:
        decompressed += decompressor.flush()
    except Exception:
        pass

    if len(decompressed) < 8:
        raise ValueError('datos descomprimidos insuficientes')

    offset = 4
    _server, offset = _read_string32(decompressed, offset)
    _start_time, offset = _read_string32(decompressed, offset)
    map_name, _offset = _read_string32(decompressed, offset)

    map_name = map_name.strip()
    if not map_name:
        raise ValueError('nombre de mapa vacio')
    if _INVALID_WIN_CHARS.search(map_name):
        raise ValueError('mapa con caracteres invalidos: %r' % map_name)
    return map_name


def _loads_json_tolerant(raw):
    """Parsea JSON; si hay basura o doble objeto, usa el primer valor valido."""
    if isinstance(raw, type(b'')):
        text = raw.decode('utf-8', 'replace')
    else:
        text = raw
    text = text.lstrip()
    if not text:
        raise ValueError('json vacio')
    try:
        return json.loads(text)
    except Exception:
        pass
    decoder = json.JSONDecoder()
    data, _end = decoder.raw_decode(text)
    return data


def _extract_map_name_from_json(path):
    """Lee MapName del summary JSON del Reality Tracker."""
    meta = _extract_round_meta_from_json(path)
    return meta['map']


def _extract_round_meta_from_json(path):
    """Lee MapName / MapMode / MapLayer del summary JSON."""
    with open(path, 'rb') as handle:
        raw = handle.read()
    if not raw:
        raise ValueError('json vacio')
    data = _loads_json_tolerant(raw)
    if not isinstance(data, dict):
        raise ValueError('json no es objeto')
    map_name = data.get('MapName') or data.get('mapName') or ''
    map_name = str(map_name).strip()
    if not map_name:
        raise ValueError('MapName vacio en json')
    if _INVALID_WIN_CHARS.search(map_name):
        raise ValueError('mapa con caracteres invalidos: %r' % map_name)
    mode = data.get('MapMode') or data.get('mapMode') or ''
    mode = str(mode).strip()
    if mode and not mode.lower().startswith('gpm_'):
        mode = 'gpm_' + mode
    if not mode:
        raise ValueError('MapMode vacio en json')
    if _INVALID_WIN_CHARS.search(mode):
        raise ValueError('modo con caracteres invalidos: %r' % mode)
    layer = data.get('MapLayer')
    if layer is None:
        layer = data.get('mapLayer')
    if layer is None or str(layer).strip() == '':
        raise ValueError('MapLayer vacio en json')
    layer = str(layer).strip()
    if _INVALID_WIN_CHARS.search(layer):
        raise ValueError('layer con caracteres invalidos: %r' % layer)
    return {'map': map_name, 'mode': mode, 'layer': layer}


def _parse_tracker_datetime(filename):
    """Extrae fecha (YMD o DMY) del prefijo tracker_..."""
    m = _TRACKER_DT.match(filename)
    if not m:
        return None
    return m.group(1)


def _extract_dmy_from_filename(filename):
    """Obtiene DD_MM_YYYY_HH_MM_SS desde tracker_* o map_*_fecha.ext."""
    dt = _parse_tracker_datetime(filename)
    if dt:
        return _ymd_to_dmy(dt)
    m = _MAP_DMY_ONLY.match(filename)
    if m:
        return m.group(2)
    # Cola YMD tipo map_2026_07_25_06_47_43.json
    m2 = _NAME_YMD_TAIL.match(filename)
    if m2:
        y, mo, d, h, mi, s = m2.group(2), m2.group(3), m2.group(4), m2.group(5), m2.group(6), m2.group(7)
        return _ymd_to_dmy('%s_%s_%s_%s_%s_%s' % (y, mo, d, h, mi, s))
    raise ValueError('no se pudo leer fecha en %s' % filename)


def _conflict_suffix_from_filename(filename):
    """Devuelve '_2' / '_3' si el nombre tiene sufijo de conflicto antes de la ext."""
    stem, _ext = os.path.splitext(filename)
    m = re.search(r'_(\d+)$', stem)
    if not m:
        return ''
    # No confundir layer final de tracker_..._128
    if _TRACKER_FULL.match(filename) or _TRACKER_DMY_OK.match(filename):
        return ''
    m_map = _MAP_DMY_ONLY.match(filename)
    if m_map and m_map.group(3):
        return m_map.group(3)
    m_ymd = _NAME_YMD_TAIL.match(filename)
    if m_ymd and m_ymd.group(8):
        return m_ymd.group(8)
    return ''


def _ymd_to_dmy(dt):
    """
    Convierte fecha de nombre a dia_mes_ano_hora_min_seg.
    Acepta YMD (origen tracker/auto) o DMY (ya convertido).
    """
    if not dt:
        raise ValueError('fecha vacia')
    m = _YMD_DT.match(dt)
    if m:
        y, mo, d, h, mi, s = m.groups()
        year = int(y)
        if year < 2000 or year > 2100:
            raise ValueError('ano invalido en fecha: %s' % dt)
        return '%s_%s_%s_%s_%s_%s' % (d, mo, y, h, mi, s)
    if _DMY_DT.match(dt):
        return dt
    raise ValueError('formato de fecha no reconocido: %s' % dt)


def _map_from_tracker_filename(filename):
    """Fallback: mapa desde tracker_DT_map_gpm_*_layer.ext."""
    m = _TRACKER_FULL.match(filename)
    if not m:
        return None
    return m.group(2)


def _build_target_name(source_name, map_name):
    """auto_YYYY_MM_DD_HH_MM_SS.ext -> map_DD_MM_YYYY_HH_MM_SS.ext"""
    if not source_name.lower().startswith('auto'):
        raise ValueError('el archivo no empieza con auto')
    m = _AUTO_YMD.match(source_name)
    if m:
        dmy = _ymd_to_dmy(m.group(1))
        return '%s_%s%s' % (map_name, dmy, m.group(2))
    # Fallback raro: conservar cola pero intentar convertir YMD embebido
    rest = source_name[4:]
    return '%s%s' % (map_name, rest)


def _build_tracker_target_name(source_name, map_name, map_mode=None, map_layer=None):
    """
    Nombre compatible con el listado PHP del tracker:
    tracker_DD_MM_YYYY_HH_MM_SS_map_gpm_mode_layer.ext
    """
    dmy = _extract_dmy_from_filename(source_name)
    if not map_mode or map_layer is None or str(map_layer) == '':
        # Intentar completar desde el nombre largo original
        m = _TRACKER_FULL.match(source_name)
        if m:
            if not map_mode:
                map_mode = m.group(3)
            if map_layer is None or str(map_layer) == '':
                map_layer = m.group(4)
    if not map_mode or map_layer is None or str(map_layer) == '':
        raise ValueError('faltan MapMode/MapLayer para %s' % source_name)
    mode = str(map_mode).strip()
    if not mode.lower().startswith('gpm_'):
        mode = 'gpm_' + mode
    layer = str(map_layer).strip()
    conflict = _conflict_suffix_from_filename(source_name)
    _stem, suffix = os.path.splitext(source_name)
    return 'tracker_%s_%s_%s_%s%s%s' % (dmy, map_name, mode, layer, conflict, suffix)


def _reformat_filename_ymd_to_dmy(filename):
    """
    Si el nombre termina en _YYYY_MM_DD_HH_MM_SS.ext (o ..._SS_2.ext),
    pasa a DMY. No toca nombres tracker_ largos (fecha no al final).
    """
    m = _NAME_YMD_TAIL.match(filename)
    if not m:
        return None
    prefix, y, mo, d, h, mi, s, conflict, ext = m.groups()
    year = int(y)
    if year < 2000 or year > 2100:
        return None
    mid = '%s_%s_%s_%s_%s_%s' % (d, mo, y, h, mi, s)
    if conflict:
        mid = mid + conflict
    return '%s%s%s' % (prefix, mid, ext)


def _unique_destination(directory, filename):
    """Si el destino existe, prueba _2, _3, ... antes de la extension."""
    candidate = os.path.join(directory, filename)
    if not os.path.exists(candidate):
        return candidate

    stem, suffix = os.path.splitext(filename)
    n = 2
    while n <= 10000:
        alt = os.path.join(directory, '%s_%s%s' % (stem, n, suffix))
        if not os.path.exists(alt):
            return alt
        n += 1
    raise RuntimeError('demasiados conflictos para %s' % filename)


def _pair_name_taken(json_dir, pr_dir, stem, json_ext, pr_ext):
    """True si ya existe el stem en json y/o prdemo destino."""
    if json_dir and os.path.exists(os.path.join(json_dir, stem + json_ext)):
        return True
    if pr_dir and os.path.exists(os.path.join(pr_dir, stem + pr_ext)):
        return True
    return False


def _unique_pair_stem(json_dir, pr_dir, stem, json_ext='.json', pr_ext='.PRdemo'):
    """
    Elige un stem libre en AMBAS carpetas (mismo nombre base para el par).
    Evita que un lado quede en _2 y el otro no -> huerfanos.
    """
    if not _pair_name_taken(json_dir, pr_dir, stem, json_ext, pr_ext):
        return stem
    n = 2
    while n <= 10000:
        alt = '%s_%s' % (stem, n)
        if not _pair_name_taken(json_dir, pr_dir, alt, json_ext, pr_ext):
            return alt
        n += 1
    raise RuntimeError('demasiados conflictos de par para %s' % stem)


def _ensure_dir(path, label):
    if os.path.isdir(path):
        return True
    try:
        os.makedirs(path)
        return True
    except Exception as exc:
        _log('%s: cannot create dir %s: %s' % (label, path, exc))
        return False


def moveTrackerPairs():
    """
    Mueve .json + .PRdemo del origen al destino conservando el MISMO stem.
    Primero los pares; despues sueltos (sin hermano).
    """
    if not _ensure_dir(DEST_2D, 'moveTrackerPairs'):
        return
    if not _ensure_dir(DEST_JSON, 'moveTrackerPairs'):
        return

    json_names = []
    pr_names = []
    if os.path.isdir(SOURCE_JSON):
        try:
            json_names = [n for n in os.listdir(SOURCE_JSON) if _has_ext(n, '.json') and n.lower() != 'unassigned.json']
        except Exception as exc:
            _log('moveTrackerPairs: json listdir failed: %s' % exc)
    if os.path.isdir(SOURCE_2D):
        try:
            pr_names = [n for n in os.listdir(SOURCE_2D) if _has_ext(n, '.prdemo')]
        except Exception as exc:
            _log('moveTrackerPairs: prdemo listdir failed: %s' % exc)

    pr_by_stem = {}
    for name in pr_names:
        stem, ext = os.path.splitext(name)
        pr_by_stem[stem] = (name, ext)

    moved_pairs = 0
    moved_json = 0
    moved_pr = 0
    used_pr = set()

    for jname in sorted(json_names):
        jstem, jext = os.path.splitext(jname)
        src_json = os.path.join(SOURCE_JSON, jname)
        if not os.path.isfile(src_json):
            continue
        sibling = pr_by_stem.get(jstem)
        try:
            if sibling:
                pr_name, pr_ext = sibling
                src_pr = os.path.join(SOURCE_2D, pr_name)
                final_stem = _unique_pair_stem(DEST_JSON, DEST_2D, jstem, jext, pr_ext)
                dest_json = os.path.join(DEST_JSON, final_stem + jext)
                dest_pr = os.path.join(DEST_2D, final_stem + pr_ext)
                shutil.move(src_json, dest_json)
                shutil.move(src_pr, dest_pr)
                used_pr.add(jstem)
                moved_pairs += 1
                if final_stem != jstem:
                    _log('moveTrackerPairs: pair conflict %s -> %s' % (jstem, final_stem))
            else:
                dest_json = _unique_destination(DEST_JSON, jname)
                shutil.move(src_json, dest_json)
                moved_json += 1
                if os.path.basename(dest_json) != jname:
                    _log('moveTrackerPairs: solo json conflict %s -> %s' % (
                        jname, os.path.basename(dest_json)))
        except Exception as exc:
            _log('moveTrackerPairs: FAIL json %s -> %s' % (jname, exc))

    for stem, (pr_name, pr_ext) in sorted(pr_by_stem.items()):
        if stem in used_pr:
            continue
        src_pr = os.path.join(SOURCE_2D, pr_name)
        if not os.path.isfile(src_pr):
            continue
        try:
            dest_pr = _unique_destination(DEST_2D, pr_name)
            shutil.move(src_pr, dest_pr)
            moved_pr += 1
            if os.path.basename(dest_pr) != pr_name:
                _log('moveTrackerPairs: solo prdemo conflict %s -> %s' % (
                    pr_name, os.path.basename(dest_pr)))
        except Exception as exc:
            _log('moveTrackerPairs: FAIL prdemo %s -> %s' % (pr_name, exc))

    _log('moveTrackerPairs: pairs=%s solo_json=%s solo_prdemo=%s' % (
        moved_pairs, moved_json, moved_pr))


def moveFiles2D():
    """Compat: mueve pares tracker (json+PRdemo) y sueltos 2D."""
    moveTrackerPairs()


def moveFilesJSON():
    """Compat: no-op si moveFiles2D/moveTrackerPairs ya movio los json."""
    # Los json sueltos restantes (por si se llamo solo) se mueven aqui.
    if not os.path.isdir(SOURCE_JSON):
        return
    if not _ensure_dir(DEST_JSON, 'moveFilesJSON'):
        return
    try:
        names = os.listdir(SOURCE_JSON)
    except Exception as exc:
        _log('moveFilesJSON: listdir failed: %s' % exc)
        return
    moved = 0
    for files in names:
        if not _has_ext(files, '.json'):
            continue
        src_path = os.path.join(SOURCE_JSON, files)
        try:
            if not os.path.isfile(src_path):
                continue
            dest_path = _unique_destination(DEST_JSON, files)
            shutil.move(src_path, dest_path)
            moved += 1
        except Exception as exc:
            _log('moveFilesJSON: %s -> %s' % (files, exc))
    if moved:
        _log('moveFilesJSON: moved leftover %s files' % moved)


def _iter_auto_demos(folder):
    """Lista .bf2demo cuyo nombre empieza con 'auto' (case-insensitive)."""
    files = []
    try:
        names = os.listdir(folder)
    except Exception:
        return files

    for name in sorted(names):
        path = os.path.join(folder, name)
        if not os.path.isfile(path):
            continue
        lower = name.lower()
        if lower.startswith('auto') and lower.endswith('.bf2demo'):
            files.append(path)
    return files


def _iter_tracker_json(folder):
    """Lista .json a normalizar (tracker viejo YMD o map_DMY sin modo)."""
    files = []
    try:
        names = os.listdir(folder)
    except Exception:
        return files

    for name in sorted(names):
        path = os.path.join(folder, name)
        if not os.path.isfile(path):
            continue
        lower = name.lower()
        if not lower.endswith('.json'):
            continue
        if lower == 'unassigned.json':
            continue
        if _TRACKER_DMY_OK.match(name):
            continue
        # tracker_ YMD / incompleto, o map_DMY corto
        if lower.startswith('tracker_') or _MAP_DMY_ONLY.match(name) or _NAME_YMD_TAIL.match(name):
            files.append(path)
    return files


def _find_sibling_prdemo(prdemo_folder, old_stem):
    """Busca old_stem.PRdemo / .prdemo en la carpeta de demos 2D."""
    if not prdemo_folder or not os.path.isdir(prdemo_folder):
        return None
    for ext in ('.PRdemo', '.prdemo', '.PRDEMO'):
        candidate = os.path.join(prdemo_folder, old_stem + ext)
        if os.path.isfile(candidate):
            return candidate
    try:
        for name in os.listdir(prdemo_folder):
            stem, suffix = os.path.splitext(name)
            if stem == old_stem and suffix.lower() == '.prdemo':
                path = os.path.join(prdemo_folder, name)
                if os.path.isfile(path):
                    return path
    except Exception:
        return None
    return None


def renameAutoBf2Demos(folder=None):
    """
    Renombra auto*.bf2demo usando el mapa de la cabecera.
    Por defecto procesa DEST_3D; tambien se puede pasar SOURCE_3D.
    Devuelve la cantidad de errores.
    """
    if folder is None:
        folder = DEST_3D
    folder = os.path.normpath(folder)

    if not os.path.isdir(folder):
        _log('renameAutoBf2Demos: missing folder %s' % folder)
        return 1

    demos = _iter_auto_demos(folder)
    if not demos:
        _log('renameAutoBf2Demos: no auto*.bf2demo in %s' % folder)
        return 0

    errors = 0
    renamed = 0
    for src in demos:
        try:
            if os.path.getsize(src) == 0:
                _log('renameAutoBf2Demos: skip empty %s' % os.path.basename(src))
                continue
            map_name = _extract_map_name(src)
            new_name = _build_target_name(os.path.basename(src), map_name)
            dest = _unique_destination(folder, new_name)
            os.rename(src, dest)
            renamed += 1
            _log('renameAutoBf2Demos: %s -> %s' % (os.path.basename(src), os.path.basename(dest)))
        except Exception as exc:
            errors += 1
            _log('renameAutoBf2Demos: FAIL %s -> %s' % (os.path.basename(src), exc))
    _log('renameAutoBf2Demos: renamed %s errors %s in %s' % (renamed, errors, folder))
    return errors


def renameTrackerFiles(json_folder=None, prdemo_folder=None):
    """
    Normaliza summaries a:
    tracker_DD_MM_YYYY_HH_MM_SS_map_gpm_mode_layer.(json|PRdemo)
    Asi el listado PHP recupera fecha, mapa y modo.
    """
    if json_folder is None:
        json_folder = DEST_JSON
    if prdemo_folder is None:
        prdemo_folder = DEST_2D
    json_folder = os.path.normpath(json_folder)
    prdemo_folder = os.path.normpath(prdemo_folder)

    if not os.path.isdir(json_folder):
        _log('renameTrackerFiles: missing json folder %s' % json_folder)
        return 1

    summaries = _iter_tracker_json(json_folder)
    if not summaries:
        _log('renameTrackerFiles: nothing to rename in %s' % json_folder)
        return _rename_orphan_prdemos(prdemo_folder, json_folder)

    errors = 0
    renamed = 0
    for src_json in summaries:
        old_json_name = os.path.basename(src_json)
        old_stem, old_json_ext = os.path.splitext(old_json_name)
        try:
            meta = _extract_round_meta_from_json(src_json)
            desired_name = _build_tracker_target_name(
                old_json_name, meta['map'], meta['mode'], meta['layer'])
            desired_stem, _ignored_ext = os.path.splitext(desired_name)

            sibling = _find_sibling_prdemo(prdemo_folder, old_stem)
            pr_ext = '.PRdemo'
            if sibling:
                _ps, pr_ext = os.path.splitext(os.path.basename(sibling))

            # Un solo stem para json + PRdemo (sin huerfanos por _2 distinto)
            final_stem = _unique_pair_stem(
                json_folder, prdemo_folder if sibling else None,
                desired_stem, old_json_ext, pr_ext)

            new_json_name = final_stem + old_json_ext
            if new_json_name != old_json_name:
                dest_json = os.path.join(json_folder, new_json_name)
                os.rename(src_json, dest_json)
                renamed += 1
                _log('renameTrackerFiles: %s -> %s' % (old_json_name, new_json_name))

            if sibling:
                old_pr = os.path.basename(sibling)
                new_pr_name = final_stem + pr_ext
                if new_pr_name != old_pr:
                    dest_pr = os.path.join(prdemo_folder, new_pr_name)
                    os.rename(sibling, dest_pr)
                    renamed += 1
                    _log('renameTrackerFiles: %s -> %s' % (old_pr, new_pr_name))
        except Exception as exc:
            errors += 1
            _log('renameTrackerFiles: FAIL %s -> %s' % (old_json_name, exc))

    orphan_errors = _rename_orphan_prdemos(prdemo_folder, json_folder)
    errors += orphan_errors
    _log('renameTrackerFiles: renamed %s errors %s (json=%s prdemo=%s)' % (
        renamed, errors, json_folder, prdemo_folder))
    return errors


def _find_json_for_short_prdemo(json_folder, prdemo_name):
    """Busca tracker_DMY_map_*.json para un PRdemo corto map_DMY.PRdemo."""
    if not json_folder or not os.path.isdir(json_folder):
        return None
    m = _MAP_DMY_ONLY.match(prdemo_name)
    if not m:
        return None
    map_guess = m.group(1)
    dmy = m.group(2)
    prefix = ('tracker_%s_%s_' % (dmy, map_guess)).lower()
    try:
        names = os.listdir(json_folder)
    except Exception:
        return None
    for name in names:
        low = name.lower()
        if low.startswith(prefix) and low.endswith('.json'):
            return os.path.join(json_folder, name)
    return None


def _rename_orphan_prdemos(prdemo_folder, json_folder=None):
    """Renombra PRdemo cortos/huerfanos emparejando JSON por fecha+mapa."""
    if not prdemo_folder or not os.path.isdir(prdemo_folder):
        return 0
    errors = 0
    try:
        names = os.listdir(prdemo_folder)
    except Exception as exc:
        _log('renameTrackerFiles: prdemo listdir failed: %s' % exc)
        return 1

    for name in sorted(names):
        if _TRACKER_DMY_OK.match(name):
            continue
        lower = name.lower()
        if not lower.endswith('.prdemo'):
            continue
        if not (lower.startswith('tracker_') or _MAP_DMY_ONLY.match(name) or _NAME_YMD_TAIL.match(name)):
            continue
        src = os.path.join(prdemo_folder, name)
        if not os.path.isfile(src):
            continue
        try:
            meta = None
            # 1) JSON hermano por fecha+mapa
            json_path = _find_json_for_short_prdemo(json_folder, name)
            if json_path:
                # Preferir el stem del JSON ya normalizado (mismo nombre base)
                jstem, _jext = os.path.splitext(os.path.basename(json_path))
                _os, old_ext = os.path.splitext(name)
                new_name = jstem + old_ext
                if new_name != name:
                    # Evitar chocar con otro PRdemo; si hace falta, mover JSON al mismo stem
                    final_stem = _unique_pair_stem(
                        json_folder, prdemo_folder, jstem, _jext, old_ext)
                    if final_stem != jstem:
                        new_json = os.path.join(json_folder, final_stem + _jext)
                        os.rename(json_path, new_json)
                        json_path = new_json
                        jstem = final_stem
                        new_name = final_stem + old_ext
                    dest = os.path.join(prdemo_folder, new_name)
                    os.rename(src, dest)
                    _log('renameTrackerFiles: orphan->jsonstem %s -> %s' % (
                        name, new_name))
                continue

            # 2) Patron tracker completo en el propio nombre
            m = _TRACKER_FULL.match(name)
            if not m:
                raise ValueError('sin JSON hermano ni patron tracker completo')
            map_name = m.group(2)
            mode = m.group(3)
            layer = m.group(4)
            if _INVALID_WIN_CHARS.search(map_name):
                raise ValueError('mapa invalido: %r' % map_name)
            new_name = _build_tracker_target_name(name, map_name, mode, layer)
            _ns, _ne = os.path.splitext(new_name)
            _os, old_ext = os.path.splitext(name)
            new_name = _ns + old_ext
            if new_name == name:
                continue
            dest = _unique_destination(prdemo_folder, new_name)
            os.rename(src, dest)
            _log('renameTrackerFiles: orphan %s -> %s' % (name, os.path.basename(dest)))
        except Exception as exc:
            errors += 1
            _log('renameTrackerFiles: FAIL orphan %s -> %s' % (name, exc))
    return errors


def reformatFilenamesToDmy(folder, extensions):
    """
    Pasa nombres ..._YYYY_MM_DD_HH_MM_SS.ext a ..._DD_MM_YYYY_HH_MM_SS.ext
    Solo en la carpeta dada (origen tipicamente; no migrar archivos historicos
    masivos en cada ronda).
    extensions: lista tipo ['.prdemo', '.json', '.bf2demo']
    """
    if not folder or not os.path.isdir(folder):
        _log('reformatFilenamesToDmy: missing folder %s' % folder)
        return 1
    folder = os.path.normpath(folder)
    exts = []
    for e in extensions or []:
        e = e.lower()
        if not e.startswith('.'):
            e = '.' + e
        exts.append(e)

    errors = 0
    renamed = 0
    try:
        names = os.listdir(folder)
    except Exception as exc:
        _log('reformatFilenamesToDmy: listdir failed: %s' % exc)
        return 1

    for name in sorted(names):
        lower = name.lower()
        if not any(lower.endswith(e) for e in exts):
            continue
        new_name = _reformat_filename_ymd_to_dmy(name)
        if not new_name or new_name == name:
            continue
        src = os.path.join(folder, name)
        if not os.path.isfile(src):
            continue
        try:
            dest = _unique_destination(folder, new_name)
            os.rename(src, dest)
            renamed += 1
            _log('reformatFilenamesToDmy: %s -> %s' % (name, os.path.basename(dest)))
        except Exception as exc:
            errors += 1
            _log('reformatFilenamesToDmy: FAIL %s -> %s' % (name, exc))
    _log('reformatFilenamesToDmy: renamed %s errors %s in %s' % (renamed, errors, folder))
    return errors


def onRoundFileJobs():
    """
    Orden de fin/inicio de ronda:
    1) renombrar auto* bf2demo y pares tracker json/PRdemo en origen
    2) convertir fechas YMD residuales de bf2demo en origen a DMY
    3) mover pares tracker (mismo stem) + bf2demo 3D
    4) renombrar auto* bf2demo en destino
    """
    _log('onRoundFileJobs: start')
    try:
        renameAutoBf2Demos(SOURCE_3D)
    except Exception as exc:
        _log('onRoundFileJobs: rename bf2demo source failed: %s' % exc)
    try:
        renameTrackerFiles(SOURCE_JSON, SOURCE_2D)
    except Exception as exc:
        _log('onRoundFileJobs: rename tracker source failed: %s' % exc)
    try:
        reformatFilenamesToDmy(SOURCE_3D, ['.bf2demo'])
    except Exception as exc:
        _log('onRoundFileJobs: reformat dmy source failed: %s' % exc)
    try:
        # Pares json+PRdemo con el mismo stem (no deja huerfanos por conflicto)
        moveTrackerPairs()
    except Exception as exc:
        _log('onRoundFileJobs: moveTrackerPairs failed: %s' % exc)
    try:
        # Por si quedo algun json suelto
        moveFilesJSON()
    except Exception as exc:
        _log('onRoundFileJobs: moveJSON leftover failed: %s' % exc)
    try:
        moveFiles3D()
    except Exception as exc:
        _log('onRoundFileJobs: move3D failed: %s' % exc)
    try:
        renameAutoBf2Demos(DEST_3D)
    except Exception as exc:
        _log('onRoundFileJobs: rename bf2demo dest failed: %s' % exc)
    _log('onRoundFileJobs: done')
