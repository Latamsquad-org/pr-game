# -*- coding: utf-8 -*-
"""Download RealityBrasil BattleRecorder hugeflag_*.png into local tracker."""
from __future__ import print_function
import os
import sys

try:
    from urllib.request import urlopen
except ImportError:
    from urllib2 import urlopen

BASE = "https://files.realitybrasil.org/PRServer/BattleRecorder/style/flags/"
DEST = r"C:\nginx\html\pr\tracker\style\flags"

FLAGS = [
    "hugeflag_ch.png",
    "hugeflag_cf.png",
    "hugeflag_arg82.png",
    "hugeflag_arf.png",
    "hugeflag_chinsurgent.png",
    "hugeflag_chechen90.png",
    "hugeflag_fr.png",
    "hugeflag_fsa.png",
    "hugeflag_gb.png",
    "hugeflag_ger.png",
    "hugeflag_hamas.png",
    "hugeflag_idf.png",
    "hugeflag_mec.png",
    "hugeflag_meinsurgent.png",
    "hugeflag_nl.png",
    "hugeflag_ru.png",
    "hugeflag_ru90.png",
    "hugeflag_saf.png",
    "hugeflag_ww2rus.png",
    "hugeflag_taliban.png",
    "hugeflag_us.png",
    "hugeflag_vnnva.png",
    "hugeflag_pl.png",
    "hugeflag_ww2ger.png",
]


def main():
    if not os.path.isdir(DEST):
        os.makedirs(DEST)
    print("DEST exists:", os.path.isdir(DEST))
    print("Existing files:")
    for name in sorted(os.listdir(DEST)):
        path = os.path.join(DEST, name)
        print(" ", name, os.path.getsize(path))

    ok = 0
    fail = 0
    for name in FLAGS:
        url = BASE + name
        out = os.path.join(DEST, name)
        try:
            resp = urlopen(url, timeout=60)
            data = resp.read()
            if hasattr(resp, "close"):
                resp.close()
            if len(data) < 100:
                raise RuntimeError("too small: %d bytes" % len(data))
            with open(out, "wb") as f:
                f.write(data)
            print("OK", name, len(data))
            ok += 1
        except Exception as e:
            print("FAIL", name, e)
            fail += 1

    print("done ok=%d fail=%d" % (ok, fail))
    huges = [n for n in os.listdir(DEST) if n.startswith("hugeflag_")]
    print("hugeflag count:", len(huges))
    return 0 if fail == 0 else 1


if __name__ == "__main__":
    sys.exit(main())
