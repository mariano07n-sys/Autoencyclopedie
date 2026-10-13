import type { Metadata } from "next";
import "./globals.css";

export const metadata: Metadata = {
  title: "AutoEncyclopédie — Toutes les marques et modèles depuis 1886",
  description:
    "L'encyclopédie automobile complète : explorez toutes les marques et modèles de voitures depuis la naissance de l'automobile en 1886 jusqu'à aujourd'hui. Fiches techniques, photos, histoires et anecdotes.",
  keywords: [
    "encyclopédie automobile",
    "marques de voiture",
    "modèles de voiture",
    "histoire automobile",
    "fiches techniques",
    "voitures historiques",
  ],
  openGraph: {
    title: "AutoEncyclopédie — Toutes les marques et modèles",
    description:
      "L'encyclopédie automobile mondiale depuis 1886.",
    type: "website",
  },
};

export default function RootLayout({
  children,
}: {
  children: React.ReactNode;
}) {
  return (
    <html lang="fr">
      <body>{children}</body>
    </html>
  );
}
