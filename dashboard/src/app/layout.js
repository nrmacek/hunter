import "./globals.css";

export const metadata = {
  title: "Hunter — Trelity Prospect Dashboard",
  description:
    "AI-powered prospect evaluation and ranking tool for Trelity Inc.",
};

export default function RootLayout({ children }) {
  return (
    <html lang="en">
      <body>{children}</body>
    </html>
  );
}
