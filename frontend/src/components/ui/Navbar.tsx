"use client";

import { motion } from "framer-motion";
import { User, Sun, Moon, LogOut, Heart, History, IdCard } from "lucide-react";
import Link from "next/link";
import { useEffect, useState } from "react";
import { useRouter } from "next/navigation";
import { AuthModal } from "./AuthModal";
import { useTheme } from "./ThemeProvider";
import { getMe, logoutUser, type AuthUser } from "@/lib/apiClient";

const MONTHS_TR = ["OCA", "ŞUB", "MAR", "NİS", "MAY", "HAZ", "TEM", "AĞU", "EYL", "EKİ", "KAS", "ARA"];

export function Navbar() {
  const [isAuthOpen, setIsAuthOpen] = useState(false);
  const [isProfileOpen, setIsProfileOpen] = useState(false);
  const [logoutMessage, setLogoutMessage] = useState<string | null>(null);
  const [user, setUser] = useState<AuthUser | null>(null);
  const [mounted, setMounted] = useState(false);
  const [today, setToday] = useState("");
  const { theme, setTheme } = useTheme();
  const router = useRouter();

  useEffect(() => {
    const timer = window.setTimeout(() => {
      setMounted(true);
      const d = new Date();
      setToday(`${d.getDate()} ${MONTHS_TR[d.getMonth()]} ${d.getFullYear()}`);
    }, 0);
    return () => window.clearTimeout(timer);
  }, []);

  useEffect(() => {
    const loadUser = async () => {
      const currentUser = await getMe();
      setUser(currentUser);
    };
    const timer = window.setTimeout(() => {
      void loadUser();
    }, 0);
    const onAuthChanged = () => {
      void loadUser();
    };
    window.addEventListener("filtre-auth-changed", onAuthChanged);
    window.addEventListener("storage", onAuthChanged);
    return () => {
      window.clearTimeout(timer);
      window.removeEventListener("filtre-auth-changed", onAuthChanged);
      window.removeEventListener("storage", onAuthChanged);
    };
  }, []);

  const handleProfileClick = () => {
    if (!user) {
      setIsAuthOpen(true);
      return;
    }
    setIsProfileOpen((open) => !open);
  };

  const handleLogout = () => {
    logoutUser();
    setUser(null);
    setIsProfileOpen(false);
    setLogoutMessage("Çıkış yapıldı");
    router.push("/");
    window.setTimeout(() => setLogoutMessage(null), 2500);
  };

  const fullName = user ? `${user.firstName || ""} ${user.lastName || ""}`.trim() || user.name : "";

  const iconBtn =
    "flex items-center justify-center w-9 h-9 rounded-[3px] border border-[var(--border-strong)] text-[var(--ink-30)] transition-colors duration-300 hover:border-[var(--brass)] hover:text-[var(--brass)]";

  return (
    <>
      <motion.nav
        initial={{ y: -16, opacity: 0 }}
        animate={{ y: 0, opacity: 1 }}
        transition={{ duration: 0.9, ease: [0.16, 1, 0.3, 1] }}
        className="relative z-50"
        style={{ background: "var(--bg-deep)", borderBottom: "1px solid var(--ink-70)" }}
      >
        <div className="mx-auto flex h-14 max-w-7xl items-center justify-between px-6">
          {/* Left — wordmark + tagline */}
          <Link href="/" className="flex items-baseline gap-3 group">
            <span className="fl-serif italic text-[20px] text-[var(--paper)] transition-colors group-hover:text-[var(--brass)]">
              FiltreLAB
            </span>
            <span className="hidden h-px w-5 bg-[var(--ink-70)] sm:inline-block" />
            <span className="hidden fl-mono text-[11px] uppercase tracking-[0.14em] text-[var(--ink-10)] sm:inline">
              Akıllı Alışveriş Asistanı
            </span>
          </Link>

          {/* Right — live status + controls */}
          <div className="flex items-center gap-4">
            <span className="hidden items-center gap-2 fl-mono text-[11px] uppercase tracking-[0.12em] text-[var(--ink-10)] sm:flex">
              <span
                className="inline-block h-1.5 w-1.5 rounded-full"
                style={{ background: "var(--brass)" }}
              />
              Canlı{today && ` · ${today}`}
            </span>

            <button
              onClick={() => setTheme(theme === "dark" ? "light" : "dark")}
              aria-label="Temayı değiştir"
              className={iconBtn}
            >
              {mounted && theme !== "dark" ? (
                <Moon className="h-[16px] w-[16px]" />
              ) : (
                <Sun className="h-[16px] w-[16px]" />
              )}
            </button>

            <div className="relative">
              <button onClick={handleProfileClick} className={iconBtn} aria-label="Profil">
                <User className="h-[16px] w-[16px]" />
              </button>
              {isProfileOpen && user && (
                <div
                  className="absolute right-0 top-12 w-72 rounded-[4px] border border-[var(--ink-70)] p-2"
                  style={{ background: "var(--bg-raised)" }}
                >
                  <div className="mb-1 border-b border-[var(--ink-70)] px-3 pb-3 pt-2">
                    <p className="fl-serif italic text-[18px] text-[var(--paper)]">{fullName}</p>
                    <p className="fl-mono mt-1 truncate text-[11px] text-[var(--ink-30)]">{user.email}</p>
                  </div>
                  <Link
                    href="/profile"
                    onClick={() => setIsProfileOpen(false)}
                    className="flex items-center gap-3 rounded-[3px] px-3 py-2.5 text-[13px] text-[var(--ink-10)] transition-colors hover:bg-[rgba(217,182,92,0.05)] hover:text-[var(--brass)]"
                  >
                    <IdCard className="h-4 w-4" />
                    Profil Görüntüle
                  </Link>
                  <Link
                    href="/history"
                    onClick={() => setIsProfileOpen(false)}
                    className="flex items-center gap-3 rounded-[3px] px-3 py-2.5 text-[13px] text-[var(--ink-10)] transition-colors hover:bg-[rgba(217,182,92,0.05)] hover:text-[var(--brass)]"
                  >
                    <History className="h-4 w-4" />
                    Analiz Geçmişi
                  </Link>
                  <Link
                    href="/favorites"
                    onClick={() => setIsProfileOpen(false)}
                    className="flex items-center gap-3 rounded-[3px] px-3 py-2.5 text-[13px] text-[var(--ink-10)] transition-colors hover:bg-[rgba(217,182,92,0.05)] hover:text-[var(--brass)]"
                  >
                    <Heart className="h-4 w-4" />
                    Favoriler
                  </Link>
                  <button
                    onClick={handleLogout}
                    className="mt-1 flex w-full items-center gap-3 rounded-[3px] px-3 py-2.5 text-[13px] text-[var(--verdict-caution)] transition-colors hover:bg-[rgba(199,147,102,0.08)]"
                  >
                    <LogOut className="h-4 w-4" />
                    Çıkış Yap
                  </button>
                </div>
              )}
            </div>
          </div>
        </div>
      </motion.nav>

      {logoutMessage && (
        <div
          className="fixed right-6 top-20 z-[120] rounded-[4px] border border-[var(--ink-70)] px-4 py-3 fl-mono text-[12px] uppercase tracking-[0.1em] text-[var(--brass)]"
          style={{ background: "var(--bg-raised)" }}
        >
          {logoutMessage}
        </div>
      )}

      <AuthModal isOpen={isAuthOpen} onClose={() => setIsAuthOpen(false)} />
    </>
  );
}
