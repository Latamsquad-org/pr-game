# -*- coding: utf-8 -*-
"""
Genera/actualiza latambots_scale_maps.json a partir de maplist.con (capas gpm_coop).

Uso (fuera del juego, en la PC del srv3):
  py -3 tools/build_latambots_scale_maps.py
  py -3 tools/build_latambots_scale_maps.py --merge

Las coordenadas quedan en null hasta que el servidor juegue el mapa (auto-detect + cache)
o hasta que las cargues a mano.
"""

from __future__ import print_function

import argparse
import json
import os
import re

SCRIPT_DIR = os.path.dirname(os.path.abspath(__file__))
GAME_DIR = os.path.dirname(SCRIPT_DIR)
MAPS_JSON = os.path.join(GAME_DIR, 'latambots_scale_maps.json')

# Raiz del mod PR en srv3 (subir dos niveles desde python/game).
PR_ROOT = os.path.abspath(os.path.join(GAME_DIR, '..', '..'))
MAPLIST_PATH = os.path.join(PR_ROOT, 'settings', 'maplist.con')

_APPEND_RE = re.compile(
    r'^\s*mapList\.append\s+(\S+)\s+gpm_coop\s+(\d+)\s*$',
    re.IGNORECASE,
)


def _empty_team_entry():
    return {
        '1': {'hold': None, 'release': None, 'source': 'pending'},
        '2': {'hold': None, 'release': None, 'source': 'pending'},
    }


def parse_coop_maplist(path):
    """Lee maplist.con y devuelve lista de (map_id, layer_int)."""
    if not os.path.isfile(path):
        raise IOError('No existe maplist: %s' % path)
    entries = []
    with open(path, 'r') as handle:
        for line in handle:
            match = _APPEND_RE.match(line)
            if not match:
                continue
            entries.append((match.group(1).lower(), int(match.group(2))))
    return entries


def load_json(path):
    if not os.path.isfile(path):
        return {'maps': {}}
    with open(path, 'r') as handle:
        data = json.load(handle)
    if 'maps' not in data:
        data['maps'] = {}
    return data


def build_template(entries, existing=None):
    """Fusiona entradas del maplist con JSON existente (no pisa coords manuales)."""
    existing = existing or {'maps': {}}
    maps = existing.get('maps', {})
    added = 0
    for map_id, layer in entries:
        layer_key = str(layer)
        if map_id not in maps:
            maps[map_id] = {}
        if layer_key not in maps[map_id]:
            maps[map_id][layer_key] = _empty_team_entry()
            added += 1
    existing['maps'] = maps
    existing['_comment'] = (
        'Overrides manuales por mapa/capa/equipo. null = auto-detect en ronda.'
    )
    return existing, added


def main():
    parser = argparse.ArgumentParser(description='Generar tabla coop para latambots_scale.')
    parser.add_argument(
        '--maplist',
        default=MAPLIST_PATH,
        help='Ruta a maplist.con (default: settings del mod PR srv3)',
    )
    parser.add_argument(
        '--output',
        default=MAPS_JSON,
        help='JSON de salida (default: latambots_scale_maps.json)',
    )
    args = parser.parse_args()

    entries = parse_coop_maplist(args.maplist)
    existing = load_json(args.output)
    data, added = build_template(entries, existing)

    with open(args.output, 'w') as handle:
        json.dump(data, handle, indent=2, sort_keys=True)
        handle.write('\n')

    print('[build_latambots_scale_maps] Capas coop en maplist: %d' % len(entries))
    print('[build_latambots_scale_maps] Entradas nuevas: %d' % added)
    print('[build_latambots_scale_maps] Escrito: %s' % args.output)


if __name__ == '__main__':
    main()
