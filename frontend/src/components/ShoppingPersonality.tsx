"use client";

/**
 * SYSTEM 2 — Shopping Psychology frontend bileşeni.
 *
 * Mevcut ürünü gezinme geçmişine kaydeder, geçmişi /shopping-psychology
 * endpoint'ine gönderir ve kullanıcının "Alışveriş Kişiliği" kartını gösterir:
 *  - Kişilik tipi + güven skoru
 *  - Davranışsal içgörüler (güven hassasiyeti, dürtüsel↔analitik, bütçe)
 *  - Kişiselleştirilmiş öneri ipucu
 *
 * API başarısız olursa bölüm hiç render edilmez — site asla çökmez.
 */

import { useEffect, useState } from "react";
import { motion } from "framer-motion";
import { UserCircle, Loader2, Brain, Wallet, ShieldCheck } from "lucide-react";
import { AnimatedCard } from "@/components/ui/AnimatedCard";
import {
  getShoppingPsychology,
  type ShoppingPsychology,
  type AIAnalysisResult,
} from "@/lib/apiClient";
import { recordBrowsing } from "@/lib/browsingHistory";

// İngilizce kişilik anahtarı → Türkçe etiket + emoji + vurgu rengi
const PERSONALITY_META: Record<string, { tr: string; emoji: string; color: string }> = {
  "Analytical Researcher": { tr: "Analitik Araştırmacı", emoji: "🔍", color: "var(--neon-blue)" },
  "Deal Hunter": { tr: "Fırsat Avcısı", emoji: "🏷️", color: "var(--neon-green)" },
  "Premium Shopper": { tr: "Premium Alışverişçi", emoji: "💎", color: "var(--neon-purple)" },
  "Impulsive Buyer": { tr: "Dürtüsel Alıcı", emoji: "⚡", color: "#f97316" },
  "Trust-Focused Shopper": { tr: "Güven Odaklı Alışverişçi", emoji: "🛡️", color: "var(--neon-blue)" },
  "Brand Loyalist": { tr: "Marka Sadığı", emoji: "❤️", color: "var(--neon-pink)" },
};

function Meter({ label, value, leftTag, rightTag, color }: {
  label: string; value: number; leftTag?: string; rightTag?: string; color: string;
}) {
  const v = Math.max(0, Math.min(100, value));
  return (
    <div>
      <div className="flex justify-between text-xs font-semibold mb-1.5">
        <span className="text-gray-600 dark:text-gray-300">{label}</span>
        <span style={{ color }}>{v}/100</span>
      </div>
      <div className="h-2.5 rounded-full bg-gray-200 dark:bg-white/10 overflow-hidden">
        <div className="h-full rounded-full" style={{ width: `${v}%`, backgroundColor: color }} />
      </div>
      {(leftTag || rightTag) && (
        <div className="flex justify-between text-[10px] text-gray-400 mt-1">
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
      <div className="mt-14 pt-10 border-t border-white/10 flex items-center gap-3 text-sm text-gray-500 dark:text-gray-400">
        <Loader2 className="h-5 w-5 animate-spin text-[var(--neon-purple)]" />
        Alışveriş kişiliğin analiz ediliyor...
      </div>
    );
  }

  // API başarısız → bölümü gösterme (sessizce gizle, çökme yok)
  if (!data) return null;

  const meta = PERSONALITY_META[data.shopping_personality] ?? {
    tr: data.shopping_personality, emoji: "🧠", color: "var(--neon-blue)",
  };

  return (
    <motion.div
      initial={{ opacity: 0, y: 20 }}
      animate={{ opacity: 1, y: 0 }}
      transition={{ delay: 0.2 }}
      className="mt-14 pt-10 border-t border-white/10"
    >
      <h3 className="text-xl font-bold mb-6 flex items-center gap-2">
        <UserCircle className="text-[var(--neon-purple)]" /> Yapay Zeka Alışveriş Kişiliğin
      </h3>

      <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
        {/* Kişilik kartı */}
        <AnimatedCard className="p-6 flex flex-col items-center text-center justify-center">
          <div className="text-5xl mb-3">{meta.emoji}</div>
          <div className="text-2xl font-black mb-1" style={{ color: meta.color }}>
            {meta.tr}
          </div>
          <div className="text-xs text-gray-500 dark:text-gray-400 mb-4">
            Alışveriş kişiliği profilin
          </div>
          <div className="w-full max-w-[220px]">
            <Meter label="Profil güven skoru" value={data.confidence_score} color={meta.color} />
          </div>
          {data.confidence_score < 35 && (
            <p className="text-[11px] text-gray-400 mt-3 leading-snug">
              Daha fazla ürün analiz ettikçe profilin netleşir.
            </p>
          )}
        </AnimatedCard>

        {/* Davranışsal içgörüler */}
        <AnimatedCard className="p-6">
          <div className="flex items-center gap-2 mb-5">
            <Brain className="w-5 h-5 text-[var(--neon-blue)]" />
            <h4 className="font-bold">Davranışsal İçgörüler</h4>
          </div>
          <div className="space-y-4">
            <Meter
              label="Güven Hassasiyeti"
              value={data.trust_sensitivity}
              leftTag="Düşük" rightTag="Yüksek"
              color="var(--neon-blue)"
            />
            <Meter
              label="Karar Tarzı"
              value={data.impulsive_vs_analytical}
              leftTag="Dürtüsel" rightTag="Analitik"
              color="var(--neon-purple)"
            />
            <div className="flex items-center gap-2 pt-1">
              <Wallet className="w-4 h-4 text-[var(--neon-green)]" />
              <span className="text-sm text-gray-600 dark:text-gray-300">Bütçe davranışı:</span>
              <span className="text-sm font-bold">{data.budget_behavior}</span>
            </div>
          </div>
        </AnimatedCard>
      </div>

      {/* Kişiselleştirilmiş öneri ipucu */}
      <div className="mt-6 flex items-start gap-3 rounded-2xl border border-[var(--neon-purple)]/20 bg-[var(--neon-purple)]/5 px-5 py-4">
        <ShieldCheck className="w-5 h-5 text-[var(--neon-purple)] flex-shrink-0 mt-0.5" />
        <div>
          <div className="text-sm font-bold mb-1">Sana Özel Öneri Stratejisi</div>
          <p className="text-sm text-gray-700 dark:text-gray-300 leading-relaxed">
            {data.recommendation_strategy}
          </p>
        </div>
      </div>
    </motion.div>
  );
}
