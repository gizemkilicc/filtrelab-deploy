"use client";

/**
 * SYSTEM 1 — Pseudo Comprehend frontend bileşeni.
 *
 * Backend'in /analyze yanıtındaki `reviewIntelligence` verisini gösterir.
 * Veri yoksa veya hiç yorum analiz edilmediyse hiçbir şey render etmez.
 */

import { motion } from "framer-motion";
import { AlertTriangle } from "lucide-react";

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

const SOURCE_LABEL: Record<string, string> = {
  aws_comprehend: "AWS Comprehend",
  deepseek_fallback: "DeepSeek AI",
};

const NEGATIVE = "#9c5b4d";

export function ReviewIntelligence({ data }: { data: ReviewIntelligenceData }) {
  const analyzed = data.positive + data.negative + data.neutral + data.mixed;
  // Hiç yorum analiz edilmediyse bölümü gösterme.
  if (analyzed <= 0) return null;

  const srcLabel = SOURCE_LABEL[data.source] ?? SOURCE_LABEL.deepseek_fallback;
  const risk = data.review_risk_score;
  const riskLevel = risk >= 60 ? "Yüksek" : risk >= 30 ? "Orta" : "Düşük";
  const riskColor = risk >= 60 ? NEGATIVE : risk >= 30 ? "var(--verdict-caution)" : "var(--verdict-buy)";

  const pct = (n: number) => Math.round((n / analyzed) * 100);

  return (
    <motion.section
      initial={{ opacity: 0, y: 16 }}
      animate={{ opacity: 1, y: 0 }}
      transition={{ duration: 0.6, ease: [0.16, 1, 0.3, 1] }}
      className="fl-divider mt-16 pt-10"
    >
      {/* Başlık + AI kaynak rozeti */}
      <div className="mb-6 flex flex-wrap items-center justify-between gap-3">
        <p className="fl-kicker">EVRE · YAPAY ZEKA YORUM ANALİZİ</p>
        <span
          title="Bu analizi üreten yapay zeka motoru"
          className="fl-pill text-[var(--ink-30)]"
        >
          {srcLabel}
        </span>
      </div>

      <div className="grid grid-cols-1 gap-6 md:grid-cols-2">
        {/* Duygu dağılımı kartı */}
        <div className="fl-card p-7">
          <p className="fl-data-label">Duygu Dağılımı</p>
          <div className="mt-2 flex items-baseline gap-2">
            <span className="fl-serif text-[48px] leading-none text-[var(--paper)]">
              %{data.sentiment_score}
            </span>
            <span className="fl-mono text-[10px] uppercase tracking-[0.1em] text-[var(--ink-30)]">
              olumlu duygu
            </span>
          </div>

          {/* Yığılmış oran çubuğu */}
          <div className="mt-5 mb-3 flex h-[6px] overflow-hidden" style={{ background: "var(--ink-70)" }}>
            {data.positive > 0 && <div style={{ width: `${pct(data.positive)}%`, background: "var(--verdict-buy)" }} />}
            {data.neutral > 0 && <div style={{ width: `${pct(data.neutral)}%`, background: "var(--ink-50)" }} />}
            {data.mixed > 0 && <div style={{ width: `${pct(data.mixed)}%`, background: "var(--brass-deep)" }} />}
            {data.negative > 0 && <div style={{ width: `${pct(data.negative)}%`, background: NEGATIVE }} />}
          </div>
          <div className="flex flex-wrap gap-x-4 gap-y-1 fl-mono text-[10px] uppercase tracking-[0.08em]">
            <span style={{ color: "var(--verdict-buy)" }}>Olumlu {data.positive}</span>
            <span style={{ color: "var(--ink-30)" }}>Nötr {data.neutral}</span>
            <span style={{ color: "var(--brass)" }}>Karışık {data.mixed}</span>
            <span style={{ color: NEGATIVE }}>Olumsuz {data.negative}</span>
          </div>
        </div>

        {/* Sahte yorum / güven kartı */}
        <div className="fl-card p-7">
          <p className="fl-data-label">Sahte Yorum Analizi</p>
          <div className="mt-2 flex items-baseline gap-2">
            <span className="fl-serif text-[48px] leading-none" style={{ color: riskColor }}>
              %{risk}
            </span>
            <span className="fl-mono text-[10px] uppercase tracking-[0.1em] text-[var(--ink-30)]">
              risk — {riskLevel}
            </span>
          </div>
          <p className="mt-4 fl-sans text-[13px] leading-relaxed text-[var(--ink-10)]">
            {analyzed} yorumdan <strong className="text-[var(--paper)]">{data.suspicious_review_count}</strong> tanesi
            şüpheli işaretlendi.
            <span className="mt-1 block fl-sans text-[11px] text-[var(--ink-30)]">
              Kontroller: tekrar eden yorum, kısa/jenerik metin, emoji spam, puan-metin uyumsuzluğu.
            </span>
          </p>
          {risk >= 60 && (
            <p
              className="mt-4 flex items-start gap-2 rounded-[3px] border px-3 py-2 fl-sans text-[12px]"
              style={{ borderColor: NEGATIVE, color: NEGATIVE }}
            >
              <AlertTriangle className="mt-0.5 h-3.5 w-3.5 flex-shrink-0" />
              <span>Bu üründe manipüle edilmiş yorum olasılığı yüksek — yorumlara temkinli yaklaşın.</span>
            </p>
          )}
        </div>
      </div>

      {/* Anahtar kelime analizi */}
      {data.detected_key_phrases.length > 0 && (
        <div className="mt-6">
          <p className="fl-kicker mb-3">YORUMLARDA ÖNE ÇIKAN KELİMELER</p>
          <div className="flex flex-wrap gap-2">
            {data.detected_key_phrases.map((kw, i) => (
              <span
                key={i}
                className="rounded-[2px] border px-3 py-1 fl-mono text-[11px] text-[var(--ink-10)]"
                style={{ borderColor: "var(--ink-70)" }}
              >
                {kw}
              </span>
            ))}
          </div>
        </div>
      )}
    </motion.section>
  );
}
