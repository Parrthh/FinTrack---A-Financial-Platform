import type { Metadata } from "next";
import "./globals.css";

import { AuthProvider } from "@/lib/auth-context";

export const metadata: Metadata = {
  title: "FinTrack — Market intelligence, personalized",
  description:
    "Track stocks, ETFs, and crypto with daily news intelligence that flags real company progress.",
};

export default function RootLayout({
  children,
}: Readonly<{
  children: React.ReactNode;
}>) {
  return (
    <html lang="en" className="h-full antialiased">
      <body className="min-h-full flex flex-col bg-slate-950 text-slate-100">
        <AuthProvider>{children}</AuthProvider>
      </body>
    </html>
  );
}
