import type { Metadata } from "next";
import { JetBrains_Mono, Playfair_Display, Syne } from "next/font/google";
import "./landing.css";

const playfair = Playfair_Display({
  variable: "--font-playfair",
  subsets: ["latin"],
  display: "swap",
});

const syne = Syne({
  variable: "--font-syne",
  subsets: ["latin"],
  display: "swap",
});

const jetbrains = JetBrains_Mono({
  variable: "--font-jetbrains",
  subsets: ["latin"],
  display: "swap",
});

export const metadata: Metadata = {
  title: "ATTREQ - Your Closet, Curated",
  description:
    "AI-powered outfit suggestions that learn your style. Capture your wardrobe, get daily recommendations, and simplify your mornings.",
  openGraph: {
    title: "ATTREQ - Your Closet, Curated",
    description:
      "AI-powered outfit suggestions that learn your style. Capture your wardrobe, get daily recommendations, and simplify your mornings.",
    type: "website",
  },
};

export default function RootLayout({
  children,
}: Readonly<{
  children: React.ReactNode;
}>) {
  return (
    <html lang="en" className={`${playfair.variable} ${syne.variable} ${jetbrains.variable}`}>
      <body>
        {children}
      </body>
    </html>
  );
}
