"use client";

import { useEffect, useState } from "react";
import type { ReactNode } from "react";
import Link from "next/link";
import { useRouter } from "next/navigation";
import { motion } from "framer-motion";
import { ArrowRight, Heart, History, Loader2 } from "lucide-react";
import {
  getAnalysisHistory,
  getFavorites,
  getMe,
  getRecommendations,
  type AuthUser,
  type Recommendation,
} from "@/lib/apiClient";

type PersonalizedHomeProps = {
  children: ReactNode;
};

type Counts = {
  history: number;
  favorites: number;
  recommendations: number;
};

const featureCards = [
  {
    title: "Analiz geçmişi",
    text: "Daha önce baktığın ürünler kayıtlı kalsın",
    href: "/history",
    countKey: "history" as const,
    icon: History,
  },
  {
    title: "Favori listesi",
    text: "Beğendiğin ürünleri kaydet",
    href: "/favorites",
    countKey: "favorites" as const,
    icon: Heart,
  },
];

export function PersonalizedHome({ children }: PersonalizedHomeProps) {
  const router = useRouter();
  const [user, setUser] = useState<AuthUser | null>(null);
  const [loading, setLoading] = useState(true);
  const [productUrl, setProductUrl] = useState("");
  const [counts, setCounts] = useState<Counts>({
    history: 0,
    favorites: 0,
    recommendations: 0,
  });
  const [recommendations, setRecommendations] = useState<Recommendation[]>([]);

  useEffect(() => {
    let mounted = true;

    const load = async () => {
      // Safety net: never stay loading longer than 6 seconds regardless of backend state
      const safetyTimer = window.setTimeout(() => {
        if (mounted) setLoading(false);
      }, 6000);

      try {
        const currentUser = await getMe();
        if (!mounted) return;
        setUser(currentUser);
        setLoading(false);

        if (!currentUser) return;

        const [historyRes, favoritesRes, recommendationsRes] = await Promise.all([
          getAnalysisHistory(),
          getFavorites(),
          getRecommendations(),
        ]);

        if (!mounted) return;
        setCounts({
          history: historyRes.success ? historyRes.data.items.length : 0,
          favorites: favoritesRes.success ? favoritesRes.data.items.length : 0,
          recommendations: recommendationsRes.success ? recommendationsRes.data.recommendations.length : 0,
        });
        setRecommendations(recommendationsRes.success ? recommendationsRes.data.recommendations.slice(0, 3) : []);
      } catch {
        if (mounted) setLoading(false);
      } finally {
        window.clearTimeout(safetyTimer);
      }
    };

    void load();

    const onAuthChanged = () => {
      setLoading(true);
      void load();
    };
    window.addEventListener("filtre-auth-changed", onAuthChanged);

    return () => {
      mounted = false;
      window.removeEventListener("filtre-auth-changed", onAuthChanged);
    };
  }, []);

  if (loading) {
    return (
      <div className="fl-page flex min-h-screen items-center justify-center">
        <Loader2 className="h-6 w-6 animate-spin text-[var(--brass)]" />
      </div>
    );
  }

  if (!user) {
    return <>{children}</>;
  }

  const firstName = (user.firstName || user.name?.split(" ")[0] || "FiltreLAB kullanıcısı").trim();

  const handleAnalyze = () => {
    const trimmed = productUrl.trim();
    if (!trimmed) return;
    router.push(`/dashboard?url=${encodeURIComponent(trimmed)}`);
  };

  const ghostLink =
    "rounded-[3px] border border-[var(--border-strong)] px-4 py-2 fl-mono text-[11px] uppercase tracking-[0.1em] text-[var(--ink-10)] transition-colors hover:border-[var(--brass)] hover:text-[var(--brass)]";

  return (
    <section className="fl-page min-h-screen px-6 pb-20 pt-32 md:px-10">
      <div className="mx-auto max-w-6xl">
        {/* Header */}
        <div className="border-b border-[var(--ink-70)] pb-9">
          <p className="fl-kicker mb-4">KİŞİSEL ALIŞVERİŞ PANELİN</p>
          <h1 className="fl-serif text-[52px] leading-[1.0] text-[var(--paper)] md:text-[80px]">
            Hoş geldin, <span className="italic text-[var(--brass)]">{firstName}</span>
          </h1>
        </div>

        {/* URL input */}
        <div className="mt-10 max-w-2xl">
          <p className="fl-kicker mb-3">YENİ ANALİZ</p>
          <div className="flex flex-col gap-3 sm:flex-row">
            <input
              type="url"
              value={productUrl}
              onChange={(event) => setProductUrl(event.target.value)}
              onKeyDown={(event) => event.key === "Enter" && handleAnalyze()}
              placeholder="Ürün linkini yapıştır, FiltreLAB analiz etsin..."
              className="fl-input flex-1"
            />
            <button onClick={handleAnalyze} disabled={!productUrl.trim()} className="fl-btn fl-btn-primary">
              Filtrele
              <ArrowRight className="h-4 w-4" />
            </button>
          </div>
        </div>

        {/* Feature cards */}
        <div className="mt-14 grid grid-cols-1 gap-5 lg:grid-cols-3">
          {featureCards.map((feature) => {
            const Icon = feature.icon;
            return (
              <Link key={feature.title} href={feature.href} className="fl-card fl-card-hover p-7">
                <div className="flex items-start justify-between">
                  <Icon className="h-5 w-5 text-[var(--brass)]" />
                  <span className="fl-serif text-[48px] leading-none text-[var(--paper)]">
                    {counts[feature.countKey]}
                  </span>
                </div>
                <h2 className="fl-serif mt-8 text-[24px] text-[var(--paper)]">{feature.title}</h2>
                <p className="fl-sans mt-2 text-[13px] leading-relaxed text-[var(--ink-30)]">
                  {feature.text}
                </p>
              </Link>
            );
          })}
        </div>

        {/* AI recommendations */}
        <section className="fl-divider mt-16 pt-10">
          <p className="fl-kicker mb-6">KİŞİSEL AI ÖNERİLERİ</p>
          {recommendations.length > 0 ? (
            <div className="grid gap-5 md:grid-cols-3">
              {recommendations.map((item) => (
                <div key={item.title} className="fl-card p-6">
                  <p className="fl-serif italic text-[20px] text-[var(--paper)]">{item.title}</p>
                  <p className="fl-sans mt-2 text-[13px] leading-relaxed text-[var(--ink-30)]">
                    {item.description}
                  </p>
                </div>
              ))}
            </div>
          ) : (
            <p className="fl-sans text-[14px] text-[var(--ink-30)]">
              İlk favori veya analiz kaydından sonra önerilerin burada görünecek.
            </p>
          )}
        </section>

        {/* Bugünkü odak */}
        <section className="fl-divider mt-16 pt-10">
          <p className="fl-kicker mb-4">BUGÜNKÜ ODAK</p>
          <p className="fl-sans max-w-2xl text-[14px] leading-relaxed text-[var(--ink-10)]">
            Favorilerini ve analiz geçmişini aynı yerden yönetebilirsin.
          </p>
          <div className="mt-5 flex flex-wrap gap-3">
            <Link href="/history" className={ghostLink}>Geçmişi aç</Link>
            <Link href="/favorites" className={ghostLink}>Favorileri aç</Link>
          </div>
        </section>
      </div>
    </section>
  );
}
