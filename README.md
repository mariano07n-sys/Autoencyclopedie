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

### 4. Mettre en ligne (recommandé) — Supabase + Vercel

1. Créer un projet Supabase et exécuter `supabase/migrations/001_schema.sql`.
2. Dans `agent/.env`, définir `DATABASE_URL` (URI Postgres Supabase).
3. Collecter les données : `python agent/seed_data.py` puis `python agent/main.py --full-run`.
4. Dans `web/.env.local`, configurer `NEXT_PUBLIC_SUPABASE_URL`, `NEXT_PUBLIC_SUPABASE_ANON_KEY`, `SUPABASE_SERVICE_ROLE_KEY`.
5. Déployer le dossier `web` sur Vercel (voir **`action.md`** pour la checklist complète).

Le site appelle les **Route Handlers Next.js** (`/api/*`) qui lisent Supabase — plus besoin de `api.py` en production.

### 5. Dev local (option SQLite legacy)

```bash
python agent/api.py
# API sur http://localhost:8000
```

Dans `web/.env.local` : `USE_LOCAL_API=true`, puis :

```bash
cd web
npm run dev
# Site sur http://localhost:3000
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
