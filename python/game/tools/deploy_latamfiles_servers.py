# -*- coding: utf-8 -*-
"""Deploy latamfiles.py from sv1 template to other PR installs with local paths."""
import os
import shutil

SRC = r'C:\prbf2_1\mods\pr\python\game\latamfiles.py'
text = open(SRC, 'rb').read().decode('utf-8')

targets = {
    2: {
        'install': 'prbf2_2',
        'sv': 'sv2',
        'dest': r'C:\prbf2_2\mods\pr\python\game\latamfiles.py',
    },
    3: {
        'install': 'prbf2_3',
        'sv': 'sv3',
        'dest': r'C:\prbf2_3\mods\pr\python\game\latamfiles.py',
    },
}

for num, cfg in sorted(targets.items()):
    dest = cfg['dest']
    if os.path.isfile(dest):
        bak = dest + '.bak_pre_pairfix'
        if not os.path.isfile(bak):
            shutil.copy2(dest, bak)
            print('backup', bak)

    out = text
    # Order matters: replace specific paths before generic tokens if needed.
    out = out.replace('C:/prbf2_1/', 'C:/%s/' % cfg['install'])
    out = out.replace('C:/prbf2_db/sv1/', 'C:/prbf2_db/%s/' % cfg['sv'])
    out = out.replace('(prbf2_1 / sv1)', '(prbf2_%d / %s)' % (num, cfg['sv']))

    open(dest, 'wb').write(out.encode('utf-8'))
    print('wrote', dest, 'bytes', os.path.getsize(dest))

print('done')
