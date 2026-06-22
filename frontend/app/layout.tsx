import type { Metadata } from "next";
import "./globals.css";

export const metadata: Metadata = {
  title: "docuchat",
  description: "Chat with your documents. Answers with citations.",
};

export default function RootLayout({ children }: { children: React.ReactNode }) {
  return (
    <html lang="en">
      <body>{children}</body>
    </html>
  );
}
