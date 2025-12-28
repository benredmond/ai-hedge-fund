import type { Metadata } from "next";
import localFont from "next/font/local";
import "./globals.css";

const commitMono = localFont({
  src: "../../public/fonts/CommitMono-400-Regular.otf",
  variable: "--font-commit-mono",
  weight: "400",
});

const satoshi = localFont({
  src: [
    { path: "../../public/fonts/Satoshi-Regular.woff2", weight: "400" },
    { path: "../../public/fonts/Satoshi-Medium.woff2", weight: "500" },
    { path: "../../public/fonts/Satoshi-Bold.woff2", weight: "700" },
  ],
  variable: "--font-satoshi",
});

const sentient = localFont({
  src: "../../public/fonts/Sentient-Regular.woff2",
  variable: "--font-sentient",
  weight: "400",
});

export const metadata: Metadata = {
  title: "AI Strategy Cohort",
  description: "Track AI-generated trading strategy performance",
};

export default function RootLayout({
  children,
}: Readonly<{
  children: React.ReactNode;
}>) {
  return (
    <html lang="en">
      <body
        className={`${commitMono.variable} ${satoshi.variable} ${sentient.variable} antialiased bg-background text-foreground`}
      >
        {children}
      </body>
    </html>
  );
}
