import type { Metadata, Viewport } from "next";
import "./globals.css";
import { Providers } from "@/components/providers";

export const metadata: Metadata = {
  title: "AutoEdit AI",
  description: "Turn a Drive folder of talking-head clips into finished vertical reels.",
};

// viewport-fit=cover so env(safe-area-inset-*) resolves inside the iOS WebView shell.
export const viewport: Viewport = {
  viewportFit: "cover",
  themeColor: "#0f1115",
};

export default function RootLayout({ children }: { children: React.ReactNode }) {
  return (
    <html lang="en">
      <body>
        <Providers>{children}</Providers>
      </body>
    </html>
  );
}
