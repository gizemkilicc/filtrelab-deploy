"use client";

import { motion } from "framer-motion";
import { Link2, BrainCircuit, Trophy } from "lucide-react";

const steps = [
  {
    number: "01",
    icon: Link2,
    title: "Link Yapıştır",
    description: "Trendyol, Hepsiburada veya Amazon'dan beğendiğin ürünün linkini kopyala ve yapıştır.",
  },
  {
    number: "02",
    icon: BrainCircuit,
    title: "AI Analiz Eder",
    description: "Yapay zeka fiyat geçmişini, satıcı güvenilirliğini ve kullanıcı uygunluk skorunu saniyeler içinde hesaplar.",
  },
  {
    number: "03",
    icon: Trophy,
    title: "En İyi Ürünü Bul",
    description: "Sana özel filtrelenmiş sonuçlarla en ideal seçim doğrudan karşına gelir, karar vermek artık çok kolay.",
  },
];

export function HowItWorks() {
  return (
    <section className="w-full px-6 py-24">
      <div className="mx-auto max-w-6xl">
        {/* Header */}
        <motion.div
          className="text-center"
          initial={{ opacity: 0, y: 20 }}
          whileInView={{ opacity: 1, y: 0 }}
          viewport={{ once: true, margin: "-80px" }}
          transition={{ duration: 0.7, ease: [0.16, 1, 0.3, 1] }}
        >
          <p className="fl-kicker">NASIL ÇALIŞIR</p>
          <h2 className="fl-serif mt-5 text-[44px] leading-[1.05] text-[var(--paper)] md:text-[60px]">
            3 adımda akıllı alışveriş
          </h2>
          <p className="fl-sans mx-auto mt-4 max-w-xl text-[15px] leading-relaxed text-[var(--ink-30)]">
            FiltreLAB ile doğru ürüne ulaşmak hiç bu kadar hızlı olmamıştı.
          </p>
        </motion.div>

        {/* Steps */}
        <div className="mt-14 grid gap-5 md:grid-cols-3">
          {steps.map((step, i) => {
            const Icon = step.icon;
            return (
              <motion.div
                key={step.number}
                initial={{ opacity: 0, y: 24 }}
                whileInView={{ opacity: 1, y: 0 }}
                viewport={{ once: true, margin: "-60px" }}
                transition={{ delay: i * 0.12, duration: 0.7, ease: [0.16, 1, 0.3, 1] }}
                className="fl-card p-8"
              >
                <div className="flex items-start justify-between">
                  <Icon className="h-5 w-5 text-[var(--brass)]" strokeWidth={1.8} />
                  <span className="fl-serif text-[64px] leading-none text-[var(--ink-70)]">
                    {step.number}
                  </span>
                </div>
                <h3 className="fl-serif mt-7 text-[24px] text-[var(--paper)]">{step.title}</h3>
                <p className="fl-sans mt-2 text-[13px] leading-relaxed text-[var(--ink-30)]">
                  {step.description}
                </p>
              </motion.div>
            );
          })}
        </div>
      </div>
    </section>
  );
}
