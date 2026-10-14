"""
verify_images.py - Contrôle en vie des URLs d'images stockées (aucun quota Gemini).

    python verify_images.py            # check logos + photos
    python verify_images.py --logos
    python verify_images.py --photos
    python verify_images.py --clean    # met NULL les URLs mortes

Deux garde-fous issus d'un incident réel (37 URLs déclarées « mortes », c'était
en fait Commons qui nous throttlait) : un statut ambigu est « indéterminé »,
jamais mort, et `--clean` refuse d'opérer si une part anormale du lot meurt.
"""

import argparse
import os
import sys
import time
from typing import List, Optional

import requests
from dotenv import load_dotenv

load_dotenv(os.path.join(os.path.dirname(__file__), ".env"))

from database_postgres import get_connection  # noqa: E402
from images import acquire_lock, release_lock  # noqa: E402

HEADERS = {
    "User-Agent": os.getenv(
        "WIKI_USER_AGENT",
        "AutoEncyclopedie/1.0 (encyclopedie automobile; https://autoencyclopedie.vercel.app)",
    )
}
DELAY = float(os.getenv("WIKI_DELAY_SECONDS", "0.3"))
# Ces statuts disent « le serveur est occupé », pas « le fichier a disparu ».
AMBIGUOUS = (408, 403, 429, 500, 502, 503, 504)


def _alive(url: str) -> Optional[bool]:
    """True = vivant, False = absent (404/410), None = indéterminé."""
    try:
        res = requests.head(url, headers=HEADERS, timeout=20, allow_redirects=True)
        code = res.status_code
        if code == 200:
            return True
        if code in (404, 410):
            return False
        return None if code in AMBIGUOUS else False
    except requests.RequestException:
        return None
    finally:
        time.sleep(DELAY)


def _rows(query: str) -> List[dict]:
    with get_connection() as conn:
        return [dict(r) for r in conn.execute(query).fetchall()]


def check(kind: str, clean: bool, force: bool) -> int:
    if kind == "logos":
        rows = _rows("SELECT id, name, logo_url AS url FROM brands WHERE logo_url IS NOT NULL")
        table, column = "brands", "logo_url"
    else:
        rows = _rows(
            "SELECT m.id, b.name || ' ' || m.name AS name, m.thumbnail_url AS url "
            "FROM models m JOIN brands b ON b.id = m.brand_id WHERE m.thumbnail_url IS NOT NULL"
        )
        table, column = "models", "thumbnail_url"

    dead, unknown = [], []
    for i, row in enumerate(rows, 1):
        state = _alive(row["url"])
        if state is False:
            dead.append(row)
            print(f"[{i}/{len(rows)}] ✗ {row['name']} -> {row['url'][:70]}", flush=True)
        elif state is None:
            unknown.append(row)
            print(f"[{i}/{len(rows)}] ? {row['name']} (réponse ambiguë, non jugée)", flush=True)

    alive = len(rows) - len(dead) - len(unknown)
    print(f"ℹ {kind}: {alive} vivantes, {len(dead)} mortes, {len(unknown)} indéterminées "
          f"sur {len(rows)}.")

    if clean and dead:
        if len(dead) > len(rows) / 2 and not force:
            print("🛑 Plus de la moitié des URLs paraissent mortes : c'est un signal de "
                  "throttling, pas de disparition. `--clean` abandonné (--force pour passer).")
            return len(dead)
        with get_connection() as conn:
            for row in dead:
                conn.execute(f"UPDATE {table} SET {column} = NULL WHERE id = %s", (row["id"],))
            conn.commit()
        print(f"🧹 {len(dead)} URLs mortes remises à NULL.")
    return len(dead)


def main():
    parser = argparse.ArgumentParser(description="Contrôle en vie des URLs d'images")
    parser.add_argument("--logos", action="store_true")
    parser.add_argument("--photos", action="store_true")
    parser.add_argument("--clean", action="store_true", help="NULL les URLs mortes")
    parser.add_argument("--force", action="store_true",
                        help="Nettoyer même si la majorité des URLs semble morte")
    parser.add_argument("--no-lock", action="store_true",
                        help="Ne pas prendre le verrou Wikimedia (déconseillé)")
    args = parser.parse_args()

    run_logos = args.logos or not args.photos
    run_photos = args.photos or not args.logos

    if not args.no_lock:
        try:
            acquire_lock("verify_images.py")
        except RuntimeError as exc:
            print(f"❌ {exc}")
            return 1
    try:
        if run_logos:
            check("logos", args.clean, args.force)
        if run_photos:
            check("photos", args.clean, args.force)
    finally:
        if not args.no_lock:
            release_lock()
    return 0


if __name__ == "__main__":
    sys.exit(main())
