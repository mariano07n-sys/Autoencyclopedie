"""
verify_images.py - Contrôle en vie des URLs d'images stockées (aucun quota Gemini).

    python verify_images.py            # check logos + photos
    python verify_images.py --logos
    python verify_images.py --photos
    python verify_images.py --clean    # met NULL les URLs mortes
"""

import argparse
import os
import sys
from typing import List

import requests
from dotenv import load_dotenv

load_dotenv(os.path.join(os.path.dirname(__file__), ".env"))

from database_postgres import get_connection  # noqa: E402

HEADERS = {
    "User-Agent": os.getenv(
        "WIKI_USER_AGENT",
        "AutoEncyclopedie/1.0 (encyclopedie automobile; https://autoencyclopedie.vercel.app)",
    )
}


def _alive(url: str) -> bool:
    try:
        res = requests.get(url, headers=HEADERS, timeout=20, stream=True, allow_redirects=True)
        code = res.status_code
        res.close()
        return code == 200
    except requests.RequestException:
        return False


def _rows(query: str) -> List[dict]:
    with get_connection() as conn:
        return [dict(r) for r in conn.execute(query).fetchall()]


def check(kind: str, clean: bool) -> int:
    if kind == "logos":
        rows = _rows("SELECT id, name, logo_url AS url FROM brands WHERE logo_url IS NOT NULL")
        table, column = "brands", "logo_url"
    else:
        rows = _rows(
            "SELECT m.id, b.name || ' ' || m.name AS name, m.thumbnail_url AS url "
            "FROM models m JOIN brands b ON b.id = m.brand_id WHERE m.thumbnail_url IS NOT NULL"
        )
        table, column = "models", "thumbnail_url"

    dead = []
    for i, row in enumerate(rows, 1):
        ok = _alive(row["url"])
        if not ok:
            dead.append(row)
            print(f"[{i}/{len(rows)}] ✗ {row['name']} -> {row['url'][:70]}", flush=True)
        if ok and clean:
            continue

    if clean and dead:
        with get_connection() as conn:
            for row in dead:
                conn.execute(
                    f"UPDATE {table} SET {column} = NULL WHERE id = %s", (row["id"],)
                )
            conn.commit()
        print(f"🧹 {len(dead)} URLs mortes remises à NULL.")
    print(f"✅ {kind}: {len(rows) - len(dead)}/{len(rows)} URLs vivantes.")
    return len(dead)


def main():
    parser = argparse.ArgumentParser(description="Contrôle en vie des URLs d'images")
    parser.add_argument("--logos", action="store_true")
    parser.add_argument("--photos", action="store_true")
    parser.add_argument("--clean", action="store_true", help="NULL les URLs mortes")
    args = parser.parse_args()

    run_logos = args.logos or not args.photos
    run_photos = args.photos or not args.logos
    if run_logos:
        check("logos", args.clean)
    if run_photos:
        check("photos", args.clean)


if __name__ == "__main__":
    sys.exit(main())
