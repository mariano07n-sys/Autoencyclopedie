"""
database.py - Gestion de la base de données SQLite pour l'encyclopédie automobile
"""

import sqlite3
import json
import os
from datetime import datetime
from typing import Optional, List, Dict, Any

DB_PATH = os.path.join(os.path.dirname(__file__), "..", "data", "cars.db")


def get_connection() -> sqlite3.Connection:
    """Retourne une connexion à la base de données avec Row Factory."""
    os.makedirs(os.path.dirname(DB_PATH), exist_ok=True)
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    conn.execute("PRAGMA journal_mode=WAL")
    conn.execute("PRAGMA foreign_keys=ON")
    return conn


def initialize_database():
    """Crée toutes les tables nécessaires si elles n'existent pas."""
    conn = get_connection()
    cursor = conn.cursor()

    # Table des marques
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS brands (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            name TEXT NOT NULL UNIQUE,
            country TEXT,
            founded_year INTEGER,
            founder TEXT,
            headquarters TEXT,
            logo_url TEXT,
            description TEXT,
            is_active BOOLEAN DEFAULT TRUE,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        )
    """)

    # Table des modèles
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS models (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            brand_id INTEGER NOT NULL REFERENCES brands(id) ON DELETE CASCADE,
            name TEXT NOT NULL,
            generation TEXT,
            year_start INTEGER,
            year_end INTEGER,
            body_styles TEXT,           -- JSON array: ["berline", "cabriolet", ...]
            segment TEXT,               -- A, B, C, D, E, F, SUV, Sport...
            description TEXT,
            anecdotes TEXT,
            image_urls TEXT,            -- JSON array of image URLs
            thumbnail_url TEXT,
            countries TEXT,             -- JSON array of countries sold in
            is_iconic BOOLEAN DEFAULT FALSE,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            UNIQUE(brand_id, name, generation)
        )
    """)

    # Table des spécifications techniques (une ligne par variante moteur)
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS specs (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            model_id INTEGER NOT NULL REFERENCES models(id) ON DELETE CASCADE,
            variant_name TEXT,          -- ex: "2.0 TDI 150ch", "GTI"
            engine_type TEXT,           -- Thermique, Électrique, Hybride, Hybride rechargeable
            engine_displacement REAL,   -- en litres (ex: 2.0)
            fuel_type TEXT,             -- Essence, Diesel, Électrique, Hydrogène, GPL
            power_hp INTEGER,           -- puissance en chevaux
            power_kw INTEGER,           -- puissance en kW
            torque_nm INTEGER,          -- couple en Nm
            transmission TEXT,          -- Manuelle, Automatique, CVT, Robotisée
            drive_type TEXT,            -- Traction, Propulsion, 4x4 intégral
            cylinders INTEGER,
            acceleration_0_100 REAL,    -- 0-100 km/h en secondes
            top_speed INTEGER,          -- vitesse max en km/h
            fuel_consumption REAL,      -- consommation mixte L/100km (ou Wh/km si électrique)
            co2_emissions INTEGER,      -- g/km
            weight_kg INTEGER,          -- poids à vide en kg
            length_mm INTEGER,
            width_mm INTEGER,
            height_mm INTEGER,
            wheelbase_mm INTEGER,
            trunk_volume INTEGER,       -- volume du coffre en litres
            range_km INTEGER,           -- autonomie en km (électrique/hybride)
            price_launch_eur REAL,      -- prix de lancement (EUR)
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        )
    """)

    # Table pour suivre les recherches de l'agent (audit trail)
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS agent_tasks (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            task_type TEXT NOT NULL,    -- "collect_brand", "collect_model", "enrich_model", "validate"
            target TEXT NOT NULL,       -- marque ou modèle ciblé
            status TEXT DEFAULT 'pending', -- pending, running, done, error
            items_processed INTEGER DEFAULT 0,
            items_added INTEGER DEFAULT 0,
            items_updated INTEGER DEFAULT 0,
            error_message TEXT,
            started_at TIMESTAMP,
            completed_at TIMESTAMP,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        )
    """)

    # Table pour le cache des recherches web (éviter les doublons de requêtes)
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS search_cache (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            query_hash TEXT UNIQUE NOT NULL,
            query TEXT NOT NULL,
            result TEXT,               -- JSON du résultat
            source TEXT,               -- "gemini", "web"
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        )
    """)

    # Index pour les performances
    cursor.execute("CREATE INDEX IF NOT EXISTS idx_models_brand ON models(brand_id)")
    cursor.execute("CREATE INDEX IF NOT EXISTS idx_models_year ON models(year_start)")
    cursor.execute("CREATE INDEX IF NOT EXISTS idx_specs_model ON specs(model_id)")
    cursor.execute("CREATE INDEX IF NOT EXISTS idx_brands_name ON brands(name)")

    conn.commit()
    conn.close()
    print("✅ Base de données initialisée avec succès.")


# ──────────────────────────────────────────────
# CRUD MARQUES
# ──────────────────────────────────────────────

def upsert_brand(data: Dict[str, Any]) -> int:
    """Insère ou met à jour une marque. Retourne l'ID."""
    conn = get_connection()
    cursor = conn.cursor()
    cursor.execute("""
        INSERT INTO brands (name, country, founded_year, founder, headquarters, logo_url, description, is_active)
        VALUES (:name, :country, :founded_year, :founder, :headquarters, :logo_url, :description, :is_active)
        ON CONFLICT(name) DO UPDATE SET
            country = excluded.country,
            founded_year = excluded.founded_year,
            founder = excluded.founder,
            headquarters = excluded.headquarters,
            logo_url = excluded.logo_url,
            description = excluded.description,
            is_active = excluded.is_active,
            updated_at = CURRENT_TIMESTAMP
    """, {
        "name": data.get("name"),
        "country": data.get("country"),
        "founded_year": data.get("founded_year"),
        "founder": data.get("founder"),
        "headquarters": data.get("headquarters"),
        "logo_url": data.get("logo_url"),
        "description": data.get("description"),
        "is_active": data.get("is_active", True),
    })
    brand_id = cursor.execute("SELECT id FROM brands WHERE name=?", (data["name"],)).fetchone()[0]
    conn.commit()
    conn.close()
    return brand_id


def get_all_brands() -> List[Dict]:
    conn = get_connection()
    rows = conn.execute("SELECT * FROM brands ORDER BY name").fetchall()
    conn.close()
    return [dict(r) for r in rows]


def get_brand_by_name(name: str) -> Optional[Dict]:
    conn = get_connection()
    row = conn.execute("SELECT * FROM brands WHERE name=? COLLATE NOCASE", (name,)).fetchone()
    conn.close()
    return dict(row) if row else None


# ──────────────────────────────────────────────
# CRUD MODÈLES
# ──────────────────────────────────────────────

def upsert_model(data: Dict[str, Any]) -> int:
    """Insère ou met à jour un modèle. Retourne l'ID."""
    conn = get_connection()
    cursor = conn.cursor()

    body_styles = json.dumps(data.get("body_styles", []), ensure_ascii=False)
    image_urls = json.dumps(data.get("image_urls", []), ensure_ascii=False)
    countries = json.dumps(data.get("countries", []), ensure_ascii=False)

    cursor.execute("""
        INSERT INTO models (brand_id, name, generation, year_start, year_end,
                            body_styles, segment, description, anecdotes,
                            image_urls, thumbnail_url, countries, is_iconic)
        VALUES (:brand_id, :name, :generation, :year_start, :year_end,
                :body_styles, :segment, :description, :anecdotes,
                :image_urls, :thumbnail_url, :countries, :is_iconic)
        ON CONFLICT(brand_id, name, generation) DO UPDATE SET
            year_start = excluded.year_start,
            year_end = excluded.year_end,
            body_styles = excluded.body_styles,
            segment = excluded.segment,
            description = excluded.description,
            anecdotes = excluded.anecdotes,
            image_urls = excluded.image_urls,
            thumbnail_url = excluded.thumbnail_url,
            countries = excluded.countries,
            is_iconic = excluded.is_iconic,
            updated_at = CURRENT_TIMESTAMP
    """, {
        "brand_id": data["brand_id"],
        "name": data["name"],
        "generation": data.get("generation", "I"),
        "year_start": data.get("year_start"),
        "year_end": data.get("year_end"),
        "body_styles": body_styles,
        "segment": data.get("segment"),
        "description": data.get("description"),
        "anecdotes": data.get("anecdotes"),
        "image_urls": image_urls,
        "thumbnail_url": data.get("thumbnail_url"),
        "countries": countries,
        "is_iconic": data.get("is_iconic", False),
    })

    model_id = cursor.execute(
        "SELECT id FROM models WHERE brand_id=? AND name=? AND generation=?",
        (data["brand_id"], data["name"], data.get("generation", "I"))
    ).fetchone()[0]
    conn.commit()
    conn.close()
    return model_id


def get_models_by_brand(brand_id: int) -> List[Dict]:
    conn = get_connection()
    rows = conn.execute(
        "SELECT * FROM models WHERE brand_id=? ORDER BY year_start", (brand_id,)
    ).fetchall()
    conn.close()
    result = []
    for r in rows:
        d = dict(r)
        d["body_styles"] = json.loads(d["body_styles"] or "[]")
        d["image_urls"] = json.loads(d["image_urls"] or "[]")
        d["countries"] = json.loads(d["countries"] or "[]")
        result.append(d)
    return result


# ──────────────────────────────────────────────
# CRUD SPECS
# ──────────────────────────────────────────────

def insert_spec(data: Dict[str, Any]) -> int:
    """Insère une fiche technique pour une variante de modèle."""
    conn = get_connection()
    cursor = conn.cursor()
    cursor.execute("""
        INSERT OR IGNORE INTO specs (
            model_id, variant_name, engine_type, engine_displacement, fuel_type,
            power_hp, power_kw, torque_nm, transmission, drive_type, cylinders,
            acceleration_0_100, top_speed, fuel_consumption, co2_emissions,
            weight_kg, length_mm, width_mm, height_mm, wheelbase_mm,
            trunk_volume, range_km, price_launch_eur
        ) VALUES (
            :model_id, :variant_name, :engine_type, :engine_displacement, :fuel_type,
            :power_hp, :power_kw, :torque_nm, :transmission, :drive_type, :cylinders,
            :acceleration_0_100, :top_speed, :fuel_consumption, :co2_emissions,
            :weight_kg, :length_mm, :width_mm, :height_mm, :wheelbase_mm,
            :trunk_volume, :range_km, :price_launch_eur
        )
    """, data)
    spec_id = cursor.lastrowid
    conn.commit()
    conn.close()
    return spec_id


# ──────────────────────────────────────────────
# STATS
# ──────────────────────────────────────────────

def get_database_stats() -> Dict[str, Any]:
    conn = get_connection()
    stats = {
        "brands": conn.execute("SELECT COUNT(*) FROM brands").fetchone()[0],
        "models": conn.execute("SELECT COUNT(*) FROM models").fetchone()[0],
        "specs": conn.execute("SELECT COUNT(*) FROM specs").fetchone()[0],
        "tasks_done": conn.execute("SELECT COUNT(*) FROM agent_tasks WHERE status='done'").fetchone()[0],
        "tasks_pending": conn.execute("SELECT COUNT(*) FROM agent_tasks WHERE status='pending'").fetchone()[0],
    }
    conn.close()
    return stats


if __name__ == "__main__":
    initialize_database()
    print(get_database_stats())
