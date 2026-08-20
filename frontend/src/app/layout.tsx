import type { Metadata } from "next";

export const metadata: Metadata = {
  title: "BFSI AI Agent Console",
  description: "Enterprise AI agent platform for financial institutions",
};

export default function RootLayout({ children }: { children: React.ReactNode }) {
  return (
    <html lang="en">
      <body style={{ margin: 0, fontFamily: "system-ui, sans-serif" }}>
        {children}
      </body>
    </html>
  );
}