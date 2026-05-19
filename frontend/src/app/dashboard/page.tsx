"use client";

import { useEffect, useState, Suspense } from "react";
import { useSearchParams } from "next/navigation";
import { motion } from "framer-motion";
import {
  runAIAnalysis,
  addFavorite,
  deleteFavorite,
  getFavorites,
  addPriceTracking,
  deletePriceTracking,
  getPriceTracking,
  addAnalysisHistory,
  type AIAnalysisResult,
} from "@/lib/apiClient";
import { AnimatedCard } from "@/components/ui/AnimatedCard";
import { ProgressBar } from "@/components/ui/ProgressBar";
import { FinalVerdict } from "@/components/ui/FinalVerdict";
import { ScanTimeline } from "@/components/ui/ScanTimeline";
import { CrossPlatformPrices } from "@/components/CrossPlatformPrices";
import { ReviewIntelligence } from "@/components/ReviewIntelligence";
import { ShoppingPersonality } from "@/components/ShoppingPersonality";
import { ShieldAlert, PackageX, BrainCircuit, ArrowLeft, Star, TrendingUp, Zap, Sparkles, Bell, Heart, Loader2 } from "lucide-react";
import Link from "next/link";
import Image from "next/image";

const LAST_ANALYSIS_KEY = "filtre_last_analysis";

function isValidImageUrl(url: unknown): url is string {
  return (
    typeof url === "string" &&
    url.trim() !== "" &&
    (url.startsWith("https://") || url.startsWith("http://"))
  );
}

function isNumber(value: unknown): value is number {
  return typeof value === "number" && Number.isFinite(value);
}

function formatPercent(value: unknown): string {
  return isNumber(value) ? `%${Math.round(value as number)}` : "—";
}

function formatScore(value: unknown, max: number): string {
  return isNumber(value) ? `${value}/${max}` : "—";
}

function progressValue(value: unknown): number {
  if (!isNumber(value)) return 0;
  return Math.max(0, Math.min(100, value as number));
}

function DashboardContent() {
  const searchParams = useSearchParams();
  const url = searchParams.get("url") || "";

  const [isScanning, setIsScanning] = useState(true);
  const [result, setResult] = useState<AIAnalysisResult | null>(null);
  const [error, setError] = useState<string | null>(null);
  const [featureMessage, setFeatureMessage] = useState<string | null>(null);
  const [favoriteId, setFavoriteId] = useState<number | null>(null);
  const [trackingId, setTrackingId] = useState<number | null>(null);
  const [statusChecked, setStatusChecked] = useState(false);
  const [favBusy, setFavBusy] = useState(false);
  const [trackBusy, setTrackBusy] = useState(false);
  type StepStatus = "pending" | "scanning" | "completed";
  const [timelineSteps, setTimelineSteps] = useState<{ id: number; message: string; status: StepStatus }[]>([
    { id: 1, message: "Link alındı", status: "pending" },
    { id: 2, message: "Yorumlar analiz ediliyor", status: "pending" },
    { id: 3, message: "Sahte yorum kontrolü", status: "pending" },
    { id: 4, message: "Fiyat karşılaştırması", status: "pending" },
    { id: 5, message: "AI karar oluşturuyor", status: "pending" },
  ]);
  const isWaitingForResult = timelineSteps.every((step) => step.status === "completed");
  
  useEffect(() => {
    let mounted = true;
    
    const runAnalysisLogic = async () => {
      try {
        const response = await runAIAnalysis(url, (stepIndex) => {
          if (!mounted) return;
          setTimelineSteps((prev) => prev.map((step, idx) => {
            if (idx < stepIndex) return { ...step, status: "completed" };
            if (idx === stepIndex) return { ...step, status: "scanning" };
            return { ...step, status: "pending" };
          }));
        });
        
        if (mounted) {
          if (response.success) {
            setResult(response.data);
            if (typeof window !== "undefined") {
              localStorage.setItem(LAST_ANALYSIS_KEY, JSON.stringify(response.data));
            }
            addAnalysisHistory({
              productName: response.data.productName,
              productUrl: response.data.sourceUrl || url,
              image: response.data.image ?? null,
              price: response.data.price ?? null,
              finalDecision: response.data.finalDecision ?? null,
              trustScore: response.data.trustScore ?? null,
            }).catch(() => undefined);
          } else {
            setError(response.error);
          }
          setTimeout(() => setIsScanning(false), 800);
        }
      } catch (err) {
        if (mounted) {
          const errorMessage = err instanceof Error ? err.message : "Bu ürün bilgileri alınamadı. Lütfen geçerli bir ürün linki deneyin.";
          setError(errorMessage);
          setIsScanning(false);
        }
      }
    };

    runAnalysisLogic();

    return () => { mounted = false; };
  }, [url]);

  // Ürün açıldığında favori / fiyat takibi durumunu kontrol et.
  useEffect(() => {
    if (!result) return;
    const productUrl = result.sourceUrl || url;
    let active = true;
    (async () => {
      const [favRes, trackRes] = await Promise.all([getFavorites(), getPriceTracking()]);
      if (!active) return;
      if (favRes.success) {
        const match = favRes.data.items?.find((it) => it.productUrl === productUrl);
        setFavoriteId(match ? match.id : null);
      }
      if (trackRes.success) {
        const match = trackRes.data.items?.find((it) => it.productUrl === productUrl);
        setTrackingId(match ? match.id : null);
      }
      setStatusChecked(true);
    })();
    return () => { active = false; };
  }, [result, url]);

  if (isScanning) {
    return (
      <div className="min-h-screen flex flex-col items-center justify-center p-8 relative overflow-hidden">
        <div className="fixed top-0 left-0 w-full h-full overflow-hidden pointer-events-none z-0">
          <div className="absolute top-[-20%] right-[-10%] w-[50%] h-[50%] bg-[var(--neon-purple)] opacity-10 blur-[150px] rounded-full" />
          <div className="absolute bottom-[-20%] left-[-10%] w-[50%] h-[50%] bg-[var(--neon-blue)] opacity-10 blur-[150px] rounded-full" />
        </div>
        <motion.div
          initial={{ opacity: 0, scale: 0.9 }}
          animate={{ opacity: 1, scale: 1 }}
          className="relative z-10 bg-white/80 dark:bg-[var(--bg-card)] border border-white/70 dark:border-white/10 rounded-3xl p-12 w-full max-w-2xl shadow-[0_20px_80px_rgba(25,24,71,0.10)] dark:shadow-[0_0_60px_rgba(0,212,255,0.08)] backdrop-blur-xl"
        >
          <div className="text-center mb-12">
            <BrainCircuit className="w-16 h-16 text-[var(--neon-blue)] mx-auto mb-6 animate-pulse" />
            <h2 className="text-3xl font-bold mb-2">FiltreLAB Analiz Motoru Devrede</h2>
            <p className="text-gray-700 dark:text-gray-300">Bu ürün için binlerce veri noktası analiz ediliyor...</p>
          </div>
          <ScanTimeline steps={timelineSteps} />
          {isWaitingForResult && (
            <motion.div
              initial={{ opacity: 0, y: 8 }}
              animate={{ opacity: 1, y: 0 }}
              className="mt-10 flex items-center justify-center gap-3 text-sm font-semibold text-gray-600 dark:text-gray-300"
            >
              <Loader2 className="h-5 w-5 animate-spin text-[var(--neon-blue)]" />
              <span>Yükleniyor, sonuç sayfası hazırlanıyor...</span>
            </motion.div>
          )}
        </motion.div>
      </div>
    );
  }

  if (error) {
    return (
      <div className="min-h-screen flex flex-col items-center justify-center p-8 relative">
        <div className="fixed top-0 left-0 w-full h-full overflow-hidden pointer-events-none z-0">
          <div className="absolute top-[-20%] right-[-10%] w-[50%] h-[50%] bg-[var(--neon-pink)] opacity-10 blur-[150px] rounded-full" />
        </div>
        <motion.div
          initial={{ opacity: 0, scale: 0.9 }}
          animate={{ opacity: 1, scale: 1 }}
          className="bg-[var(--bg-card)] border border-[var(--neon-pink)]/30 rounded-3xl p-12 w-full max-w-xl shadow-[0_0_50px_rgba(255,42,109,0.1)] backdrop-blur-xl text-center relative z-10"
        >
          <ShieldAlert className="w-20 h-20 text-[var(--neon-pink)] mx-auto mb-6" />
          <h2 className="text-3xl font-bold mb-4">Analiz Başarısız</h2>
          <p className="text-gray-700 dark:text-gray-300 mb-8 leading-relaxed">{error}</p>
          <Link href="/">
            <button className="bg-[#191847] hover:bg-[#242266] dark:bg-white/5 dark:hover:bg-white/10 text-white border border-[#191847]/20 dark:border-white/20 px-8 py-3 rounded-full font-bold transition-all">
              Yeni Arama Yap
            </button>
          </Link>
        </motion.div>
      </div>
    );
  }

  if (!result) return null;

  const handleTogglePriceTracking = async () => {
    if (!result || trackBusy) return;
    setTrackBusy(true);
    if (trackingId !== null) {
      const res = await deletePriceTracking(trackingId);
      if (res.success) {
        setTrackingId(null);
        setFeatureMessage("Fiyat takibinden çıkarıldı.");
      } else {
        setFeatureMessage(res.error === "Backend bağlantısı kurulamadı." ? "Bağlantı hatası." : "İşlem başarısız.");
      }
    } else {
      const res = await addPriceTracking({
        productName: result.productName,
        productUrl: result.sourceUrl || url,
        currentPrice: result.price || "0 TL",
        image: result.image ?? null,
        platform: result.sourcePlatform ?? null,
      });
      if (res.success) {
        setTrackingId(res.data.item?.id ?? null);
        setFeatureMessage("Fiyat takibine eklendi!");
      } else {
        setFeatureMessage(res.error === "Backend bağlantısı kurulamadı." ? "Bağlantı hatası." : "Giriş yapmalısınız.");
      }
    }
    setTrackBusy(false);
    setTimeout(() => setFeatureMessage(null), 3000);
  };

  const handleToggleFavorite = async () => {
    if (!result || favBusy) return;
    setFavBusy(true);
    if (favoriteId !== null) {
      const res = await deleteFavorite(favoriteId);
      if (res.success) {
        setFavoriteId(null);
        setFeatureMessage("Favorilerden kaldırıldı.");
      } else {
        setFeatureMessage(res.error === "Backend bağlantısı kurulamadı." ? "Bağlantı hatası." : "İşlem başarısız.");
      }
    } else {
      const res = await addFavorite({
        productName: result.productName,
        productUrl: result.sourceUrl || url,
        image: result.image ?? null,
        price: result.price ?? null,
        platform: result.sourcePlatform ?? null,
      });
      if (res.success) {
        setFavoriteId(res.data.item?.id ?? null);
        setFeatureMessage("Favorilere eklendi!");
      } else {
        setFeatureMessage(res.error === "Backend bağlantısı kurulamadı." ? "Bağlantı hatası." : "Giriş yapmalısınız.");
      }
    }
    setFavBusy(false);
    setTimeout(() => setFeatureMessage(null), 3000);
  };

  return (
    <div className="min-h-screen p-6 md:p-12 relative">
      {/* Abstract Background */}
      <div className="fixed top-0 left-0 w-full h-full overflow-hidden pointer-events-none z-0">
        <div className="absolute top-[-20%] right-[-10%] w-[50%] h-[50%] bg-[var(--neon-purple)] opacity-10 blur-[150px] rounded-full" />
        <div className="absolute bottom-[-20%] left-[-10%] w-[50%] h-[50%] bg-[var(--neon-blue)] opacity-10 blur-[150px] rounded-full" />
      </div>

      <div className="max-w-7xl mx-auto relative z-10">
        <Link href="/" className="inline-flex items-center text-gray-500 hover:text-[#191847] dark:text-gray-400 dark:hover:text-white transition-colors mb-8">
          <ArrowLeft className="w-5 h-5 mr-2" />
          Aramaya Dön
        </Link>

        <div className="grid grid-cols-1 lg:grid-cols-12 gap-8">
          
          {/* Left Column: Product Info */}
          <div className="lg:col-span-4 space-y-6">
            <AnimatedCard className="p-0 overflow-hidden" delay={0.1}>
              {isValidImageUrl(result.image) ? (
                <div className="relative h-80 w-full bg-white rounded-t-3xl overflow-hidden">
                  <Image
                    src={result.image}
                    alt={result.productName || "Ürün görseli"}
                    fill
                    className="object-contain p-4"
                    sizes="(max-width: 768px) 100vw, 420px"
                  />
                </div>
              ) : (
                <div className="flex h-80 w-full items-center justify-center bg-gray-100 dark:bg-neutral-900 text-gray-500 dark:text-neutral-500 text-sm rounded-t-3xl">
                  Görsel bulunamadı
                </div>
              )}
              <div className="p-6">
                <div className="flex flex-col gap-1 mb-2">
                  <span className="text-xs font-bold uppercase tracking-wider text-gray-500 dark:text-gray-400">{result.category}</span>
                  <span className="text-sm font-semibold text-[var(--neon-purple)]">{result.brand}</span>
                </div>
                <h2 className="text-2xl font-bold mb-3 leading-tight">{result.productName}</h2>
                <div className="text-3xl font-black text-[var(--neon-blue)] neon-text-blue mb-4">{result.price}</div>

                <div className="grid grid-cols-1 sm:grid-cols-2 gap-3 mb-4">
                  <button
                    onClick={handleTogglePriceTracking}
                    disabled={!statusChecked || trackBusy}
                    className="inline-flex items-center justify-center gap-2 rounded-2xl border border-[var(--neon-blue)]/30 bg-[var(--neon-blue)]/10 px-4 py-3 text-sm font-bold text-[var(--neon-blue)] hover:bg-[var(--neon-blue)]/15 transition-colors disabled:opacity-60 disabled:cursor-not-allowed"
                  >
                    <Bell className="h-4 w-4" />
                    {trackingId !== null ? "Takipten Çıkar" : "Fiyat Takibine Ekle"}
                  </button>
                  <button
                    onClick={handleToggleFavorite}
                    disabled={!statusChecked || favBusy}
                    className="inline-flex items-center justify-center gap-2 rounded-2xl border border-[var(--neon-pink)]/30 bg-[var(--neon-pink)]/10 px-4 py-3 text-sm font-bold text-[var(--neon-pink)] hover:bg-[var(--neon-pink)]/15 transition-colors disabled:opacity-60 disabled:cursor-not-allowed"
                  >
                    <Heart className={`h-4 w-4 ${favoriteId !== null ? "fill-current" : ""}`} />
                    {favoriteId !== null ? "Favorilerden Kaldır" : "Favorilere Ekle"}
                  </button>
                </div>

                {featureMessage && (
                  <p className="mb-4 rounded-2xl border border-black/10 dark:border-white/10 bg-white/80 dark:bg-white/5 px-4 py-3 text-sm text-gray-700 dark:text-gray-300">
                    {featureMessage}
                  </p>
                )}
                
              </div>
            </AnimatedCard>

            <AnimatedCard delay={0.2} className="bg-gradient-to-br from-white to-blue-50/80 dark:from-gray-900 dark:to-black border-[var(--neon-blue)]/20">
              <h3 className="text-lg font-bold mb-3 flex items-center gap-2">
                <Sparkles className="text-yellow-400" /> Alışveriş Psikolojisi Analizi
              </h3>
              <p className="text-sm text-gray-700 dark:text-gray-300 leading-relaxed">
                {result.shoppingBehavior}
              </p>
            </AnimatedCard>
          </div>

          {/* Right Column: Analytics & Verdict */}
          <div className="lg:col-span-8 space-y-6">
            
            {/* Top row analytics */}
            <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
              <AnimatedCard delay={0.3}>
                <div className="flex items-center mb-6">
                  <ShieldAlert className="w-6 h-6 text-[var(--neon-pink)] mr-3" />
                  <h3 className="text-lg font-bold">Sahte Yorum Riski</h3>
                </div>
                <div className="flex items-end mb-4">
                  <span className="text-5xl font-black">{`%${result.fakeReviewRisk}`}</span>
                  <span className="text-gray-500 dark:text-gray-400 ml-2 mb-1">risk skoru</span>
                </div>
                <ProgressBar label="Fiyat Performansı" value={progressValue(result.pricePerformance)} color="var(--neon-green)" />
                <ProgressBar label="Sahte Yorum Riski" value={progressValue(result.fakeReviewRisk)} color="var(--neon-pink)" />
              </AnimatedCard>

              <AnimatedCard delay={0.4}>
                <div className="flex items-center mb-6">
                  <PackageX className="w-6 h-6 text-[var(--neon-purple)] mr-3" />
                  <h3 className="text-lg font-bold">İade Riski</h3>
                </div>
                <div className="flex items-end mb-4">
                  <span className="text-5xl font-black text-[var(--neon-purple)]">{result.returnRisk}</span>
                </div>
                <ProgressBar value={result.returnRisk === "Yüksek" ? 85 : result.returnRisk === "Orta" ? 50 : 15} color="var(--neon-purple)" showValue={false} />
              </AnimatedCard>
            </div>

            {/* Middle row scores */}
            <div className="grid grid-cols-1 md:grid-cols-3 gap-6">
              <AnimatedCard delay={0.5} className="flex flex-col items-center justify-center text-center p-4">
                <Star className="w-8 h-8 text-yellow-500 mb-2" />
                <div className="text-3xl font-bold">{formatScore(result.trustScore, 100)}</div>
                <div className="text-xs text-gray-500 dark:text-gray-400 uppercase tracking-wider mt-1">Güven Skoru</div>
              </AnimatedCard>

              <AnimatedCard delay={0.6} className="flex flex-col items-center justify-center text-center p-4">
                <TrendingUp className="w-8 h-8 text-[var(--neon-green)] mb-2" />
                <div className="text-3xl font-bold">{formatPercent(result.sentimentScore)}</div>
                <div className="text-xs text-gray-500 dark:text-gray-400 uppercase tracking-wider mt-1">Yorum Duygu Skoru</div>
              </AnimatedCard>

              <AnimatedCard delay={0.7} className="flex flex-col items-center justify-center text-center p-4">
                <Zap className="w-8 h-8 text-[var(--neon-blue)] mb-2" />
                <div className="text-3xl font-bold">{formatScore(result.pricePerformance, 100)}</div>
                <div className="text-xs text-gray-500 dark:text-gray-400 uppercase tracking-wider mt-1">Fiyat / Performans</div>
              </AnimatedCard>
            </div>

            {/* Final Verdict */}
            <FinalVerdict
              decision={result.finalDecision}
              reason={result.analysis || ""}
              confidenceLevel={result.confidenceLevel}
              dataWarning={result.dataWarning}
            />

            {/* SYSTEM 1 — Yapay Zeka Yorum Analizi (Pseudo Comprehend) */}
            {result.reviewIntelligence && (
              <ReviewIntelligence data={result.reviewIntelligence} />
            )}

            {/* Yapay Zeka Kararı */}
            <motion.div
              initial={{ opacity: 0, y: 20 }}
              animate={{ opacity: 1, y: 0 }}
              transition={{ delay: 1 }}
              className="mt-14 pt-10 border-t border-white/10"
            >
              <h3 className="text-xl font-bold mb-5 flex items-center gap-2">
                <BrainCircuit className="text-[var(--neon-blue)]" /> Yapay Zeka Kararı
              </h3>
              <p className="text-gray-700 dark:text-gray-300 leading-relaxed">
                {result.analysis}
              </p>
            </motion.div>

            {/* Platform Fiyat Karşılaştırması — tam genişlik */}
            <div className="mt-16 pt-12 border-t-2 border-white/10 flex flex-wrap gap-8 items-start">
              <motion.div
                initial={{ opacity: 0, y: 20 }}
                animate={{ opacity: 1, y: 0 }}
                transition={{ delay: 1.1 }}
                className="order-1 w-full flex-[1_1_100%]"
              >
                <CrossPlatformPrices
                  sourcePlatform={result.sourcePlatform ?? ""}
                  productName={result.productName ?? ""}
                  brand={result.brand ?? ""}
                  priceStr={result.price ?? ""}
                  sourceUrl={result.sourceUrl}
                  sourceImage={result.image}
                  className="mt-0 pt-0 border-t-0"
                />
              </motion.div>

            {/* Daha İyi Alternatif Bulundu — tam genişlik, belirgin ayraçla */}
            <motion.div
              id="alternatives"
              initial={{ opacity: 0, y: 20 }}
              animate={{ opacity: 1, y: 0 }}
              transition={{ delay: 1.2 }}
              className="order-2 flex-[1_1_100%]"
            >
              <h3 className="text-xl font-bold mb-8 flex items-center">
                <Sparkles className="w-5 h-5 text-[var(--neon-blue)] mr-2" />
                Daha İyi Alternatif Bulundu
              </h3>
              {(result.betterAlternatives || []).length > 0 ? (
                <div className="grid grid-cols-1 gap-6">
                  {(result.betterAlternatives || []).map((alt, idx) => (
                    <Link
                      href={alt.url || "#"}
                      key={idx}
                      className="block group"
                      target="_blank"
                      rel="noopener noreferrer"
                    >
                      <AnimatedCard className="flex items-center p-5 lg:p-6 gap-4 lg:gap-5 bg-white/75 dark:bg-white/5 border-black/10 dark:border-white/10 group-hover:bg-white dark:group-hover:bg-white/10 group-hover:border-[var(--neon-blue)]/30 transition-all cursor-pointer">
                        <div className="relative w-24 h-24 rounded-lg overflow-hidden flex-shrink-0 bg-white">
                          {isValidImageUrl(alt.image) ? (
                            <Image src={alt.image} alt={alt.name || "Ürün görseli"} fill className="object-contain p-1" sizes="96px" />
                          ) : (
                            <div className="flex h-full w-full items-center justify-center bg-gray-100 dark:bg-neutral-800 text-gray-500 dark:text-neutral-500 text-xs text-center p-1 leading-tight">
                              Görsel Yok
                            </div>
                          )}
                        </div>
                        <div className="min-w-0 flex-1">
                          <div className="flex items-center gap-2 mb-1.5">
                            {alt.platform && (
                              <span className="text-xs font-semibold px-2 py-0.5 rounded-full bg-gray-100 dark:bg-white/10 text-gray-600 dark:text-gray-300 border border-black/10 dark:border-white/10">
                                {alt.platform}
                              </span>
                            )}
                          </div>
                          <h4 className="font-bold text-base leading-snug break-normal group-hover:text-[var(--neon-blue)] transition-colors">{alt.name}</h4>
                          <p className="text-lg text-[var(--neon-blue)] font-black mt-1.5">{alt.price}</p>
                          <p className="text-sm text-gray-700 dark:text-gray-300 mt-2 leading-relaxed">{alt.reason}</p>
                        </div>
                        <div className="hidden xl:flex px-4 py-2 rounded-lg bg-[var(--neon-blue)]/10 text-[var(--neon-blue)] text-sm font-bold border border-[var(--neon-blue)]/20 whitespace-nowrap">
                          Ürüne Git
                        </div>
                      </AnimatedCard>
                    </Link>
                  ))}
                </div>
              ) : (
                <AnimatedCard className="text-center p-10 border-dashed border-white/20 bg-transparent">
                  <p className="text-gray-500 dark:text-gray-400">Doğrulanmış alternatif ürün bulunamadı.</p>
                </AnimatedCard>
              )}
            </motion.div>

            {/* SYSTEM 2 — Alışveriş Kişiliği (Shopping Psychology) */}
            <ShoppingPersonality result={result} />
            </div>

          </div>
        </div>
      </div>
    </div>
  );
}

export default function DashboardPage() {
  return (
    <Suspense fallback={<div className="min-h-screen flex items-center justify-center text-[#191847] dark:text-white">Yükleniyor...</div>}>
      <DashboardContent />
    </Suspense>
  );
}
