"use client";

import { useState, useEffect } from "react";
import { useParams, useRouter } from "next/navigation";
import Link from "next/link";
import Navbar from "@/components/Navbar";
import PageLoader from "@/components/PageLoader";
import ImageDots from "@/components/ImageDots";

interface Spec {
  id: number;
  variant_name: string;
  engine_type: string;
  fuel_type: string;
  power_hp: number;
  power_kw: number;
  torque_nm: number;
  transmission: string;
  drive_type: string;
  engine_displacement: number;
  cylinders: number;
  acceleration_0_100: number;
  top_speed: number;
  fuel_consumption: number;
  co2_emissions: number;
  weight_kg: number;
  length_mm: number;
  width_mm: number;
  height_mm: number;
  wheelbase_mm: number;
  trunk_volume: number;
  range_km: number | null;
  price_launch_eur: number | null;
}

interface Model {
  id: number;
  name: string;
  generation: string;
  brand_name: string;
  year_start: number | null;
  year_end: number | null;
  body_styles: string[];
  segment: string;
  description: string;
  anecdotes: string;
  image_urls: string[];
  thumbnail_url: string;
  countries: string[];
  is_iconic: boolean;
  specs: Spec[];
}

// Le remontage par `key` réarme l'état de chargement à chaque image de la
// galerie : un effet qui remettrait l'indicateur à zéro serait interdit ici.
function HeroImage({ src, alt }: { src: string; alt: string }) {
  const [loaded, setLoaded] = useState(false);
  return (
    <>
      {/* eslint-disable-next-line @next/next/no-img-element */}
      <img
        src={src}
        alt={alt}
        className={`model-card-img${loaded ? " is-loaded" : ""}`}
        ref={(node) => {
          if (node?.complete) setLoaded(true);
        }}
        onLoad={() => setLoaded(true)}
        onError={(e) => {
          e.currentTarget.style.visibility = "hidden";
          // Une URL morte ne déclenche jamais onLoad : sans ceci les gouttes
          // tourneraient indéfiniment sur une image invisible.
          setLoaded(true);
        }}
      />
      {!loaded && <ImageDots />}
    </>
  );
}

export default function ModelPage() {
  const { id } = useParams<{ id: string }>();
  const router = useRouter();
  const [model, setModel] = useState<Model | null>(null);
  const [loading, setLoading] = useState(true);
  const [activeSpec, setActiveSpec] = useState(0);
  const [activeImage, setActiveImage] = useState(0);

  useEffect(() => {
    fetch(`/api/models/${id}`)
      .then((r) => r.json())
      .then((data) => {
        if (data.error) router.push("/modeles");
        else setModel(data);
        setLoading(false);
      })
      .catch(() => setLoading(false));
  }, [id, router]);

  if (loading) {
    return (
      <>
        <Navbar />
        <PageLoader />
      </>
    );
  }

  if (!model) return null;

  const images = model.image_urls?.length ? model.image_urls : model.thumbnail_url ? [model.thumbnail_url] : [];
  const spec = model.specs?.[activeSpec];

  return (
    <>
      <Navbar />
      <div className="page-offset">
        {/* Image gallery */}
        {images.length > 0 && (
          <div
            style={{
              position: "relative",
              height: "clamp(280px, 45vw, 520px)",
              background: "var(--bg-surface)",
              overflow: "hidden",
            }}
          >
            <HeroImage
              key={activeImage}
              src={images[activeImage]}
              alt={`${model.brand_name} ${model.name}`}
            />
            <div
              style={{
                position: "absolute",
                inset: 0,
                background: "linear-gradient(to top, rgba(20,22,25,0.85) 0%, transparent 50%)",
              }}
            />
            {images.length > 1 && (
              <>
                <button
                  type="button"
                  className="gallery-arrow gallery-arrow-left"
                  aria-label="Image précédente"
                  onClick={() => setActiveImage((activeImage - 1 + images.length) % images.length)}
                >
                  <svg viewBox="0 0 24 24" width="22" height="22" stroke="currentColor" strokeWidth="2" fill="none"><path d="M15 18l-6-6 6-6" /></svg>
                </button>
                <button
                  type="button"
                  className="gallery-arrow gallery-arrow-right"
                  aria-label="Image suivante"
                  onClick={() => setActiveImage((activeImage + 1) % images.length)}
                >
                  <svg viewBox="0 0 24 24" width="22" height="22" stroke="currentColor" strokeWidth="2" fill="none"><path d="M9 18l6-6-6-6" /></svg>
                </button>
                <span className="gallery-counter">
                  {activeImage + 1} / {images.length}
                </span>
              </>
            )}
            {images.length > 1 && (
              <div
                style={{
                  position: "absolute",
                  bottom: 20,
                  left: "50%",
                  transform: "translateX(-50%)",
                  display: "flex",
                  gap: 8,
                }}
              >
                {images.map((_, i) => (
                  <button
                    key={i}
                    onClick={() => setActiveImage(i)}
                    style={{
                      width: i === activeImage ? 24 : 8,
                      height: 8,
                      borderRadius: 4,
                      background: i === activeImage ? "var(--accent-primary)" : "rgba(237,240,242,0.35)",
                      border: "none",
                      cursor: "pointer",
                      transition: "all 0.3s",
                    }}
                  />
                ))}
              </div>
            )}
          </div>
        )}

        <div className="container" style={{ paddingTop: 40, paddingBottom: 80 }}>
          {/* Breadcrumb */}
          <div className="breadcrumb">
            <Link href="/marques" style={{ color: "var(--accent-primary)" }}>Marques</Link>
            <span>›</span>
            <Link href={`/marques/${encodeURIComponent(model.brand_name)}`} style={{ color: "var(--accent-primary)" }}>
              {model.brand_name}
            </Link>
            <span>›</span>
            <span>{model.name}</span>
          </div>

          <div className="model-layout">
            {/* Main column */}
            <div>
              {/* Title */}
              <div style={{ marginBottom: 32 }}>
                <div style={{ display: "flex", gap: 10, marginBottom: 12, flexWrap: "wrap" }}>
                  {model.is_iconic && <span className="tag tag-gold">⭐ Modèle Iconique</span>}
                  {model.segment && <span className="tag tag-blue">{model.segment}</span>}
                  {model.body_styles?.map((s) => (
                    <span key={s} className="tag" style={{ background: "var(--bg-glass)", color: "var(--text-secondary)", border: "1px solid var(--border-subtle)" }}>{s}</span>
                  ))}
                </div>
                <h1 style={{ marginBottom: 8 }}>
                  {model.brand_name} {model.name}
                  {model.generation && model.generation !== "I" && (
                    <span style={{ color: "var(--accent-primary)", marginLeft: 12, fontSize: "0.7em" }}>
                      {model.generation}
                    </span>
                  )}
                </h1>
                <p style={{ color: "var(--text-secondary)", fontSize: "1.1rem" }}>
                  {model.year_start ?? "Année inconnue"}
                  {model.year_start && (model.year_end ? ` – ${model.year_end}` : " – aujourd'hui")}
                  {model.countries?.length > 0 && (
                    <span style={{ marginLeft: 16, color: "var(--text-muted)" }}>
                      🌍 {model.countries.slice(0, 3).join(", ")}
                      {model.countries.length > 3 && ` +${model.countries.length - 3}`}
                    </span>
                  )}
                </p>
              </div>

              {/* Description */}
              {model.description && (
                <div className="glass-panel" style={{ marginBottom: 24 }}>
                  <h3 style={{ marginBottom: 16, color: "var(--accent-primary)" }}>À propos</h3>
                  <p style={{ color: "var(--text-secondary)", lineHeight: 1.9, fontSize: "0.95rem" }}>
                    {model.description}
                  </p>
                </div>
              )}

              {/* Anecdotes */}
              {model.anecdotes && (
                <div className="glass-panel" style={{ marginBottom: 24, borderColor: "var(--border-accent)" }}>
                  <h3 style={{ marginBottom: 16, color: "var(--accent-primary)" }}>⚡ Le savais-tu ?</h3>
                  <p style={{ color: "var(--text-secondary)", lineHeight: 1.9, fontStyle: "italic" }}>
                    {model.anecdotes}
                  </p>
                </div>
              )}

              {/* Specs tabs */}
              {model.specs && model.specs.length > 0 && (
                <div>
                  <h2 style={{ marginBottom: 20 }}>Fiches techniques</h2>
                  {/* Variant selector */}
                  {model.specs.length > 1 && (
                    <div style={{ display: "flex", gap: 8, flexWrap: "wrap", marginBottom: 20 }}>
                      {model.specs.map((s, i) => (
                        <button
                          key={s.id}
                          onClick={() => setActiveSpec(i)}
                          className={`tag ${i === activeSpec ? "tag-gold" : ""}`}
                          style={{
                            cursor: "pointer",
                            border: i === activeSpec ? "1px solid rgba(255,107,26,0.45)" : "1px solid var(--border-subtle)",
                            background: i === activeSpec ? "rgba(255,107,26,0.16)" : "var(--bg-glass)",
                            color: i === activeSpec ? "var(--accent-primary)" : "var(--text-secondary)",
                            padding: "6px 14px",
                            borderRadius: "50px",
                            fontFamily: "Inter, sans-serif",
                            fontSize: "0.8rem",
                            fontWeight: 600,
                          }}
                        >
                          {s.variant_name}
                        </button>
                      ))}
                    </div>
                  )}

                  {spec && <SpecTable spec={spec} />}
                </div>
              )}
            </div>

            {/* Sidebar */}
            <div className="model-aside">
              <div className="glass-panel">
                <h3 style={{ marginBottom: 20, fontSize: "1rem" }}>Informations rapides</h3>
                {[
                  { label: "Marque", value: model.brand_name },
                  { label: "Modèle", value: model.name },
                  { label: "Génération", value: model.generation },
                  { label: "Production", value: model.year_start ? (model.year_end ? `${model.year_start} – ${model.year_end}` : `${model.year_start} – présent`) : null },
                  { label: "Segment", value: model.segment },
                  { label: "Carrosseries", value: model.body_styles?.join(", ") },
                  { label: "Marchés", value: model.countries?.slice(0, 5).join(", ") },
                ].filter((r) => r.value).map((row) => (
                  <div
                    key={row.label}
                    style={{
                      display: "flex",
                      justifyContent: "space-between",
                      padding: "10px 0",
                      borderBottom: "1px solid var(--border-subtle)",
                      fontSize: "0.875rem",
                      gap: 12,
                    }}
                  >
                    <span style={{ color: "var(--text-muted)" }}>{row.label}</span>
                    <span style={{ color: "var(--text-primary)", textAlign: "right" }}>{row.value}</span>
                  </div>
                ))}
              </div>
            </div>
          </div>
        </div>
      </div>
    </>
  );
}

function SpecTable({ spec }: { spec: Spec }) {
  const rows: { label: string; value: string | number | null; unit?: string; icon?: string }[] = [
    { icon: "⚡", label: "Type de moteur", value: spec.engine_type },
    { icon: "⛽", label: "Carburant", value: spec.fuel_type },
    { icon: "🔢", label: "Cylindrée", value: spec.engine_displacement, unit: "L" },
    { icon: "🔩", label: "Cylindres", value: spec.cylinders },
    { icon: "💪", label: "Puissance", value: spec.power_hp ? `${spec.power_hp} ch (${spec.power_kw} kW)` : null },
    { icon: "🔄", label: "Couple", value: spec.torque_nm, unit: "Nm" },
    { icon: "🕹", label: "Transmission", value: spec.transmission },
    { icon: "🛞", label: "Traction", value: spec.drive_type },
    { icon: "🏎", label: "0 à 100 km/h", value: spec.acceleration_0_100, unit: "s" },
    { icon: "🚀", label: "Vitesse max", value: spec.top_speed, unit: "km/h" },
    { icon: "🛢", label: "Consommation mixte", value: spec.fuel_consumption, unit: spec.engine_type === "Électrique" ? "kWh/100km" : "L/100km" },
    { icon: "🌿", label: "CO₂", value: spec.co2_emissions, unit: "g/km" },
    { icon: "⚖️", label: "Poids", value: spec.weight_kg, unit: "kg" },
    { icon: "📏", label: "Longueur", value: spec.length_mm, unit: "mm" },
    { icon: "↔️", label: "Largeur", value: spec.width_mm, unit: "mm" },
    { icon: "📐", label: "Hauteur", value: spec.height_mm, unit: "mm" },
    { icon: "🔧", label: "Empattement", value: spec.wheelbase_mm, unit: "mm" },
    { icon: "🧳", label: "Coffre", value: spec.trunk_volume, unit: "L" },
    { icon: "🔋", label: "Autonomie", value: spec.range_km, unit: "km" },
    { icon: "💶", label: "Prix de lancement", value: spec.price_launch_eur ? new Intl.NumberFormat("fr-FR", { style: "currency", currency: "EUR" }).format(spec.price_launch_eur) : null },
  ];

  return (
    <div className="glass-panel">
      <h4 style={{ marginBottom: 16, color: "var(--accent-primary)", fontSize: "0.9rem" }}>
        {spec.variant_name}
      </h4>
      <div className="specs-grid">
        {rows.filter((r) => r.value !== null && r.value !== undefined && r.value !== 0).map((row) => (
          <div
            key={row.label}
            style={{
              display: "flex",
              justifyContent: "space-between",
              alignItems: "center",
              padding: "10px 12px",
              borderRadius: "var(--radius-sm)",
              transition: "background 0.15s",
            }}
            onMouseEnter={(e) => (e.currentTarget.style.background = "var(--bg-card)")}
            onMouseLeave={(e) => (e.currentTarget.style.background = "transparent")}
          >
            <span style={{ color: "var(--text-muted)", fontSize: "0.8rem" }}>
              {row.icon} {row.label}
            </span>
            <span style={{ color: "var(--text-primary)", fontWeight: 600, fontSize: "0.85rem" }}>
              {row.value}{row.unit && typeof row.value === "number" ? ` ${row.unit}` : ""}
            </span>
          </div>
        ))}
      </div>
    </div>
  );
}
