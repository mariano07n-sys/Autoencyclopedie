"""
images.py - Enrichit les visuels depuis Wikimedia Commons (aucun quota Gemini consommé).

    python images.py                    # logos de marques + photos de modèles
    python images.py --logos            # logos uniquement
    python images.py --photos           # photos de modèles uniquement
    python images.py --limit 30         # limite le nombre d'entités traitées
"""

import argparse
import os
import re
import sys
import time
from typing import Dict, List, Optional, Tuple

import requests
from dotenv import load_dotenv

load_dotenv(os.path.join(os.path.dirname(__file__), ".env"))

from database import (  # noqa: E402
    get_all_brands,
    get_models_for_media,
    update_brand_logo,
    update_model_images,
)

COMMONS_API = "https://commons.wikimedia.org/w/api.php"
HEADERS = {
    "User-Agent": os.getenv(
        "WIKI_USER_AGENT",
        "AutoEncyclopedie/1.0 (encyclopedie automobile; https://autoencyclopedie.vercel.app)",
    )
}
DELAY = float(os.getenv("WIKI_DELAY_SECONDS", "0.15"))
LOGO_STOPWORDS = ("team", "racing", "f1", "flag", "wordmark", "sticker", "plate")
PHOTO_MIMES = {"image/jpeg", "image/png", "image/svg+xml", "image/webp"}


def _tokens(text: str, min_len: int = 3) -> List[str]:
    return [t for t in re.split(r"[^a-z0-9]+", (text or "").lower()) if len(t) >= min_len]


def _search_files(query: str, limit: int = 8) -> List[Dict]:
    """Recherche des fichiers sur Commons, triés par pertinence."""
    params = {
        "action": "query",
        "generator": "search",
        "gsrsearch": query,
        "gsrnamespace": 6,
        "gsrlimit": limit,
        "prop": "imageinfo",
        "iiprop": "url|mime|size",
        "iiurlwidth": 900,
        "maxlag": 5,
        "format": "json",
    }
    try:
        res = requests.get(COMMONS_API, params=params, headers=HEADERS, timeout=25)
        res.raise_for_status()
        pages = (res.json().get("query") or {}).get("pages") or {}
    except (requests.RequestException, ValueError) as exc:
        print(f"   ⚠ Commons indisponible ({exc})")
        return []

    out = []
    for page in sorted(pages.values(), key=lambda p: p.get("index", 99)):
        info = (page.get("imageinfo") or [{}])[0]
        url = info.get("thumburl") or info.get("url")
        if not url or info.get("mime") not in PHOTO_MIMES:
            continue
        out.append({"title": page.get("title", ""), "url": url, "mime": info.get("mime"),
                    "width": info.get("width") or 0})
    time.sleep(DELAY)
    return out


def _is_alive(url: str) -> bool:
    try:
        res = requests.head(url, headers=HEADERS, timeout=15, allow_redirects=True)
        return res.status_code == 200
    except requests.RequestException:
        return False


LOGO_HINTS = ("logo", "logotype", "crest", "badge", "emblem", "seal", "arms", "wordmark")
# Mots tolérés dans le nom d'un fichier de logo, en plus de ceux de la marque.
LOGO_FILE_WORDS = set(LOGO_HINTS) | {
    "logos", "logotypes", "badges", "emblems", "crests", "seals", "wordmarks",
    "brand", "brands", "identity", "flag", "flags", "icon", "icons", "symbol",
    "official", "current", "old", "new", "variant", "version", "type", "the",
    "file", "svg", "png", "jpg", "jpeg", "webp", "px", "thumb", "xx", "com",
    "de", "la", "le", "du", "das",
}
LOGO_REJECTS = ("map", "location", "distribution", "graph", "chart", "timeline", "liverie",
                "sticker", "diagram", "rebranding", "poster", "factory", "plant")


def _logo_score(title: str, mime: str, brand_tokens: set) -> int:
    """Score de propreté d'un fichier « logo » (<= 0 = rejeté)."""
    base = re.sub(r"\.[a-z0-9]+$", "", title.lower())
    words = [w for w in re.split(r"[^a-z0-9]+", base) if w and w != "file"]
    if "logo" not in words or not words or words[0] not in brand_tokens:
        return 0
    if any(stop in base for stop in LOGO_STOPWORDS + LOGO_REJECTS):
        return 0
    extra = [w for w in words if w not in brand_tokens and w != "logo"]
    mime_rank = {"image/svg+xml": 4, "image/png": 3, "image/jpeg": 1}.get(mime, 0)
    return mime_rank - 3 * len(extra)


def _page_lead(lang: str, query: str) -> Optional[Tuple[str, Optional[str], Optional[str]]]:
    """Article Wikipédia trouvé pour `query` : (titre, image originale, vignette)."""
    try:
        hit = requests.get(
            f"https://{lang}.wikipedia.org/w/api.php",
            params={
                "action": "query",
                "list": "search",
                "srsearch": query,
                "srlimit": 1,
                "format": "json",
                "maxlag": 5,
            },
            headers=HEADERS,
            timeout=25,
        ).json()
        titles = [s["title"] for s in (hit.get("query") or {}).get("search", [])]
        if not titles:
            return None
        title = titles[0]
        summary = requests.get(
            f"https://{lang}.wikipedia.org/api/rest_v1/page/summary/{requests.utils.quote(title)}",
            headers=HEADERS,
            timeout=25,
        ).json()
    except (requests.RequestException, ValueError):
        return None
    time.sleep(DELAY)
    original = (summary.get("originalimage") or {}).get("source")
    thumb = (summary.get("thumbnail") or {}).get("source")
    return title, original, thumb


def _article_logo_file(lang: str, title: str, brand_name: str) -> Optional[str]:
    """Le fichier « logo » joint à l'article (les logos fair-use ne passent pas par l'API summary)."""
    brand_tokens = set(_tokens(brand_name, 2))
    api = f"https://{lang}.wikipedia.org/w/api.php"
    try:
        listing = requests.get(api, params={
            "action": "query", "titles": title, "prop": "images",
            "imlimit": 40, "format": "json", "maxlag": 5,
        }, headers=HEADERS, timeout=25).json()
        names = [img["title"] for page in (listing.get("query") or {}).get("pages", {}).values()
                 for img in page.get("images", [])]
        names = [n for n in names if not n.lower().endswith((".gif", ".webm", ".ogg"))]
        if not names:
            return None
        time.sleep(DELAY)
        info = requests.get(api, params={
            "action": "query", "titles": "|".join(names[:40]), "prop": "imageinfo",
            "iiprop": "url|mime", "iiurlwidth": 900, "format": "json", "maxlag": 5,
        }, headers=HEADERS, timeout=25).json()
    except (requests.RequestException, ValueError, KeyError):
        return None
    time.sleep(DELAY)

    best_url, best_rank = None, 0
    for page in (info.get("query") or {}).get("pages", {}).values():
        fname = (page.get("title") or "").lower()
        file_info = (page.get("imageinfo") or [{}])[0]
        mime = file_info.get("mime")
        url = file_info.get("thumburl") or file_info.get("url")
        if not url or mime not in PHOTO_MIMES:
            continue
        if any(bad in fname for bad in LOGO_REJECTS):
            continue
        # Un fichier joint « photo » (JPG/PNG sans mention de logo) n'est pas une
        # identité visuelle : seule l'extension SVG se suffit à elle-même.
        if mime != "image/svg+xml" and not any(h in fname for h in LOGO_HINTS):
            continue
        if not (brand_tokens & set(_tokens(fname, 2))):
            continue
        # Le fichier doit être LE logo, pas une photo dont le nom mentionne « logo ».
        extras = [w for w in re.split(r"[^a-z0-9]+", fname)
                  if w and not w.isdigit() and w not in brand_tokens and w not in LOGO_FILE_WORDS]
        if len(extras) > 1:
            continue
        rank = {"image/svg+xml": 4, "image/png": 3}.get(mime, 0)
        rank += 2 if any(h in fname for h in LOGO_HINTS) else 0
        if rank > best_rank and _is_alive(url):
            best_url, best_rank = url, rank
    return best_url


def _article_lead_image(brand_name: str) -> Optional[str]:
    """Image d'accroche de l'article Wikipédia de la marque (souvent le logo officiel)."""
    brand_tokens = set(_tokens(brand_name, 2))
    for lang in ("en", "fr"):
        lead = _page_lead(lang, brand_name)
        if not lead:
            continue
        title, original, thumb = lead
        # L'article doit bien être celui de cette marque, pas un article dérivé.
        if brand_tokens and not brand_tokens <= set(_tokens(title, 2)):
            continue
        candidates = []
        for url in (original, thumb):
            if not url:
                continue
            path = url.split("?")[0].lower()
            if any(bad in path for bad in LOGO_REJECTS):
                continue
            # Un logo libre est un SVG (même réduit en vignette) ; un logo de marque
            # connue est un fichier « fair use » rangé sous /wikipedia/<lang>/.
            looks_like_logo = ".svg" in path or f"/wikipedia/{lang}/" in path
            if looks_like_logo and (brand_tokens & set(_tokens(path))):
                candidates.append(url)
        for url in candidates:
            if _is_alive(url):
                return url
        logo = _article_logo_file(lang, title, brand_name)
        if logo:
            return logo
    return None


def find_logo(brand_name: str) -> Optional[str]:
    """Retourne le logo le plus plausible pour cette marque, ou None."""
    brand_tokens = set(_tokens(brand_name))
    best_url, best_score = None, 0
    for item in _search_files(f"{brand_name} logo", limit=12):
        score = _logo_score(item["title"], item["mime"], brand_tokens)
        if score > best_score and _is_alive(item["url"]):
            best_url, best_score = item["url"], score
    if best_url:
        return best_url
    lead = _article_lead_image(brand_name)
    if lead and _is_alive(lead):
        return lead
    return None


PHOTO_REJECTS = LOGO_REJECTS + ("logo", "badge", "emblem", "crest", "sign",
                                "register", "table", "wikitable", "list", "document",
                                "scan", "brochure", "newspaper", "advertisement",
                                "poster", "sheet", "index", "data", "coverage", "detail",
                                "spec", "specs", "comparison", "standings", "program")
MIN_PHOTO_WIDTH = 500


def _primary_name(model_name: str) -> str:
    """'Abarth 500 / 595 / 695' -> 'Abarth 500' : une seule variante nommable."""
    base = re.split(r"[/()]", model_name or "")[0]
    base = re.sub(r"\s+(I|II|III|IV|V|VI|VII)$", "", base.strip())
    return re.sub(r"\s+", " ", base).strip()


def _photo_score(title: str, brand_head: str, name_tokens: List[str]) -> float:
    """0 = hors sujet ; sinon part des mots du modèle retrouvés dans le titre."""
    tokens = set(_tokens(title, 2))
    if brand_head and brand_head not in tokens:
        return 0.0
    if not name_tokens:
        return 0.0
    if name_tokens[0] not in tokens:
        return 0.0
    return sum(1 for t in name_tokens if t in tokens) / len(name_tokens)


def find_photos(brand_name: str, model_name: str, year: Optional[int]) -> Tuple[Optional[str], List[str]]:
    """Photos d'un modèle : le titre du fichier doit nommer ce modèle précis."""
    primary = _primary_name(model_name)
    brand_head = (_tokens(brand_name, 2) or [""])[0]
    name_tokens = [t for t in _tokens(primary, 2) if t != brand_head]
    queries = [
        f"{primary} {year or ''} filetype:bitmap".strip(),
        f"{brand_name} {primary} filetype:bitmap".strip(),
    ]

    for query in queries:
        scored = []
        for item in _search_files(query, limit=14):
            title = item["title"]
            if any(bad in title.lower() for bad in PHOTO_REJECTS):
                continue
            if item["mime"] == "image/svg+xml":
                continue
            if item.get("width", 0) and item["width"] < MIN_PHOTO_WIDTH:
                continue
            score = _photo_score(title, brand_head, name_tokens)
            if score > 0:
                scored.append((score, item["url"]))
        scored.sort(key=lambda pair: pair[0], reverse=True)
        candidates = [u for _, u in scored[:5]]
        if candidates:
            alive = [u for u in candidates if _is_alive(u)]
            if alive:
                return alive[0], alive

    for lang in ("en", "fr"):
        lead = _page_lead(lang, f"{brand_name} {primary} {year or ''}".strip())
        if not lead:
            continue
        title, original, thumb = lead
        title_tokens = set(_tokens(title, 2))
        if brand_head and brand_head not in title_tokens:
            continue
        if name_tokens and name_tokens[0] not in title_tokens:
            continue
        url = thumb or original
        if not url or not url.split("?")[0].lower().endswith((".jpg", ".jpeg", ".png", ".webp")):
            continue
        if any(bad in url.lower() for bad in PHOTO_REJECTS):
            continue
        if _is_alive(url):
            return url, [url]
    return None, []


def enrich_logos(limit: Optional[int] = None, skip_done: bool = True) -> int:
    brands = get_all_brands()
    if skip_done:
        pending = [b for b in brands if not b.get("logo_url")]
        print(f"↷ {len(brands) - len(pending)} marques déjà logoïsées, {len(pending)} à traiter.")
        brands = pending
    if limit:
        brands = brands[:limit]
    found = 0
    for i, brand in enumerate(brands, 1):
        print(f"[{i}/{len(brands)}] logo {brand['name']}", flush=True)
        url = find_logo(brand["name"])
        update_brand_logo(brand["id"], url)
        if url:
            found += 1
            print(f"   ✓ {url[:90]}")
        else:
            print("   ∅ aucun logo fiable (placeholder conservé)")
    print(f"✅ {found}/{len(brands)} logos trouvés.")
    return found


def enrich_photos(limit: Optional[int] = None) -> int:
    models = get_models_for_media()
    if limit:
        models = models[:limit]
    found = 0
    for i, model in enumerate(models, 1):
        label = f"{model['brand_name']} {model['name']}"
        print(f"[{i}/{len(models)}] photos {label}", flush=True)
        thumb, gallery = find_photos(model["brand_name"], model["name"], model.get("year_start"))
        update_model_images(model["id"], thumb, gallery)
        if thumb:
            found += 1
            print(f"   ✓ {thumb[:90]}")
        else:
            print("   ∅ aucune photo pertinente (placeholder conservé)")
    print(f"✅ {found}/{len(models)} visuels rattachés.")
    return found


def main():
    parser = argparse.ArgumentParser(description="Enrichissement des visuels (Wikimedia Commons)")
    parser.add_argument("--logos", action="store_true", help="Logos des marques")
    parser.add_argument("--photos", action="store_true", help="Photos des modèles")
    parser.add_argument("--limit", type=int, default=None, help="Nombre d'entités à traiter")
    parser.add_argument("--all", action="store_true",
                        help="Re-traiter aussi les marques déjà pourvues d'un logo")
    args = parser.parse_args()

    run_logos = args.logos or not args.photos
    run_photos = args.photos or not args.logos

    if run_logos:
        enrich_logos(args.limit, skip_done=not args.all)
    if run_photos:
        enrich_photos(args.limit)


if __name__ == "__main__":
    sys.exit(main())
