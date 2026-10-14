"use client";

import { useState, useEffect } from "react";
import Link from "next/link";
import Navbar from "@/components/Navbar";
import BlurWords from "@/components/BlurWords";
import ModelThumb from "@/components/ModelThumb";
import Reveal from "@/components/Reveal";

interface Stats {
  brands: number;
  models: number;
  specs: number;
}

interface Brand {
  id: number;
  name: string;
  country: string;
  founded_year: number;
  logo_url: string;
  is_active: boolean;
}

interface Model {
  id: number;
  name: string;
  brand_name: string;
  year_start: number | null;
  year_end: number | null;
  thumbnail_url: string;
  segment: string;
  is_iconic: boolean;
  body_styles: string[];
}

export default function HomePage() {
  const [stats, setStats] = useState<Stats>({ brands: 0, models: 0, specs: 0 });
  const [brands, setBrands] = useState<Brand[]>([]);
  const [iconicModels, setIconicModels] = useState<Model[]>([]);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    Promise.all([
      fetch("/api/stats").then((r) => r.json()).catch(() => ({ brands: 0, models: 0, specs: 0 })),
      fetch("/api/brands").then((r) => r.json()).catch(() => ({ brands: [] })),
      fetch("/api/models?search=").then((r) => r.json()).catch(() => ({ models: [] })),
    ]).then(([statsData, brandsData, modelsData]) => {
      setStats(statsData);
      setBrands((brandsData.brands || []).slice(0, 18));
      setIconicModels((modelsData.models || []).filter((m: Model) => m.is_iconic).slice(0, 6));
      setLoading(false);
    });
  }, []);

  return (
    <>
      <Navbar />
      <Reveal />

      {/* ── HERO ── */}
      <section className="hero">
        <div className="hero-bg" />
        <div className="container">
          <div className="hero-content">
            <div className="hero-badge liquid-glass reveal-element" style={{ transitionDelay: "0.4s" }}>
              <span className="badge-pill">Nouveau</span>
              <span className="badge-text">Encyclopédie automobile mondiale — données enrichies par IA</span>
            </div>
            <h1 className="hero-title">
              <BlurWords text="Toutes les voitures depuis 1886" />
            </h1>
            <p className="hero-subtitle reveal-element" style={{ transitionDelay: "0.9s" }}>
              Explorez l'histoire complète de l'automobile — des premières
              tricycles à vapeur aux hypercars électriques d'aujourd'hui.
              Chaque marque, chaque modèle, chaque génération.
            </p>
            <div className="hero-cta reveal-element" style={{ transitionDelay: "1.1s" }}>
              <Link href="/marques" className="btn btn-primary">
                Explorer les marques
                <svg viewBox="0 0 24 24" width="16" height="16" stroke="currentColor" strokeWidth="2" fill="none"><path d="M7 17L17 7" /><path d="M7 7h10v10" /></svg>
              </Link>
              <Link href="/modeles" className="btn btn-secondary">
                Tous les modèles
              </Link>
            </div>

            <div className="hero-stats">
              {[
                { num: loading ? "..." : stats.brands.toLocaleString(), label: "Marques" },
                { num: loading ? "..." : stats.models.toLocaleString(), label: "Modèles" },
                { num: loading ? "..." : stats.specs.toLocaleString(), label: "Fiches techniques" },
                { num: "140+", label: "Ans d'histoire" },
              ].map((s, i) => (
                <div
                  className="stat-item liquid-glass reveal-element"
                  key={s.label}
                  style={{ transitionDelay: `${1.2 + i * 0.1}s` }}
                >
                  <div className="stat-number">{s.num}</div>
                  <div className="stat-label">{s.label}</div>
                </div>
              ))}
            </div>
          </div>
        </div>
      </section>

      {/* ── MARQUES ── */}
      <section className="section" style={{ paddingTop: 0 }}>
        <div className="container">
          <div className="section-header reveal-element">
            <span className="section-label">Constructeurs</span>
            <h2 className="section-title">Marques du monde entier</h2>
            <p className="section-subtitle">
              Des pionniers européens aux géants asiatiques, en passant par les
              icônes américaines.
            </p>
          </div>

          {loading ? (
            <div className="grid-brands">
              {Array.from({ length: 12 }).map((_, i) => (
                <div key={i} className="card" style={{ height: 236 }}>
                  <div className="skeleton" style={{ width: "100%", height: "100%" }} />
                </div>
              ))}
            </div>
          ) : brands.length > 0 ? (
            <div className="grid-brands">
              {brands.map((brand, i) => (
                <Link key={brand.id} href={`/marques/${encodeURIComponent(brand.name)}`}>
                  <div
                    className="card brand-card animate-fadeInUp"
                    style={{ animationDelay: `${i * 50}ms` }}
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
                      {brand.country}
                      {brand.founded_year && ` · ${brand.founded_year}`}
                    </div>
                    {!brand.is_active && (
                      <span className="tag tag-red" style={{ fontSize: "0.65rem" }}>Disparue</span>
                    )}
                  </div>
                </Link>
              ))}
            </div>
          ) : (
            <EmptyState
              icon="🏭"
              title="Base de données vide"
              description="Aucune marque collectée pour le moment. L'agent de collecte alimente cette encyclopédie."
            />
          )}

          {brands.length > 0 && (
            <div style={{ textAlign: "center", marginTop: 32 }}>
              <Link href="/marques" className="btn btn-secondary">
                Voir toutes les marques →
              </Link>
            </div>
          )}
        </div>
      </section>

      {/* ── MODÈLES ICONIQUES ── */}
      {iconicModels.length > 0 && (
        <section className="section" style={{ background: "var(--bg-surface)" }}>
          <div className="container">
            <div className="section-header reveal-element">
              <span className="section-label">Légendes</span>
              <h2 className="section-title">Modèles iconiques</h2>
            </div>
            <div className="grid-models">
              {iconicModels.map((model, i) => (
                <Link key={model.id} href={`/modeles/${model.id}`}>
                  <div
                    className="card model-card animate-fadeInUp"
                    style={{ animationDelay: `${i * 80}ms` }}
                  >
                    <ModelThumb src={model.thumbnail_url} alt={`${model.brand_name} ${model.name}`} />
                    <div className="model-card-body">
                      <div className="model-card-brand">{model.brand_name}</div>
                      <div className="model-card-name">{model.name}</div>
                      <div className="model-card-year">
                        {model.year_start
                          ? `${model.year_start}${model.year_end ? ` – ${model.year_end}` : " – aujourd'hui"}`
                          : "Année inconnue"}
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
          </div>
        </section>
      )}

      {/* ── FOOTER ── */}
      <footer className="footer">
        <div className="container footer-inner">
          <div className="navbar-logo">
            <span className="logo-icon">🚗</span>
            <span className="logo-text">AutoEncyclopédie</span>
          </div>
          <div className="footer-text">
            Propulsé par Google Gemini · Base de données automobile mondiale
          </div>
        </div>
      </footer>
    </>
  );
}

function EmptyState({
  icon,
  title,
  description,
}: {
  icon: string;
  title: string;
  description: string;
}) {
  return (
    <div
      style={{
        textAlign: "center",
        padding: "64px 24px",
        border: "2px dashed var(--border-subtle)",
        borderRadius: "var(--radius-lg)",
      }}
    >
      <div style={{ fontSize: "3rem", marginBottom: 16 }}>{icon}</div>
      <h3 style={{ marginBottom: 8, color: "var(--text-secondary)" }}>{title}</h3>
      <p style={{ color: "var(--text-muted)", fontSize: "0.9rem" }}>{description}</p>
    </div>
  );
}
