import type { Metadata } from "next";
import "./globals.css";
import { ThemeProvider } from "@/components/ui/ThemeProvider";
import { GlobalChatbot } from "@/components/ui/GlobalChatbot";

export const metadata: Metadata = {
  title: "FiltreLAB",
  description: "Yapay zeka destekli akıllı alışveriş filtresi",
};

export default function RootLayout({
  children,
}: Readonly<{
  children: React.ReactNode;
}>) {
  return (
    <html lang="tr" suppressHydrationWarning>
      <body className="min-h-screen flex flex-col antialiased">
        <ThemeProvider>
          {children}
          <GlobalChatbot />
        </ThemeProvider>
      </body>
    </html>
  );
}
