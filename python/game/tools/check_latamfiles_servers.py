# -*- coding: utf-8 -*-
import os
import re
import hashlib

def file_sha(path):
    h = hashlib.sha256()
    with open(path, 'rb') as f:
        for chunk in iter(lambda: f.read(65536), b''):
            h.update(chunk)
    return h.hexdigest()[:12]

for i in [1, 2, 3, 4]:
    p = r'C:\prbf2_%d\mods\pr\python\game\latamfiles.py' % i
    print('=== sv%d ===' % i)
    print(' path', p)
    print(' exists', os.path.isfile(p))
    if not os.path.isfile(p):
        continue
    print(' size', os.path.getsize(p))
    print(' sha', file_sha(p))
    text = open(p, 'r').read()
    src = re.findall(r"SOURCE_(?:2D|JSON|3D)\s*=\s*'([^']+)'", text)
    dst = re.findall(r"DEST_(?:2D|JSON|3D)\s*=\s*'([^']+)'", text)
    print(' moveTrackerPairs', 'moveTrackerPairs' in text)
    print(' _unique_pair_stem', '_unique_pair_stem' in text)
    print(' _ymd_to_dmy', '_ymd_to_dmy' in text)
    print(' renameTrackerFiles', 'renameTrackerFiles' in text)
    print(' SOURCE', src)
    print(' DEST', dst)
