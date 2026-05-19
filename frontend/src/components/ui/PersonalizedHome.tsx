"use client";

import { useEffect, useRef, useState } from "react";
import type { ReactNode } from "react";
import Link from "next/link";
import { useRouter } from "next/navigation";
import { motion } from "framer-motion";
import {
  ArrowRight,
  BrainCircuit,
  Heart,
  History,
  Loader2,
  Package,
  Search,
  ShoppingCart,
  Sparkles,
  Star,
  TrendingDown,
} from "lucide-react";
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

const shoppingStreamItems = [
  { Icon: Package, delay: 0, color: "text-sky-500", bg: "bg-sky-100/90 dark:bg-sky-400/15" },
  { Icon: Heart, delay: 1.1, color: "text-rose-500", bg: "bg-rose-100/90 dark:bg-rose-400/15" },
  { Icon: Star, delay: 2.2, color: "text-amber-500", bg: "bg-amber-100/90 dark:bg-amber-400/15" },
  { Icon: Package, delay: 3.3, color: "text-violet-500", bg: "bg-violet-100/90 dark:bg-violet-400/15" },
  { Icon: Heart, delay: 4.4, color: "text-fuchsia-500", bg: "bg-fuchsia-100/90 dark:bg-fuchsia-400/15" },
  { Icon: Star, delay: 5.5, color: "text-cyan-500", bg: "bg-cyan-100/90 dark:bg-cyan-400/15" },
];

function CategorySpiral() {
  const pathRef = useRef<SVGPathElement>(null);
  // Spiral sampled into equal-length points (% of the 1440×760 viewBox).
  // The final point is the cart, so items ride the line straight into it.
  const [ride, setRide] = useState<{ x: number; y: number }[]>([]);

  useEffect(() => {
    const path = pathRef.current;
    if (!path) return;
    const total = path.getTotalLength();
    if (!total) return;
    const SAMPLES = 28;
    const pts: { x: number; y: number }[] = [];
    for (let i = 0; i <= SAMPLES; i += 1) {
      const p = path.getPointAtLength((total * i) / SAMPLES);
      pts.push({ x: (p.x / 1440) * 100, y: (p.y / 760) * 100 });
    }
    pts.push({ x: 86, y: 24 }); // cart centre — items drop in here
    setRide(pts);
  }, []);

  return (
    <div className="pointer-events-none absolute inset-x-[-8%] top-28 z-0 h-[560px] overflow-hidden opacity-95 md:top-20 md:h-[720px] lg:inset-x-[-4%] lg:h-[780px]">
      <div className="absolute inset-0 bg-[radial-gradient(circle_at_55%_42%,rgba(255,255,255,0.55),rgba(216,180,254,0.18)_34%,rgba(124,58,237,0.18)_70%,transparent)] dark:bg-[radial-gradient(circle_at_55%_42%,rgba(255,255,255,0.08),rgba(124,58,237,0.22)_34%,rgba(49,46,129,0.24)_70%,transparent)]" />
      <svg
        className="absolute inset-0 h-full w-full"
        viewBox="0 0 1440 760"
        fill="none"
        aria-hidden="true"
        preserveAspectRatio="none"
      >
        <defs>
          <linearGradient id="categorySpiralGradient" x1="96" y1="440" x2="1340" y2="190" gradientUnits="userSpaceOnUse">
            <stop stopColor="#38bdf8" stopOpacity="0.28" />
            <stop offset="0.38" stopColor="#a78bfa" stopOpacity="0.7" />
            <stop offset="0.72" stopColor="#f0abfc" stopOpacity="0.62" />
            <stop offset="1" stopColor="#22d3ee" stopOpacity="0.34" />
          </linearGradient>
          <filter id="categorySpiralGlow" x="-20%" y="-40%" width="140%" height="180%">
            <feGaussianBlur stdDeviation="14" result="blur" />
            <feMerge>
              <feMergeNode in="blur" />
              <feMergeNode in="SourceGraphic" />
            </feMerge>
          </filter>
        </defs>
        <motion.path
          ref={pathRef}
          d="M80 420 C190 150 385 150 470 330 C544 488 338 560 318 365 C294 130 615 110 720 325 C826 542 548 610 542 346 C536 82 912 76 1010 318 C1112 568 895 644 806 470 C710 282 930 140 1360 178"
          stroke="rgba(255,255,255,0.68)"
          strokeWidth="42"
          strokeLinecap="round"
          filter="url(#categorySpiralGlow)"
        />
        <motion.path
          d="M80 420 C190 150 385 150 470 330 C544 488 338 560 318 365 C294 130 615 110 720 325 C826 542 548 610 542 346 C536 82 912 76 1010 318 C1112 568 895 644 806 470 C710 282 930 140 1360 178"
          stroke="url(#categorySpiralGradient)"
          strokeWidth="12"
          strokeLinecap="round"
          strokeDasharray="26 18"
          animate={{ strokeDashoffset: [0, -88] }}
          transition={{ duration: 6.5, repeat: Infinity, ease: "linear" }}
        />
      </svg>

      <motion.div
        className="absolute right-[7%] top-[18%] grid h-28 w-28 place-items-center rounded-[2rem] border border-white/70 bg-white/72 text-[#191847] shadow-[0_26px_70px_rgba(25,24,71,0.18)] backdrop-blur-xl dark:border-white/10 dark:bg-white/10 dark:text-white md:h-36 md:w-36"
        animate={{ scale: [1, 1.04, 1], y: [0, -6, 0] }}
        transition={{ duration: 3.8, repeat: Infinity, ease: "easeInOut" }}
      >
        <div className="absolute inset-3 rounded-[1.5rem] bg-[radial-gradient(circle_at_30%_25%,rgba(255,255,255,0.85),rgba(125,211,252,0.22),rgba(168,85,247,0.18))] dark:bg-[radial-gradient(circle_at_30%_25%,rgba(255,255,255,0.18),rgba(125,211,252,0.12),rgba(168,85,247,0.18))]" />
        <ShoppingCart className="relative h-14 w-14 drop-shadow-[0_12px_24px_rgba(25,24,71,0.18)] md:h-20 md:w-20" strokeWidth={1.4} />
      </motion.div>

      {/* Heart / star / box icons travelling along the spiral and into the cart */}
      {ride.length > 1 &&
        shoppingStreamItems.map(({ Icon, delay, color, bg }) => (
          <motion.div
            key={`${color}-${delay}`}
            className={`absolute grid h-10 w-10 place-items-center rounded-2xl border border-white/70 ${bg} shadow-[0_18px_42px_rgba(25,24,71,0.14)] backdrop-blur-md dark:border-white/10 md:h-12 md:w-12`}
            style={{ left: 0, top: 0, x: "-50%", y: "-50%", opacity: 0 }}
            animate={{
              left: ride.map((p) => `${p.x}%`),
              top: ride.map((p) => `${p.y}%`),
              opacity: [0, 1, 1, 1, 1, 0.6, 0],
              scale: [0.45, 1, 1, 1, 1, 0.5, 0.12],
              rotate: [0, 16, -12, 14, -10, 8, 0],
            }}
            transition={{ duration: 9, delay, repeat: Infinity, ease: "linear" }}
          >
            <Icon className={`h-5 w-5 ${color} md:h-6 md:w-6`} strokeWidth={1.8} />
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
      <CategorySpiral />

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

        <div className="mb-24 max-w-2xl">
          <div className="rounded-[2rem] border border-white/70 bg-white/80 p-3 shadow-[0_24px_80px_rgba(25,24,71,0.12)] backdrop-blur-xl dark:border-white/10 dark:bg-white/10">
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
              Ürün linkini yapıştır, FiltreLAB sepetine girmeden önce analiz etsin.
            </p>
          </div>
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
              İlk favori veya analiz kaydından sonra önerilerin burada görünecek.
            </p>
          )}
        </div>

        <div className="mt-8 rounded-3xl border border-black/10 bg-white p-8 dark:border-white/10 dark:bg-white/5">
          <div className="mb-5 flex items-center gap-3">
            <TrendingDown className="h-6 w-6 text-sky-500" />
            <h2 className="text-2xl font-black">Bugünkü odak</h2>
          </div>
          <p className="text-gray-600 dark:text-gray-300">
            Favorilerini ve analiz geçmişini aynı yerden yönetebilirsin.
          </p>
          <div className="mt-5 flex flex-wrap gap-3">
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
