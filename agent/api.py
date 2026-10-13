"""
api.py - Serveur API local pour exposer la base de données au site Next.js
Lancer avec : python api.py
L'API sera disponible sur http://localhost:8000
"""

import json
from http.server import HTTPServer, BaseHTTPRequestHandler
from urllib.parse import urlparse, parse_qs
from database import (
    get_connection, get_all_brands, get_brand_by_name,
    get_models_by_brand, get_database_stats
)


def cors_headers(handler):
    handler.send_header("Access-Control-Allow-Origin", "*")
    handler.send_header("Access-Control-Allow-Methods", "GET, OPTIONS")
    handler.send_header("Access-Control-Allow-Headers", "Content-Type")
    handler.send_header("Content-Type", "application/json; charset=utf-8")


class CarsAPIHandler(BaseHTTPRequestHandler):
    def log_message(self, format, *args):
        print(f"[API] {self.path} → {args[1]}")

    def send_json(self, data: dict, status: int = 200):
        body = json.dumps(data, ensure_ascii=False, default=str).encode("utf-8")
        self.send_response(status)
        cors_headers(self)
        self.send_header("Content-Length", str(len(body)))
        self.end_headers()
        self.wfile.write(body)

    def do_OPTIONS(self):
        self.send_response(200)
        cors_headers(self)
        self.end_headers()

    def do_GET(self):
        parsed = urlparse(self.path)
        path = parsed.path.rstrip("/")
        params = parse_qs(parsed.query)

        try:
            # GET /api/stats
            if path == "/api/stats":
                self.send_json(get_database_stats())

            # GET /api/brands
            elif path == "/api/brands":
                search = params.get("search", [None])[0]
                country = params.get("country", [None])[0]
                brands = get_all_brands()
                if search:
                    brands = [b for b in brands if search.lower() in b["name"].lower()]
                if country:
                    brands = [b for b in brands if b.get("country", "").lower() == country.lower()]
                self.send_json({"brands": brands, "total": len(brands)})

            # GET /api/brands/:name
            elif path.startswith("/api/brands/"):
                brand_name = path.split("/api/brands/")[1]
                brand = get_brand_by_name(brand_name)
                if brand:
                    brand["models"] = get_models_by_brand(brand["id"])
                    self.send_json(brand)
                else:
                    self.send_json({"error": "Marque non trouvée"}, 404)

            # GET /api/models?brand_id=1
            elif path == "/api/models":
                brand_id = params.get("brand_id", [None])[0]
                year_from = params.get("year_from", [None])[0]
                year_to = params.get("year_to", [None])[0]
                segment = params.get("segment", [None])[0]
                search = params.get("search", [None])[0]

                conn = get_connection()
                query = "SELECT m.*, b.name as brand_name FROM models m JOIN brands b ON m.brand_id = b.id WHERE 1=1"
                args = []

                if brand_id:
                    query += " AND m.brand_id = ?"
                    args.append(int(brand_id))
                if year_from:
                    query += " AND m.year_start >= ?"
                    args.append(int(year_from))
                if year_to:
                    query += " AND (m.year_end <= ? OR m.year_end IS NULL)"
                    args.append(int(year_to))
                if segment:
                    query += " AND m.segment = ?"
                    args.append(segment)
                if search:
                    query += " AND (m.name LIKE ? OR b.name LIKE ?)"
                    args.extend([f"%{search}%", f"%{search}%"])

                query += " ORDER BY b.name, m.year_start LIMIT 100"
                rows = conn.execute(query, args).fetchall()
                conn.close()

                models = []
                for r in rows:
                    d = dict(r)
                    d["body_styles"] = json.loads(d.get("body_styles") or "[]")
                    d["image_urls"] = json.loads(d.get("image_urls") or "[]")
                    d["countries"] = json.loads(d.get("countries") or "[]")
                    models.append(d)

                self.send_json({"models": models, "total": len(models)})

            # GET /api/models/:id
            elif path.startswith("/api/models/"):
                model_id = int(path.split("/api/models/")[1])
                conn = get_connection()
                row = conn.execute(
                    "SELECT m.*, b.name as brand_name FROM models m JOIN brands b ON m.brand_id=b.id WHERE m.id=?",
                    (model_id,)
                ).fetchone()

                if row:
                    model = dict(row)
                    model["body_styles"] = json.loads(model.get("body_styles") or "[]")
                    model["image_urls"] = json.loads(model.get("image_urls") or "[]")
                    model["countries"] = json.loads(model.get("countries") or "[]")
                    specs = conn.execute("SELECT * FROM specs WHERE model_id=?", (model_id,)).fetchall()
                    model["specs"] = [dict(s) for s in specs]
                    conn.close()
                    self.send_json(model)
                else:
                    conn.close()
                    self.send_json({"error": "Modèle non trouvé"}, 404)

            # GET /api/search?q=mustang
            elif path == "/api/search":
                q = params.get("q", [""])[0]
                if not q:
                    self.send_json({"error": "Paramètre q requis"}, 400)
                    return

                conn = get_connection()
                brands = conn.execute(
                    "SELECT id, name, country, logo_url FROM brands WHERE name LIKE ? LIMIT 5",
                    (f"%{q}%",)
                ).fetchall()
                models = conn.execute(
                    """SELECT m.id, m.name, m.generation, m.year_start, m.year_end,
                              m.thumbnail_url, b.name as brand_name
                       FROM models m JOIN brands b ON m.brand_id=b.id
                       WHERE m.name LIKE ? OR b.name LIKE ? LIMIT 20""",
                    (f"%{q}%", f"%{q}%")
                ).fetchall()
                conn.close()

                self.send_json({
                    "query": q,
                    "brands": [dict(r) for r in brands],
                    "models": [dict(r) for r in models],
                    "total": len(brands) + len(models)
                })

            # GET /api/countries
            elif path == "/api/countries":
                conn = get_connection()
                rows = conn.execute(
                    "SELECT DISTINCT country FROM brands WHERE country IS NOT NULL ORDER BY country"
                ).fetchall()
                conn.close()
                self.send_json({"countries": [r[0] for r in rows]})

            else:
                self.send_json({"error": "Route non trouvée", "available": [
                    "/api/stats", "/api/brands", "/api/brands/:name",
                    "/api/models", "/api/models/:id", "/api/search", "/api/countries"
                ]}, 404)

        except Exception as e:
            self.send_json({"error": str(e)}, 500)


if __name__ == "__main__":
    PORT = 8000
    server = HTTPServer(("localhost", PORT), CarsAPIHandler)
    print(f"🚀 API démarrée sur http://localhost:{PORT}")
    print("   Endpoints disponibles :")
    print("   GET /api/stats")
    print("   GET /api/brands?search=&country=")
    print("   GET /api/brands/:name")
    print("   GET /api/models?brand_id=&year_from=&year_to=&segment=&search=")
    print("   GET /api/models/:id")
    print("   GET /api/search?q=")
    print("   GET /api/countries")
    print("\n   Appuyez sur Ctrl+C pour arrêter.\n")
    try:
        server.serve_forever()
    except KeyboardInterrupt:
        print("\n⏹ API arrêtée.")
