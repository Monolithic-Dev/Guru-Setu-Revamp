import type { Metadata, Viewport } from "next";
import localFont from "next/font/local";
import "./globals.css";

// Local font files only: the demo runs offline (no CDN fonts).
const geistSans = localFont({
  src: "./fonts/GeistVF.woff",
  variable: "--font-geist-sans",
  weight: "100 900",
});

export const metadata: Metadata = {
  title: "GuruSetu",
  description: "Verified mentorship: certificates, fit checks and mentoring records for one department.",
};

export const viewport: Viewport = {
  width: "device-width",
  initialScale: 1,
  themeColor: "#8C1515",
};

export default function RootLayout({ children }: Readonly<{ children: React.ReactNode }>) {
  return (
    <html lang="en">
      <body className={geistSans.variable}>{children}</body>
    </html>
  );
}
