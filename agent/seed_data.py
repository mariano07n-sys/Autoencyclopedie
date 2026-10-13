"""
seed_data.py - Initialise la base avec les grandes marques historiques
sans passer par Gemini (données statiques de départ)
Usage: python seed_data.py
"""
import sys
import os
sys.path.insert(0, os.path.dirname(__file__))

from database import initialize_database, upsert_brand, upsert_model, get_database_stats

# ─── MARQUES HISTORIQUES FONDATRICES ───
SEED_BRANDS = [
    {"name": "Benz & Cie", "country": "Allemagne", "founded_year": 1883, "founder": "Karl Benz", "headquarters": "Mannheim, Allemagne", "is_active": False,
     "description": "Fondée par Karl Benz en 1883, Benz & Cie est à l'origine de la première véritable automobile à moteur à explosion, la Benz Patent-Motorwagen de 1886. Cette invention révolutionnaire marque la naissance officielle de l'automobile moderne. Karl Benz déposa le brevet DRP-37435 le 29 janvier 1886, date considérée comme l'acte de naissance de l'automobile."},

    {"name": "Daimler Motoren Gesellschaft", "country": "Allemagne", "founded_year": 1890, "founder": "Gottlieb Daimler, Wilhelm Maybach", "headquarters": "Stuttgart, Allemagne", "is_active": False,
     "description": "Fondée par Gottlieb Daimler et Wilhelm Maybach, la DMG fut pionnière dans le développement des moteurs à grande vitesse. Elle produisit les premières voitures Mercedes en 1901, nommées d'après Mercedes Jellinek, fille d'Emil Jellinek. La fusion avec Benz & Cie en 1926 donna naissance à Mercedes-Benz."},

    {"name": "Mercedes-Benz", "country": "Allemagne", "founded_year": 1926, "founder": "Karl Benz, Gottlieb Daimler", "headquarters": "Stuttgart, Allemagne", "is_active": True,
     "description": "Née de la fusion entre Benz & Cie et Daimler Motoren Gesellschaft en 1926, Mercedes-Benz est l'une des marques automobiles les plus prestigieuses au monde. Héritière de l'invention de l'automobile par Karl Benz, la marque à l'étoile à trois branches est synonyme de luxe, d'innovation technologique et de performances. Elle a produit des modèles légendaires comme la 300 SL 'Ailes de mouette', la Classe S, et la marque AMG."},

    {"name": "Peugeot", "country": "France", "founded_year": 1889, "founder": "Armand Peugeot", "headquarters": "Rueil-Malmaison, France", "is_active": True,
     "description": "Armand Peugeot fonde la Société Anonyme des Automobiles Peugeot en 1889 après avoir collaboré avec Panhard et Levassor. La marque au lion est la plus ancienne marque automobile encore en activité. Elle a produit des modèles iconiques comme la 205 GTI, la 405 Mi16, et les séries 3, 5 et 6. Aujourd'hui intégrée au groupe Stellantis, Peugeot continue d'innover avec une gamme de véhicules électriques."},

    {"name": "Renault", "country": "France", "founded_year": 1899, "founder": "Louis Renault, Marcel Renault, Fernand Renault", "headquarters": "Boulogne-Billancourt, France", "is_active": True,
     "description": "Fondée par les frères Renault en 1899, la Régie Nationale des Usines Renault est un pilier de l'industrie automobile française. Nationalisée après la Seconde Guerre mondiale, elle a produit des modèles populaires comme la 4CV, la Dauphine, la R5, la Clio et la Mégane. Renault est pionnière en matière de véhicules électriques avec la Zoé et désormais la R5 E-Tech électrique."},

    {"name": "Citroën", "country": "France", "founded_year": 1919, "founder": "André Citroën", "headquarters": "Saint-Ouen, France", "is_active": True,
     "description": "André Citroën fonde sa société en 1919, adoptant les méthodes de production à la chaîne de Ford. La marque aux chevrons est connue pour son innovation technique radicale : suspension hydraulique (DS), traction avant (Traction Avant 1934), et les designs futuristes de la DS, SM et CX. Aujourd'hui membre du groupe Stellantis, Citroën mise sur le confort et les véhicules accessibles."},

    {"name": "Ford", "country": "États-Unis", "founded_year": 1903, "founder": "Henry Ford", "headquarters": "Dearborn, Michigan, États-Unis", "is_active": True,
     "description": "Henry Ford révolutionne l'industrie automobile en 1908 avec le modèle T et l'invention de la production à la chaîne en 1913. Ford Motor Company a rendu l'automobile accessible aux masses. Parmi ses modèles iconiques : la Mustang (1964), la GT40 vainqueur du Mans, le F-Series (camionnette la plus vendue au monde). Ford est aujourd'hui pionnier dans les véhicules électriques avec le Mustang Mach-E et le F-150 Lightning."},

    {"name": "General Motors", "country": "États-Unis", "founded_year": 1908, "founder": "William Durant", "headquarters": "Detroit, Michigan, États-Unis", "is_active": True,
     "description": "General Motors, fondé par William Durant en 1908, est pendant longtemps le plus grand constructeur automobile mondial. Le groupe chapeaute des marques emblématiques comme Chevrolet, Cadillac, Buick, GMC et Corvette. La Corvette (1953) et la Camaro sont des icônes de la culture américaine. GM est aujourd'hui en forte transition vers l'électrique avec son architecture Ultium."},

    {"name": "Rolls-Royce", "country": "Royaume-Uni", "founded_year": 1906, "founder": "Charles Rolls, Henry Royce", "headquarters": "Goodwood, Royaume-Uni", "is_active": True,
     "description": "Fondée en 1906 par l'honorable Charles Stewart Rolls et Frederick Henry Royce, Rolls-Royce est la définition même du luxe automobile absolu. La marque est connue pour la qualité artisanale irréprochable de ses véhicules, le silence légendaire de ses habitacles et des finitions à la main. Modèles emblématiques : Silver Ghost (1906), Phantom, Silver Shadow, Ghost, Wraith, et la Spectre entièrement électrique (2023)."},

    {"name": "Bentley", "country": "Royaume-Uni", "founded_year": 1919, "founder": "Walter Owen Bentley", "headquarters": "Crewe, Royaume-Uni", "is_active": True,
     "description": "W.O. Bentley fonde sa société en 1919 avec l'ambition de construire 'un bon moteur dans une bonne voiture'. Les Bentley Boys triomphèrent aux 24 Heures du Mans dans les années 1920. Propriété de Volkswagen Group depuis 1998, Bentley allie performance sportive et luxe raffiné. Modèles phares : Continental GT, Flying Spur, Bentayga, et la transition vers l'électrique avec la stratégie Beyond100+."},

    {"name": "Ferrari", "country": "Italie", "founded_year": 1939, "founder": "Enzo Ferrari", "headquarters": "Maranello, Italie", "is_active": True,
     "description": "Enzo Ferrari crée la Scuderia Ferrari en 1929 d'abord comme écurie de course pour Alfa Romeo, puis fonde Ferrari S.p.A. en 1939. La marque au cheval cabré de Maranello est synonyme de supercars exclusives, de course automobile et d'émotion italienne. Ferrari est l'une des marques les plus valorisées au monde. Modèles iconiques : 250 GTO, Testarossa, F40, F50, Enzo, LaFerrari, 296 GTB."},

    {"name": "Lamborghini", "country": "Italie", "founded_year": 1963, "founder": "Ferruccio Lamborghini", "headquarters": "Sant'Agata Bolognese, Italie", "is_active": True,
     "description": "Ferruccio Lamborghini, fabricant de tracteurs, fonde Automobili Lamborghini en 1963 pour concurrencer Ferrari après un désaccord avec Enzo Ferrari. La marque du taureau est connue pour ses supercars extravagantes et ses moteurs V10 et V12 atmosphériques. Propriété d'Audi (Volkswagen Group) depuis 1998. Modèles légendaires : Miura, Countach, Diablo, Murciélago, Aventador, Huracán, Urus."},

    {"name": "Porsche", "country": "Allemagne", "founded_year": 1931, "founder": "Ferdinand Porsche", "headquarters": "Stuttgart, Allemagne", "is_active": True,
     "description": "Ferdinand Porsche fonde son bureau d'études en 1931, concepteur notamment de la Volkswagen Beetle. La première voiture portant le nom Porsche, la 356, est construite en 1948. La 911, lancée en 1963 et toujours produite aujourd'hui, est le modèle le plus iconique de la marque. Porsche est aussi un vainqueur majeur au Mans et dans l'endurance mondiale. Modèles : 911, Boxster, Cayenne, Macan, Panamera, Taycan (électrique)."},

    {"name": "Volkswagen", "country": "Allemagne", "founded_year": 1937, "founder": "Ferdinand Porsche, Adolf Hitler", "headquarters": "Wolfsburg, Allemagne", "is_active": True,
     "description": "Volkswagen ('voiture du peuple' en allemand) est fondée en 1937 pour produire une voiture accessible à tous les Allemands. La Beetle (Coccinelle), dessinée par Ferdinand Porsche, devient l'une des voitures les plus vendues de l'histoire. VW construit le plus grand groupe automobile mondial avec Audi, Porsche, Seat, Škoda, Lamborghini, Bentley, Bugatti. Le Groupe VW est en pleine transition électrique avec la gamme ID."},

    {"name": "Toyota", "country": "Japon", "founded_year": 1937, "founder": "Kiichiro Toyoda", "headquarters": "Toyota City, Aichi, Japon", "is_active": True,
     "description": "Kiichiro Toyoda transforme la division automobile de l'entreprise familiale en Toyota Motor Corporation en 1937. Toyota est devenu le premier constructeur automobile mondial en volume depuis 2008. La Corolla est la voiture la plus vendue de l'histoire (55+ millions d'unités). Toyota est pionnier de l'hybride avec la Prius (1997) et développe activement la pile à combustible hydrogène (Mirai). Modèles phares : Corolla, Camry, RAV4, Land Cruiser, Supra, GR86, bZ4X."},

    {"name": "Honda", "country": "Japon", "founded_year": 1948, "founder": "Soichiro Honda, Takeo Fujisawa", "headquarters": "Tokyo, Japon", "is_active": True,
     "description": "Soichiro Honda fonde Honda Motor Co. en 1948, commençant par équiper des vélos de moteurs de surplus de guerre. Honda est le plus grand fabricant de moteurs à combustion interne au monde (automobiles, motos, moteurs marins, générateurs). NSX (1989 et 2016), Civic, Jazz (Fit), CR-V et HR-V sont ses modèles phares. Honda s'est illustré en Formule 1 comme fournisseur de moteurs pour Red Bull Racing."},

    {"name": "BMW", "country": "Allemagne", "founded_year": 1916, "founder": "Franz Josef Popp, Camillo Castiglioni, Karl Rapp", "headquarters": "Munich, Allemagne", "is_active": True,
     "description": "Bayerische Motoren Werke (BMW) est fondée en 1916 comme fabricant de moteurs d'avions. La marque à l'hélice stylisée commence la production automobile en 1928. BMW est synonyme de dynamisme de conduite, incarné par le slogan 'Sheer Driving Pleasure'. Modèles iconiques : Série 3, Série 7, M3, M5, Z3, Z4, i3, i8, X5. BMW Group comprend aussi Mini et Rolls-Royce."},

    {"name": "Audi", "country": "Allemagne", "founded_year": 1909, "founder": "August Horch", "headquarters": "Ingolstadt, Allemagne", "is_active": True,
     "description": "August Horch fonde Audi en 1909 à Zwickau après avoir quitté la société qu'il avait précédemment fondée (Horch). Les quatre anneaux d'Audi représentent la fusion en 1932 de quatre constructeurs : Audi, DKW, Horch et Wanderer en Auto Union. Audi est connu pour son quattro (4x4 intégral), sa gamme premium et la série R (R8, RS). Propriété de Volkswagen Group, Audi est en forte transition électrique avec la gamme e-tron/Q8 e-tron."},
]

# ─── MODÈLES FONDATEURS (les premiers de l'histoire) ───
SEED_MODELS_BENZ = [
    {"name": "Patent-Motorwagen", "generation": "I", "year_start": 1886, "year_end": 1893,
     "body_styles": ["Tricycle motorisé"], "segment": "Précurseur", "is_iconic": True,
     "description": "La Benz Patent-Motorwagen Nº1, brevetée le 29 janvier 1886 (brevet DRP-37435), est universellement reconnue comme la première véritable automobile à moteur à explosion. Motorisée par un bicylindre 4 temps de 954cc développant 0,75ch (puis 2ch en version améliorée), elle atteignait 16 km/h. C'est Bertha Benz, épouse de Karl, qui réalise le premier long voyage en automobile de l'histoire en août 1888 (106 km de Mannheim à Pforzheim) pour prouver la fiabilité du véhicule.",
     "anecdotes": "Bertha Benz effectua le premier grand voyage en automobile de l'histoire (106 km) à l'insu de son mari pour démontrer la fiabilité du véhicule. En route, elle inventa les plaquettes de frein en faisant garnir les sabots de cuir par un cordonnier.",
     "countries": ["Allemagne"]},
]

def seed_database():
    print("🚀 Initialisation de la base de données...")
    initialize_database()

    print(f"\n📦 Insertion de {len(SEED_BRANDS)} marques fondatrices...")
    brand_ids = {}
    for brand_data in SEED_BRANDS:
        bid = upsert_brand(brand_data)
        brand_ids[brand_data["name"]] = bid
        print(f"  ✅ {brand_data['name']} ({brand_data['founded_year']}) — ID: {bid}")

    print(f"\n🚗 Insertion des modèles fondateurs...")
    for model_data in SEED_MODELS_BENZ:
        model_data["brand_id"] = brand_ids["Benz & Cie"]
        from database import upsert_model
        mid = upsert_model(model_data)
        print(f"  ✅ Benz {model_data['name']} ({model_data['year_start']}) — ID: {mid}")

    stats = get_database_stats()
    print(f"\n✨ Base de données initialisée !")
    print(f"   🏭 Marques  : {stats['brands']}")
    print(f"   🚗 Modèles  : {stats['models']}")
    print(f"\n💡 Lancez maintenant 'python main.py --collect-models' pour enrichir la base via Gemini.")

if __name__ == "__main__":
    seed_database()
