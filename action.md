# Plan de mise en ligne — AutoEncyclopédie

Suivi des tâches **dans l’ordre** pour publier le site (Vercel + Supabase).

Légende : ✅ fait · ⬜ à faire · 🔧 action manuelle (vous)

---

## Phase 1 — Supabase (base de données cloud)

| # | Tâche | Statut |
|---|--------|--------|
| 1.1 | Schéma SQL `brands`, `models`, `specs`, `agent_tasks`, `search_cache` + RLS lecture publique | ✅ |
| 1.2 | Créer un projet sur [supabase.com](https://supabase.com) | 🔧 |
| 1.3 | Exécuter `supabase/migrations/001_schema.sql` dans **SQL Editor** | 🔧 |
| 1.4 | Copier **Project URL**, **anon key**, **service role key**, **Database URI** | 🔧 |

---

## Phase 2 — Agent Python → Supabase

| # | Tâche | Statut |
|---|--------|--------|
| 2.1 | Backend PostgreSQL `agent/database_postgres.py` | ✅ |
| 2.2 | Sélection auto SQLite / Postgres via `DATABASE_URL` dans `agent/database.py` | ✅ |
| 2.3 | Cache Gemini compatible Postgres (`get_cached_result` / `cache_result`) | ✅ |
| 2.4 | Dépendance `psycopg` dans `agent/requirements.txt` | ✅ |
| 2.5 | Documenter variables dans `agent/.env.example` | ✅ |
| 2.6 | `pip install -r agent/requirements.txt` | 🔧 |
| 2.7 | Renseigner `DATABASE_URL` (URI Postgres Supabase) dans `agent/.env` | 🔧 |
| 2.8 | `python agent/database_postgres.py` ou `python -c "from database import initialize_database; initialize_database()"` depuis `agent/` | 🔧 |
| 2.9 | `python agent/seed_data.py` puis collecte (`python agent/main.py --full-run` ou menu) | 🔧 |
| 2.10 | Retirer `agent/.env` du suivi Git (`git rm --cached agent/.env`) si encore versionné | 🔧 |

---

## Phase 3 — API Next.js (remplace `api.py` en production)

| # | Tâche | Statut |
|---|--------|--------|
| 3.1 | Client Supabase admin `web/src/lib/supabase/admin.ts` | ✅ |
| 3.2 | Routes `GET /api/stats`, `/api/brands`, `/api/brands/[name]`, `/api/models`, `/api/models/[id]`, `/api/search`, `/api/countries` | ✅ |
| 3.3 | Proxy localhost désactivé par défaut (`USE_LOCAL_API=true` pour dev SQLite + `api.py`) | ✅ |
| 3.4 | `@supabase/supabase-js` + `web/.env.example` | ✅ |
| 3.5 | `cd web && npm install` | 🔧 |
| 3.6 | Copier `web/.env.example` → `web/.env.local` avec les clés Supabase | 🔧 |
| 3.7 | `npm run dev` et vérifier accueil / marques / modèles | 🔧 |

---

## Phase 4 — Déploiement Vercel

| # | Tâche | Statut |
|---|--------|--------|
| 4.1 | Fichier `web/vercel.json` | ✅ |
| 4.2 | Importer le repo sur [vercel.com](https://vercel.com) — **Root Directory : `web`** | 🔧 |
| 4.3 | Variables d’environnement Vercel : `NEXT_PUBLIC_SUPABASE_URL`, `NEXT_PUBLIC_SUPABASE_ANON_KEY`, `SUPABASE_SERVICE_ROLE_KEY` | 🔧 |
| 4.4 | Premier déploiement + test URL de production | 🔧 |
| 4.5 | (Optionnel) Domaine personnalisé | ⬜ |

---

## Phase 5 — Qualité produit (post-MVP)

| # | Tâche | Statut |
|---|--------|--------|
| 5.1 | Page `/timeline` (lien navbar actuel → 404) | ⬜ |
| 5.2 | Pagination modèles (au-delà de 100 entrées) | ⬜ |
| 5.3 | Collecte batch des fiches techniques (`specs`) dans `--full-run` | ⬜ |
| 5.4 | Alimenter `agent_tasks` pour le suivi de collecte | ⬜ |
| 5.5 | Logos marques dans les prompts Gemini | ⬜ |
| 5.6 | Script migration SQLite → Supabase (si ancienne `data/cars.db`) | ⬜ |
| 5.7 | README web aligné sur Supabase / Vercel | ⬜ |

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

_Dernière mise à jour : implémentation initiale Supabase + routes Next._
