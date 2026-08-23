import type { Metadata } from "next";
import { DM_Sans, Fraunces } from "next/font/google";
import "./globals.css";

const sans = DM_Sans({
  subsets: ["latin"],
  variable: "--font-dm-sans",
});

const serif = Fraunces({
  subsets: ["latin"],
  variable: "--font-fraunces",
});

export const metadata: Metadata = {
  title: "Estate Portal · Probate Guardians TN",
  description:
    "A calm place for executors, heirs, and probate attorneys to stay aligned during the sale of an inherited home in Middle Tennessee.",
  icons: {
    icon: "/images/favicon-32.png",
    apple: "/images/pg-logo.png",
  },
};

export default function RootLayout({ children }: { children: React.ReactNode }) {
  return (
    <html lang="en">
      <body className={`${sans.variable} ${serif.variable} bg-cream text-forest antialiased`}>
        {children}
      </body>
    </html>
  );
}
