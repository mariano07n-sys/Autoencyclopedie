"""
Backend PostgreSQL (Supabase) — même API publique que database_sqlite.py.
Activé lorsque DATABASE_URL ou SUPABASE_DB_URL est défini.
"""

import hashlib
import json
import os
from typing import Any, Dict, List, Optional

import psycopg
from psycopg.rows import dict_row


def _database_url() -> str:
    url = os.getenv("DATABASE_URL") or os.getenv("SUPABASE_DB_URL")
    if not url:
        raise RuntimeError("DATABASE_URL ou SUPABASE_DB_URL requis pour PostgreSQL")
    return url


def get_connection():
    return psycopg.connect(_database_url(), row_factory=dict_row)


def get_cached_result(query: str) -> Optional[str]:
    query_hash = hashlib.md5(query.encode()).hexdigest()
    with get_connection() as conn:
        row = conn.execute(
            "SELECT result FROM search_cache WHERE query_hash = %(h)s",
            {"h": query_hash},
        ).fetchone()
    return row["result"] if row else None


def cache_result(query: str, result: str, source: str = "gemini"):
    query_hash = hashlib.md5(query.encode()).hexdigest()
    with get_connection() as conn:
        conn.execute(
            """
            INSERT INTO search_cache (query_hash, query, result, source)
            VALUES (%(h)s, %(q)s, %(r)s, %(s)s)
            ON CONFLICT (query_hash) DO UPDATE SET
                query = EXCLUDED.query,
                result = EXCLUDED.result,
                source = EXCLUDED.source
            """,
            {"h": query_hash, "q": query, "r": result, "s": source},
        )
        conn.commit()


def initialize_database():
    migration = os.path.join(
        os.path.dirname(__file__), "..", "supabase", "migrations", "001_schema.sql"
    )
    if not os.path.isfile(migration):
        print("⚠ Fichier de migration introuvable. Créez les tables via le SQL Editor Supabase.")
        return
    with open(migration, encoding="utf-8") as f:
        sql = f.read()
    with get_connection() as conn:
        exists = conn.execute(
            "SELECT to_regclass('public.brands') IS NOT NULL AS ok"
        ).fetchone()["ok"]
        if exists:
            print("✅ Schéma PostgreSQL déjà en place (Supabase).")
            return
        conn.execute(sql)
        conn.commit()
    print("✅ Schéma PostgreSQL appliqué (Supabase).")


def upsert_brand(data: Dict[str, Any]) -> int:
    with get_connection() as conn:
        conn.execute(
            """
            INSERT INTO brands (name, country, founded_year, founder, headquarters, logo_url, description, is_active)
            VALUES (%(name)s, %(country)s, %(founded_year)s, %(founder)s, %(headquarters)s, %(logo_url)s, %(description)s, %(is_active)s)
            ON CONFLICT (name) DO UPDATE SET
                country = EXCLUDED.country,
                founded_year = EXCLUDED.founded_year,
                founder = EXCLUDED.founder,
                headquarters = EXCLUDED.headquarters,
                logo_url = EXCLUDED.logo_url,
                description = EXCLUDED.description,
                is_active = EXCLUDED.is_active,
                updated_at = NOW()
            """,
            {
                "name": data.get("name"),
                "country": data.get("country"),
                "founded_year": data.get("founded_year"),
                "founder": data.get("founder"),
                "headquarters": data.get("headquarters"),
                "logo_url": data.get("logo_url"),
                "description": data.get("description"),
                "is_active": data.get("is_active", True),
            },
        )
        row = conn.execute(
            "SELECT id FROM brands WHERE name = %(name)s",
            {"name": data["name"]},
        ).fetchone()
        conn.commit()
        return int(row["id"])


def get_all_brands() -> List[Dict]:
    with get_connection() as conn:
        rows = conn.execute("SELECT * FROM brands ORDER BY name").fetchall()
    return [dict(r) for r in rows]


def get_brand_by_name(name: str) -> Optional[Dict]:
    with get_connection() as conn:
        row = conn.execute(
            "SELECT * FROM brands WHERE LOWER(name) = LOWER(%(name)s)",
            {"name": name},
        ).fetchone()
    return dict(row) if row else None


def _json_val(value: Any) -> str:
    if isinstance(value, str):
        return value
    return json.dumps(value or [], ensure_ascii=False)


def upsert_model(data: Dict[str, Any]) -> int:
    generation = data.get("generation", "I")
    payload = {
        "brand_id": data["brand_id"],
        "name": data["name"],
        "generation": generation,
        "year_start": data.get("year_start"),
        "year_end": data.get("year_end"),
        "body_styles": _json_val(data.get("body_styles", [])),
        "segment": data.get("segment"),
        "description": data.get("description"),
        "anecdotes": data.get("anecdotes"),
        "image_urls": _json_val(data.get("image_urls", [])),
        "thumbnail_url": data.get("thumbnail_url"),
        "countries": _json_val(data.get("countries", [])),
        "is_iconic": data.get("is_iconic", False),
    }
    with get_connection() as conn:
        conn.execute(
            """
            INSERT INTO models (brand_id, name, generation, year_start, year_end,
                                body_styles, segment, description, anecdotes,
                                image_urls, thumbnail_url, countries, is_iconic)
            VALUES (%(brand_id)s, %(name)s, %(generation)s, %(year_start)s, %(year_end)s,
                    %(body_styles)s::jsonb, %(segment)s, %(description)s, %(anecdotes)s,
                    %(image_urls)s::jsonb, %(thumbnail_url)s, %(countries)s::jsonb, %(is_iconic)s)
            ON CONFLICT (brand_id, name, generation) DO UPDATE SET
                year_start = EXCLUDED.year_start,
                year_end = EXCLUDED.year_end,
                body_styles = EXCLUDED.body_styles,
                segment = EXCLUDED.segment,
                description = EXCLUDED.description,
                anecdotes = EXCLUDED.anecdotes,
                image_urls = EXCLUDED.image_urls,
                thumbnail_url = EXCLUDED.thumbnail_url,
                countries = EXCLUDED.countries,
                is_iconic = EXCLUDED.is_iconic,
                updated_at = NOW()
            """,
            payload,
        )
        row = conn.execute(
            """
            SELECT id FROM models
            WHERE brand_id = %(brand_id)s AND name = %(name)s AND generation = %(generation)s
            """,
            {"brand_id": data["brand_id"], "name": data["name"], "generation": generation},
        ).fetchone()
        conn.commit()
        return int(row["id"])


def _parse_model_row(d: Dict) -> Dict:
    out = dict(d)
    for key in ("body_styles", "image_urls", "countries"):
        val = out.get(key)
        if isinstance(val, str):
            out[key] = json.loads(val or "[]")
        elif val is None:
            out[key] = []
    return out


def get_models_by_brand(brand_id: int) -> List[Dict]:
    with get_connection() as conn:
        rows = conn.execute(
            "SELECT * FROM models WHERE brand_id = %(id)s ORDER BY year_start",
            {"id": brand_id},
        ).fetchall()
    return [_parse_model_row(dict(r)) for r in rows]


def get_models_for_media() -> List[Dict]:
    with get_connection() as conn:
        rows = conn.execute(
            """
            SELECT m.id, m.name, m.generation, m.year_start, m.year_end,
                   m.thumbnail_url, b.name AS brand_name
            FROM models m JOIN brands b ON b.id = m.brand_id
            ORDER BY b.name, m.year_start
            """
        ).fetchall()
    return [dict(r) for r in rows]


def update_brand_logo(brand_id: int, logo_url: Optional[str]):
    with get_connection() as conn:
        conn.execute(
            "UPDATE brands SET logo_url = %(url)s, updated_at = NOW() WHERE id = %(id)s",
            {"url": logo_url, "id": brand_id},
        )
        conn.commit()


def update_model_images(model_id: int, thumbnail_url: Optional[str], image_urls: List[str]):
    with get_connection() as conn:
        conn.execute(
            """
            UPDATE models
               SET thumbnail_url = %(thumb)s,
                   image_urls = %(urls)s::jsonb,
                   updated_at = NOW()
             WHERE id = %(id)s
            """,
            {
                "thumb": thumbnail_url,
                "urls": json.dumps(image_urls or [], ensure_ascii=False),
                "id": model_id,
            },
        )
        conn.commit()


def get_models_for_specs(limit: Optional[int] = None) -> List[Dict]:
    """Modèles sans fiche technique, iconiques d'abord (permet de reprendre après un quota atteint)."""
    sql = """
        SELECT m.id, m.name, m.generation, m.year_start, m.year_end, m.is_iconic,
               b.name AS brand_name
        FROM models m JOIN brands b ON b.id = m.brand_id
        WHERE NOT EXISTS (SELECT 1 FROM specs s WHERE s.model_id = m.id)
        ORDER BY m.is_iconic DESC NULLS LAST, b.name, m.year_start
    """
    params: Dict[str, Any] = {}
    if limit:
        sql += " LIMIT %(limit)s"
        params["limit"] = limit
    with get_connection() as conn:
        rows = conn.execute(sql, params).fetchall()
    return [dict(r) for r in rows]


def insert_spec(data: Dict[str, Any]) -> int:
    with get_connection() as conn:
        cur = conn.execute(
            """
            INSERT INTO specs (
                model_id, variant_name, engine_type, engine_displacement, fuel_type,
                power_hp, power_kw, torque_nm, transmission, drive_type, cylinders,
                acceleration_0_100, top_speed, fuel_consumption, co2_emissions,
                weight_kg, length_mm, width_mm, height_mm, wheelbase_mm,
                trunk_volume, range_km, price_launch_eur
            ) VALUES (
                %(model_id)s, %(variant_name)s, %(engine_type)s, %(engine_displacement)s, %(fuel_type)s,
                %(power_hp)s, %(power_kw)s, %(torque_nm)s, %(transmission)s, %(drive_type)s, %(cylinders)s,
                %(acceleration_0_100)s, %(top_speed)s, %(fuel_consumption)s, %(co2_emissions)s,
                %(weight_kg)s, %(length_mm)s, %(width_mm)s, %(height_mm)s, %(wheelbase_mm)s,
                %(trunk_volume)s, %(range_km)s, %(price_launch_eur)s
            )
            RETURNING id
            """,
            data,
        )
        row = cur.fetchone()
        conn.commit()
        return int(row["id"]) if row else 0


def get_database_stats() -> Dict[str, Any]:
    with get_connection() as conn:
        return {
            "brands": conn.execute("SELECT COUNT(*) AS c FROM brands").fetchone()["c"],
            "models": conn.execute("SELECT COUNT(*) AS c FROM models").fetchone()["c"],
            "specs": conn.execute("SELECT COUNT(*) AS c FROM specs").fetchone()["c"],
            "tasks_done": conn.execute(
                "SELECT COUNT(*) AS c FROM agent_tasks WHERE status = 'done'"
            ).fetchone()["c"],
            "tasks_pending": conn.execute(
                "SELECT COUNT(*) AS c FROM agent_tasks WHERE status = 'pending'"
            ).fetchone()["c"],
        }
