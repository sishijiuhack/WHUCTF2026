import "./globals.css";
import type { Metadata } from "next";

export const metadata: Metadata = {
  title: "Hell City Intranet",
  description: "Internal Next.js service for the Hell City challenge",
};

export default function RootLayout({
  children,
}: Readonly<{
  children: React.ReactNode;
}>) {
  return (
    <html lang="zh-CN">
      <body>{children}</body>
    </html>
  );
}
