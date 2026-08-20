import type { Metadata } from "next";
import "./globals.css";

export const metadata: Metadata = {
  title: "Macro Report",
  description: "FRED 宏观数据仪表板",
};

export default function RootLayout({ children }: { children: React.ReactNode }) {
  return (
    <html lang="zh">
      <body className="bg-gray-50 min-h-screen">{children}</body>
    </html>
  );
}
