export default function PageLoader({ label = "Chargement de la page…" }: { label?: string }) {
  return (
    <div className="page-loader" role="status" aria-live="polite">
      <div className="page-loader-spinner" aria-hidden="true">
        {Array.from({ length: 6 }).map((_, i) => (
          <span key={i} />
        ))}
      </div>
      <p className="page-loader-label">{label}</p>
    </div>
  );
}
