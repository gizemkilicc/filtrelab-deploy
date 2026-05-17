"use client";

import { motion } from "framer-motion";
import { User, Menu, Sparkles, Sun, Moon, LogOut, Heart, History, IdCard } from "lucide-react";
import Link from "next/link";
import Image from "next/image";
import { useEffect, useState } from "react";
import { useRouter } from "next/navigation";
import { AuthModal } from "./AuthModal";
import { useTheme } from "./ThemeProvider";
import { getMe, logoutUser, type AuthUser } from "@/lib/apiClient";

export function Navbar() {
  const [isAuthOpen, setIsAuthOpen] = useState(false);
  const [isProfileOpen, setIsProfileOpen] = useState(false);
  const [logoutMessage, setLogoutMessage] = useState<string | null>(null);
  const [user, setUser] = useState<AuthUser | null>(null);
  const [mounted, setMounted] = useState(false);
  const { theme, setTheme } = useTheme();
  const router = useRouter();

  useEffect(() => {
    const timer = window.setTimeout(() => setMounted(true), 0);
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

  return (
    <>
      <motion.nav 
        initial={{ y: -20, opacity: 0 }}
        animate={{ y: 0, opacity: 1 }}
        transition={{ duration: 1, ease: [0.16, 1, 0.3, 1] }}
        className="fixed top-0 left-0 right-0 z-50 p-4 md:p-6 pointer-events-none"
      >
        <div className="max-w-7xl mx-auto liquid-glass gloss-overlay rounded-full px-7 py-3.5 flex items-center justify-between pointer-events-auto shadow-[0_12px_40px_rgba(0,0,0,0.05)] dark:shadow-[0_12px_40px_rgba(0,0,0,0.4)] border border-white dark:border-white/10">

          {/* Logo */}
          <Link href="/" className="flex items-center space-x-3 group">
            <div className="relative w-12 h-12 rounded-[14px] overflow-hidden group-hover:scale-105 transition-transform duration-700 will-change-transform shadow-[0_4px_15px_rgba(0,0,0,0.06)] border border-white/60 bg-white dark:bg-white/10">
              <Image src="/images/logo.png" alt="FiltreLAB Logo" fill className="object-cover scale-110" />
            </div>

            <span className="text-[22px] font-medium tracking-tight hidden sm:block text-gray-700 dark:text-gray-200 drop-shadow-sm">Filtre<span className="font-bold text-gray-900 dark:text-white">LAB</span></span>
          </Link>

          {/* Desktop Navigation */}
          <div className="hidden md:flex items-center space-x-1">
            <Link href="/#products" className="px-4 py-2 rounded-full text-[15px] font-medium text-gray-600 dark:text-gray-300 hover:text-gray-900 dark:hover:text-white hover:bg-gray-100/50 dark:hover:bg-white/10 transition-colors">Kadın</Link>
            <Link href="/#products" className="px-4 py-2 rounded-full text-[15px] font-medium text-gray-600 dark:text-gray-300 hover:text-gray-900 dark:hover:text-white hover:bg-gray-100/50 dark:hover:bg-white/10 transition-colors">Erkek</Link>
            <Link href="/#products" className="px-4 py-2 rounded-full text-[15px] font-medium text-gray-600 dark:text-gray-300 hover:text-gray-900 dark:hover:text-white hover:bg-gray-100/50 dark:hover:bg-white/10 transition-colors">Aksesuar</Link>
            <Link href="/dashboard" className="px-4 py-2 rounded-full text-[15px] font-medium text-purple-600 dark:text-purple-400 bg-purple-50/50 dark:bg-purple-500/10 hover:bg-purple-100/50 dark:hover:bg-purple-500/20 transition-colors flex items-center">
              <Sparkles className="w-4 h-4 mr-1.5" />
              AI Tavsiyeleri
            </Link>
          </div>

          {/* Icons */}
          <div className="flex items-center space-x-3 sm:space-x-4">
            {/* Dark/Light Toggle */}
            <button
              onClick={() => setTheme(theme === "dark" ? "light" : "dark")}
              aria-label="Temayı değiştir"
              className="text-gray-500 dark:text-gray-400 hover:text-gray-900 dark:hover:text-white transition-all hover:scale-105 will-change-transform p-2 bg-white/60 dark:bg-white/5 hover:bg-white dark:hover:bg-white/10 rounded-full shadow-[inset_0_1px_2px_rgba(255,255,255,1)]"
            >
              {mounted ? (
                theme === "dark" ? (
                  <Sun className="w-[18px] h-[18px]" />
                ) : (
                  <Moon className="w-[18px] h-[18px]" />
                )
              ) : (
                <Moon className="w-[18px] h-[18px]" />
              )}
            </button>

            <div className="relative">
              <button
                onClick={handleProfileClick}
                className="text-gray-700 dark:text-gray-200 transition-all duration-500 hover:scale-105 bg-white dark:bg-white/10 hover:bg-gray-50 dark:hover:bg-white/20 border border-white dark:border-white/10 p-2.5 rounded-full shadow-[inset_0_2px_4px_rgba(255,255,255,1),0_4px_12px_rgba(0,0,0,0.05)] will-change-transform flex items-center justify-center"
                aria-label="Profil"
              >
                <User className="w-[18px] h-[18px]" />
              </button>
              {isProfileOpen && user && (
                <div className="absolute right-0 top-14 w-72 rounded-3xl border border-white/80 dark:border-white/10 bg-white/95 dark:bg-[#12101a]/95 p-4 shadow-[0_20px_60px_rgba(0,0,0,0.12)] backdrop-blur-2xl">
                  <div className="border-b border-black/10 dark:border-white/10 pb-3 mb-3">
                    <p className="font-bold text-[#191847] dark:text-white">{fullName}</p>
                    <p className="text-sm text-gray-500 dark:text-gray-400 truncate">{user.email}</p>
                  </div>
                  <Link href="/profile" onClick={() => setIsProfileOpen(false)} className="flex items-center gap-3 rounded-2xl px-3 py-2 text-sm text-gray-700 dark:text-gray-300 hover:bg-gray-100 dark:hover:bg-white/10">
                    <IdCard className="h-4 w-4" />
                    Profil Görüntüle
                  </Link>
                  <Link href="/history" onClick={() => setIsProfileOpen(false)} className="flex items-center gap-3 rounded-2xl px-3 py-2 text-sm text-gray-700 dark:text-gray-300 hover:bg-gray-100 dark:hover:bg-white/10">
                    <History className="h-4 w-4" />
                    Analiz Geçmişi
                  </Link>
                  <Link href="/favorites" onClick={() => setIsProfileOpen(false)} className="flex items-center gap-3 rounded-2xl px-3 py-2 text-sm text-gray-700 dark:text-gray-300 hover:bg-gray-100 dark:hover:bg-white/10">
                    <Heart className="h-4 w-4" />
                    Favoriler
                  </Link>
                  <button onClick={handleLogout} className="mt-2 flex w-full items-center gap-3 rounded-2xl px-3 py-2 text-sm text-red-600 dark:text-red-300 hover:bg-red-50 dark:hover:bg-red-500/10">
                    <LogOut className="h-4 w-4" />
                    Çıkış Yap
                  </button>
                </div>
              )}
            </div>
            <button className="md:hidden text-gray-500 dark:text-gray-400 hover:text-gray-900 dark:hover:text-white transition-colors p-2 bg-white/60 dark:bg-white/5 rounded-full shadow-[inset_0_1px_2px_rgba(255,255,255,1)]">
              <Menu className="w-5 h-5" />
            </button>
          </div>

        </div>
      </motion.nav>

      {logoutMessage && (
        <div className="fixed right-6 top-24 z-[120] rounded-2xl border border-black/10 dark:border-white/10 bg-white/95 dark:bg-[#12101a]/95 px-4 py-3 text-sm font-medium text-[#191847] dark:text-white shadow-lg">
          {logoutMessage}
        </div>
      )}

      {/* Auth Modal */}
      <AuthModal isOpen={isAuthOpen} onClose={() => setIsAuthOpen(false)} />
    </>
  );
}
