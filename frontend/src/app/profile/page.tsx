"use client";

import { useEffect, useState } from "react";
import type { FormEvent } from "react";
import Link from "next/link";
import { ArrowLeft, Save } from "lucide-react";
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

  const labelClass = "block fl-mono text-[10px] uppercase tracking-[0.16em] text-[var(--ink-30)] mb-2";

  return (
    <main className="fl-page px-6 py-14 md:px-12">
      <div className="mx-auto max-w-3xl">
        <Link href="/" className="fl-link mb-10 inline-flex items-center fl-mono text-[11px] uppercase tracking-[0.14em]">
          <ArrowLeft className="mr-2 h-4 w-4" />
          Ana Sayfaya Dön
        </Link>

        <p className="fl-kicker mb-3">EVRE · HESAP</p>
        <h1 className="fl-serif text-[44px] leading-[1.0] text-[var(--paper)] md:text-[72px]">Profilim</h1>
        <p className="fl-sans mt-4 text-[15px] text-[var(--ink-30)]">
          Hesap bilgilerini düzenle ve FiltreLAB kullanım özetini gör.
        </p>

        {message && (
          <div className="mt-10 fl-card p-6 fl-sans text-[14px] text-[var(--ink-30)]">{message}</div>
        )}

        {user && (
          <div className="mt-12 space-y-12">
            {/* Bilgileri düzenle */}
            <section>
              <div className="fl-divider pt-6">
                <p className="fl-kicker mb-1">BİLGİLERİNİ DÜZENLE</p>
                <p className="fl-serif italic text-[22px] text-[var(--paper)]">{fullName}</p>
              </div>

              <form onSubmit={handleSubmit} className="mt-8">
                <div className="grid gap-6 md:grid-cols-2">
                  <div>
                    <label className={labelClass}>Ad</label>
                    <input
                      value={firstName}
                      onChange={(event) => setFirstName(event.target.value)}
                      className="fl-input"
                      required
                    />
                  </div>
                  <div>
                    <label className={labelClass}>Soyad</label>
                    <input
                      value={lastName}
                      onChange={(event) => setLastName(event.target.value)}
                      className="fl-input"
                      required
                    />
                  </div>
                  <div className="md:col-span-2">
                    <label className={labelClass}>E-Posta</label>
                    <input
                      type="email"
                      value={email}
                      onChange={(event) => setEmail(event.target.value)}
                      className="fl-input"
                      required
                    />
                  </div>
                </div>

                <div className="mt-7 flex flex-col gap-4 sm:flex-row sm:items-center">
                  <button type="submit" disabled={saving} className="fl-btn fl-btn-primary">
                    <Save className="h-4 w-4" />
                    {saving ? "Kaydediliyor..." : "Kaydet"}
                  </button>
                  {status && (
                    <p className="fl-mono text-[11px] uppercase tracking-[0.1em] text-[var(--ink-30)]">
                      {status}
                    </p>
                  )}
                </div>
              </form>
            </section>

            {/* Hesap özeti — data rows */}
            <section>
              <p className="fl-kicker fl-divider pt-6 mb-6">HESAP ÖZETİ</p>
              <dl>
                <div className="fl-row flex items-baseline justify-between gap-6 px-2 py-5">
                  <dt className="fl-data-label">E-Posta</dt>
                  <dd className="fl-data-value break-all text-right">{user.email}</dd>
                </div>
                <div className="fl-row flex items-baseline justify-between gap-6 px-2 py-5">
                  <dt className="fl-data-label">Analiz Sayısı</dt>
                  <dd className="fl-data-value text-right">{user.analysisCount ?? 0}</dd>
                </div>
                <div className="fl-row flex items-baseline justify-between gap-6 border-b border-[var(--ink-70)] px-2 py-5">
                  <dt className="fl-data-label">Kayıt Tarihi</dt>
                  <dd className="fl-data-value text-right">
                    {user.createdAt ? new Date(user.createdAt).toLocaleDateString("tr-TR") : "Veri yok"}
                  </dd>
                </div>
              </dl>
            </section>
          </div>
        )}
      </div>
    </main>
  );
}
