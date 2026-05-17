"use client";

import { useEffect, useState } from "react";
import type { FormEvent } from "react";
import Link from "next/link";
import { ArrowLeft, History, Mail, Save, User } from "lucide-react";
import { getMe, updateMe, type AuthUser } from "@/lib/apiClient";

export default function ProfilePage() {
  const [user, setUser] = useState<AuthUser | null>(null);
  const [message, setMessage] = useState("Yükleniyor...");
  const [status, setStatus] = useState<string | null>(null);
  const [saving, setSaving] = useState(false);
  const [firstName, setFirstName] = useState("");
  const [lastName, setLastName] = useState("");
  const [email, setEmail] = useState("");

  useEffect(() => {
    const timer = window.setTimeout(() => {
      const load = async () => {
        const currentUser = await getMe();
        setUser(currentUser);
        setMessage(currentUser ? "" : "Bu özellik için giriş yapmalısınız.");
        if (currentUser) {
          setFirstName(currentUser.firstName || "");
          setLastName(currentUser.lastName || "");
          setEmail(currentUser.email || "");
        }
      };
      void load();
    }, 0);
    return () => window.clearTimeout(timer);
  }, []);

  const handleSubmit = async (event: FormEvent<HTMLFormElement>) => {
    event.preventDefault();
    setSaving(true);
    setStatus(null);

    const result = await updateMe({ firstName, lastName, email });
    if (result.success) {
      setUser(result.user);
      setFirstName(result.user.firstName || "");
      setLastName(result.user.lastName || "");
      setEmail(result.user.email || "");
      setStatus("Profil bilgilerin güncellendi.");
    } else {
      setStatus(result.error);
    }
    setSaving(false);
  };

  const fullName = user ? `${user.firstName || ""} ${user.lastName || ""}`.trim() || user.name : "";

  return (
    <main className="min-h-screen bg-[#f8f7fa] p-6 text-[#191847] dark:bg-[#05050a] dark:text-white md:p-12">
      <div className="mx-auto max-w-4xl pt-8">
        <Link href="/" className="mb-8 inline-flex items-center text-gray-500 transition-colors hover:text-[#191847] dark:text-gray-400 dark:hover:text-white">
          <ArrowLeft className="mr-2 h-5 w-5" />
          Ana Sayfaya Dön
        </Link>

        <h1 className="mb-3 text-4xl font-black">Profilim</h1>
        <p className="mb-8 text-gray-700 dark:text-gray-300">Hesap bilgilerini düzenle ve FiltreLAB kullanım özetini gör.</p>

        {message && (
          <div className="rounded-3xl border border-black/10 bg-white/80 p-6 text-gray-700 dark:border-white/10 dark:bg-white/5 dark:text-gray-300">
            {message}
          </div>
        )}

        {user && (
          <div className="space-y-6">
            <form onSubmit={handleSubmit} className="rounded-3xl border border-black/10 bg-white/80 p-6 dark:border-white/10 dark:bg-white/5 md:p-8">
              <div className="mb-6 flex items-center gap-3">
                <User className="h-5 w-5 text-[var(--neon-purple)]" />
                <div>
                  <h2 className="text-2xl font-black">Bilgilerini düzenle</h2>
                  <p className="text-sm text-gray-500 dark:text-gray-400">{fullName}</p>
                </div>
              </div>

              <div className="grid gap-5 md:grid-cols-2">
                <label className="block">
                  <span className="mb-2 block text-sm font-bold text-gray-600 dark:text-gray-300">Ad</span>
                  <input
                    value={firstName}
                    onChange={(event) => setFirstName(event.target.value)}
                    className="w-full rounded-2xl border border-black/10 bg-white px-4 py-3 text-[#191847] outline-none transition-colors focus:border-[#191847] dark:border-white/10 dark:bg-white/10 dark:text-white dark:focus:border-white/40"
                    required
                  />
                </label>
                <label className="block">
                  <span className="mb-2 block text-sm font-bold text-gray-600 dark:text-gray-300">Soyad</span>
                  <input
                    value={lastName}
                    onChange={(event) => setLastName(event.target.value)}
                    className="w-full rounded-2xl border border-black/10 bg-white px-4 py-3 text-[#191847] outline-none transition-colors focus:border-[#191847] dark:border-white/10 dark:bg-white/10 dark:text-white dark:focus:border-white/40"
                    required
                  />
                </label>
                <label className="block md:col-span-2">
                  <span className="mb-2 block text-sm font-bold text-gray-600 dark:text-gray-300">E-posta</span>
                  <input
                    type="email"
                    value={email}
                    onChange={(event) => setEmail(event.target.value)}
                    className="w-full rounded-2xl border border-black/10 bg-white px-4 py-3 text-[#191847] outline-none transition-colors focus:border-[#191847] dark:border-white/10 dark:bg-white/10 dark:text-white dark:focus:border-white/40"
                    required
                  />
                </label>
              </div>

              <div className="mt-6 flex flex-col gap-3 sm:flex-row sm:items-center">
                <button
                  type="submit"
                  disabled={saving}
                  className="inline-flex items-center justify-center gap-2 rounded-full bg-[#191847] px-5 py-3 text-sm font-bold text-white transition-colors hover:bg-[#25235f] disabled:cursor-not-allowed disabled:opacity-60 dark:bg-white dark:text-[#191847] dark:hover:bg-gray-100"
                >
                  <Save className="h-4 w-4" />
                  {saving ? "Kaydediliyor..." : "Kaydet"}
                </button>
                {status && <p className="text-sm font-semibold text-gray-600 dark:text-gray-300">{status}</p>}
              </div>
            </form>

            <div className="rounded-3xl border border-black/10 bg-white/80 p-6 dark:border-white/10 dark:bg-white/5 md:p-8">
              <div className="grid gap-5 md:grid-cols-2">
                <div className="rounded-2xl border border-black/10 bg-white/70 p-5 dark:border-white/10 dark:bg-white/5">
                  <Mail className="mb-3 h-5 w-5 text-[var(--neon-blue)]" />
                  <p className="text-sm text-gray-500 dark:text-gray-400">Email</p>
                  <p className="break-all text-lg font-bold">{user.email}</p>
                </div>
                <div className="rounded-2xl border border-black/10 bg-white/70 p-5 dark:border-white/10 dark:bg-white/5">
                  <History className="mb-3 h-5 w-5 text-emerald-500" />
                  <p className="text-sm text-gray-500 dark:text-gray-400">Analiz Sayısı</p>
                  <p className="text-lg font-bold">{user.analysisCount ?? 0}</p>
                </div>
                <div className="rounded-2xl border border-black/10 bg-white/70 p-5 dark:border-white/10 dark:bg-white/5 md:col-span-2">
                  <p className="text-sm text-gray-500 dark:text-gray-400">Kayıt Tarihi</p>
                  <p className="text-lg font-bold">
                    {user.createdAt ? new Date(user.createdAt).toLocaleDateString("tr-TR") : "Veri yok"}
                  </p>
                </div>
              </div>
            </div>
          </div>
        )}
      </div>
    </main>
  );
}
