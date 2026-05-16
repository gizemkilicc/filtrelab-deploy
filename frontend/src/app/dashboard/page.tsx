"use client";

import { useEffect, useState, Suspense } from "react";
import { useSearchParams } from "next/navigation";
import { motion } from "framer-motion";
import { runAIAnalysis, type AIAnalysisResult } from "@/lib/apiClient";
import { ScanTimeline } from "@/components/ui/ScanTimeline";
import { AnimatedCard } from "@/components/ui/AnimatedCard";
import { ProgressBar } from "@/components/ui/ProgressBar";
import { FinalVerdict } from "@/components/ui/FinalVerdict";
import { ShieldAlert, PackageX, BrainCircuit, ArrowLeft, Star, TrendingUp, Zap, Sparkles } from "lucide-react";
import Link from "next/link";
import Image from "next/image";

function isValidImageUrl(url: unknown): url is string {
  return (
    typeof url === "string" &&
    url.trim() !== "" &&
    (url.startsWith("https://") || url.startsWith("http://"))
  );
}

function DashboardContent() {
  const searchParams = useSearchParams();
  const url = searchParams.get("url") || "";

  const [isScanning, setIsScanning] = useState(true);
  const [result, setResult] = useState<AIAnalysisResult | null>(null);
  const [error, setError] = useState<string | null>(null);
  
  type StepStatus = "pending" | "scanning" | "completed";
  const [timelineSteps, setTimelineSteps] = useState<{id: number, message: string, status: StepStatus}[]>([
    { id: 1, message: "Ürün linki inceleniyor...", status: "pending" },
    { id: 2, message: "Yorumlar analiz ediliyor...", status: "pending" },
    { id: 3, message: "Sahte yorum kalıpları aranıyor...", status: "pending" },
    { id: 4, message: "İade riski hesaplanıyor...", status: "pending" },
    { id: 5, message: "Alternatif ürünler karşılaştırılıyor...", status: "pending" },
    { id: 6, message: "Nihai karar oluşturuluyor...", status: "pending" }
  ]);

  useEffect(() => {
    let mounted = true;
    
    const runAnalysisLogic = async () => {
      try {
        const response = await runAIAnalysis(url, (stepIndex) => {
          if (!mounted) return;
          setTimelineSteps(prev => prev.map((step, idx) => {
            if (idx < stepIndex) return { ...step, status: "completed" };
            if (idx === stepIndex) return { ...step, status: "scanning" };
            return step;
          }));
        });
        
        if (mounted) {
          if (response.success) {
            setResult(response.data);
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

  if (isScanning) {
    return (
      <div className="min-h-screen flex flex-col items-center justify-center p-8">
        <motion.div
          initial={{ opacity: 0, scale: 0.9 }}
          animate={{ opacity: 1, scale: 1 }}
          className="bg-[var(--bg-card)] border border-white/10 rounded-3xl p-12 w-full max-w-2xl shadow-2xl backdrop-blur-xl"
        >
          <div className="text-center mb-12">
            <BrainCircuit className="w-16 h-16 text-[var(--neon-blue)] mx-auto mb-6 animate-pulse" />
            <h2 className="text-3xl font-bold mb-2">FiltreLAB Analiz Motoru Devrede</h2>
            <p className="text-gray-400">Bu ürün için binlerce veri noktası analiz ediliyor...</p>
          </div>
          <ScanTimeline steps={timelineSteps} />
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
          <p className="text-gray-300 mb-8 leading-relaxed">{error}</p>
          <Link href="/">
            <button className="bg-white/5 hover:bg-white/10 text-white border border-white/20 px-8 py-3 rounded-full font-bold transition-all">
              Yeni Arama Yap
            </button>
          </Link>
        </motion.div>
      </div>
    );
  }

  if (!result) return null;

  return (
    <div className="min-h-screen p-6 md:p-12 relative">
      {/* Abstract Background */}
      <div className="fixed top-0 left-0 w-full h-full overflow-hidden pointer-events-none z-0">
        <div className="absolute top-[-20%] right-[-10%] w-[50%] h-[50%] bg-[var(--neon-purple)] opacity-10 blur-[150px] rounded-full" />
        <div className="absolute bottom-[-20%] left-[-10%] w-[50%] h-[50%] bg-[var(--neon-blue)] opacity-10 blur-[150px] rounded-full" />
      </div>

      <div className="max-w-7xl mx-auto relative z-10">
        <Link href="/" className="inline-flex items-center text-gray-400 hover:text-white transition-colors mb-8">
          <ArrowLeft className="w-5 h-5 mr-2" />
          Aramaya Dön
        </Link>

        <div className="grid grid-cols-1 lg:grid-cols-12 gap-8">
          
          {/* Left Column: Product Info */}
          <div className="lg:col-span-4 space-y-6">
            <AnimatedCard className="p-0 overflow-hidden" delay={0.1}>
              {isValidImageUrl(result.image) ? (
                <div className="relative h-64 w-full">
                  <Image src={result.image} alt={result.productName || "Ürün görseli"} fill className="object-cover" />
                </div>
              ) : (
                <div className="flex h-64 w-full items-center justify-center bg-neutral-900 text-neutral-400">
                  Görsel bulunamadı
                </div>
              )}
              <div className="p-6">
                <div className="flex flex-col gap-1 mb-2">
                  <span className="text-xs font-bold uppercase tracking-wider text-gray-400">{result.category}</span>
                  <span className="text-sm font-semibold text-[var(--neon-purple)]">{result.brand}</span>
                </div>
                <h2 className="text-2xl font-bold mb-3 leading-tight">{result.productName}</h2>
                <div className="text-3xl font-black text-[var(--neon-blue)] neon-text-blue mb-4">{result.price}</div>
                
                {result.rating > 0 && (
                  <div className="flex items-center gap-4 pt-4 border-t border-white/10 text-sm">
                    <div className="flex flex-col gap-1">
                      <span className="text-sm text-gray-400">İade Riski</span>
                      <span className={`font-bold ${result.returnRisk === "Yüksek" ? "text-red-400" : result.returnRisk === "Orta" ? "text-yellow-400" : "text-green-400"}`}>
                        {result.returnRisk}
                      </span>
                    </div>
                    <div className="text-gray-400 border-l border-white/10 pl-4">
                      <span>{result.reviewCount.toLocaleString("tr-TR")} Değerlendirme</span>
                    </div>
                    {result.questionCount && (
                      <div className="text-gray-400 border-l border-white/10 pl-4">
                        <span>{result.questionCount.toLocaleString("tr-TR")} Soru</span>
                      </div>
                    )}
                  </div>
                )}
              </div>
            </AnimatedCard>

            <AnimatedCard delay={0.2} className="bg-gradient-to-br from-gray-900 to-black border-[var(--neon-blue)]/20">
              <h3 className="text-lg font-bold mb-3 flex items-center gap-2">
                <Sparkles className="text-yellow-400" /> Alışveriş Psikolojisi Analizi
              </h3>
              <p className="text-sm text-gray-400 italic">
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
                  <span className="text-5xl font-black">%{result.fakeReviewRisk}</span>
                  <span className="text-gray-400 ml-2 mb-1">risk skoru</span>
                </div>
                <ProgressBar label="Fiyat Performansı" value={result.pricePerformance * 10} color="var(--neon-green)" />
                <ProgressBar label="Sahte Yorum Riski" value={result.fakeReviewRisk} color="var(--neon-pink)" />
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
                <div className="text-3xl font-bold">{result.trustScore}/100</div>
                <div className="text-xs text-gray-400 uppercase tracking-wider">Güven Skoru</div>
              </AnimatedCard>
              
              <AnimatedCard delay={0.6} className="flex flex-col items-center justify-center text-center p-4">
                <TrendingUp className="w-8 h-8 text-[var(--neon-green)] mb-2" />
                <div className="text-3xl font-bold">{result.sentimentScore}/10</div>
                <div className="text-xs text-gray-400 uppercase tracking-wider">Yorum Duygu Skoru</div>
              </AnimatedCard>

              <AnimatedCard delay={0.7} className="flex flex-col items-center justify-center text-center p-4">
                <Zap className="w-8 h-8 text-[var(--neon-blue)] mb-2" />
                <div className="text-3xl font-bold">{result.pricePerformance}/10</div>
                <div className="text-xs text-gray-400 uppercase tracking-wider">Fiyat / Performans</div>
              </AnimatedCard>
            </div>

            {/* Final Verdict */}
            <FinalVerdict decision={result.finalDecision} reason={(result.analysis || "").substring(0, 150) + (result.analysis && result.analysis.length > 150 ? "..." : "")} />

            {/* Alternatives */}
            <motion.div
              id="alternatives"
              initial={{ opacity: 0, y: 20 }}
              animate={{ opacity: 1, y: 0 }}
              transition={{ delay: 1 }}
              className="mt-12 pt-8 border-t border-white/10"
            >
              <h3 className="text-xl font-bold mb-4 flex items-center gap-2">
                <BrainCircuit className="text-[var(--neon-blue)]" /> Yapay Zeka Kararı
              </h3>
              <p className="text-gray-300 leading-relaxed mb-6">
                {result.analysis}
              </p>
              
              <h3 className="text-xl font-bold mb-6 flex items-center">
                <Sparkles className="w-5 h-5 text-[var(--neon-blue)] mr-2" />
                Daha İyi Alternatif Bulundu
              </h3>
              
              {(result.betterAlternatives || []).length > 0 ? (
                <div className="grid grid-cols-1 gap-4">
                  {(result.betterAlternatives || []).map((alt, idx) => (
                    <Link 
                      href={alt.url || "#"} 
                      key={idx} 
                      className="block group" 
                      target="_blank" 
                      rel="noopener noreferrer"
                    >
                      <AnimatedCard className="flex items-center p-4 gap-4 bg-white/5 border-white/10 group-hover:bg-white/10 group-hover:border-[var(--neon-blue)]/30 transition-all cursor-pointer">
                        <div className="relative w-24 h-24 rounded-lg overflow-hidden flex-shrink-0">
                          {isValidImageUrl(alt.image) ? (
                            <Image src={alt.image} alt={alt.name || "Ürün görseli"} fill className="object-cover" />
                          ) : (
                            <div className="flex h-full w-full items-center justify-center bg-neutral-900 text-neutral-400 text-xs text-center p-1 leading-tight">
                              Görsel Yok
                            </div>
                          )}
                        </div>
                        <div className="flex-1">
                          <h4 className="font-bold text-lg group-hover:text-[var(--neon-blue)] transition-colors">{alt.name}</h4>
                          <p className="text-lg text-[var(--neon-blue)] font-black mt-1">{alt.price}</p>
                          <p className="text-sm text-gray-400 mt-2 line-clamp-2">{alt.reason}</p>
                        </div>
                        <div className="hidden sm:flex px-4 py-2 rounded-lg bg-[var(--neon-blue)]/10 text-[var(--neon-blue)] text-sm font-bold border border-[var(--neon-blue)]/20 whitespace-nowrap">
                          Ürüne Git
                        </div>
                      </AnimatedCard>
                    </Link>
                  ))}
                </div>
              ) : (
                <AnimatedCard className="text-center p-8 border-dashed border-white/20 bg-transparent">
                  <p className="text-gray-400">Bu ürün için şu anda daha iyi alternatif bulunamadı.</p>
                </AnimatedCard>
              )}
            </motion.div>

          </div>
        </div>
      </div>
    </div>
  );
}

export default function DashboardPage() {
  return (
    <Suspense fallback={<div className="min-h-screen flex items-center justify-center text-white">Yükleniyor...</div>}>
      <DashboardContent />
    </Suspense>
  );
}
