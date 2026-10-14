# Plan de mise en ligne — AutoEncyclopédie

Suivi des tâches **dans l’ordre** pour publier le site (Vercel + Supabase).

Légende : ✅ fait · ⬜ à faire · 🔧 action manuelle (vous)

---

## Phase 1 — Supabase (base de données cloud)

| # | Tâche | Statut |
|---|--------|--------|
| 1.1 | Schéma SQL `brands`, `models`, `specs`, `agent_tasks`, `search_cache` + RLS lecture publique | ✅ |
| 1.2 | Créer un projet sur [supabase.com](https://supabase.com) | ✅ `autoencyclopedie` (ref `vieafbhisxqfnkevcivn`, Paris eu-west-3) |
| 1.3 | Exécuter `supabase/migrations/001_schema.sql` dans **SQL Editor** | ✅ (via Management API) |
| 1.4 | Copier **Project URL**, **anon key**, **service role key**, **Database URI** | ✅ écrits dans `agent/.env` + `web/.env.local` |

---

## Phase 2 — Agent Python → Supabase

| # | Tâche | Statut |
|---|--------|--------|
| 2.1 | Backend PostgreSQL `agent/database_postgres.py` | ✅ |
| 2.2 | Sélection auto SQLite / Postgres via `DATABASE_URL` dans `agent/database.py` | ✅ |
| 2.3 | Cache Gemini compatible Postgres (`get_cached_result` / `cache_result`) | ✅ |
| 2.4 | Dépendance `psycopg` dans `agent/requirements.txt` | ✅ |
| 2.5 | Documenter variables dans `agent/.env.example` | ✅ |
| 2.6 | `pip install -r agent/requirements.txt` | ✅ `.venv` créé ; psycopg+dotenv installés (complet requis pour le collecteur Gemini) |
| 2.7 | Renseigner `DATABASE_URL` (URI Postgres Supabase) dans `agent/.env` | ✅ rôle dédié `agent_app` |
| 2.8 | Initialiser le schéma | ✅ (tables + RLS présents) |
| 2.9 | `python agent/seed_data.py` puis collecte (`python agent/main.py --full-run` ou menu) | ✅ seed (18 marques) via la Management API, puis **collecte Gemini en local via le pooler IPv4** : 193 marques + 197 modèles (9 marques traitées), stoppée par le quota gratuit (voir note quota) |
| 2.10 | Retirer `agent/.env` du suivi Git (`git rm --cached agent/.env`) si encore versionné | ✅ |

---

## Phase 3 — API Next.js (remplace `api.py` en production)

| # | Tâche | Statut |
|---|--------|--------|
| 3.1 | Client Supabase admin `web/src/lib/supabase/admin.ts` | ✅ |
| 3.2 | Routes `GET /api/stats`, `/api/brands`, `/api/brands/[name]`, `/api/models`, `/api/models/[id]`, `/api/search`, `/api/countries` | ✅ |
| 3.3 | Proxy localhost désactivé par défaut (`USE_LOCAL_API=true` pour dev SQLite + `api.py`) | ✅ |
| 3.4 | `@supabase/supabase-js` + `web/.env.example` | ✅ |
| 3.5 | `cd web && npm install` | ✅ (@supabase présent) |
| 3.6 | Copier `web/.env.example` → `web/.env.local` avec les clés Supabase | ✅ |
| 3.7 | `npm run dev` et vérifier accueil / marques / modèles | ✅ (`/api/stats` renvoie 18 marques) |

---

## Phase 4 — Déploiement Vercel

| # | Tâche | Statut |
|---|--------|--------|
| 4.1 | Fichier `web/vercel.json` | ✅ |
| 4.2 | Importer le repo sur [vercel.com](https://vercel.com) — **Root Directory : `web`** | ✅ via CLI (projet `autoencyclopedie`, root `web`) |
| 4.3 | Variables d’environnement Vercel : `NEXT_PUBLIC_SUPABASE_URL`, `NEXT_PUBLIC_SUPABASE_ANON_KEY`, `SUPABASE_SERVICE_ROLE_KEY` | ✅ (production + preview) |
| 4.4 | Premier déploiement + test URL de production | ✅ https://autoencyclopedie.vercel.app |
| 4.5 | (Optionnel) Domaine personnalisé | ⬜ |

---

## Phase 5 — Qualité produit (post-MVP)

| # | Tâche | Statut |
|---|--------|--------|
| 5.1 | Page `/timeline` (lien navbar actuel → 404) | ✅ `/timeline` + `/api/timeline` (groupement par décennie, filtre par chips) |
| 5.2 | Pagination modèles (au-delà de 100 entrées) | ⚠️ limite `/api/models` relevée de 100 → 1000 ; vraie pagination (offset/cursor) non implémentée |
| 5.3 | Collecte batch des fiches techniques (`specs`) dans `--full-run` | ✅ `--collect-specs` (icôniques d'abord, reprise auto) + enchaîné dans `--full-run` ; 32 variantes en base |
| 5.4 | Alimenter `agent_tasks` pour le suivi de collecte | ⬜ |
| 5.5 | Logos marques dans les prompts Gemini | ⬜ |
| 5.6 | Script migration SQLite → Supabase (si ancienne `data/cars.db`) | ⬜ |
| 5.7 | README web aligné sur Supabase / Vercel | ⬜ |
| 5.8 | Images réelles (logos + photos) via Wikimedia Commons | ✅ `agent/images.py` : 160/193 logos et 188/197 photos rattachés, 100 % d'URLs vivantes vérifiées par `agent/verify_images.py` ; les 42 entités restantes gardent le placeholder |
| 5.9 | Palette « Asphalte & Orange » | ✅ fond graphite `#141619`, surfaces `#1D2024`, navbar/recherche `#232629`, titres `#EDF0F2`, texte secondaire `#9AA3AC`, accents/boutons orange `#FF6B1A` (remplace la palette vert/crème testée le 2026-10-13) |

---

## Récap rapide (commandes)

```bash
# 1. Agent → Supabase (depuis agent/, avec DATABASE_URL dans .env)
pip install -r requirements.txt
python seed_data.py
python main.py --collect-brands

# 2. Site en local
cd ../web
npm install
cp .env.example .env.local   # puis éditer les clés
npm run dev

# 3. Dev legacy SQLite + api.py
# agent/.env sans DATABASE_URL
# web/.env.local : USE_LOCAL_API=true
# python api.py  +  npm run dev
```

---

## Fichiers clés ajoutés ou modifiés

- `supabase/migrations/001_schema.sql`
- `agent/database.py`, `database_sqlite.py`, `database_postgres.py`
- `web/src/app/api/**/route.ts`
- `web/src/lib/supabase/admin.ts`
- `.gitignore` (racine)
- `action.md` (ce fichier)

_Dernière mise à jour : migration Supabase + déploiement Vercel effectués (2026-10-13)._

## Note — accès réseau local à la base (IPv6)

- Le projet Supabase expose la connexion Postgres **directe en IPv6 uniquement** (`db.vieafbhisxqfnkevcivn.supabase.co`, pas d'enregistrement A IPv4). L'agent Python (`psycopg`) a donc besoin d'une **sortie IPv6** sur la machine qui le lance.
- Sur cette machine, l'IPv6 ne sort pas → le **seed a été exécuté via la Management API** (HTTPS/IPv4, rôle superuser) et non via psycopg direct.
- **Résolu (2026-10-13)** : le pooler Supavisor **IPv4** fonctionne — hôte `aws-1-eu-west-3.pooler.supabase.com`, port 6543 (mode transaction), utilisateur `agent_app.vieafbhisxqfnkevcivn`. L'`agent/.env` (`DATABASE_URL`) pointe dessus, et l'agent écrit désormais directement dans Supabase.
- Le **site n'est pas concerné** : il passe par l'API REST Supabase (supabase-js, HTTPS/IPv4), qui fonctionne partout — vérifié en production.

## Note — quota Gemini (gratuit)

- `gemini-1.5-flash`, `gemini-2.0-flash` et `gemini-2.5-flash` sont **retirés de l'API** (404). Le collecteur utilise `gemini-flash-latest` (surchargeable par `GEMINI_MODEL` dans `agent/.env`).
- Le palier gratuit est limité à **20 requêtes/jour et par modèle** (`generate_content_free_tier_requests`). Une collecte complète (193 marques → modèles) demande donc une dizaine de jours, ou le passage à un facturation payante.
- Les réponses sont mises en cache dans la table `search_cache` : relancer une requête déjà faite ne consomme pas de quota.
- Premier chargement réel (2026-10-13) : **193 marques**, **197 modèles** sur 9 marques, puis `429 ResourceExhausted`.

