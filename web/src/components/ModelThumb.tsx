"use client";

import { useState } from "react";
import ImageDots from "@/components/ImageDots";

export default function ModelThumb({ src, alt }: { src?: string | null; alt: string }) {
  const [broken, setBroken] = useState(false);
  const [loaded, setLoaded] = useState(false);

  if (src && !broken) {
    return (
      <div className={`model-card-image${loaded ? " is-loaded" : ""}`}>
        {/* eslint-disable-next-line @next/next/no-img-element */}
        <img
          src={src}
          alt={alt}
          className="model-card-img"
          loading="lazy"
          // Une image déjà en cache mémoire n'émet pas toujours d'événement load.
          ref={(node) => {
            if (node?.complete) setLoaded(true);
          }}
          onLoad={() => setLoaded(true)}
          onError={() => setBroken(true)}
        />
        {!loaded && <ImageDots />}
      </div>
    );
  }

  return <div className="model-card-image model-card-image-empty">🚗</div>;
}
