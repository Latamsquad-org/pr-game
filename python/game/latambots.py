# -*- coding: utf-8 -*-
"""
latambots.py — Solo servidor 3 (prbf2_3).

Descarga el top N del ranking publico de LatamStats y regenera
mods/pr/ai/botnames.ai para que los bots usen esos nombres al iniciar.

Uso:
  py -3 latambots.py
  py -3 latambots.py --dry-run
"""

from __future__ import print_function

import argparse
import html as html_lib
import os
import re
import shutil
import sys
import tempfile
import time

try:
    # Python 3
    from urllib.error import HTTPError, URLError
    from urllib.request import Request, urlopen
except ImportError:
    # Python 2 (poco probable en este host, pero defensivo)
    from urllib2 import HTTPError, Request, URLError, urlopen  # type: ignore

# --- Rutas fijas del servidor 3 ---
SCRIPT_DIR = os.path.dirname(os.path.abspath(__file__))
# .../mods/pr/python/game -> .../mods/pr
PR_ROOT = os.path.abspath(os.path.join(SCRIPT_DIR, "..", ".."))
BOTNAMES_PATH = os.path.join(PR_ROOT, "ai", "botnames.ai")
BOTNAMES_BACKUP = os.path.join(PR_ROOT, "ai", "botnames.ai.bak_latambots")

RANKING_URL = "https://stats.latamsquad.org/ranking"
TOP_N = 50
BOT_TAG = "[L-BOT]"
# Límite práctico de nombre BF2/PR (sin contar el tag).
MAX_NAME_LEN = 23
USER_AGENT = "LatamBots/1.0 (+prbf2_3; stats.latamsquad.org)"
TIMEOUT_SEC = 45

# Extrae el texto visible del enlace de jugador en el ranking.
_PLAYER_NAME_RE = re.compile(
    r'<a\s+class="player-name"\s+href="[^"]*">\s*([^<]+?)\s*</a>',
    re.IGNORECASE,
)


def fetch_ranking_html(url):
    """Descarga el HTML del ranking. Lanza excepción si falla."""
    req = Request(url, headers={"User-Agent": USER_AGENT, "Accept": "text/html"})
    resp = urlopen(req, timeout=TIMEOUT_SEC)
    try:
        raw = resp.read()
    finally:
        try:
            resp.close()
        except Exception:
            pass
    # utf-8 con fallback
    try:
        return raw.decode("utf-8")
    except UnicodeDecodeError:
        return raw.decode("utf-8", "replace")


def parse_top_names(html_text, limit):
    """
    Parsea los nombres del top del ranking (orden de aparición = posición).
    Devuelve lista de strings únicos, hasta `limit`.
    """
    names = []
    seen = set()
    for match in _PLAYER_NAME_RE.finditer(html_text):
        raw = html_lib.unescape(match.group(1)).strip()
        name = sanitize_bot_name(raw)
        if not name:
            continue
        key = name.lower()
        if key in seen:
            continue
        seen.add(key)
        names.append(name)
        if len(names) >= limit:
            break
    return names


def sanitize_bot_name(name):
    """
    Limpia el nombre para botnames.ai sin romper la sintaxis.
    Conserva la mayoría de caracteres usados en PR (._-!$* etc.).
    """
    if not name:
        return ""
    # Sin saltos de línea ni comillas que rompan el .ai
    name = name.replace("\r", " ").replace("\n", " ").replace("\t", " ")
    name = name.replace('"', "").replace("'", "")
    # Colapsar espacios
    name = re.sub(r"\s+", " ", name).strip()
    # BF2 suele ir mal con espacios en bot names → guión bajo
    name = name.replace(" ", "_")
    if len(name) > MAX_NAME_LEN:
        name = name[:MAX_NAME_LEN].rstrip("._-")
    return name


def build_botnames_content(names):
    """Genera el contenido completo de botnames.ai."""
    stamp = time.strftime("%Y-%m-%d %H:%M:%S")
    lines = [
        "rem *** LATAMSTATS Top {n} Botnames ***".format(n=len(names)),
        "rem Generado por latambots.py - {stamp}".format(stamp=stamp),
        "rem Fuente: {url}".format(url=RANKING_URL),
        "rem Solo servidor 3 (prbf2_3). No editar a mano: se sobrescribe al iniciar.",
        "rem",
    ]
    for name in names:
        lines.append("aiSettings.addBotName {tag} {name}".format(tag=BOT_TAG, name=name))
    lines.append("")
    return "\n".join(lines)


def atomic_write(path, content):
    """Escribe el archivo de forma atómica (temp + replace)."""
    folder = os.path.dirname(path)
    fd, tmp = tempfile.mkstemp(prefix="botnames_", suffix=".ai", dir=folder)
    try:
        with os.fdopen(fd, "w", encoding="utf-8", newline="\n") as handle:
            handle.write(content)
        # En Windows os.replace es atómico si mismo volumen.
        os.replace(tmp, path)
    except Exception:
        try:
            os.unlink(tmp)
        except OSError:
            pass
        raise


def update_botnames(dry_run=False):
    """
    Flujo principal. Retorna código de salida:
      0 = OK (o dry-run OK)
      1 = error de red/parseo (no toca el archivo)
      2 = error al escribir
    """
    print("[latambots] Descargando ranking: {0}".format(RANKING_URL))
    try:
        html_text = fetch_ranking_html(RANKING_URL)
    except (HTTPError, URLError, OSError) as exc:
        print("[latambots] ERROR al descargar ranking: {0}".format(exc), file=sys.stderr)
        return 1

    names = parse_top_names(html_text, TOP_N)
    if len(names) < TOP_N:
        print(
            "[latambots] ERROR: solo se parsearon {got}/{need} nombres.".format(
                got=len(names), need=TOP_N
            ),
            file=sys.stderr,
        )
        return 1

    content = build_botnames_content(names)
    print("[latambots] Top {0} OK. Destino: {1}".format(len(names), BOTNAMES_PATH))
    print("[latambots] Ejemplos: {0}".format(", ".join(names[:5])))

    if dry_run:
        print("[latambots] dry-run: no se escribe el archivo.")
        print(content[:500])
        print("...")
        return 0

    try:
        if os.path.isfile(BOTNAMES_PATH):
            shutil.copy2(BOTNAMES_PATH, BOTNAMES_BACKUP)
            print("[latambots] Backup: {0}".format(BOTNAMES_BACKUP))
        atomic_write(BOTNAMES_PATH, content)
    except OSError as exc:
        print("[latambots] ERROR al escribir botnames.ai: {0}".format(exc), file=sys.stderr)
        return 2

    print("[latambots] botnames.ai actualizado.")
    return 0


def main(argv=None):
    parser = argparse.ArgumentParser(
        description="Actualiza botnames.ai con el top del ranking LatamStats (solo prbf2_3)."
    )
    parser.add_argument(
        "--dry-run",
        action="store_true",
        help="Descarga y parsea sin escribir botnames.ai",
    )
    args = parser.parse_args(argv)
    return update_botnames(dry_run=args.dry_run)


if __name__ == "__main__":
    sys.exit(main())
