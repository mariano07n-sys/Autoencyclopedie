"""
Backend SQLite — développement local sans Supabase.
"""

import hashlib
import json
import os
import sqlite3
from typing import Any, Dict, List, Optional

DB_PATH = os.path.join(os.path.dirname(__file__), "..", "data", "cars.db")


def get_connection() -> sqlite3.Connection:
    os.makedirs(os.path.dirname(DB_PATH), exist_ok=True)
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    conn.execute("PRAGMA journal_mode=WAL")
    conn.execute("PRAGMA foreign_keys=ON")
    return conn


def initialize_database():
    conn = get_connection()
    cursor = conn.cursor()

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

    cursor.execute("""
        CREATE TABLE IF NOT EXISTS models (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            brand_id INTEGER NOT NULL REFERENCES brands(id) ON DELETE CASCADE,
            name TEXT NOT NULL,
            generation TEXT,
            year_start INTEGER,
            year_end INTEGER,
            body_styles TEXT,
            segment TEXT,
            description TEXT,
            anecdotes TEXT,
            image_urls TEXT,
            thumbnail_url TEXT,
            countries TEXT,
            is_iconic BOOLEAN DEFAULT FALSE,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            UNIQUE(brand_id, name, generation)
        )
    """)

    cursor.execute("""
        CREATE TABLE IF NOT EXISTS specs (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            model_id INTEGER NOT NULL REFERENCES models(id) ON DELETE CASCADE,
            variant_name TEXT,
            engine_type TEXT,
            engine_displacement REAL,
            fuel_type TEXT,
            power_hp INTEGER,
            power_kw INTEGER,
            torque_nm INTEGER,
            transmission TEXT,
            drive_type TEXT,
            cylinders INTEGER,
            acceleration_0_100 REAL,
            top_speed INTEGER,
            fuel_consumption REAL,
            co2_emissions INTEGER,
            weight_kg INTEGER,
            length_mm INTEGER,
            width_mm INTEGER,
            height_mm INTEGER,
            wheelbase_mm INTEGER,
            trunk_volume INTEGER,
            range_km INTEGER,
            price_launch_eur REAL,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        )
    """)

    cursor.execute("""
        CREATE TABLE IF NOT EXISTS agent_tasks (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            task_type TEXT NOT NULL,
            target TEXT NOT NULL,
            status TEXT DEFAULT 'pending',
            items_processed INTEGER DEFAULT 0,
            items_added INTEGER DEFAULT 0,
            items_updated INTEGER DEFAULT 0,
            error_message TEXT,
            started_at TIMESTAMP,
            completed_at TIMESTAMP,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        )
    """)

    cursor.execute("""
        CREATE TABLE IF NOT EXISTS search_cache (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            query_hash TEXT UNIQUE NOT NULL,
            query TEXT NOT NULL,
            result TEXT,
            source TEXT,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        )
    """)

    cursor.execute("CREATE INDEX IF NOT EXISTS idx_models_brand ON models(brand_id)")
    cursor.execute("CREATE INDEX IF NOT EXISTS idx_models_year ON models(year_start)")
    cursor.execute("CREATE INDEX IF NOT EXISTS idx_specs_model ON specs(model_id)")
    cursor.execute("CREATE INDEX IF NOT EXISTS idx_brands_name ON brands(name)")

    conn.commit()
    conn.close()
    print("✅ Base de données SQLite initialisée avec succès.")


def get_cached_result(query: str) -> Optional[str]:
    query_hash = hashlib.md5(query.encode()).hexdigest()
    conn = get_connection()
    row = conn.execute(
        "SELECT result FROM search_cache WHERE query_hash=?", (query_hash,)
    ).fetchone()
    conn.close()
    return row[0] if row else None


def cache_result(query: str, result: str, source: str = "gemini"):
    query_hash = hashlib.md5(query.encode()).hexdigest()
    conn = get_connection()
    conn.execute(
        "INSERT OR REPLACE INTO search_cache (query_hash, query, result, source) VALUES (?,?,?,?)",
        (query_hash, query, result, source),
    )
    conn.commit()
    conn.close()


def upsert_brand(data: Dict[str, Any]) -> int:
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


def upsert_model(data: Dict[str, Any]) -> int:
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
        (data["brand_id"], data["name"], data.get("generation", "I")),
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


def insert_spec(data: Dict[str, Any]) -> int:
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
