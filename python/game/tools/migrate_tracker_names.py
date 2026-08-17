# -*- coding: utf-8 -*-
import os
import sys
import re
import importlib

sys.path.insert(0, r'C:\prbf2_1\mods\pr\python\game')
import latamfiles as lf
importlib.reload(lf)

ROOT = r'C:\prbf2_db'
for sv in ['sv1', 'sv2', 'sv3', 'sv4']:
    e = lf.renameTrackerFiles(
        os.path.join(ROOT, sv, 'json'),
        os.path.join(ROOT, sv, 'demos2d'),
    )
    print(sv, 'err', e)

ok = re.compile(
    r'^tracker_\d{2}_\d{2}_\d{4}_\d{2}_\d{2}_\d{2}_.+_gpm_.+_\d+\.(json|PRdemo|prdemo)$',
    re.I,
)
short = re.compile(
    r'^.+_\d{2}_\d{2}_\d{4}_\d{2}_\d{2}_\d{2}\.(PRdemo|prdemo|json)$',
    re.I,
)
for sv in ['sv1', 'sv2', 'sv3', 'sv4']:
    for sub in ('json', 'demos2d'):
        names = os.listdir(os.path.join(ROOT, sv, sub))
        bad = [n for n in names if not ok.match(n) and n.lower() != 'unassigned.json']
        print(sv, sub, 'bad', len(bad), 'short_php', sum(1 for n in bad if short.match(n)))
        if bad[:3]:
            print(' ', bad[:3])

# sample latest ok names
d2 = os.path.join(ROOT, 'sv1', 'demos2d')
latest = sorted(
    [n for n in os.listdir(d2) if ok.match(n)],
    key=lambda n: os.path.getmtime(os.path.join(d2, n)),
    reverse=True,
)[:5]
print('latest', latest)
