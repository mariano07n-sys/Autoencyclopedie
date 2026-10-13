"use client";

import { useState } from "react";

export default function ModelThumb({ src, alt }: { src?: string | null; alt: string }) {
  const [broken, setBroken] = useState(false);

  if (src && !broken) {
    return (
      // eslint-disable-next-line @next/next/no-img-element
      <img
        src={src}
        alt={alt}
        className="model-card-image"
        loading="lazy"
        onError={() => setBroken(true)}
      />
    );
  }

  return <div className="model-card-image model-card-image-empty">🚗</div>;
}
