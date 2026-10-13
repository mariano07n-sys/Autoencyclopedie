"use client";

export default function BlurWords({
  text,
  className,
  baseDelay = 0.5,
  stagger = 0.1,
}: {
  text: string;
  className?: string;
  baseDelay?: number;
  stagger?: number;
}) {
  const words = text.split(" ");
  return (
    <span className={`blur-text-container ${className ?? ""}`}>
      {words.map((word, i) => (
        <span
          key={i}
          className="blur-word"
          style={{ transitionDelay: `${i * stagger + baseDelay}s` }}
        >
          {word}{" "}
        </span>
      ))}
    </span>
  );
}
