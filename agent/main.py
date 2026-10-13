"""
main.py - Point d'entrée principal de l'agent IA automobile
Usage:
    python main.py                        # Menu interactif
    python main.py --collect-brands       # Collecter toutes les marques
    python main.py --collect-models       # Collecter tous les modèles
    python main.py --collect-brand Toyota # Modèles d'une marque précise
    python main.py --collect-specs        # Fiches techniques (modèles iconiques d'abord)
    python main.py --collect-images       # Logos + photos via Wikimedia Commons (sans Gemini)
    python main.py --stats                # Afficher les statistiques
    python main.py --full-run             # Lancer la collecte complète
"""

import os
import sys
import argparse
from dotenv import load_dotenv
from rich.console import Console
from rich.panel import Panel
from rich.prompt import Prompt, Confirm

from database import initialize_database, get_database_stats
from collector import CarDataAgent

load_dotenv()
console = Console()


BANNER = """
[bold cyan]
╔══════════════════════════════════════════════════════════════╗
║        🚗  AGENT IA - ENCYCLOPÉDIE AUTOMOBILE  🚗            ║
║           Powered by Google Gemini Pro                       ║
╚══════════════════════════════════════════════════════════════╝
[/bold cyan]
"""


def get_api_key() -> str:
    """Récupère la clé API Gemini depuis l'environnement ou la demande à l'utilisateur."""
    api_key = os.getenv("GEMINI_API_KEY")
    if not api_key:
        console.print("[yellow]⚠ Variable GEMINI_API_KEY non trouvée dans .env[/yellow]")
        api_key = Prompt.ask("🔑 Entrez votre clé API Google Gemini")
        # Sauvegarder dans .env
        with open(".env", "a") as f:
            f.write(f"\nGEMINI_API_KEY={api_key}\n")
        console.print("[green]✅ Clé API sauvegardée dans .env[/green]")
    return api_key


def interactive_menu(agent: CarDataAgent):
    """Menu interactif pour piloter l'agent."""
    while True:
        console.print("\n[bold]━━━ Menu Principal ━━━[/bold]")
        console.print("  [cyan]1[/cyan] 📊 Afficher les statistiques")
        console.print("  [cyan]2[/cyan] 🏭 Collecter toutes les marques")
        console.print("  [cyan]3[/cyan] 🚗 Collecter tous les modèles")
        console.print("  [cyan]4[/cyan] 🔍 Collecter les modèles d'une marque")
        console.print("  [cyan]5[/cyan] ⚙  Collecter les specs d'un modèle")
        console.print("  [cyan]6[/cyan] 🚀 Lancer la collecte complète (TOUTES données)")
        console.print("  [cyan]0[/cyan] 🚪 Quitter")

        choice = Prompt.ask("\nVotre choix", choices=["0", "1", "2", "3", "4", "5", "6"])

        if choice == "1":
            agent.print_stats()

        elif choice == "2":
            if Confirm.ask("Collecter toutes les marques automobiles ?"):
                agent.collect_brands()

        elif choice == "3":
            limit_str = Prompt.ask("Limite de marques (laisser vide = toutes)", default="")
            limit = int(limit_str) if limit_str else None
            agent.collect_all_models(limit=limit)

        elif choice == "4":
            brand_name = Prompt.ask("Nom de la marque")
            agent.collect_models_for_brand(brand_name)

        elif choice == "5":
            from database import get_brand_by_name, get_models_by_brand
            brand_name = Prompt.ask("Nom de la marque")
            brand = get_brand_by_name(brand_name)
            if brand:
                models = get_models_by_brand(brand["id"])
                for m in models[:20]:
                    console.print(f"  [{m['id']}] {m['name']} {m['generation']} ({m['year_start']})")
                model_id = int(Prompt.ask("ID du modèle"))
                model = next((m for m in models if m["id"] == model_id), None)
                if model:
                    count = agent.collect_specs_for_model(
                        model_id=model["id"],
                        brand_name=brand_name,
                        model_name=model["name"],
                        generation=model.get("generation", "I"),
                        year_start=model.get("year_start"),
                        year_end=model.get("year_end")
                    )
                    console.print(f"[green]✅ {count} variantes enregistrées.[/green]")

        elif choice == "6":
            console.print("[yellow]⚠ La collecte complète peut prendre plusieurs heures.[/yellow]")
            if Confirm.ask("Confirmer le lancement complet ?"):
                console.print("\n[bold green]🚀 Démarrage de la collecte complète...[/bold green]")
                agent.collect_brands()
                agent.collect_all_models()
                agent.print_stats()

        elif choice == "0":
            console.print("[green]Au revoir ! 👋[/green]")
            break


def main():
    console.print(BANNER)

    # Initialiser la base de données
    initialize_database()

    parser = argparse.ArgumentParser(description="Agent IA Encyclopédie Automobile")
    parser.add_argument("--collect-brands", action="store_true", help="Collecter toutes les marques")
    parser.add_argument("--collect-models", action="store_true", help="Collecter tous les modèles")
    parser.add_argument("--collect-brand", type=str, metavar="BRAND", help="Modèles d'une marque précise")
    parser.add_argument("--collect-specs", action="store_true", help="Collecter les fiches techniques")
    parser.add_argument("--collect-images", action="store_true", help="Logos + photos (Wikimedia Commons)")
    parser.add_argument("--stats", action="store_true", help="Afficher les statistiques")
    parser.add_argument("--full-run", action="store_true", help="Collecte complète (marques + modèles)")
    parser.add_argument("--limit", type=int, default=None, help="Limiter le nombre d'entités à traiter")

    args = parser.parse_args()

    # Obtenir la clé API
    api_key = get_api_key()

    if args.collect_images:
        import images

        images.enrich_logos(args.limit)
        images.enrich_photos(args.limit)
        return

    agent = CarDataAgent(api_key=api_key)

    if args.stats:
        agent.print_stats()

    elif args.collect_brands:
        agent.collect_brands()

    elif args.collect_models:
        agent.collect_all_models(limit=args.limit)

    elif args.collect_specs:
        agent.collect_specs_batch(limit=args.limit)

    elif args.collect_brand:
        agent.collect_models_for_brand(args.collect_brand)

    elif args.full_run:
        console.print("[bold green]🚀 Collecte complète lancée...[/bold green]")
        agent.collect_brands()
        agent.collect_all_models(limit=args.limit)
        agent.collect_specs_batch(limit=args.limit)
        agent.print_stats()

    else:
        # Mode interactif
        interactive_menu(agent)


if __name__ == "__main__":
    main()
