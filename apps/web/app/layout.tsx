import type { Metadata } from "next";
import "./globals.css";

export const metadata: Metadata = {
  title: "AgriFlow — Honest European agri-data middleware",
  description:
    "Price transparency, voluntary provenance, and warm introductions for fresh produce + EVOO across Spain, Italy, and Germany.",
  metadataBase: new URL("https://agriflow.eu"),
  openGraph: {
    title: "AgriFlow",
    description: "Honest European agri-data middleware",
    type: "website",
    locale: "en",
  },
};

export default function RootLayout({ children }: { children: React.ReactNode }) {
  return (
    <html lang="en">
      <body className="antialiased">{children}</body>
    </html>
  );
}
