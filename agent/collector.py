"""
collector.py - Agent IA de collecte de données automobiles via Google Gemini
"""

import json
import os
import time
from typing import Optional, Dict, Any, List
from datetime import datetime

import google.generativeai as genai
from tenacity import retry, stop_after_attempt, wait_exponential
from rich.console import Console
from rich.progress import Progress, SpinnerColumn, TextColumn

from database import (
    get_cached_result,
    cache_result,
    upsert_brand,
    upsert_model,
    insert_spec,
    get_brand_by_name,
    get_all_brands,
    get_database_stats,
)

console = Console()

# ──────────────────────────────────────────────
# CONFIGURATION GEMINI
# ──────────────────────────────────────────────

def configure_gemini(api_key: str):
    genai.configure(api_key=api_key)
    return genai.GenerativeModel(
        model_name="gemini-1.5-flash",
        generation_config={
            "temperature": 0.2,
            "top_p": 0.95,
            "max_output_tokens": 8192,
            "response_mime_type": "application/json",
        }
    )


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
- description (string): Description historique détaillée (300-500 mots) incluant l'histoire, les valeurs, les modèles phares
- is_active (boolean): Est-ce que la marque est encore active?

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
- description (string): Description complète du modèle (200-400 mots)
- anecdotes (string): Anecdotes, records, faits marquants, contexte historique (100-200 mots)
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
    def __init__(self, api_key: str):
        self.model = configure_gemini(api_key)
        console.print("[bold green]🤖 Agent IA Automobile initialisé avec Gemini Pro[/bold green]")

    @retry(stop=stop_after_attempt(3), wait=wait_exponential(multiplier=2, min=4, max=30))
    def _call_gemini(self, prompt: str) -> str:
        """Appelle l'API Gemini avec retry automatique."""
        cached = get_cached_result(prompt[:200])
        if cached:
            console.print("[dim]   ↩ Résultat depuis le cache[/dim]")
            return cached

        response = self.model.generate_content(prompt)
        result = response.text
        cache_result(prompt[:200], result)
        return result

    def _parse_json(self, raw: str, key: str) -> List[Dict]:
        """Parse le JSON retourné par Gemini."""
        try:
            # Nettoyer le JSON si nécessaire
            if "```json" in raw:
                raw = raw.split("```json")[1].split("```")[0].strip()
            elif "```" in raw:
                raw = raw.split("```")[1].split("```")[0].strip()

            data = json.loads(raw)
            if key in data:
                return data[key]
            if isinstance(data, list):
                return data
            return [data]
        except json.JSONDecodeError as e:
            console.print(f"[red]⚠ Erreur JSON : {e}[/red]")
            return []

    # ── COLLECTE DES MARQUES ──

    def collect_brands(self):
        """Collecte et stocke toutes les marques automobiles."""
        console.print("\n[bold blue]━━━ Phase 1 : Collecte des Marques ━━━[/bold blue]")
        
        raw = self._call_gemini(BRANDS_COLLECTION_PROMPT)
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

        raw = self._call_gemini(prompt)
        models = self._parse_json(raw, "models")

        added = 0
        for model_data in models:
            try:
                model_data["brand_id"] = brand["id"]
                upsert_model(model_data)
                added += 1
            except Exception as e:
                console.print(f"[red]    ⚠ Erreur modèle {model_data.get('name', '?')}: {e}[/red]")

        console.print(f"    [green]✓ {added} modèles enregistrés pour {brand_name}[/green]")
        time.sleep(1)  # Pause pour respecter les rate limits
        return added

    def collect_all_models(self, limit: Optional[int] = None):
        """Collecte les modèles pour toutes les marques en base."""
        console.print("\n[bold blue]━━━ Phase 2 : Collecte des Modèles ━━━[/bold blue]")
        brands = get_all_brands()
        if limit:
            brands = brands[:limit]

        total_models = 0
        for i, brand in enumerate(brands, 1):
            console.print(f"[{i}/{len(brands)}] ", end="")
            total_models += self.collect_models_for_brand(brand["name"])

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

        raw = self._call_gemini(prompt)
        specs = self._parse_json(raw, "specs")

        added = 0
        for spec_data in specs:
            try:
                spec_data["model_id"] = model_id
                insert_spec(spec_data)
                added += 1
            except Exception as e:
                console.print(f"[red]    ⚠ Erreur spec {spec_data.get('variant_name', '?')}: {e}[/red]")

        return added

    # ── RAPPORT DE PROGRESSION ──

    def print_stats(self):
        stats = get_database_stats()
        console.print("\n[bold yellow]━━━ 📊 Statistiques de la Base de Données ━━━[/bold yellow]")
        console.print(f"  🏭 Marques       : [cyan]{stats['brands']}[/cyan]")
        console.print(f"  🚗 Modèles       : [cyan]{stats['models']}[/cyan]")
        console.print(f"  ⚙  Fiches tech.  : [cyan]{stats['specs']}[/cyan]")
        console.print(f"  ✅ Tâches done   : [green]{stats['tasks_done']}[/green]")
        console.print(f"  ⏳ Tâches pend.  : [yellow]{stats['tasks_pending']}[/yellow]")
