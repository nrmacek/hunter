import "./globals.css";

export const metadata = {
  title: "Trelity Prospect Scout",
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
