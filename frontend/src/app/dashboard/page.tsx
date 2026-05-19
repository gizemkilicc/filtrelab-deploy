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
import { ScanTimeline } from "@/components/ui/ScanTimeline";
import { CrossPlatformPrices } from "@/components/CrossPlatformPrices";
import { ReviewIntelligence } from "@/components/ReviewIntelligence";
import { ShoppingPersonality } from "@/components/ShoppingPersonality";
import { ArrowLeft, Bell, Heart, Loader2 } from "lucide-react";
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

function verdictColor(decision: string | null | undefined): string {
  const d = (decision || "").toLocaleUpperCase("tr-TR");
  if (d.includes("ALINAB") || d.includes("ÖNER")) return "var(--verdict-buy)";
  if (d.includes("DİKKAT") || d.includes("KARARSIZ") || d.includes("ORTA")) return "var(--verdict-caution)";
  if (d.includes("ALMA") || d.includes("UZAK") || d.includes("BEKLE")) return "var(--verdict-wait)";
  return "var(--brass)";
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
      <div className="fl-page flex flex-col items-center justify-center px-6 py-20">
        <motion.div
          initial={{ opacity: 0, y: 16 }}
          animate={{ opacity: 1, y: 0 }}
          transition={{ duration: 0.6, ease: [0.16, 1, 0.3, 1] }}
          className="fl-card w-full max-w-2xl p-10 md:p-14"
        >
          <p className="fl-kicker mb-3">EVRE · TARAMA</p>
          <h2 className="fl-serif text-[40px] leading-[1.05] text-[var(--paper)]">
            FiltreLAB Analiz Motoru Devrede
          </h2>
          <p className="fl-sans mt-3 text-[14px] text-[var(--ink-30)]">
            Bu ürün için binlerce veri noktası analiz ediliyor.
          </p>
          <div className="mt-9">
            <ScanTimeline steps={timelineSteps} />
          </div>
          {isWaitingForResult && (
            <motion.div
              initial={{ opacity: 0, y: 8 }}
              animate={{ opacity: 1, y: 0 }}
              className="mt-9 flex items-center gap-3 fl-mono text-[11px] uppercase tracking-[0.12em] text-[var(--ink-30)]"
            >
              <Loader2 className="h-4 w-4 animate-spin text-[var(--brass)]" />
              <span>Yükleniyor, sonuç sayfası hazırlanıyor...</span>
            </motion.div>
          )}
        </motion.div>
      </div>
    );
  }

  if (error) {
    return (
      <div className="fl-page flex items-center justify-center px-6 py-20">
        <motion.div
          initial={{ opacity: 0, y: 16 }}
          animate={{ opacity: 1, y: 0 }}
          transition={{ duration: 0.6, ease: [0.16, 1, 0.3, 1] }}
          className="fl-card w-full max-w-xl p-10 md:p-14 text-center"
        >
          <p className="fl-kicker mb-3" style={{ color: "var(--verdict-caution)" }}>
            EVRE · HATA
          </p>
          <h2 className="fl-serif text-[44px] leading-[1.05] text-[var(--paper)]">Analiz Başarısız</h2>
          <p className="fl-sans mt-4 text-[14px] leading-relaxed text-[var(--ink-30)]">{error}</p>
          <Link href="/" className="mt-8 inline-block">
            <span className="fl-btn fl-btn-primary">Yeni Arama Yap</span>
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

  const decisionTone = verdictColor(result.finalDecision);

  const dataRows: { label: string; value: string }[] = [
    { label: "Güven Skoru", value: formatScore(result.trustScore, 100) },
    { label: "Yorum Duygu Skoru", value: formatPercent(result.sentimentScore) },
    { label: "Fiyat / Performans", value: formatScore(result.pricePerformance, 100) },
    { label: "Sahte Yorum Riski", value: isNumber(result.fakeReviewRisk) ? `%${result.fakeReviewRisk}` : "—" },
    { label: "İade Riski", value: result.returnRisk || "—" },
  ];

  return (
    <div className="fl-page px-6 py-14 md:px-12">
      <div className="mx-auto max-w-6xl">
        <Link href="/" className="fl-link inline-flex items-center fl-mono text-[11px] uppercase tracking-[0.14em]">
          <ArrowLeft className="mr-2 h-4 w-4" />
          Aramaya Dön
        </Link>

        <p className="fl-kicker mt-9">EVRE · NİHAİ KARAR</p>

        {/* HERO — ürün görseli sol, karar sağ */}
        <div className="mt-6 grid grid-cols-1 gap-10 lg:grid-cols-12">
          {/* Sol: ürün görseli + meta */}
          <motion.div
            initial={{ opacity: 0, y: 16 }}
            animate={{ opacity: 1, y: 0 }}
            transition={{ duration: 0.6, ease: [0.16, 1, 0.3, 1] }}
            className="lg:col-span-5"
          >
            <div className="fl-card overflow-hidden">
              {isValidImageUrl(result.image) ? (
                <div className="relative h-80 w-full bg-[var(--bg-deep)]">
                  <Image
                    src={result.image}
                    alt={result.productName || "Ürün görseli"}
                    fill
                    className="object-contain p-5"
                    sizes="(max-width: 1024px) 100vw, 460px"
                  />
                </div>
              ) : (
                <div className="flex h-80 w-full items-center justify-center fl-mono text-[11px] uppercase tracking-[0.12em] text-[var(--ink-50)]">
                  Görsel bulunamadı
                </div>
              )}
            </div>

            <div className="mt-6">
              <p className="fl-kicker">
                {[result.category, result.brand].filter(Boolean).join(" · ") || "ÜRÜN"}
              </p>
              <h2 className="fl-serif mt-2 text-[26px] leading-snug text-[var(--paper)]">
                {result.productName}
              </h2>
              <p className="fl-mono mt-3 text-[24px] text-[var(--brass)]">{result.price}</p>

              <div className="mt-5 grid grid-cols-1 gap-3 sm:grid-cols-2">
                <button
                  onClick={handleTogglePriceTracking}
                  disabled={!statusChecked || trackBusy}
                  className={`fl-btn ${trackingId !== null ? "fl-btn-primary" : "fl-btn-ghost"}`}
                >
                  <Bell className="h-4 w-4" />
                  {trackingId !== null ? "Takipten Çıkar" : "Fiyat Takibi"}
                </button>
                <button
                  onClick={handleToggleFavorite}
                  disabled={!statusChecked || favBusy}
                  className={`fl-btn ${favoriteId !== null ? "fl-btn-primary" : "fl-btn-ghost"}`}
                >
                  <Heart className={`h-4 w-4 ${favoriteId !== null ? "fill-current" : ""}`} />
                  {favoriteId !== null ? "Favoriden Çıkar" : "Favorilere Ekle"}
                </button>
              </div>

              {featureMessage && (
                <p className="mt-4 rounded-[3px] border border-[var(--ink-70)] px-4 py-3 fl-mono text-[11px] uppercase tracking-[0.1em] text-[var(--ink-10)]">
                  {featureMessage}
                </p>
              )}
            </div>
          </motion.div>

          {/* Sağ: karar */}
          <motion.div
            initial={{ opacity: 0, y: 16 }}
            animate={{ opacity: 1, y: 0 }}
            transition={{ duration: 0.6, delay: 0.1, ease: [0.16, 1, 0.3, 1] }}
            className="lg:col-span-7"
          >
            <p className="fl-kicker">FİLTRELAB KARARI</p>
            <h1
              className="fl-serif mt-3 text-[56px] leading-[1.02] md:text-[72px]"
              style={{ color: decisionTone }}
            >
              {result.finalDecision || "Karar Yok"}
            </h1>

            <div className="mt-5 flex flex-wrap items-center gap-3">
              <span className="fl-pill" style={{ color: decisionTone }}>
                {result.finalDecision || "KARAR YOK"}
              </span>
              {result.confidenceLevel && (
                <span className="fl-mono text-[11px] uppercase tracking-[0.12em] text-[var(--ink-30)]">
                  Güven Düzeyi · {result.confidenceLevel}
                </span>
              )}
            </div>

            {result.analysis && (
              <p className="fl-sans mt-6 text-[15px] leading-relaxed text-[var(--ink-10)]">
                {result.analysis}
              </p>
            )}

            {result.dataWarning && (
              <p className="mt-5 rounded-[3px] border border-[var(--verdict-caution)] px-4 py-3 fl-sans text-[13px] text-[var(--verdict-caution)]">
                {result.dataWarning}
              </p>
            )}

            {/* Data rows */}
            <dl className="mt-9 border-b border-[var(--ink-70)]">
              {dataRows.map((row) => (
                <div
                  key={row.label}
                  className="fl-row flex items-baseline justify-between gap-6 px-2 py-5"
                >
                  <dt className="fl-data-label">{row.label}</dt>
                  <dd className="fl-data-value text-right">{row.value}</dd>
                </div>
              ))}
            </dl>
          </motion.div>
        </div>

        {/* Alışveriş psikolojisi metni */}
        {result.shoppingBehavior && (
          <section className="fl-divider mt-16 pt-10">
            <p className="fl-kicker mb-4">EVRE · ALIŞVERİŞ PSİKOLOJİSİ</p>
            <p className="fl-sans max-w-3xl text-[15px] leading-relaxed text-[var(--ink-10)]">
              {result.shoppingBehavior}
            </p>
          </section>
        )}

        {/* SYSTEM 1 — Yapay Zeka Yorum Analizi */}
        {result.reviewIntelligence && (
          <div className="mt-12">
            <ReviewIntelligence data={result.reviewIntelligence} />
          </div>
        )}

        {/* Platform fiyat karşılaştırması */}
        <section className="fl-divider mt-16 pt-10">
          <CrossPlatformPrices
            sourcePlatform={result.sourcePlatform ?? ""}
            productName={result.productName ?? ""}
            brand={result.brand ?? ""}
            priceStr={result.price ?? ""}
            sourceUrl={result.sourceUrl}
            sourceImage={result.image}
            className="mt-0 pt-0 border-t-0"
          />
        </section>

        {/* Daha iyi alternatif */}
        <section id="alternatives" className="fl-divider mt-16 pt-10">
          <p className="fl-kicker mb-6">EVRE · DAHA İYİ ALTERNATİF</p>
          {(result.betterAlternatives || []).length > 0 ? (
            <div className="border-b border-[var(--ink-70)]">
              {(result.betterAlternatives || []).map((alt, idx) => (
                <Link
                  href={alt.url || "#"}
                  key={idx}
                  target="_blank"
                  rel="noopener noreferrer"
                  className="fl-row flex items-center gap-5 px-2 py-6"
                >
                  <div className="relative h-24 w-24 flex-shrink-0 overflow-hidden border border-[var(--ink-70)] bg-[var(--bg-deep)]">
                    {isValidImageUrl(alt.image) ? (
                      <Image src={alt.image} alt={alt.name || "Ürün görseli"} fill className="object-contain p-2" sizes="96px" />
                    ) : (
                      <div className="flex h-full w-full items-center justify-center fl-mono text-[9px] uppercase tracking-[0.1em] text-[var(--ink-50)]">
                        Görsel Yok
                      </div>
                    )}
                  </div>
                  <div className="min-w-0 flex-1">
                    {alt.platform && <p className="fl-kicker">{alt.platform}</p>}
                    <h4 className="fl-serif italic mt-1 text-[20px] leading-snug text-[var(--paper)]">
                      {alt.name}
                    </h4>
                    <p className="fl-mono mt-1.5 text-[16px] text-[var(--brass)]">{alt.price}</p>
                    {alt.reason && (
                      <p className="fl-sans mt-2 text-[13px] leading-relaxed text-[var(--ink-30)]">
                        {alt.reason}
                      </p>
                    )}
                  </div>
                  <span className="hidden flex-shrink-0 fl-mono text-[11px] uppercase tracking-[0.1em] text-[var(--ink-30)] xl:inline">
                    Ürüne Git →
                  </span>
                </Link>
              ))}
            </div>
          ) : (
            <div className="fl-card p-10 text-center fl-sans text-[14px] text-[var(--ink-30)]">
              Doğrulanmış alternatif ürün bulunamadı.
            </div>
          )}
        </section>

        {/* SYSTEM 2 — Alışveriş Kişiliği */}
        <div className="mt-12">
          <ShoppingPersonality result={result} />
        </div>
      </div>
    </div>
  );
}

export default function DashboardPage() {
  return (
    <Suspense
      fallback={
        <div className="fl-page flex items-center justify-center">
          <span className="fl-mono text-[12px] uppercase tracking-[0.14em] text-[var(--ink-30)]">
            Yükleniyor...
          </span>
        </div>
      }
    >
      <DashboardContent />
    </Suspense>
  );
}
