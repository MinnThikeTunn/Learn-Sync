import type { Metadata } from "next";
import "./globals.css";

export const metadata: Metadata = {
  title: "LearnSync AI | Context-Aware Adaptive Co-Pilot",
  description: "High-end adaptive learning co-pilot, virtual folder resource manager, and workload co-pilot.",
};

export default function RootLayout({
  children,
}: {
  children: React.ReactNode;
}) {
  return (
    <html lang="en" className="dark">
      <body className="min-h-screen bg-obsidian-950 font-sans text-slate-100 flex flex-col">
        {children}
      </body>
    </html>
  );
}
