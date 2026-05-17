"use client";

import { useEffect, useState } from "react";
import type { ReactNode } from "react";
import Link from "next/link";
import { useRouter } from "next/navigation";
import { motion } from "framer-motion";
import {
  ArrowRight,
  Bell,
  BrainCircuit,
  Heart,
  History,
  Loader2,
  Search,
  Sparkles,
  TrendingDown,
} from "lucide-react";
import {
  getAnalysisHistory,
  getFavorites,
  getMe,
  getPriceTracking,
  getRecommendations,
  type AuthUser,
  type Recommendation,
} from "@/lib/apiClient";

type PersonalizedHomeProps = {
  children: ReactNode;
};

type Counts = {
  tracking: number;
  history: number;
  favorites: number;
  recommendations: number;
};

const featureCards = [
  {
    title: "Fiyat takibi",
    text: "Bu ürün ucuzlayınca haber ver",
    href: "/price-tracking",
    countKey: "tracking" as const,
    icon: Bell,
    accent: "text-sky-600 dark:text-sky-300",
    bg: "bg-sky-50 dark:bg-sky-500/10",
  },
  {
    title: "Analiz geçmişi",
    text: "Daha önce baktığın ürünler kayıtlı kalsın",
    href: "/history",
    countKey: "history" as const,
    icon: History,
    accent: "text-emerald-600 dark:text-emerald-300",
    bg: "bg-emerald-50 dark:bg-emerald-500/10",
  },
  {
    title: "Favori listesi",
    text: "Beğendiğin ürünleri kaydet",
    href: "/favorites",
    countKey: "favorites" as const,
    icon: Heart,
    accent: "text-rose-600 dark:text-rose-300",
    bg: "bg-rose-50 dark:bg-rose-500/10",
  },
];

const categoryOrbits = [
  { label: "Kadın", x: "50%", y: "13%", delay: 0 },
  { label: "Erkek", x: "73%", y: "22%", delay: 0.2 },
  { label: "Çocuk", x: "82%", y: "47%", delay: 0.4 },
  { label: "Ev & Yaşam", x: "66%", y: "72%", delay: 0.6 },
  { label: "Kozmetik", x: "39%", y: "80%", delay: 0.8 },
  { label: "Ayakkabı & Çanta", x: "17%", y: "61%", delay: 1 },
  { label: "Elektronik", x: "18%", y: "32%", delay: 1.2 },
  { label: "Aksesuar", x: "42%", y: "43%", delay: 1.4 },
  { label: "Spor", x: "56%", y: "57%", delay: 1.6 },
];

function CategorySpiral() {
  return (
    <div className="relative min-h-[360px] overflow-hidden rounded-[2.5rem] border border-white/60 bg-[radial-gradient(circle_at_50%_45%,rgba(255,255,255,0.72),rgba(216,180,254,0.26)_34%,rgba(124,58,237,0.22)_70%,rgba(14,165,233,0.16))] p-6 shadow-[0_28px_90px_rgba(91,33,182,0.18)] backdrop-blur-xl dark:border-white/10 dark:bg-[radial-gradient(circle_at_50%_45%,rgba(255,255,255,0.12),rgba(124,58,237,0.28)_34%,rgba(49,46,129,0.38)_70%,rgba(5,5,10,0.7))]">
      <motion.div
        aria-hidden="true"
        className="absolute left-1/2 top-1/2 h-72 w-72 -translate-x-1/2 -translate-y-1/2 rounded-full border-2 border-[#191847]/18 dark:border-white/15"
        animate={{ rotate: 360 }}
        transition={{ duration: 22, repeat: Infinity, ease: "linear" }}
      />
      <motion.div
        aria-hidden="true"
        className="absolute left-1/2 top-1/2 h-48 w-48 -translate-x-1/2 -translate-y-1/2 rounded-full border-2 border-[#191847]/18 dark:border-white/15"
        animate={{ rotate: -360 }}
        transition={{ duration: 18, repeat: Infinity, ease: "linear" }}
      />
      <motion.div
        aria-hidden="true"
        className="absolute left-1/2 top-1/2 h-24 w-24 -translate-x-1/2 -translate-y-1/2 rounded-full border-2 border-[#191847]/18 dark:border-white/15"
        animate={{ rotate: 360 }}
        transition={{ duration: 14, repeat: Infinity, ease: "linear" }}
      />
      <motion.div
        aria-hidden="true"
        className="absolute left-[49%] top-[43%] h-20 w-20 rounded-full bg-[radial-gradient(circle_at_30%_30%,#fff,#67e8f9_28%,#a855f7_62%,#191847)] shadow-[0_18px_50px_rgba(124,58,237,0.45)]"
        animate={{ y: [0, -10, 0], scale: [1, 1.05, 1] }}
        transition={{ duration: 5, repeat: Infinity, ease: "easeInOut" }}
      />
      <motion.div
        aria-hidden="true"
        className="absolute left-[7%] top-[12%] h-20 w-20 rounded-full bg-[radial-gradient(circle_at_30%_30%,#fff,#f0abfc_26%,#38bdf8_66%,#7c3aed)]"
        animate={{ y: [0, 16, 0], x: [0, 8, 0] }}
        transition={{ duration: 6.5, repeat: Infinity, ease: "easeInOut" }}
      />
      <motion.div
        aria-hidden="true"
        className="absolute bottom-8 right-10 h-16 w-16 rounded-full bg-[radial-gradient(circle_at_30%_30%,#fff,#22d3ee_25%,#f472b6_62%,#7c3aed)]"
        animate={{ y: [0, -18, 0], x: [0, -10, 0] }}
        transition={{ duration: 7, repeat: Infinity, ease: "easeInOut" }}
      />

      {categoryOrbits.map((category) => (
        <motion.div
          key={category.label}
          className="absolute -translate-x-1/2 -translate-y-1/2 whitespace-nowrap rounded-full border border-white/70 bg-white/80 px-3 py-1.5 text-xs font-black text-[#191847] shadow-[0_12px_32px_rgba(25,24,71,0.12)] backdrop-blur-md dark:border-white/10 dark:bg-white/10 dark:text-white"
          style={{ left: category.x, top: category.y }}
          animate={{ y: [0, -8, 0], x: [0, 4, 0] }}
          transition={{ duration: 4.2, delay: category.delay, repeat: Infinity, ease: "easeInOut" }}
        >
          {category.label}
        </motion.div>
      ))}
    </div>
  );
}

export function PersonalizedHome({ children }: PersonalizedHomeProps) {
  const router = useRouter();
  const [user, setUser] = useState<AuthUser | null>(null);
  const [loading, setLoading] = useState(true);
  const [productUrl, setProductUrl] = useState("");
  const [counts, setCounts] = useState<Counts>({
    tracking: 0,
    history: 0,
    favorites: 0,
    recommendations: 0,
  });
  const [recommendations, setRecommendations] = useState<Recommendation[]>([]);

  useEffect(() => {
    let mounted = true;

    const load = async () => {
      const currentUser = await getMe();
      if (!mounted) return;
      setUser(currentUser);
      setLoading(false);

      if (!currentUser) return;

      const [trackingRes, historyRes, favoritesRes, recommendationsRes] = await Promise.all([
        getPriceTracking(),
        getAnalysisHistory(),
        getFavorites(),
        getRecommendations(),
      ]);

      if (!mounted) return;
      setCounts({
        tracking: trackingRes.success ? trackingRes.data.items.length : 0,
        history: historyRes.success ? historyRes.data.items.length : 0,
        favorites: favoritesRes.success ? favoritesRes.data.items.length : 0,
        recommendations: recommendationsRes.success ? recommendationsRes.data.recommendations.length : 0,
      });
      setRecommendations(recommendationsRes.success ? recommendationsRes.data.recommendations.slice(0, 3) : []);
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
      <div className="flex min-h-screen items-center justify-center bg-[#f8f7fa] text-[#191847] dark:bg-[#05050a] dark:text-white">
        <Loader2 className="h-7 w-7 animate-spin" />
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

  return (
    <section className="relative min-h-screen overflow-hidden bg-[#f8f7fa] px-6 pb-16 pt-32 text-[#191847] dark:bg-[#05050a] dark:text-white md:px-10">
      <motion.div
        aria-hidden="true"
        className="absolute inset-0 bg-[linear-gradient(120deg,rgba(244,114,182,0.18),rgba(125,211,252,0.18),rgba(167,139,250,0.20),rgba(255,255,255,0.62))] bg-[length:260%_260%] dark:bg-[linear-gradient(120deg,rgba(88,28,135,0.42),rgba(14,116,144,0.24),rgba(79,70,229,0.28),rgba(5,5,10,0.90))]"
        animate={{ backgroundPosition: ["0% 50%", "100% 50%", "0% 50%"] }}
        transition={{ duration: 16, repeat: Infinity, ease: "linear" }}
      />
      <div
        aria-hidden="true"
        className="absolute inset-0 bg-[linear-gradient(rgba(25,24,71,.055)_1px,transparent_1px),linear-gradient(90deg,rgba(25,24,71,.055)_1px,transparent_1px)] bg-[size:76px_76px] opacity-70 [mask-image:linear-gradient(180deg,black,transparent_88%)] dark:bg-[linear-gradient(rgba(255,255,255,.05)_1px,transparent_1px),linear-gradient(90deg,rgba(255,255,255,.05)_1px,transparent_1px)]"
      />

      <div className="relative z-10 mx-auto max-w-7xl">
        <div className="mb-10 border-b border-black/10 pb-8 dark:border-white/10">
          <p className="mb-3 inline-flex items-center gap-2 rounded-full border border-black/10 bg-white px-4 py-2 text-sm font-semibold text-gray-600 dark:border-white/10 dark:bg-white/5 dark:text-gray-300">
            <Sparkles className="h-4 w-4 text-violet-500" />
            Kişisel alışveriş panelin
          </p>
          <h1 className="max-w-4xl text-5xl font-black leading-tight tracking-normal md:text-7xl">
            Hoşgeldin, {firstName}
          </h1>
        </div>

        <div className="mb-12 grid items-center gap-7 lg:grid-cols-[0.95fr_1.05fr]">
          <div className="rounded-[2rem] border border-white/70 bg-white/75 p-3 shadow-[0_24px_80px_rgba(25,24,71,0.12)] backdrop-blur-xl dark:border-white/10 dark:bg-white/10">
            <div className="flex flex-col gap-3 md:flex-row md:items-center">
              <div className="flex min-h-14 flex-1 items-center gap-3 rounded-3xl bg-white px-4 dark:bg-[#12101a]/70">
                <Search className="h-5 w-5 shrink-0 text-violet-500" />
                <input
                  type="url"
                  value={productUrl}
                  onChange={(event) => setProductUrl(event.target.value)}
                  onKeyDown={(event) => event.key === "Enter" && handleAnalyze()}
                  placeholder="Ürün linkini yapıştır, FiltreLAB analiz etsin..."
                  className="w-full bg-transparent py-4 text-sm font-medium text-[#191847] outline-none placeholder:text-gray-400 dark:text-white dark:placeholder:text-gray-500"
                />
              </div>
              <button
                onClick={handleAnalyze}
                disabled={!productUrl.trim()}
                className="inline-flex min-h-14 items-center justify-center gap-2 rounded-3xl bg-[#191847] px-6 text-sm font-bold text-white transition-all hover:bg-[#25235f] disabled:cursor-not-allowed disabled:opacity-45 dark:bg-white dark:text-[#191847] dark:hover:bg-gray-100"
              >
                Filtrele
                <ArrowRight className="h-4 w-4" />
              </button>
            </div>
            <p className="px-4 pb-2 pt-3 text-xs font-semibold text-gray-500 dark:text-gray-400">
              Kadın, erkek, çocuk, kozmetik, elektronik ve daha fazlası için ürün linki yapıştır.
            </p>
          </div>
          <CategorySpiral />
        </div>

        <div className="mb-12 flex flex-col gap-5 lg:flex-row lg:gap-0">
          {featureCards.map((feature, index) => {
            const Icon = feature.icon;
            return (
              <motion.div
                key={feature.title}
                className={`group relative min-h-72 flex-1 rounded-[2rem] border border-white/80 bg-white/85 p-8 shadow-[0_24px_70px_rgba(25,24,71,0.12)] backdrop-blur-xl transition-colors hover:border-white dark:border-white/10 dark:bg-white/10 ${
                  index > 0 ? "lg:-ml-7" : ""
                }`}
                style={{ zIndex: 10 + index }}
                initial={{ opacity: 0, y: 22, rotate: index === 1 ? -1.5 : index === 2 ? 1.5 : 0 }}
                animate={{ opacity: 1, y: [0, index % 2 === 0 ? -8 : 8, 0] }}
                whileHover={{ y: -14, rotate: 0, zIndex: 30 }}
                transition={{
                  opacity: { duration: 0.45, delay: index * 0.08 },
                  y: { duration: 4.2 + index * 0.4, repeat: Infinity, ease: "easeInOut" },
                }}
              >
                <Link href={feature.href} className="block h-full">
                  <div className={`mb-7 flex h-16 w-16 items-center justify-center rounded-2xl ${feature.bg}`}>
                    <Icon className={`h-8 w-8 ${feature.accent}`} />
                  </div>
                  <div className="flex items-end justify-between gap-4">
                    <div>
                      <h2 className="text-2xl font-black">{feature.title}</h2>
                      <p className="mt-3 max-w-xs text-base leading-7 text-gray-600 dark:text-gray-300">{feature.text}</p>
                    </div>
                    <p className="text-5xl font-black text-[#191847] dark:text-white">{counts[feature.countKey]}</p>
                  </div>
                </Link>
              </motion.div>
            );
          })}
        </div>

        <div className="mt-8 rounded-3xl border border-black/10 bg-white p-8 dark:border-white/10 dark:bg-white/5">
          <div className="mb-5 flex items-center gap-3">
            <BrainCircuit className="h-6 w-6 text-violet-500" />
            <h2 className="text-2xl font-black">Kişisel AI önerileri</h2>
          </div>
          {recommendations.length > 0 ? (
            <div className="grid gap-4 md:grid-cols-3">
              {recommendations.map((item) => (
                <div key={item.title} className="rounded-2xl border border-black/10 p-5 dark:border-white/10">
                  <p className="font-bold">{item.title}</p>
                  <p className="mt-2 text-sm leading-6 text-gray-600 dark:text-gray-300">{item.description}</p>
                </div>
              ))}
            </div>
          ) : (
            <p className="text-gray-600 dark:text-gray-300">
              İlk favori, fiyat takibi veya analiz kaydından sonra önerilerin burada görünecek.
            </p>
          )}
        </div>

        <div className="mt-8 rounded-3xl border border-black/10 bg-white p-8 dark:border-white/10 dark:bg-white/5">
          <div className="mb-5 flex items-center gap-3">
            <TrendingDown className="h-6 w-6 text-sky-500" />
            <h2 className="text-2xl font-black">Bugünkü odak</h2>
          </div>
          <p className="text-gray-600 dark:text-gray-300">
            Takibe aldığın ürünleri, favorilerini ve analiz geçmişini aynı yerden yönetebilirsin.
          </p>
          <div className="mt-5 flex flex-wrap gap-3">
            <Link href="/price-tracking" className="rounded-full border border-black/10 px-4 py-2 text-sm font-bold hover:bg-black/5 dark:border-white/10 dark:hover:bg-white/10">
              Fiyat takibine git
            </Link>
            <Link href="/history" className="rounded-full border border-black/10 px-4 py-2 text-sm font-bold hover:bg-black/5 dark:border-white/10 dark:hover:bg-white/10">
              Geçmişi aç
            </Link>
            <Link href="/favorites" className="rounded-full border border-black/10 px-4 py-2 text-sm font-bold hover:bg-black/5 dark:border-white/10 dark:hover:bg-white/10">
              Favorileri aç
            </Link>
          </div>
        </div>
      </div>
    </section>
  );
}
