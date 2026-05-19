"use client";

import { motion } from "framer-motion";
import { useRouter } from "next/navigation";
import { useEffect, useRef, useState } from "react";
import { ArrowRight } from "lucide-react";

const processSteps = [
  { n: "01", cat: "ÜRÜN BİLGİSİ", name: "Linki Tarıyoruz" },
  { n: "02", cat: "DUYGU ANALİZİ", name: "Yorumları Süzüyoruz" },
  { n: "03", cat: "BOT TESPİTİ", name: "Sahteleri Yakalıyoruz" },
  { n: "04", cat: "KULLANICI ŞİKAYETLERİ", name: "İade Riskini Ölçüyoruz" },
  { n: "05", cat: "PAZAR YERİ", name: "Fiyatı Karşılaştırıyoruz" },
  { n: "06", cat: "TEK NET SONUÇ", name: "Kararı Açıklıyoruz" },
];

const heroStats = [
  "12.400+ ürün analiz edildi",
  "AI destekli",
  "Ücretsiz · reklamsız",
];

export function HeroWave() {
  const router = useRouter();
  const inputRef = useRef<HTMLInputElement>(null);
  const [productUrl, setProductUrl] = useState("");

  // Pre-fill from ?url= query param on mount
  useEffect(() => {
    const params = new URLSearchParams(window.location.search);
    const urlParam = params.get("url");
    if (urlParam) setProductUrl(decodeURIComponent(urlParam));
  }, []);

  const handleAnalyze = () => {
    const trimmed = productUrl.trim();
    if (!trimmed) {
      inputRef.current?.focus();
      return;
    }
    router.push(`/dashboard?url=${encodeURIComponent(trimmed)}`);
  };

  return (
    <section className="fl-page relative min-h-screen overflow-hidden px-6 pb-16 pt-16 md:px-12">
      {/* Faint speckle texture */}
      <div
        aria-hidden="true"
        className="pointer-events-none absolute inset-0 opacity-[0.5]"
        style={{
          backgroundImage:
            "radial-gradient(circle, rgba(217,182,92,0.12) 0.5px, transparent 0.6px)",
          backgroundSize: "46px 46px",
        }}
      />

      <div className="relative mx-auto grid max-w-6xl items-center gap-14 lg:grid-cols-[1.05fr_0.95fr]">
        {/* ─── Left: copy + input ─────────────────────────────── */}
        <motion.div
          initial={{ opacity: 0, y: 20 }}
          animate={{ opacity: 1, y: 0 }}
          transition={{ duration: 0.8, ease: [0.16, 1, 0.3, 1] }}
        >
          <div className="flex items-center gap-3">
            <span className="fl-kicker">NASIL ÇALIŞIR</span>
            <span className="h-px w-10" style={{ background: "var(--ink-70)" }} />
            <span className="fl-kicker">6 ADIMDA KARAR</span>
          </div>

          <h1 className="fl-serif mt-7 text-[58px] leading-[1.0] text-[var(--paper)] md:text-[72px]">
            Bir link yapıştırın.
            <br />
            6 adımda
            <br />
            <span className="italic text-[var(--brass)]">net cevap alın.</span>
          </h1>

          <p className="fl-sans mt-7 max-w-md text-[14px] leading-relaxed text-[var(--ink-30)]">
            FiltreLAB, Trendyol, Hepsiburada ve Amazon&apos;dan aldığınız ürün linkini analiz
            eder. Yorumları, iade oranlarını ve fiyatı inceler; size yalnızca tek bir karar
            verir:{" "}
            <span className="italic text-[var(--ink-10)]">
              alın, dikkatli inceleyin ya da bekleyin.
            </span>
          </p>

          {/* URL input */}
          <div className="mt-9 flex max-w-lg items-stretch gap-3">
            <div
              className="flex-1 rounded-[3px] border px-4 py-2.5"
              style={{ borderColor: "var(--input-border)", background: "var(--input-bg)" }}
            >
              <label className="block fl-mono text-[9px] uppercase tracking-[0.18em] text-[var(--ink-30)]">
                Ürün Linki
              </label>
              <input
                ref={inputRef}
                type="url"
                value={productUrl}
                onChange={(e) => setProductUrl(e.target.value)}
                onKeyDown={(e) => e.key === "Enter" && handleAnalyze()}
                placeholder="Trendyol ürün linkini yapıştır..."
                className="mt-1 w-full bg-transparent fl-sans text-[14px] text-[var(--paper)] outline-none placeholder:text-[var(--ink-30)]"
              />
            </div>
            <button onClick={handleAnalyze} className="fl-btn fl-btn-primary px-6">
              Analiz Et
              <ArrowRight className="h-4 w-4" />
            </button>
          </div>

          <p className="mt-3 fl-mono text-[10px] uppercase tracking-[0.14em] text-[var(--ink-30)]">
            Trendyol · Hepsiburada · Amazon linklerini destekler
          </p>

          {/* Hero stats */}
          <div className="mt-7 flex flex-wrap items-center gap-x-5 gap-y-2">
            {heroStats.map((stat) => (
              <span
                key={stat}
                className="flex items-center gap-2 fl-mono text-[9px] uppercase tracking-[0.12em] text-[var(--ink-30)]"
              >
                <span
                  className="inline-block h-1 w-1 rounded-full"
                  style={{ background: "var(--brass)" }}
                />
                {stat}
              </span>
            ))}
          </div>
        </motion.div>

        {/* ─── Right: brass column + 6 steps ──────────────────── */}
        <motion.div
          initial={{ opacity: 0, y: 24 }}
          animate={{ opacity: 1, y: 0 }}
          transition={{ duration: 0.9, delay: 0.15, ease: [0.16, 1, 0.3, 1] }}
          className="relative hidden lg:block"
        >
          <div className="flex h-[560px] items-stretch justify-center">
            {/* Steps (right-aligned text) */}
            <div className="flex flex-col justify-between py-4">
              {processSteps.map((s) => (
                <div key={s.n} className="flex items-center gap-3">
                  <div className="text-right">
                    <p className="fl-mono text-[9px] uppercase tracking-[0.14em] text-[var(--ink-30)]">
                      {s.cat}
                    </p>
                    <p className="fl-serif italic text-[19px] leading-tight text-[var(--brass)]">
                      {s.name}
                    </p>
                  </div>
                  <span className="w-6 text-right fl-mono text-[11px] text-[var(--ink-30)]">
                    {s.n}
                  </span>
                  <span
                    className="block h-px w-7"
                    style={{ background: "var(--brass-deep)" }}
                  />
                </div>
              ))}
            </div>

            {/* The brass column */}
            <div className="flex flex-col items-center self-stretch">
              {/* capital */}
              <div
                className="h-3 w-[148px]"
                style={{ background: "linear-gradient(180deg,#efce75,#876130)" }}
              />
              <div
                className="h-5 w-[118px]"
                style={{
                  background:
                    "linear-gradient(90deg,#5a3f1f,#876130,#efce75,#d9b65c,#876130,#5a3f1f)",
                }}
              />
              {/* shaft */}
              <div
                className="w-[86px] flex-1"
                style={{
                  background:
                    "linear-gradient(90deg,#4a3318 0%,#876130 14%,#d9b65c 38%,#efce75 50%,#d9b65c 62%,#876130 86%,#4a3318 100%)",
                }}
              />
              {/* base */}
              <div
                className="h-5 w-[118px]"
                style={{
                  background:
                    "linear-gradient(90deg,#5a3f1f,#876130,#efce75,#d9b65c,#876130,#5a3f1f)",
                }}
              />
              <div
                className="h-3 w-[148px]"
                style={{ background: "linear-gradient(0deg,#efce75,#876130)" }}
              />
              <div
                className="h-2 w-[176px]"
                style={{ background: "linear-gradient(0deg,#876130,#4a3318)" }}
              />
            </div>
          </div>

          {/* Decorative product tag */}
          <div
            className="absolute -bottom-2 right-0 rounded-[3px] border px-4 py-2.5"
            style={{ borderColor: "var(--ink-70)", background: "var(--bg-raised)" }}
          >
            <p className="fl-mono text-[10px] uppercase tracking-[0.12em] text-[var(--paper)]">
              Stellar X2 · TY-9484017
            </p>
            <p className="fl-mono mt-1 text-[9px] uppercase tracking-[0.12em] text-[var(--ink-30)]">
              Analiz tamamlandı · 6.127 yorum
            </p>
          </div>
        </motion.div>
      </div>
    </section>
  );
}
