export default function ImageDots({ label = "Chargement de l'image…" }: { label?: string }) {
  return (
    <div className="image-dots" role="status" aria-label={label}>
      {[0, 1, 2, 3, 4].map((i) => (
        <span key={i} />
      ))}
    </div>
  );
}
