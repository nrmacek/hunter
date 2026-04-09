import { Nunito_Sans, Signika_Negative } from "next/font/google";
import "./globals.css";

const nunitoSans = Nunito_Sans({
  subsets: ["latin"],
  weight: ["400", "500", "600"],
  variable: "--font-body",
});

const signikaNegative = Signika_Negative({
  subsets: ["latin"],
  weight: ["400", "600", "700"],
  variable: "--font-heading",
});

export const metadata = {
  title: "Trelity Prospect Scout",
  description:
    "AI-powered prospect evaluation and ranking tool for Trelity Inc.",
};

export default function RootLayout({ children }) {
  return (
    <html lang="en" className={`${nunitoSans.variable} ${signikaNegative.variable}`}>
      <body>{children}</body>
    </html>
  );
}
