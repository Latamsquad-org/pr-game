# -*- coding: utf-8 -*-
import os
import sys
import json
import shutil
import tempfile
import importlib

sys.path.insert(0, r'C:\prbf2_1\mods\pr\python\game')
import latamfiles as lf
importlib.reload(lf)

td = tempfile.mkdtemp()
try:
    js = os.path.join(td, 'json')
    pr = os.path.join(td, 'pr')
    os.makedirs(js)
    os.makedirs(pr)

    # Conflicto solo en json: el par debe usar el mismo _2
    open(os.path.join(js, 'tracker_25_07_2026_04_50_53_yamalia_gpm_cq_128.json'), 'w').write('{}')
    stem = 'tracker_25_07_2026_04_50_53_yamalia_gpm_cq_128'
    got = lf._unique_pair_stem(js, pr, stem, '.json', '.PRdemo')
    assert got == stem + '_2', got

    # renameTrackerFiles mantiene stem igual
    open(os.path.join(js, 'tracker_2026_07_25_06_47_43_deagle5_gpm_gungame_16.json'), 'w').write(
        json.dumps({'MapName': 'deagle5', 'MapMode': 'gpm_gungame', 'MapLayer': 16})
    )
    open(os.path.join(pr, 'tracker_2026_07_25_06_47_43_deagle5_gpm_gungame_16.PRdemo'), 'wb').write(b'x')
    # forzar conflicto en destino deseado
    desired = 'tracker_25_07_2026_06_47_43_deagle5_gpm_gungame_16'
    open(os.path.join(js, desired + '.json'), 'w').write('{}')
    open(os.path.join(pr, desired + '.PRdemo'), 'wb').write(b'y')

    err = lf.renameTrackerFiles(js, pr)
    assert err == 0, err
    j_ok = desired + '_2.json'
    p_ok = desired + '_2.PRdemo'
    assert os.path.isfile(os.path.join(js, j_ok)), os.listdir(js)
    assert os.path.isfile(os.path.join(pr, p_ok)), os.listdir(pr)

    # moveTrackerPairs
    src_j = os.path.join(td, 'sj')
    src_p = os.path.join(td, 'sp')
    dst_j = os.path.join(td, 'dj')
    dst_p = os.path.join(td, 'dp')
    os.makedirs(src_j)
    os.makedirs(src_p)
    os.makedirs(dst_j)
    os.makedirs(dst_p)
    stem2 = 'tracker_01_01_2026_00_00_00_test_airfield_gpm_cq_64'
    open(os.path.join(src_j, stem2 + '.json'), 'w').write('{}')
    open(os.path.join(src_p, stem2 + '.PRdemo'), 'wb').write(b'z')
    open(os.path.join(dst_j, stem2 + '.json'), 'w').write('{}')  # conflicto solo json

    old_sj, old_sp = lf.SOURCE_JSON, lf.SOURCE_2D
    old_dj, old_dp = lf.DEST_JSON, lf.DEST_2D
    lf.SOURCE_JSON, lf.SOURCE_2D = src_j + os.sep, src_p + os.sep
    lf.DEST_JSON, lf.DEST_2D = dst_j + os.sep, dst_p + os.sep
    try:
        lf.moveTrackerPairs()
        assert os.path.isfile(os.path.join(dst_j, stem2 + '_2.json'))
        assert os.path.isfile(os.path.join(dst_p, stem2 + '_2.PRdemo'))
        assert not os.path.isfile(os.path.join(src_j, stem2 + '.json'))
        assert not os.path.isfile(os.path.join(src_p, stem2 + '.PRdemo'))
    finally:
        lf.SOURCE_JSON, lf.SOURCE_2D = old_sj, old_sp
        lf.DEST_JSON, lf.DEST_2D = old_dj, old_dp

    print('ALL PASS')
finally:
    shutil.rmtree(td, ignore_errors=True)
