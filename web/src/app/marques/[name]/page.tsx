"use client";

import { useState, useEffect } from "react";
import { useParams, useRouter } from "next/navigation";
import Link from "next/link";
import Navbar from "@/components/Navbar";
import ModelThumb from "@/components/ModelThumb";

interface Brand {
  id: number;
  name: string;
  country: string;
  founded_year: number;
  founder: string;
  headquarters: string;
  logo_url: string;
  description: string;
  is_active: boolean;
  models: Model[];
}

interface Model {
  id: number;
  name: string;
  generation: string;
  year_start: number;
  year_end: number | null;
  thumbnail_url: string;
  segment: string;
  is_iconic: boolean;
  body_styles: string[];
  description: string;
}

export default function BrandPage() {
  const { name } = useParams<{ name: string }>();
  const router = useRouter();
  const [brand, setBrand] = useState<Brand | null>(null);
  const [loading, setLoading] = useState(true);
  const [activeTab, setActiveTab] = useState<"models" | "history">("models");

  useEffect(() => {
    fetch(`/api/brands/${encodeURIComponent(name)}`)
      .then((r) => r.json())
      .then((data) => {
        if (data.error) router.push("/marques");
        else setBrand(data);
        setLoading(false);
      })
      .catch(() => setLoading(false));
  }, [name, router]);

  if (loading) {
    return (
      <>
        <Navbar />
        <div style={{ paddingTop: 120, textAlign: "center" }}>
          <div className="skeleton" style={{ width: 80, height: 80, borderRadius: "50%", margin: "0 auto 24px" }} />
          <div className="skeleton" style={{ width: 200, height: 32, margin: "0 auto 12px" }} />
          <div className="skeleton" style={{ width: 120, height: 20, margin: "0 auto" }} />
        </div>
      </>
    );
  }

  if (!brand) return null;

  return (
    <>
      <Navbar />
      <div style={{ paddingTop: 80 }}>
        {/* Brand Header */}
        <div
          style={{
            background: "linear-gradient(180deg, rgba(255,107,26,0.10) 0%, transparent 100%)",
            borderBottom: "1px solid var(--border-subtle)",
            padding: "60px 0 40px",
          }}
        >
          <div className="container">
            <Link href="/marques" style={{ color: "var(--text-muted)", fontSize: "0.85rem", display: "inline-flex", alignItems: "center", gap: 6, marginBottom: 24 }}>
              ← Retour aux marques
            </Link>
            <div style={{ display: "flex", alignItems: "center", gap: 28, flexWrap: "wrap" }}>
              <div
                style={{
                  width: 96,
                  height: 96,
                  borderRadius: "50%",
                  background: "var(--bg-glass)",
                  border: "2px solid var(--border-accent)",
                  display: "flex",
                  alignItems: "center",
                  justifyContent: "center",
                  boxShadow: "var(--shadow-glow)",
                  flexShrink: 0,
                }}
              >
                {brand.logo_url ? (
                  // eslint-disable-next-line @next/next/no-img-element
                  <img src={brand.logo_url} alt={brand.name} style={{ width: 60, height: 60, objectFit: "contain" }} />
                ) : (
                  <span style={{ fontSize: "2.5rem" }}>🏭</span>
                )}
              </div>
              <div>
                <div style={{ display: "flex", alignItems: "center", gap: 12, marginBottom: 8 }}>
                  <h1 style={{ margin: 0 }}>{brand.name}</h1>
                  {!brand.is_active && <span className="tag tag-red">Disparue</span>}
                  {brand.is_active && <span className="tag tag-green">Active</span>}
                </div>
                <div style={{ display: "flex", gap: 20, flexWrap: "wrap" }}>
                  {brand.country && (
                    <span style={{ color: "var(--text-secondary)", fontSize: "0.9rem" }}>
                      🌍 {brand.country}
                    </span>
                  )}
                  {brand.founded_year && (
                    <span style={{ color: "var(--text-secondary)", fontSize: "0.9rem" }}>
                      📅 Fondée en {brand.founded_year}
                    </span>
                  )}
                  {brand.founder && (
                    <span style={{ color: "var(--text-secondary)", fontSize: "0.9rem" }}>
                      👤 {brand.founder}
                    </span>
                  )}
                  {brand.headquarters && (
                    <span style={{ color: "var(--text-secondary)", fontSize: "0.9rem" }}>
                      📍 {brand.headquarters}
                    </span>
                  )}
                </div>
              </div>
            </div>
          </div>
        </div>

        {/* Tabs */}
        <div style={{ borderBottom: "1px solid var(--border-subtle)", background: "var(--bg-surface)" }}>
          <div className="container" style={{ display: "flex", gap: 0 }}>
            {(["models", "history"] as const).map((tab) => (
              <button
                key={tab}
                onClick={() => setActiveTab(tab)}
                style={{
                  padding: "16px 24px",
                  background: "none",
                  border: "none",
                  borderBottom: activeTab === tab ? "2px solid var(--accent-primary)" : "2px solid transparent",
                  color: activeTab === tab ? "var(--accent-primary)" : "var(--text-secondary)",
                  fontFamily: "Inter, sans-serif",
                  fontWeight: 600,
                  fontSize: "0.9rem",
                  cursor: "pointer",
                  transition: "color 0.2s",
                }}
              >
                {tab === "models" ? `🚗 Modèles (${brand.models?.length || 0})` : "📖 Histoire"}
              </button>
            ))}
          </div>
        </div>

        {/* Content */}
        <div className="container" style={{ paddingTop: 40, paddingBottom: 80 }}>
          {activeTab === "models" && (
            <>
              {brand.models && brand.models.length > 0 ? (
                <div className="grid-models">
                  {brand.models.map((model, i) => (
                    <Link key={model.id} href={`/modeles/${model.id}`}>
                      <div
                        className="card model-card animate-fadeInUp"
                        style={{ animationDelay: `${Math.min(i * 40, 600)}ms` }}
                      >
                        <ModelThumb src={model.thumbnail_url} alt={`${brand.name} ${model.name}`} />
                        <div className="model-card-body">
                          <div className="model-card-brand">{brand.name}</div>
                          <div className="model-card-name">{model.name} {model.generation !== "I" ? model.generation : ""}</div>
                          <div className="model-card-year">
                            {model.year_start}
                            {model.year_end ? ` – ${model.year_end}` : " – présent"}
                          </div>
                          <div className="model-card-tags">
                            {model.is_iconic && <span className="tag tag-gold">⭐ Iconique</span>}
                            {model.segment && <span className="tag tag-blue">{model.segment}</span>}
                            {model.body_styles?.slice(0, 1).map((s) => (
                              <span key={s} className="tag" style={{ background: "var(--bg-glass)", color: "var(--text-secondary)", border: "1px solid var(--border-subtle)" }}>{s}</span>
                            ))}
                          </div>
                        </div>
                      </div>
                    </Link>
                  ))}
                </div>
              ) : (
                <div style={{ textAlign: "center", padding: "60px 0", color: "var(--text-muted)" }}>
                  <div style={{ fontSize: "3rem", marginBottom: 16 }}>🔍</div>
                  <p>Aucun modèle référencé pour cette marque.</p>
                  <p style={{ fontSize: "0.85rem", marginTop: 8 }}>Lancez l'agent pour collecter les modèles de {brand.name}.</p>
                </div>
              )}
            </>
          )}

          {activeTab === "history" && (
            <div style={{ maxWidth: 800 }}>
              <div className="glass-panel">
                <h2 style={{ marginBottom: 20, color: "var(--accent-primary)" }}>Histoire de {brand.name}</h2>
                {brand.description ? (
                  <p style={{ color: "var(--text-secondary)", lineHeight: 1.9, fontSize: "0.95rem" }}>
                    {brand.description}
                  </p>
                ) : (
                  <p style={{ color: "var(--text-muted)" }}>Aucune information historique disponible.</p>
                )}
              </div>
            </div>
          )}
        </div>
      </div>
    </>
  );
}
