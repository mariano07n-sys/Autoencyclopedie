# 🚗 AutoEncyclopédie — Encyclopédie Automobile Mondiale

> L'encyclopédie automobile complète depuis 1886, propulsée par un agent IA basé sur Google Gemini.

## 🏗 Architecture du Projet

```
Agentic-IA/
├── agent/                     # 🤖 Agent IA de collecte (Python)
│   ├── main.py               # Point d'entrée (CLI + menu interactif)
│   ├── collector.py          # Agent Gemini de collecte de données
│   ├── database.py           # Gestion SQLite (CRUD complet)
│   ├── api.py                # Serveur API HTTP local
│   ├── requirements.txt      # Dépendances Python
│   └── .env.example          # Template de configuration
│
├── web/                       # 🌐 Site web Next.js
│   └── src/app/              # Pages et composants
│
└── data/                      # 🗄 Base de données SQLite
    └── cars.db               # Créé automatiquement
```

## ⚡ Démarrage rapide

### 1. Configurer l'API Google Gemini
```bash
cp agent/.env.example agent/.env
# Éditez agent/.env et ajoutez votre clé : https://aistudio.google.com/apikey
```

### 2. Installer les dépendances Python
```bash
python -m venv .venv
.venv\Scripts\activate
pip install -r agent/requirements.txt
```

### 3. Lancer l'agent IA
```bash
python agent/main.py                         # Menu interactif
python agent/main.py --full-run              # Collecte complète
python agent/main.py --collect-brands        # Marques seulement
python agent/main.py --collect-brand Toyota  # Une marque précise
python agent/main.py --stats                 # Statistiques
```

### 4. Démarrer l'API Python
```bash
python agent/api.py
# API disponible sur http://localhost:8000
```

### 5. Démarrer le site web
```bash
cd web
npm run dev
# Site disponible sur http://localhost:3000
```

## 🌐 API Endpoints

| Endpoint | Description |
|----------|-------------|
| GET /api/stats | Statistiques de la base |
| GET /api/brands | Liste des marques |
| GET /api/brands/:name | Fiche marque + modèles |
| GET /api/models | Liste des modèles (filtres multiples) |
| GET /api/models/:id | Fiche modèle + specs |
| GET /api/search?q= | Recherche globale |
| GET /api/countries | Liste des pays |
