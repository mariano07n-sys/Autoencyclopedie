"use client";

import { useState, useEffect } from "react";
import Link from "next/link";
import Navbar from "@/components/Navbar";
import Reveal from "@/components/Reveal";

interface Brand {
  id: number;
  name: string;
  country: string;
  founded_year: number;
  logo_url: string;
  is_active: boolean;
  description: string;
}

export default function MarquesPage() {
  const [brands, setBrands] = useState<Brand[]>([]);
  const [filtered, setFiltered] = useState<Brand[]>([]);
  const [countries, setCountries] = useState<string[]>([]);
  const [loading, setLoading] = useState(true);
  const [search, setSearch] = useState("");
  const [countryFilter, setCountryFilter] = useState("");
  const [statusFilter, setStatusFilter] = useState<"all" | "active" | "inactive">("all");
  const [sortBy, setSortBy] = useState<"name" | "founded">("name");

  useEffect(() => {
    Promise.all([
      fetch("/api/brands").then((r) => r.json()).catch(() => ({ brands: [] })),
      fetch("/api/countries").then((r) => r.json()).catch(() => ({ countries: [] })),
    ]).then(([brandsData, countriesData]) => {
      setBrands(brandsData.brands || []);
      setCountries(countriesData.countries || []);
      setLoading(false);
    });
  }, []);

  useEffect(() => {
    let result = [...brands];
    if (search) {
      result = result.filter((b) =>
        b.name.toLowerCase().includes(search.toLowerCase()) ||
        b.country?.toLowerCase().includes(search.toLowerCase())
      );
    }
    if (countryFilter) {
      result = result.filter((b) => b.country === countryFilter);
    }
    if (statusFilter === "active") result = result.filter((b) => b.is_active);
    if (statusFilter === "inactive") result = result.filter((b) => !b.is_active);

    result.sort((a, b) => {
      if (sortBy === "name") return a.name.localeCompare(b.name);
      return (a.founded_year || 9999) - (b.founded_year || 9999);
    });

    setFiltered(result);
  }, [brands, search, countryFilter, statusFilter, sortBy]);

  return (
    <>
      <Navbar />
      <Reveal />
      <div style={{ paddingTop: 100 }}>
        <div className="container">
          {/* Header */}
          <div className="section-header animate-fadeInUp">
            <span className="section-label">Constructeurs automobiles</span>
            <h1 className="section-title">Toutes les marques</h1>
            <p className="section-subtitle">
              {loading ? "Chargement..." : `${brands.length} marques référencées — des pionniers du XIXe siècle aux startups EV modernes`}
            </p>
          </div>

          {/* Filters */}
          <div className="filters-bar">
            <input
              type="text"
              placeholder="🔍 Rechercher une marque..."
              value={search}
              onChange={(e) => setSearch(e.target.value)}
              style={{
                flex: 1,
                minWidth: 200,
                padding: "8px 14px",
                background: "var(--bg-surface)",
                border: "1px solid var(--border-subtle)",
                borderRadius: "var(--radius-sm)",
                color: "var(--text-primary)",
                fontFamily: "Inter, sans-serif",
                fontSize: "0.85rem",
                outline: "none",
              }}
            />
            <select
              className="filter-select"
              value={countryFilter}
              onChange={(e) => setCountryFilter(e.target.value)}
            >
              <option value="">🌍 Tous les pays</option>
              {countries.map((c) => (
                <option key={c} value={c}>{c}</option>
              ))}
            </select>
            <select
              className="filter-select"
              value={statusFilter}
              onChange={(e) => setStatusFilter(e.target.value as "all" | "active" | "inactive")}
            >
              <option value="all">Toutes</option>
              <option value="active">✅ Actives</option>
              <option value="inactive">❌ Disparues</option>
            </select>
            <select
              className="filter-select"
              value={sortBy}
              onChange={(e) => setSortBy(e.target.value as "name" | "founded")}
            >
              <option value="name">Trier A–Z</option>
              <option value="founded">Trier par année</option>
            </select>
            <span style={{ color: "var(--text-muted)", fontSize: "0.8rem", whiteSpace: "nowrap" }}>
              {filtered.length} résultats
            </span>
          </div>

          {/* Grid */}
          {loading ? (
            <div className="grid-brands">
              {Array.from({ length: 24 }).map((_, i) => (
                <div key={i} className="skeleton" style={{ height: 160, borderRadius: "var(--radius-md)" }} />
              ))}
            </div>
          ) : filtered.length > 0 ? (
            <div className="grid-brands" style={{ marginBottom: 80 }}>
              {filtered.map((brand, i) => (
                <Link key={brand.id} href={`/marques/${encodeURIComponent(brand.name)}`}>
                  <div
                    className="card brand-card animate-fadeInUp"
                    style={{ animationDelay: `${Math.min(i * 30, 600)}ms` }}
                  >
                    <div className="brand-logo-wrapper">
                      {brand.logo_url ? (
                        // eslint-disable-next-line @next/next/no-img-element
                        <img
                          src={brand.logo_url}
                          alt={brand.name}
                          style={{ width: 48, height: 48, objectFit: "contain" }}
                        />
                      ) : (
                        <span style={{ fontSize: "2rem" }}>🏭</span>
                      )}
                    </div>
                    <div className="brand-name">{brand.name}</div>
                    <div className="brand-meta">
                      {brand.country || "Pays inconnu"}
                    </div>
                    <div className="brand-meta">
                      {brand.founded_year ? `Fondée en ${brand.founded_year}` : ""}
                    </div>
                    {!brand.is_active && (
                      <span className="tag tag-red">Disparue</span>
                    )}
                  </div>
                </Link>
              ))}
            </div>
          ) : (
            <div style={{ textAlign: "center", padding: "64px 0", color: "var(--text-muted)" }}>
              <div style={{ fontSize: "3rem", marginBottom: 16 }}>🔍</div>
              <p>Aucune marque ne correspond à votre recherche.</p>
            </div>
          )}
        </div>
      </div>
    </>
  );
}
