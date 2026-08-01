import "./globals.css";

export const metadata = {
  title: "loopLamp Dashboard",
  description: "Minimal dashboard UI for loopLamp domain reports.",
};

export default function RootLayout({ children }) {
  return (
    <html lang="en">
      <body>{children}</body>
    </html>
  );
}
