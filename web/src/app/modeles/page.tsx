"use client";

import { useState, useEffect } from "react";
import Link from "next/link";
import Navbar from "@/components/Navbar";
import Reveal from "@/components/Reveal";

interface Model {
  id: number;
  name: string;
  brand_name: string;
  year_start: number;
  year_end: number | null;
  thumbnail_url: string;
  segment: string;
  is_iconic: boolean;
  body_styles: string[];
}

const SEGMENTS = ["A", "B", "C", "D", "E", "F", "Sport", "Supercar", "Hypercar", "SUV compact", "SUV medium", "SUV large", "Utilitaire", "Commercial"];

export default function ModelesPage() {
  const [models, setModels] = useState<Model[]>([]);
  const [loading, setLoading] = useState(true);
  const [search, setSearch] = useState("");
  const [segmentFilter, setSegmentFilter] = useState("");
  const [yearFrom, setYearFrom] = useState("");
  const [yearTo, setYearTo] = useState("");
  const [iconicOnly, setIconicOnly] = useState(false);

  useEffect(() => {
    const params = new URLSearchParams();
    if (search) params.set("search", search);
    if (segmentFilter) params.set("segment", segmentFilter);
    if (yearFrom) params.set("year_from", yearFrom);
    if (yearTo) params.set("year_to", yearTo);

    fetch(`/api/models?${params.toString()}`)
      .then((r) => r.json())
      .then((data) => {
        setModels(data.models || []);
        setLoading(false);
      })
      .catch(() => setLoading(false));
  }, [search, segmentFilter, yearFrom, yearTo]);

  const filtered = iconicOnly ? models.filter((m) => m.is_iconic) : models;

  return (
    <>
      <Navbar />
      <Reveal />
      <div style={{ paddingTop: 100 }}>
        <div className="container">
          <div className="section-header animate-fadeInUp">
            <span className="section-label">Catalogue automobile</span>
            <h1 className="section-title">Tous les modèles</h1>
            <p className="section-subtitle">
              {loading ? "Chargement..." : `${filtered.length} modèles référencés`}
            </p>
          </div>

          {/* Filters */}
          <div className="filters-bar">
            <input
              type="text"
              placeholder="🔍 Rechercher..."
              value={search}
              onChange={(e) => { setSearch(e.target.value); setLoading(true); }}
              style={{
                flex: 1,
                minWidth: 180,
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
            <select className="filter-select" value={segmentFilter} onChange={(e) => { setSegmentFilter(e.target.value); setLoading(true); }}>
              <option value="">Tous segments</option>
              {SEGMENTS.map((s) => <option key={s} value={s}>{s}</option>)}
            </select>
            <input
              type="number"
              placeholder="De (année)"
              value={yearFrom}
              onChange={(e) => { setYearFrom(e.target.value); setLoading(true); }}
              style={{
                width: 110,
                padding: "8px 12px",
                background: "var(--bg-surface)",
                border: "1px solid var(--border-subtle)",
                borderRadius: "var(--radius-sm)",
                color: "var(--text-primary)",
                fontFamily: "Inter, sans-serif",
                fontSize: "0.85rem",
                outline: "none",
              }}
            />
            <input
              type="number"
              placeholder="À (année)"
              value={yearTo}
              onChange={(e) => { setYearTo(e.target.value); setLoading(true); }}
              style={{
                width: 110,
                padding: "8px 12px",
                background: "var(--bg-surface)",
                border: "1px solid var(--border-subtle)",
                borderRadius: "var(--radius-sm)",
                color: "var(--text-primary)",
                fontFamily: "Inter, sans-serif",
                fontSize: "0.85rem",
                outline: "none",
              }}
            />
            <label style={{ display: "flex", alignItems: "center", gap: 8, cursor: "pointer", fontSize: "0.85rem", color: "var(--text-secondary)", whiteSpace: "nowrap" }}>
              <input
                type="checkbox"
                checked={iconicOnly}
                onChange={(e) => setIconicOnly(e.target.checked)}
                style={{ accentColor: "var(--accent-primary)" }}
              />
              ⭐ Iconiques uniquement
            </label>
            <span style={{ color: "var(--text-muted)", fontSize: "0.8rem", whiteSpace: "nowrap" }}>
              {filtered.length} résultats
            </span>
          </div>

          {/* Grid */}
          {loading ? (
            <div className="grid-models">
              {Array.from({ length: 12 }).map((_, i) => (
                <div key={i} className="skeleton" style={{ height: 280, borderRadius: "var(--radius-md)" }} />
              ))}
            </div>
          ) : filtered.length > 0 ? (
            <div className="grid-models" style={{ marginBottom: 80 }}>
              {filtered.map((model, i) => (
                <Link key={model.id} href={`/modeles/${model.id}`}>
                  <div className="card model-card animate-fadeInUp" style={{ animationDelay: `${Math.min(i * 30, 600)}ms` }}>
                    {model.thumbnail_url ? (
                      // eslint-disable-next-line @next/next/no-img-element
                      <img src={model.thumbnail_url} alt={`${model.brand_name} ${model.name}`} className="model-card-image" />
                    ) : (
                      <div className="model-card-image" style={{ display: "flex", alignItems: "center", justifyContent: "center", fontSize: "3rem", background: "var(--bg-surface)" }}>
                        🚗
                      </div>
                    )}
                    <div className="model-card-body">
                      <div className="model-card-brand">{model.brand_name}</div>
                      <div className="model-card-name">{model.name}</div>
                      <div className="model-card-year">
                        {model.year_start}{model.year_end ? ` – ${model.year_end}` : " – présent"}
                      </div>
                      <div className="model-card-tags">
                        {model.is_iconic && <span className="tag tag-gold">⭐ Iconique</span>}
                        {model.segment && <span className="tag tag-blue">{model.segment}</span>}
                      </div>
                    </div>
                  </div>
                </Link>
              ))}
            </div>
          ) : (
            <div style={{ textAlign: "center", padding: "64px 0", color: "var(--text-muted)" }}>
              <div style={{ fontSize: "3rem", marginBottom: 16 }}>🔍</div>
              <p>Aucun modèle trouvé. Modifiez vos filtres ou lancez l'agent pour collecter des données.</p>
            </div>
          )}
        </div>
      </div>
    </>
  );
}
