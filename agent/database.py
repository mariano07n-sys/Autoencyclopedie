"""
database.py - Point d'entrée base de données
SQLite (local) si DATABASE_URL / SUPABASE_DB_URL absent, sinon PostgreSQL (Supabase).
"""

import os

if os.getenv("DATABASE_URL") or os.getenv("SUPABASE_DB_URL"):
    from database_postgres import *  # noqa: F401, F403
else:
    from database_sqlite import *  # noqa: F401, F403
