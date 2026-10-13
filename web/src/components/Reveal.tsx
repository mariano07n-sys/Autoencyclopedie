"use client";

import { useEffect } from "react";

export default function Reveal() {
  useEffect(() => {
    const io = new IntersectionObserver(
      (entries) => {
        for (const e of entries) {
          if (e.isIntersecting) {
            e.target.classList.add("is-visible");
            io.unobserve(e.target);
          }
        }
      },
      { threshold: 0, rootMargin: "0px 0px -60px 0px" }
    );
    document
      .querySelectorAll(".reveal-element:not(.is-visible), .blur-text-container:not(.is-visible)")
      .forEach((el) => io.observe(el));
    return () => io.disconnect();
  });

  return null;
}
