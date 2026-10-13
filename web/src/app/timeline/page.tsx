"use client";

import { useState, useEffect } from "react";
import Link from "next/link";
import Navbar from "@/components/Navbar";
import ModelThumb from "@/components/ModelThumb";
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
}

interface Decade {
  decade: number;
  models: Model[];
}

export default function TimelinePage() {
  const [decades, setDecades] = useState<Decade[]>([]);
  const [total, setTotal] = useState(0);
  const [loading, setLoading] = useState(true);
  const [selected, setSelected] = useState<number | null>(null);

  useEffect(() => {
    fetch("/api/timeline")
      .then((r) => r.json())
      .then((data) => {
        setDecades(data.decades || []);
        setTotal(data.total || 0);
        setLoading(false);
      })
      .catch(() => setLoading(false));
  }, []);

  const visible = selected ? decades.filter((d) => d.decade === selected) : decades;

  return (
    <>
      <Navbar />
      <Reveal />
      <div style={{ paddingTop: 100 }}>
        <div className="container">
          <div className="section-header animate-fadeInUp">
            <span className="section-label">Chronologie</span>
            <h1 className="section-title">L&apos;histoire modèle par modèle</h1>
            <p className="section-subtitle">
              {loading
                ? "Chargement..."
                : `${total} modèles répartis sur ${decades.length} décennies, de 1886 à nos jours`}
            </p>
          </div>

          {!loading && decades.length > 0 && (
            <div className="decade-nav animate-fadeInUp">
              <button
                type="button"
                className={`decade-chip ${selected === null ? "active" : ""}`}
                onClick={() => setSelected(null)}
              >
                Toutes les décennies
              </button>
              {decades.map((d) => (
                <button
                  key={d.decade}
                  type="button"
                  className={`decade-chip ${selected === d.decade ? "active" : ""}`}
                  onClick={() => setSelected(d.decade)}
                >
                  {d.decade}s
                </button>
              ))}
            </div>
          )}

          {loading ? (
            <div className="timeline">
              {[0, 1, 2].map((i) => (
                <div key={i} className="skeleton" style={{ height: 340, marginBottom: 32 }} />
              ))}
            </div>
          ) : visible.length > 0 ? (
            <div className="timeline">
              {visible.map((d) => (
                <section className="timeline-decade" key={d.decade}>
                  <div className="timeline-marker reveal-element">
                    <span className="timeline-dot" />
                    <div className="timeline-year">{d.decade}</div>
                    <div className="timeline-count">
                      {d.models.length} modèle{d.models.length > 1 ? "s" : ""}
                    </div>
                  </div>
                  <div className="grid-models">
                    {d.models.map((model) => (
                      <Link key={model.id} href={`/modeles/${model.id}`}>
                        <div className="card model-card">
                          <ModelThumb src={model.thumbnail_url} alt={`${model.brand_name} ${model.name}`} />
                          <div className="model-card-body">
                            <div className="model-card-brand">{model.brand_name}</div>
                            <div className="model-card-name">{model.name}</div>
                            <div className="model-card-year">
                              {model.year_start}
                              {model.year_end ? ` – ${model.year_end}` : " – présent"}
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
                </section>
              ))}
            </div>
          ) : (
            <div style={{ textAlign: "center", padding: "64px 0", color: "var(--text-muted)" }}>
              <div style={{ fontSize: "3rem", marginBottom: 16 }}>🕰️</div>
              <p>
                Aucun modèle daté en base. Lancez l&apos;agent IA pour collecter les modèles et leurs
                années de production.
              </p>
            </div>
          )}
        </div>
      </div>
    </>
  );
}
