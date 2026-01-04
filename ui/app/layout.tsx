import type { Metadata } from "next";
import { Geist_Mono } from "next/font/google";
import "./globals.css";
import { Sidebar } from "@/components/layout/sidebar";
import { Bell } from "lucide-react";

const geistMono = Geist_Mono({
  variable: "--font-mono",
  subsets: ["latin"],
});

export const metadata: Metadata = {
  title: "Hagrid AI | Trading Terminal",
  description: "AI-Powered Trading Interface",
};

export default function RootLayout({
  children,
}: Readonly<{
  children: React.ReactNode;
}>) {
  return (
    <html lang="en" className="dark">
      <body
        className={`${geistMono.variable} antialiased bg-background text-foreground h-screen w-full flex overflow-hidden font-mono`}
      >
        <Sidebar />

        {/* Main Content Area Wrapper */}
        <div className="flex-1 flex flex-col min-w-0 bg-card h-full">
          <header className="h-12 border-b border-border bg-card flex items-center justify-between px-4 shrink-0 z-10">
            <div className="text-xs uppercase font-bold tracking-widest text-muted-foreground">
              {/* This could be dynamic based on route if needed, for now simplified */}
              {'> SYSTEM STATUS: NOMINAL'}
            </div>
            <div className="flex items-center gap-4">
              <button
                className="hover:bg-accent p-2 border border-transparent hover:border-border text-muted-foreground hover:text-foreground transition-colors"
              >
                <Bell size={16} />
              </button>
              <div className="h-4 w-[1px] bg-border"></div>
              <div className="flex items-center gap-2 text-xs text-muted-foreground">
                <span className="w-2 h-2 bg-chart-2 rounded-none animate-pulse" />
                <span>LIVE</span>
              </div>
            </div>
          </header>

          <main className="flex-1 overflow-hidden relative bg-background">
            {children}
          </main>
        </div>
      </body>
    </html>
  );
}
