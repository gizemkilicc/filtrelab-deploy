"use client";

import { useEffect, useState } from "react";
import Link from "next/link";
import { ArrowLeft, History, Mail, User } from "lucide-react";
import { getMe, type AuthUser } from "@/lib/apiClient";

export default function ProfilePage() {
  const [user, setUser] = useState<AuthUser | null>(null);
  const [message, setMessage] = useState("Yükleniyor...");

  useEffect(() => {
    const timer = window.setTimeout(() => {
      const load = async () => {
        const currentUser = await getMe();
        setUser(currentUser);
        setMessage(currentUser ? "" : "Bu özellik için giriş yapmalısınız.");
      };
      void load();
    }, 0);
    return () => window.clearTimeout(timer);
  }, []);

  const fullName = user ? `${user.firstName || ""} ${user.lastName || ""}`.trim() || user.name : "";

  return (
    <main className="min-h-screen bg-[#f8f7fa] dark:bg-[#05050a] text-[#191847] dark:text-white p-6 md:p-12">
      <div className="mx-auto max-w-4xl pt-8">
        <Link href="/" className="inline-flex items-center text-gray-500 hover:text-[#191847] dark:text-gray-400 dark:hover:text-white transition-colors mb-8">
          <ArrowLeft className="w-5 h-5 mr-2" />
          Ana Sayfaya Dön
        </Link>

        <h1 className="text-4xl font-black mb-3">Profil</h1>
        <p className="text-gray-700 dark:text-gray-300 mb-8">Hesap bilgilerin ve FiltreLAB kullanım özetin.</p>

        {message && (
          <div className="rounded-3xl border border-black/10 dark:border-white/10 bg-white/80 dark:bg-white/5 p-6 text-gray-700 dark:text-gray-300">
            {message}
          </div>
        )}

        {user && (
          <div className="rounded-3xl border border-black/10 dark:border-white/10 bg-white/80 dark:bg-white/5 p-6 md:p-8">
            <div className="grid gap-5 md:grid-cols-2">
              <div className="rounded-2xl bg-white/70 dark:bg-white/5 border border-black/10 dark:border-white/10 p-5">
                <User className="h-5 w-5 text-[var(--neon-purple)] mb-3" />
                <p className="text-sm text-gray-500 dark:text-gray-400">Ad Soyad</p>
                <p className="text-lg font-bold">{fullName}</p>
              </div>
              <div className="rounded-2xl bg-white/70 dark:bg-white/5 border border-black/10 dark:border-white/10 p-5">
                <Mail className="h-5 w-5 text-[var(--neon-blue)] mb-3" />
                <p className="text-sm text-gray-500 dark:text-gray-400">Email</p>
                <p className="text-lg font-bold break-all">{user.email}</p>
              </div>
              <div className="rounded-2xl bg-white/70 dark:bg-white/5 border border-black/10 dark:border-white/10 p-5">
                <History className="h-5 w-5 text-emerald-500 mb-3" />
                <p className="text-sm text-gray-500 dark:text-gray-400">Analiz Sayısı</p>
                <p className="text-lg font-bold">{user.analysisCount ?? 0}</p>
              </div>
              <div className="rounded-2xl bg-white/70 dark:bg-white/5 border border-black/10 dark:border-white/10 p-5">
                <p className="text-sm text-gray-500 dark:text-gray-400">Kayıt Tarihi</p>
                <p className="text-lg font-bold">
                  {user.createdAt ? new Date(user.createdAt).toLocaleDateString("tr-TR") : "Veri yok"}
                </p>
              </div>
            </div>
          </div>
        )}
      </div>
    </main>
  );
}
