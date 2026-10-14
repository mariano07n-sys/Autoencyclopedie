"""
collect_images.py - Pilotage automatique des visuels Wikimedia (0 quota Gemini).

    python collect_images.py                      # logos puis photos, jusqu'à la panne de progrès
    python collect_images.py --photos             # photos uniquement
    python collect_images.py --max-minutes 90     # budget temps élargi
    python collect_images.py --batch 20           # 20 entités par salve
    python collect_images.py --report             # état des lieux, aucun appel réseau

Le script fait ce que les relances manuelles ne faisaient pas :
  - verrou Wikimedia (un seul client à la fois, sinon 429 et visuels perdus),
  - reprise sur ce qui manque (`only_missing`), donc relançable après un Ctrl+C,
  - auto-régulation du débit selon les saturations observées,
  - arrêt propre sur budget temps ou absence de progrès,
  - rapport final chiffré.
"""

import argparse
import os
import sys
import time
from typing import Dict

from dotenv import load_dotenv

load_dotenv(os.path.join(os.path.dirname(__file__), ".env"))

import images  # noqa: E402
from database import (  # noqa: E402
    get_all_brands,
    get_database_stats,
    get_models_for_media,
)

BASE_DELAY = float(os.getenv("WIKI_DELAY_SECONDS", "0.15"))


def _counts() -> Dict[str, int]:
    brands = get_all_brands()
    models = get_models_for_media()
    pending_models = get_models_for_media(only_missing=True)
    return {
        "brands": len(brands),
        "logos": sum(1 for b in brands if b.get("logo_url")),
        "models": len(models),
        "galleries": len(models) - len(pending_models),
        "pending_logos": sum(1 for b in brands if not b.get("logo_url")),
        "pending_models": len(pending_models),
    }


def _tune_speed(state: Dict[str, int], before: Dict[str, int]) -> None:
    """Commons nous dit son degré de saturation : on ralentit ou on réaccélère."""
    searches = state["searches"] - before["searches"]
    throttled = state["throttled"] - before["throttled"]
    rate = throttled / searches if searches else 0.0
    if rate > 0.10:
        images.DELAY = min(2.0, max(0.6, images.DELAY * 2))
        os.environ["WIKI_THROTTLE_WAIT"] = "60"
    elif rate == 0.0:
        images.DELAY = max(BASE_DELAY, images.DELAY * 0.75)
        os.environ["WIKI_THROTTLE_WAIT"] = os.getenv("WIKI_THROTTLE_WAIT_BASE", "20")
    print(f"   🛰  débit ajusté : {searches} requêtes, {throttled} saturation(s), "
          f"pause unitaire {images.DELAY:.2f}s")


def _run_phase(kind: str, batch: int, deadline: float, skip_done: bool) -> int:
    """Salves successives d'une phase. Renvoie le nombre de visuels ajoutés."""
    runner = images.enrich_logos if kind == "logos" else images.enrich_photos
    total = 0
    while time.time() < deadline:
        before = dict(images.STATS)
        count = runner(batch, skip_done=skip_done)
        total += count
        _tune_speed(images.STATS, before)
        if not skip_done:
            # Re-cherche intégrale : une seule salve, sinon on repasserait
            # indéfiniment sur les mêmes entités déjà pourvues.
            break
        if count == 0:
            print(f"⏹ {kind} : salve sans aucun nouveau visuel, phase close.")
            break
        if count < max(1, batch // 8):
            # La tête de file est sèche sur Commons : y retourner gaspille le quota.
            print(f"⏹ {kind} : {count}/{batch} seulement, la file d'attente est épuisée.")
            break
    else:
        print(f"⏰ Budget temps écoulé ({kind} reprendra à la prochaine exécution).")
    return total


def report() -> None:
    stats = get_database_stats()
    counts = _counts()
    print("\n── État des visuels ─────────────────────────────")
    print(f"   marques : {counts['logos']}/{counts['brands']} avec logo "
          f"({counts['pending_logos']} en attente)")
    print(f"   modèles : {counts['galleries']}/{counts['models']} avec galerie "
          f"({counts['pending_models']} en attente)")
    print(f"   fiches techniques : {stats.get('specs', '?')}")
    print("───────────────────────────────────────────────")


def main() -> int:
    parser = argparse.ArgumentParser(description="Collecte automatisée des visuels Wikimedia")
    parser.add_argument("--logos", action="store_true", help="Uniquement les logos")
    parser.add_argument("--photos", action="store_true", help="Uniquement les photos")
    parser.add_argument("--batch", type=int, default=40, help="Entités par salve (défaut 40)")
    parser.add_argument("--max-minutes", type=int, default=45, help="Budget temps (défaut 45)")
    parser.add_argument("--reprocess", action="store_true",
                        help="Re-chercher aussi ce qui est déjà pourvu (coûteux en requêtes)")
    parser.add_argument("--report", action="store_true", help="Rapport seul, sans requêtes")
    parser.add_argument("--force", action="store_true", help="Passer outre le verrou Wikimedia")
    args = parser.parse_args()

    if args.report:
        report()
        return 0

    run_logos = args.logos or not args.photos
    run_photos = args.photos or not args.logos

    if args.force:
        images.release_lock()
    try:
        images.acquire_lock("collect_images.py")
    except RuntimeError as exc:
        print(f"❌ {exc}")
        return 1

    deadline = time.time() + args.max_minutes * 60
    skip_done = not args.reprocess
    try:
        print(f"🔍 Visuels Wikimedia — budget {args.max_minutes} min, salves de {args.batch}.")
        report()
        added = {}
        if run_logos:
            print("\n══ LOGOS ══════════════════════════════════════")
            added["logos"] = _run_phase("logos", args.batch, deadline, skip_done)
        if run_photos and time.time() < deadline:
            print("\n══ PHOTOS ═════════════════════════════════════")
            added["photos"] = _run_phase("photos", args.batch, deadline, skip_done)
        elif run_photos:
            print("\n⏰ Budget déjà épuisé avant les photos (relance pour la suite).")
    except KeyboardInterrupt:
        print("\n✋ Interruption manuelle — la prochaine exécution reprendra les manquants.")
        return 130
    finally:
        images.release_lock()

    searches = images.STATS["searches"]
    print(f"\n📊 {sum(added.values())} visuels ajoutés "
          f"({', '.join(f'{k}: {v}' for k, v in added.items()) or 'aucun'}) "
          f"en {searches} requêtes, {images.STATS['throttled']} saturation(s), "
          f"{images.STATS['errors']} erreur(s).")
    report()
    return 0


if __name__ == "__main__":
    sys.exit(main())
