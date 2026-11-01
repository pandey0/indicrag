import type { ReactNode } from "react";

export const metadata = {
  title: "IndicRAG",
  description: "Ask about Indian citizen services in English, Hindi or Kannada, with cited sources.",
};

export default function RootLayout({ children }: { children: ReactNode }) {
  return (
    <html lang="en">
      <body style={{ fontFamily: "system-ui, 'Noto Sans Devanagari', 'Noto Sans Kannada', sans-serif", margin: 0, background: "#fafafa", color: "#111" }}>
        {children}
      </body>
    </html>
  );
}
