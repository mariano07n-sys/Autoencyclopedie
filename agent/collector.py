"""
collector.py - Agent IA de collecte de données automobiles (Gemini ou NVIDIA)
"""

import json
import os
import time
from typing import Optional, Dict, Any, List
from datetime import datetime

import google.generativeai as genai
import requests
from tenacity import retry, stop_after_attempt, wait_exponential
from rich.console import Console
from rich.progress import Progress, SpinnerColumn, TextColumn

from database import (
    get_cached_result,
    cache_result,
    invalidate_cached_result,
    get_models_for_specs,
    get_brands_without_models,
    upsert_brand,
    upsert_model,
    insert_spec,
    get_brand_by_name,
    get_database_stats,
)

console = Console()


def _log_retry(state):
    """Rend les pannes intermittentes des fournisseurs lisibles dans les journaux de vague."""
    error = state.outcome.exception()
    console.print(f"[yellow]   ↺ Tentative {state.attempt_number} : {str(error)[:160]}[/yellow]")

SPEC_FIELDS = (
    "variant_name", "engine_type", "engine_displacement", "fuel_type", "power_hp",
    "power_kw", "torque_nm", "transmission", "drive_type", "cylinders",
    "acceleration_0_100", "top_speed", "fuel_consumption", "co2_emissions", "weight_kg",
    "length_mm", "width_mm", "height_mm", "wheelbase_mm", "trunk_volume",
    "range_km", "price_launch_eur",
)

# ──────────────────────────────────────────────
# FOURISSEURS DE LANGAGE (2 budgets de quota distincts)
# ──────────────────────────────────────────────

class GeminiProvider:
    label = "Gemini"

    def __init__(self, api_key: str):
        genai.configure(api_key=api_key)
        self.model = genai.GenerativeModel(
            model_name=os.getenv("GEMINI_MODEL", "gemini-flash-latest"),
            generation_config={
                "temperature": 0.2,
                "top_p": 0.95,
                "max_output_tokens": 65536,
                "response_mime_type": "application/json",
            }
        )

    def generate(self, prompt: str) -> str:
        return self.model.generate_content(prompt).text


class NvidiaProvider:
    """Endpoint compatible OpenAI de NVIDIA : quota indépendant de Gemini.

    Le service est capricieux (401 et timeouts intermittents) : les réponses
    vides ou les codes d'erreur remontent en exception pour déclencher le retry.
    """

    label = "NVIDIA"
    URL = "https://integrate.api.nvidia.com/v1/chat/completions"
    SYSTEM = "Tu réponds exclusivement par un objet JSON valide, sans markdown ni texte autour."

    def __init__(self, api_key: str):
        self.api_key = api_key
        self.model = os.getenv("NVIDIA_MODEL", "openai/gpt-oss-20b")

    def generate(self, prompt: str) -> str:
        response = requests.post(
            self.URL,
            headers={"Authorization": f"Bearer {self.api_key}", "Content-Type": "application/json"},
            json={
                "model": self.model,
                "messages": [
                    {"role": "system", "content": self.SYSTEM},
                    {"role": "user", "content": prompt},
                ],
                "temperature": 0.2,
                "top_p": 0.95,
                # 8000 suffisait pour les petites marques mais tronquait BMW/Mercedes,
                # ce qui rendait toute la réponse inexploitable.
                "max_tokens": int(os.getenv("NVIDIA_MAX_TOKENS", 20000)),
                # Sans cette option, gpt-oss consomme tout le budget en « reasoning »
                # et renvoie un contenu vide.
                "reasoning_effort": os.getenv("NVIDIA_REASONING_EFFORT", "low"),
            },
            timeout=240,
        )
        if response.status_code != 200:
            raise RuntimeError(f"NVIDIA {response.status_code} : {response.text[:150]}")
        body = response.json()
        choices = body.get("choices") or []
        content = (choices[0].get("message") or {}).get("content") if choices else None
        if not content:
            raise RuntimeError("Réponse NVIDIA vide")
        usage = body.get("usage") or {}
        if usage.get("completion_tokens"):
            console.print(f"[dim]   ⤳ {usage['completion_tokens']} tokens générés[/dim]")
        return content


def _extract_json(raw: str) -> Optional[Any]:
    """Extrait l'objet JSON d'une réponse, fenced ou encadrée de prose. None si illisible."""
    text = raw.strip()
    if "```json" in text:
        text = text.split("```json", 1)[1]
    if "```" in text:
        text = text.split("```", 1)[1]
    text = text.strip()

    candidates = [text]
    start, end = text.find("{"), text.rfind("}")
    if 0 <= start < end:
        candidates.append(text[start:end + 1])
    start, end = text.find("["), text.rfind("]")
    if 0 <= start < end:
        candidates.append(text[start:end + 1])

    for candidate in candidates:
        try:
            data = json.loads(candidate)
        except json.JSONDecodeError:
            continue
        if isinstance(data, (dict, list)):
            return data
    return None


def _is_empty_result(data: Any) -> bool:
    """{"models": []} : le modèle n'a rien proposé — ni à cacher, ni à tenir la marque pour traitée."""
    if isinstance(data, list):
        return not data
    if isinstance(data, dict):
        return bool(data) and all(
            isinstance(v, list) and not v for v in data.values()
        )
    return True


def build_provider(backend: str) -> Any:
    backend = (backend or os.getenv("AGENT_LLM_BACKEND", "gemini")).lower()
    if backend == "nvidia":
        api_key = os.getenv("NVIDIA_API_KEY")
        if not api_key:
            raise SystemExit("❌ NVIDIA_API_KEY absente de agent/.env (backend 'nvidia' demandé).")
        return NvidiaProvider(api_key)
    api_key = os.getenv("GEMINI_API_KEY")
    if not api_key:
        raise SystemExit("❌ GEMINI_API_KEY absente de agent/.env.")
    return GeminiProvider(api_key)


# ──────────────────────────────────────────────
# PROMPTS DE COLLECTE
# ──────────────────────────────────────────────

BRANDS_COLLECTION_PROMPT = """
Tu es un expert automobile avec une connaissance encyclopédique.

Fournis une liste EXHAUSTIVE de toutes les marques automobiles qui ont existé ou existent encore dans le monde entier.
Inclus les marques historiques, actuelles, de niche, de luxe, électriques, et celles de tous les pays.

Pour chaque marque, retourne un objet JSON avec les champs :
- name (string): Nom officiel de la marque
- country (string): Pays d'origine (en français)
- founded_year (integer): Année de fondation
- founder (string): Nom du ou des fondateurs
- headquarters (string): Siège social (ville, pays)
- description (string): Description historique en 2-3 phrases (60 à 100 mots) : histoire, valeurs, modèles phares
- is_active (boolean): Est-ce que la marque est encore active?

Cible : au moins 250 marques distinctes, sans doublon ni variante de nom (ex: "BMW" une seule fois).
Retourne un JSON avec la clé "brands" contenant un tableau de toutes ces marques.
Inclus TOUTES les marques que tu connais, même les plus obscures.
"""

MODELS_COLLECTION_PROMPT = """
Tu es un expert automobile encyclopédique. Pour la marque "{brand_name}" (fondée en {founded_year}, {country}),
fournis une liste EXHAUSTIVE de tous les modèles qu'elle a produits depuis sa création.

Pour chaque modèle, retourne un objet JSON avec :
- name (string): Nom du modèle
- generation (string): Génération (ex: "I", "II", "III", ou "Mk1", "E30", etc.)
- year_start (integer): Année de début de production
- year_end (integer ou null): Année de fin de production (null si toujours en production)
- body_styles (array): Types de carrosseries ["Berline", "Cabriolet", "Coupé", "Break", "SUV", "Monospace", "Pick-up", "Roadster", "Spider"]
- segment (string): Segment de marché ("A", "B", "C", "D", "E", "F", "Sport", "Supercar", "Hypercar", "SUV compact", "SUV medium", "SUV large", "Utilitaire", "Commercial")
- description (string): Description du modèle en 3-4 phrases (60-100 mots)
- anecdotes (string): Anecdotes, records, faits marquants (30-60 mots)
- thumbnail_url (string): URL d'une image représentative (Wikipedia ou source fiable)
- countries (array): Principaux pays de commercialisation
- is_iconic (boolean): Modèle iconique ou emblématique?

Retourne un JSON avec la clé "models" contenant un tableau de tous ces modèles.
"""

SPECS_COLLECTION_PROMPT = """
Tu es un expert en fiches techniques automobiles.
Pour le modèle "{model_name}" {generation} de la marque "{brand_name}" ({year_start}-{year_end}),
fournis une fiche technique complète pour CHAQUE variante moteur disponible.

Pour chaque variante, retourne un objet JSON avec :
- variant_name (string): Nom de la variante (ex: "2.0 TDI 150 ch", "GTI 2.0 TSI", "e-208 EV50")
- engine_type (string): Type de moteur ("Thermique", "Électrique", "Hybride", "Hybride rechargeable", "Hydrogène")
- engine_displacement (float): Cylindrée en litres (null si électrique)
- fuel_type (string): Carburant ("Essence", "Diesel", "Électrique", "GPL", "Hydrogène", "Hybride Essence", "Hybride Diesel")
- power_hp (integer): Puissance en chevaux
- power_kw (integer): Puissance en kW
- torque_nm (integer): Couple en Nm
- transmission (string): Type de boîte ("Manuelle", "Automatique", "CVT", "Robotisée à double embrayage")
- drive_type (string): Type de traction ("Traction avant", "Propulsion", "4x4 intégral", "4x4 à la demande")
- cylinders (integer): Nombre de cylindres (null si électrique)
- acceleration_0_100 (float): 0-100 km/h en secondes
- top_speed (integer): Vitesse maximale en km/h
- fuel_consumption (float): Consommation mixte en L/100km (ou kWh/100km si électrique)
- co2_emissions (integer): Émissions CO2 en g/km (0 si électrique)
- weight_kg (integer): Poids à vide en kg
- length_mm (integer): Longueur en mm
- width_mm (integer): Largeur en mm
- height_mm (integer): Hauteur en mm
- wheelbase_mm (integer): Empattement en mm
- trunk_volume (integer): Volume du coffre en litres
- range_km (integer ou null): Autonomie en km (pour électrique/hybride)
- price_launch_eur (float): Prix de lancement indicatif en EUR (null si inconnu)

Retourne un JSON avec la clé "specs" contenant un tableau de toutes les variantes.
"""


# ──────────────────────────────────────────────
# AGENT DE COLLECTE
# ──────────────────────────────────────────────

class CarDataAgent:
    def __init__(self, backend: Optional[str] = None):
        self.provider = build_provider(backend)
        console.print(f"[bold green]🤖 Agent IA Automobile initialisé avec {self.provider.label}[/bold green]")

    @retry(stop=stop_after_attempt(5), wait=wait_exponential(multiplier=3, min=6, max=45),
           before_sleep=_log_retry)
    def _call_llm(self, prompt: str) -> str:
        """Appelle le fournisseur avec retry automatique (quota, 401 et timeouts intermittents)."""
        key = prompt[:200]
        cached = get_cached_result(key)
        if cached:
            data = _extract_json(cached)
            if data is not None and not _is_empty_result(data):
                console.print("[dim]   ↩ Résultat depuis le cache[/dim]")
                return cached
            # Réponse coupée ou vide mémorisée par une vague précédente.
            console.print("[yellow]   ⚠ Cache inexploitable, ré-interrogé[/yellow]")
            invalidate_cached_result(key)

        result = self.provider.generate(prompt)
        data = _extract_json(result)
        # Une prose, un objet tronqué ou une liste vide ne doivent pas immobiliser le
        # cache : ils resserviraient à chaque vague et bloqueraient la marque.
        if data is None or _is_empty_result(data):
            raise RuntimeError(f"Réponse inexploitable : {result[:120]}")
        cache_result(key, result, source=self.provider.label.lower())
        return result

    def _parse_json(self, raw: str, key: str) -> List[Dict]:
        """Parse le JSON retourné par le modèle."""
        data = _extract_json(raw)
        if data is None:
            console.print("[red]⚠ Erreur JSON : réponse du modèle illisible[/red]")
            return []
        if isinstance(data, list):
            return data
        if key in data:
            return data[key]
        return [data]

    # ── COLLECTE DES MARQUES ──

    def collect_brands(self):
        """Collecte et stocke toutes les marques automobiles."""
        console.print("\n[bold blue]━━━ Phase 1 : Collecte des Marques ━━━[/bold blue]")
        
        raw = self._call_llm(BRANDS_COLLECTION_PROMPT)
        brands = self._parse_json(raw, "brands")

        if not brands:
            console.print("[red]❌ Aucune marque collectée.[/red]")
            return 0

        added = 0
        with Progress(SpinnerColumn(), TextColumn("[progress.description]{task.description}")) as progress:
            task = progress.add_task(f"Enregistrement de {len(brands)} marques...", total=len(brands))
            for brand in brands:
                try:
                    upsert_brand(brand)
                    added += 1
                    progress.advance(task)
                except Exception as e:
                    console.print(f"[red]  ⚠ Erreur pour {brand.get('name', '?')}: {e}[/red]")

        console.print(f"[green]✅ {added} marques enregistrées.[/green]")
        return added

    # ── COLLECTE DES MODÈLES ──

    def collect_models_for_brand(self, brand_name: str) -> int:
        """Collecte tous les modèles d'une marque donnée."""
        brand = get_brand_by_name(brand_name)
        if not brand:
            console.print(f"[red]❌ Marque '{brand_name}' non trouvée en base.[/red]")
            return 0

        console.print(f"  🔍 Collecte des modèles : [cyan]{brand_name}[/cyan]")

        prompt = MODELS_COLLECTION_PROMPT.format(
            brand_name=brand["name"],
            founded_year=brand.get("founded_year", "?"),
            country=brand.get("country", "?")
        )

        raw = self._call_llm(prompt)
        models = self._parse_json(raw, "models")

        added = 0
        for model_data in models:
            try:
                year = model_data.get("year_start")
                # gpt-oss a daté des Autobianchi A112 en 2028/2032 : rien de futuriste
                # n'est jamais rentré dans l'encyclopédie.
                if isinstance(year, int) and year > datetime.now().year + 1:
                    console.print(
                        f"[yellow]    ⚠ Année aberrante ({year}) ignorée : {model_data.get('name')}[/yellow]"
                    )
                    continue
                model_data["brand_id"] = brand["id"]
                upsert_model(model_data)
                added += 1
            except Exception as e:
                console.print(f"[red]    ⚠ Erreur modèle {model_data.get('name', '?')}: {e}[/red]")

        console.print(f"    [green]✓ {added} modèles enregistrés pour {brand_name}[/green]")
        time.sleep(1)  # Pause pour respecter les rate limits
        return added

    def collect_all_models(self, limit: Optional[int] = None):
        """Collecte les modèles des marques encore vierges (les vagues suivantes reprennent ailleurs)."""
        console.print("\n[bold blue]━━━ Phase 2 : Collecte des Modèles ━━━[/bold blue]")
        brands = get_brands_without_models(limit=limit)
        if not brands:
            console.print("[green]✅ Chaque marque a déjà ses modèles.[/green]")
            return

        total_models = 0
        for i, brand in enumerate(brands, 1):
            console.print(f"[{i}/{len(brands)}] ", end="")
            try:
                total_models += self.collect_models_for_brand(brand["name"])
            except Exception as exc:
                # Marque non cacheable (quota, 401, JSON invalide) : on passe à la suivante.
                console.print(f"[red] ⛔ {brand['name']} : {str(exc)[:150]}[/red]")

        console.print(f"\n[green]✅ Total : {total_models} modèles collectés.[/green]")

    # ── COLLECTE DES SPECS ──

    def collect_specs_for_model(self, model_id: int, brand_name: str,
                                 model_name: str, generation: str,
                                 year_start: Optional[int], year_end: Optional[int]) -> int:
        """Collecte les fiches techniques d'un modèle."""
        prompt = SPECS_COLLECTION_PROMPT.format(
            model_name=model_name,
            generation=generation,
            brand_name=brand_name,
            year_start=year_start or "?",
            year_end=year_end or "présent"
        )

        raw = self._call_llm(prompt)
        specs = self._parse_json(raw, "specs")

        added = 0
        for spec_data in specs:
            try:
                spec = {field: spec_data.get(field) for field in SPEC_FIELDS}
                # Une variante sans aucune donnée utile ferait croire que le modèle
                # est déjà traité et bloquerait sa recompilation.
                if not any(v is not None for k, v in spec.items() if k != "variant_name"):
                    console.print(f"[yellow]    ⚠ Variante vide ignorée ({spec_data.get('variant_name', '?')})[/yellow]")
                    continue
                spec["model_id"] = model_id
                insert_spec(spec)
                added += 1
            except Exception as e:
                console.print(f"[red]    ⚠ Erreur spec {spec_data.get('variant_name', '?')}: {e}[/red]")

        return added

    def collect_specs_batch(self, limit: Optional[int] = None) -> int:
        """Fiches techniques des modèles restants, iconiques d'abord.

        S'arrête proprement quand le quota Gemini est atteint : les modèles déjà
        traités étant ignorés, la commande peut être relancée chaque jour.
        """
        console.print("\n[bold blue]━━━ Phase 3 : Fiches techniques ━━━[/bold blue]")
        targets = get_models_for_specs(limit=limit)
        if not targets:
            console.print("[green]✅ Chaque modèle a déjà sa fiche technique.[/green]")
            return 0

        total = 0
        done = 0
        for i, model in enumerate(targets, 1):
            console.print(
                f"[{i}/{len(targets)}] ⚙ {model['brand_name']} {model['name']} {model.get('generation') or ''}"
            )
            try:
                total += self.collect_specs_for_model(
                    model_id=model["id"],
                    brand_name=model["brand_name"],
                    model_name=model["name"],
                    generation=model.get("generation") or "I",
                    year_start=model.get("year_start"),
                    year_end=model.get("year_end"),
                )
                done += 1
            except Exception as exc:
                console.print(f"[red]⛔ Arrêt de la collecte : {str(exc)[:200]}[/red]")
                console.print("[yellow]Relancez plus tard : les modèles déjà traités sont sautés.[/yellow]")
                break

        console.print(f"[green]✅ {total} variantes enregistrées ({done} modèles traités).[/green]")
        return total

    # ── RAPPORT DE PROGRESSION ──

    def print_stats(self):
        stats = get_database_stats()
        console.print("\n[bold yellow]━━━ 📊 Statistiques de la Base de Données ━━━[/bold yellow]")
        console.print(f"  🏭 Marques       : [cyan]{stats['brands']}[/cyan]")
        console.print(f"  🚗 Modèles       : [cyan]{stats['models']}[/cyan]")
        console.print(f"  ⚙  Fiches tech.  : [cyan]{stats['specs']}[/cyan]")
        console.print(f"  ✅ Tâches done   : [green]{stats['tasks_done']}[/green]")
        console.print(f"  ⏳ Tâches pend.  : [yellow]{stats['tasks_pending']}[/yellow]")
