"use client";

import { useState, useEffect, useRef } from "react";
import Link from "next/link";

interface SearchResult {
  brands: { id: number; name: string; country: string }[];
  models: { id: number; name: string; brand_name: string; year_start: number }[];
}

export default function Navbar() {
  const [query, setQuery] = useState("");
  const [results, setResults] = useState<SearchResult | null>(null);
  const [loading, setLoading] = useState(false);
  const [open, setOpen] = useState(false);
  const ref = useRef<HTMLDivElement>(null);

  useEffect(() => {
    const handler = (e: MouseEvent) => {
      if (ref.current && !ref.current.contains(e.target as Node)) {
        setOpen(false);
      }
    };
    document.addEventListener("mousedown", handler);
    return () => document.removeEventListener("mousedown", handler);
  }, []);

  useEffect(() => {
    if (query.length < 2) {
      setResults(null);
      setOpen(false);
      return;
    }
    const timer = setTimeout(async () => {
      setLoading(true);
      try {
        const res = await fetch(`/api/search?q=${encodeURIComponent(query)}`);
        const data = await res.json();
        setResults(data);
        setOpen(true);
      } catch {
        /* ignore */
      } finally {
        setLoading(false);
      }
    }, 300);
    return () => clearTimeout(timer);
  }, [query]);

  return (
    <nav className="navbar">
      <div className="navbar-inner reveal-element">
        {/* Logo */}
        <Link href="/" className="navbar-logo">
          <span className="logo-icon">a</span>
          <span className="logo-text">AutoEncyclopédie</span>
        </Link>

        {/* Search */}
        <div className="navbar-search" ref={ref}>
          <span className="search-icon">🔍</span>
          <input
            id="navbar-search"
            type="text"
            placeholder="Rechercher une marque ou un modèle..."
            value={query}
            onChange={(e) => setQuery(e.target.value)}
            onFocus={() => results && setOpen(true)}
            autoComplete="off"
          />
          {open && results && (
            <div className="search-dropdown animate-fadeIn">
              {results.brands.length > 0 && (
                <>
                  <div style={{ padding: "8px 16px 4px", fontSize: "0.7rem", color: "var(--text-muted)", textTransform: "uppercase", letterSpacing: "0.1em", fontWeight: 700 }}>
                    Marques
                  </div>
                  {results.brands.map((b) => (
                    <Link
                      key={b.id}
                      href={`/marques/${encodeURIComponent(b.name)}`}
                      className="search-dropdown-item"
                      onClick={() => setOpen(false)}
                    >
                      <span style={{ fontSize: "1.2rem" }}>🏭</span>
                      <div>
                        <div style={{ fontWeight: 600, fontSize: "0.9rem" }}>{b.name}</div>
                        <div style={{ fontSize: "0.75rem", color: "var(--text-muted)" }}>{b.country}</div>
                      </div>
                    </Link>
                  ))}
                </>
              )}
              {results.models.length > 0 && (
                <>
                  <div style={{ padding: "8px 16px 4px", fontSize: "0.7rem", color: "var(--text-muted)", textTransform: "uppercase", letterSpacing: "0.1em", fontWeight: 700 }}>
                    Modèles
                  </div>
                  {results.models.slice(0, 6).map((m) => (
                    <Link
                      key={m.id}
                      href={`/modeles/${m.id}`}
                      className="search-dropdown-item"
                      onClick={() => setOpen(false)}
                    >
                      <span style={{ fontSize: "1.2rem" }}>🚗</span>
                      <div>
                        <div style={{ fontWeight: 600, fontSize: "0.9rem" }}>{m.brand_name} {m.name}</div>
                        <div style={{ fontSize: "0.75rem", color: "var(--text-muted)" }}>{m.year_start}</div>
                      </div>
                    </Link>
                  ))}
                </>
              )}
              {results.brands.length === 0 && results.models.length === 0 && (
                <div style={{ padding: "16px", color: "var(--text-muted)", textAlign: "center", fontSize: "0.85rem" }}>
                  Aucun résultat pour « {query} »
                </div>
              )}
            </div>
          )}
        </div>

        {/* Nav Links */}
        <nav className="navbar-nav">
          <Link href="/" className="nav-link">Accueil</Link>
          <Link href="/marques" className="nav-link">Marques</Link>
          <Link href="/modeles" className="nav-link">Modèles</Link>
          <Link href="/timeline" className="nav-link">Timeline</Link>
        </nav>
      </div>
    </nav>
  );
}
