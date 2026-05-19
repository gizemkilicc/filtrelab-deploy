"use client";

/**
 * SYSTEM 1 — Pseudo Comprehend frontend bileşeni.
 *
 * Backend'in /analyze yanıtındaki `reviewIntelligence` verisini gösterir:
 *  - AI kaynak rozeti (AWS Comprehend / DeepSeek)
 *  - Duygu dağılımı kartı
 *  - Sahte yorum riski / güven kartı + uyarı
 *  - Yorumlarda öne çıkan anahtar kelimeler
 *
 * Veri yoksa veya hiç yorum analiz edilmediyse hiçbir şey render etmez.
 */

import { motion } from "framer-motion";
import { Brain, ShieldAlert, ShieldCheck, Tag, Cloud, Sparkles } from "lucide-react";
import { AnimatedCard } from "@/components/ui/AnimatedCard";

export interface ReviewIntelligenceData {
  sentiment_score: number;
  positive: number;
  negative: number;
  neutral: number;
  mixed: number;
  suspicious_review_count: number;
  review_risk_score: number;
  detected_key_phrases: string[];
  source: "aws_comprehend" | "deepseek_fallback";
}

const SOURCE_META: Record<string, { label: string; cls: string }> = {
  aws_comprehend: {
    label: "AWS Comprehend",
    cls: "bg-orange-100 text-orange-700 border-orange-300/50 dark:bg-orange-900/30 dark:text-orange-300",
  },
  deepseek_fallback: {
    label: "DeepSeek AI",
    cls: "bg-blue-100 text-blue-700 border-blue-300/50 dark:bg-blue-900/30 dark:text-blue-300",
  },
};

export function ReviewIntelligence({ data }: { data: ReviewIntelligenceData }) {
  const analyzed = data.positive + data.negative + data.neutral + data.mixed;
  // Hiç yorum analiz edilmediyse bölümü gösterme.
  if (analyzed <= 0) return null;

  const src = SOURCE_META[data.source] ?? SOURCE_META.deepseek_fallback;
  const risk = data.review_risk_score;
  const riskLevel = risk >= 60 ? "Yüksek" : risk >= 30 ? "Orta" : "Düşük";
  const riskColor = risk >= 60 ? "text-red-500" : risk >= 30 ? "text-yellow-500" : "text-green-500";

  const pct = (n: number) => Math.round((n / analyzed) * 100);

  return (
    <motion.div
      initial={{ opacity: 0, y: 20 }}
      animate={{ opacity: 1, y: 0 }}
      transition={{ delay: 0.9 }}
      className="mt-14 pt-10 border-t border-white/10"
    >
      {/* Başlık + AI kaynak rozeti */}
      <div className="flex items-center justify-between flex-wrap gap-3 mb-6">
        <h3 className="text-xl font-bold flex items-center gap-2">
          <Brain className="text-[var(--neon-purple)]" /> Yapay Zeka Yorum Analizi
        </h3>
        <span
          title="Bu analizi üreten yapay zeka motoru"
          className={`inline-flex items-center gap-1.5 text-xs font-bold px-3 py-1.5 rounded-full border ${src.cls}`}
        >
          <Cloud className="w-3.5 h-3.5" /> {src.label}
        </span>
      </div>

      <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
        {/* Duygu dağılımı kartı */}
        <AnimatedCard className="p-6">
          <div className="flex items-center gap-2 mb-4">
            <Sparkles className="w-5 h-5 text-[var(--neon-green)]" />
            <h4 className="font-bold">Duygu Dağılımı</h4>
          </div>
          <div className="text-4xl font-black mb-1">%{data.sentiment_score}</div>
          <div className="text-xs text-gray-500 dark:text-gray-400 mb-4">olumlu duygu skoru</div>

          {/* Yığılmış oran çubuğu */}
          <div className="flex h-3 rounded-full overflow-hidden mb-3 bg-gray-200 dark:bg-white/10">
            {data.positive > 0 && <div style={{ width: `${pct(data.positive)}%` }} className="bg-green-500" />}
            {data.neutral > 0 && <div style={{ width: `${pct(data.neutral)}%` }} className="bg-gray-400" />}
            {data.mixed > 0 && <div style={{ width: `${pct(data.mixed)}%` }} className="bg-yellow-400" />}
            {data.negative > 0 && <div style={{ width: `${pct(data.negative)}%` }} className="bg-red-500" />}
          </div>
          <div className="flex flex-wrap gap-x-4 gap-y-1 text-xs font-semibold">
            <span className="text-green-600 dark:text-green-400">● Olumlu {data.positive}</span>
            <span className="text-gray-500 dark:text-gray-400">● Nötr {data.neutral}</span>
            <span className="text-yellow-600 dark:text-yellow-400">● Karışık {data.mixed}</span>
            <span className="text-red-600 dark:text-red-400">● Olumsuz {data.negative}</span>
          </div>
        </AnimatedCard>

        {/* Sahte yorum / güven kartı */}
        <AnimatedCard className="p-6">
          <div className="flex items-center gap-2 mb-4">
            {risk >= 60 ? (
              <ShieldAlert className="w-5 h-5 text-red-500" />
            ) : (
              <ShieldCheck className="w-5 h-5 text-[var(--neon-green)]" />
            )}
            <h4 className="font-bold">Sahte Yorum Analizi</h4>
          </div>
          <div className={`text-4xl font-black mb-1 ${riskColor}`}>%{risk}</div>
          <div className="text-xs text-gray-500 dark:text-gray-400 mb-4">
            şüpheli yorum risk skoru — {riskLevel}
          </div>
          <p className="text-sm text-gray-700 dark:text-gray-300">
            {analyzed} yorumdan <strong>{data.suspicious_review_count}</strong> tanesi şüpheli işaretlendi.
            <span className="block text-xs text-gray-500 dark:text-gray-400 mt-1">
              Kontroller: tekrar eden yorum, kısa/jenerik metin, emoji spam, puan-metin uyumsuzluğu.
            </span>
          </p>
          {risk >= 60 && (
            <p className="mt-3 text-xs rounded-xl border border-red-300/50 bg-red-50 px-3 py-2 text-red-700 dark:bg-red-900/20 dark:text-red-300">
              ⚠ Bu üründe manipüle edilmiş yorum olasılığı yüksek — yorumlara temkinli yaklaşın.
            </p>
          )}
        </AnimatedCard>
      </div>

      {/* Anahtar kelime analizi */}
      {data.detected_key_phrases.length > 0 && (
        <div className="mt-6">
          <div className="flex items-center gap-2 mb-3">
            <Tag className="w-4 h-4 text-[var(--neon-blue)]" />
            <h4 className="text-sm font-bold">Yorumlarda Öne Çıkan Kelimeler</h4>
          </div>
          <div className="flex flex-wrap gap-2">
            {data.detected_key_phrases.map((kw, i) => (
              <span
                key={i}
                className="rounded-full border border-[var(--neon-blue)]/20 bg-[var(--neon-blue)]/10 px-3 py-1 text-xs font-semibold text-[var(--neon-blue)]"
              >
                {kw}
              </span>
            ))}
          </div>
        </div>
      )}
    </motion.div>
  );
}
