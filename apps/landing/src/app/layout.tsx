import type { Metadata } from "next";
import { Cormorant_Garamond, DM_Sans, IBM_Plex_Mono } from "next/font/google";
import "./landing.css";

const cormorant = Cormorant_Garamond({
  variable: "--font-display",
  subsets: ["latin"],
  weight: ["400", "500", "600"],
  style: ["normal", "italic"],
  display: "swap",
});

const dmSans = DM_Sans({
  variable: "--font-body",
  subsets: ["latin"],
  display: "swap",
});

const plexMono = IBM_Plex_Mono({
  variable: "--font-mono",
  subsets: ["latin"],
  weight: ["400", "500"],
  display: "swap",
});

export const metadata: Metadata = {
  title: "ATTREQ — Your closet, curated",
  description:
    "ATTREQ learns your taste, checks the weather, and lays out morning looks made only from clothes you already own.",
  openGraph: {
    title: "ATTREQ — Your closet, curated",
    description:
      "ATTREQ learns your taste, checks the weather, and lays out morning looks made only from clothes you already own.",
    type: "website",
  },
};

export default function RootLayout({
  children,
}: Readonly<{
  children: React.ReactNode;
}>) {
  return (
    <html lang="en" className={`${cormorant.variable} ${dmSans.variable} ${plexMono.variable}`}>
      <body>
        {children}
      </body>
    </html>
  );
}
