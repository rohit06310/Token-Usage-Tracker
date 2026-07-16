import type { Metadata } from "next";
import { Inter } from "next/font/google";
import "./globals.css";

const inter = Inter({
  subsets: ["latin"],
  variable: "--font-inter",
  display: "swap",
});

export const metadata: Metadata = {
  title: {
    default: "AI Usage Dashboard",
    template: "%s | AI Usage Dashboard",
  },
  description:
    "Unified dashboard for tracking LLM token usage, costs, and rate limits across OpenAI, Anthropic, Groq, and Gemini.",
  robots: "noindex, nofollow", // Internal tool
};

export default function RootLayout({ children }: { children: React.ReactNode }) {
  return (
    <html lang="en" className={inter.variable}>
      <body className="min-h-screen antialiased">{children}</body>
    </html>
  );
}
