"use client";

import { useState, useEffect } from "react";
import Link from "next/link";
import Navbar from "@/components/Navbar";

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
  year_start: number;
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

      {/* ── HERO ── */}
      <section className="hero">
        <div className="hero-bg" />
        <div className="container">
          <div className="hero-content animate-fadeInUp">
            <div className="hero-badge">
              <span>⚡</span>
              Encyclopédie Automobile Mondiale
            </div>
            <h1 className="hero-title">
              Toutes les voitures<br />depuis 1886
            </h1>
            <p className="hero-subtitle">
              Explorez l'histoire complète de l'automobile — des premières
              tricycles à vapeur aux hypercars électriques d'aujourd'hui.
              Chaque marque, chaque modèle, chaque génération.
            </p>
            <div className="hero-cta">
              <Link href="/marques" className="btn btn-primary">
                🏭 Explorer les marques
              </Link>
              <Link href="/modeles" className="btn btn-secondary">
                🚗 Tous les modèles
              </Link>
            </div>

            <div className="hero-stats">
              {[
                { num: loading ? "..." : stats.brands.toLocaleString(), label: "Marques" },
                { num: loading ? "..." : stats.models.toLocaleString(), label: "Modèles" },
                { num: loading ? "..." : stats.specs.toLocaleString(), label: "Fiches techniques" },
                { num: "140+", label: "Ans d'histoire" },
              ].map((s) => (
                <div className="stat-item" key={s.label}>
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
          <div className="section-header">
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
                <div key={i} className="card" style={{ height: 160 }}>
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
              description="Lancez l'agent IA pour collecter les marques et modèles automobiles."
              action={{ label: "Comment démarrer ?", href: "#guide" }}
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
            <div className="section-header">
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
                    {model.thumbnail_url ? (
                      // eslint-disable-next-line @next/next/no-img-element
                      <img
                        src={model.thumbnail_url}
                        alt={`${model.brand_name} ${model.name}`}
                        className="model-card-image"
                      />
                    ) : (
                      <div
                        className="model-card-image"
                        style={{
                          display: "flex",
                          alignItems: "center",
                          justifyContent: "center",
                          fontSize: "3rem",
                          background: "var(--bg-surface)",
                        }}
                      >
                        🚗
                      </div>
                    )}
                    <div className="model-card-body">
                      <div className="model-card-brand">{model.brand_name}</div>
                      <div className="model-card-name">{model.name}</div>
                      <div className="model-card-year">
                        {model.year_start}
                        {model.year_end ? ` – ${model.year_end}` : " – aujourd'hui"}
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

      {/* ── GUIDE DE DÉMARRAGE ── */}
      <section className="section" id="guide">
        <div className="container">
          <div className="section-header">
            <span className="section-label">Démarrage rapide</span>
            <h2 className="section-title">Comment alimenter la base de données ?</h2>
            <p className="section-subtitle">
              L'agent IA utilise Google Gemini pour collecter automatiquement toutes les données.
            </p>
          </div>

          <div style={{ display: "grid", gridTemplateColumns: "repeat(auto-fit, minmax(280px, 1fr))", gap: 20 }}>
            {[
              {
                step: "01",
                icon: "🔑",
                title: "Configurer l'API Gemini",
                desc: "Copiez agent/.env.example en agent/.env et ajoutez votre clé Google Gemini (gratuite sur aistudio.google.com).",
                code: "cp agent/.env.example agent/.env",
              },
              {
                step: "02",
                icon: "📦",
                title: "Installer les dépendances",
                desc: "Installez les bibliothèques Python nécessaires à l'agent de collecte.",
                code: "pip install -r agent/requirements.txt",
              },
              {
                step: "03",
                icon: "🚀",
                title: "Lancer l'agent",
                desc: "Démarrez l'agent pour collecter toutes les marques et modèles depuis Gemini.",
                code: "python agent/main.py --full-run",
              },
              {
                step: "04",
                icon: "🌐",
                title: "Démarrer le site",
                desc: "Lancez l'API Python et le serveur Next.js pour visualiser les données.",
                code: "python agent/api.py & npm run dev",
              },
            ].map((item) => (
              <div key={item.step} className="glass-panel" style={{ position: "relative" }}>
                <div
                  style={{
                    position: "absolute",
                    top: 24,
                    right: 24,
                    fontFamily: "Outfit, sans-serif",
                    fontSize: "2.5rem",
                    fontWeight: 900,
                    color: "rgba(255,255,255,0.04)",
                    lineHeight: 1,
                  }}
                >
                  {item.step}
                </div>
                <div style={{ fontSize: "2rem", marginBottom: 12 }}>{item.icon}</div>
                <h3 style={{ marginBottom: 8, fontSize: "1rem" }}>{item.title}</h3>
                <p style={{ fontSize: "0.875rem", color: "var(--text-secondary)", marginBottom: 16, lineHeight: 1.7 }}>
                  {item.desc}
                </p>
                <code
                  style={{
                    display: "block",
                    background: "var(--bg-surface)",
                    border: "1px solid var(--border-subtle)",
                    borderRadius: "var(--radius-sm)",
                    padding: "8px 12px",
                    fontSize: "0.78rem",
                    color: "var(--accent-primary)",
                    fontFamily: "monospace",
                  }}
                >
                  {item.code}
                </code>
              </div>
            ))}
          </div>
        </div>
      </section>

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
  action,
}: {
  icon: string;
  title: string;
  description: string;
  action?: { label: string; href: string };
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
      <p style={{ color: "var(--text-muted)", fontSize: "0.9rem", marginBottom: 24 }}>{description}</p>
      {action && (
        <a href={action.href} className="btn btn-secondary">
          {action.label}
        </a>
      )}
    </div>
  );
}
