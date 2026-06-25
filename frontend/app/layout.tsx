import "./globals.css";
import type { Metadata } from "next";

export const metadata: Metadata = {
  title: "Sistema de Decisao Financeira",
  description: "Base inicial do sistema de decisao financeira pessoal.",
};

export default function RootLayout({
  children,
}: Readonly<{
  children: React.ReactNode;
}>) {
  return (
    <html lang="pt-BR">
      <body>{children}</body>
    </html>
  );
}
