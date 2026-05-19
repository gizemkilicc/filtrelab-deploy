"use client";

/**
 * SYSTEM 2 — Shopping Psychology frontend bileşeni.
 *
 * Mevcut ürünü gezinme geçmişine kaydeder, geçmişi /shopping-psychology
 * endpoint'ine gönderir ve kullanıcının "Alışveriş Kişiliği" kartını gösterir.
 * API başarısız olursa bölüm hiç render edilmez — site asla çökmez.
 */

import { useEffect, useState } from "react";
import { motion } from "framer-motion";
import { Loader2 } from "lucide-react";
import {
  getShoppingPsychology,
  type ShoppingPsychology,
  type AIAnalysisResult,
} from "@/lib/apiClient";
import { recordBrowsing } from "@/lib/browsingHistory";

// İngilizce kişilik anahtarı → Türkçe etiket + vurgu rengi
const PERSONALITY_META: Record<string, { tr: string; color: string }> = {
  "Analytical Researcher": { tr: "Analitik Araştırmacı", color: "var(--brass)" },
  "Deal Hunter": { tr: "Fırsat Avcısı", color: "var(--verdict-buy)" },
  "Premium Shopper": { tr: "Premium Alışverişçi", color: "var(--brass-hot)" },
  "Impulsive Buyer": { tr: "Dürtüsel Alıcı", color: "var(--verdict-caution)" },
  "Trust-Focused Shopper": { tr: "Güven Odaklı Alışverişçi", color: "var(--brass)" },
  "Brand Loyalist": { tr: "Marka Sadığı", color: "var(--verdict-buy)" },
};

function Meter({ label, value, leftTag, rightTag, color }: {
  label: string; value: number; leftTag?: string; rightTag?: string; color: string;
}) {
  const v = Math.max(0, Math.min(100, value));
  return (
    <div>
      <div className="mb-2 flex justify-between">
        <span className="fl-mono text-[10px] uppercase tracking-[0.12em] text-[var(--ink-30)]">{label}</span>
        <span className="fl-mono text-[10px]" style={{ color }}>{v}/100</span>
      </div>
      <div className="h-[3px] w-full overflow-hidden" style={{ background: "var(--ink-70)" }}>
        <div className="h-full" style={{ width: `${v}%`, backgroundColor: color }} />
      </div>
      {(leftTag || rightTag) && (
        <div className="mt-1.5 flex justify-between fl-mono text-[9px] uppercase tracking-[0.1em] text-[var(--ink-50)]">
          <span>{leftTag}</span>
          <span>{rightTag}</span>
        </div>
      )}
    </div>
  );
}

export function ShoppingPersonality({ result }: { result: AIAnalysisResult }) {
  const [data, setData] = useState<ShoppingPsychology | null>(null);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    let active = true;
    setLoading(true);
    // Mevcut ürünü geçmişe işle ve güncel geçmişi al
    const history = recordBrowsing({
      category: result.category,
      brand: result.brand,
      price: result.price,
      productName: result.productName,
      productUrl: result.sourceUrl,
      trustScore: result.trustScore,
    });
    getShoppingPsychology(history).then((res) => {
      if (!active) return;
      setData(res);
      setLoading(false);
    });
    return () => { active = false; };
  }, [result]);

  if (loading) {
    return (
      <div className="fl-divider mt-16 flex items-center gap-3 pt-10 fl-mono text-[11px] uppercase tracking-[0.12em] text-[var(--ink-30)]">
        <Loader2 className="h-4 w-4 animate-spin text-[var(--brass)]" />
        Alışveriş kişiliğin analiz ediliyor...
      </div>
    );
  }

  // API başarısız → bölümü gösterme (sessizce gizle, çökme yok)
  if (!data) return null;

  const meta = PERSONALITY_META[data.shopping_personality] ?? {
    tr: data.shopping_personality, color: "var(--brass)",
  };

  return (
    <motion.section
      initial={{ opacity: 0, y: 16 }}
      animate={{ opacity: 1, y: 0 }}
      transition={{ duration: 0.6, ease: [0.16, 1, 0.3, 1] }}
      className="fl-divider mt-16 pt-10"
    >
      <p className="fl-kicker mb-6">EVRE · ALIŞVERİŞ KİŞİLİĞİN</p>

      <div className="grid grid-cols-1 gap-6 lg:grid-cols-2">
        {/* Kişilik kartı */}
        <div className="fl-card flex flex-col justify-center p-7">
          <p className="fl-mono text-[10px] uppercase tracking-[0.14em] text-[var(--ink-30)]">
            Alışveriş kişiliği profilin
          </p>
          <h3 className="fl-serif mt-2 text-[40px] leading-[1.05]" style={{ color: meta.color }}>
            {meta.tr}
          </h3>
          <div className="mt-6 max-w-[280px]">
            <Meter label="Profil güven skoru" value={data.confidence_score} color={meta.color} />
          </div>
          {data.confidence_score < 35 && (
            <p className="mt-3 fl-sans text-[12px] leading-snug text-[var(--ink-30)]">
              Daha fazla ürün analiz ettikçe profilin netleşir.
            </p>
          )}
        </div>

        {/* Davranışsal içgörüler */}
        <div className="fl-card p-7">
          <p className="fl-mono mb-5 text-[10px] uppercase tracking-[0.14em] text-[var(--ink-30)]">
            Davranışsal İçgörüler
          </p>
          <div className="space-y-5">
            <Meter
              label="Güven Hassasiyeti"
              value={data.trust_sensitivity}
              leftTag="Düşük" rightTag="Yüksek"
              color="var(--brass)"
            />
            <Meter
              label="Karar Tarzı"
              value={data.impulsive_vs_analytical}
              leftTag="Dürtüsel" rightTag="Analitik"
              color="var(--verdict-buy)"
            />
            <div className="fl-divider flex items-baseline justify-between gap-4 pt-4">
              <span className="fl-data-label">Bütçe Davranışı</span>
              <span className="fl-serif text-[22px] text-[var(--paper)]">{data.budget_behavior}</span>
            </div>
          </div>
        </div>
      </div>

      {/* Kişiselleştirilmiş öneri ipucu */}
      <div
        className="mt-6 rounded-[3px] border px-6 py-5"
        style={{ borderColor: "var(--brass-deep)", background: "rgba(217,182,92,0.04)" }}
      >
        <p className="fl-kicker mb-2">SANA ÖZEL ÖNERİ STRATEJİSİ</p>
        <p className="fl-sans text-[14px] leading-relaxed text-[var(--ink-10)]">
          {data.recommendation_strategy}
        </p>
      </div>
    </motion.section>
  );
}
