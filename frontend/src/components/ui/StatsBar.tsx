"use client";

import { motion } from "framer-motion";

const stats = [
  { value: "12.400+", label: "Ürün Analiz Edildi" },
  { value: "4.800+", label: "Mutlu Kullanıcı" },
  { value: "3", label: "Platform Destekleniyor" },
  { value: "%94", label: "Doğruluk Oranı" },
];

export function StatsBar() {
  return (
    <section className="w-full border-y border-[var(--ink-70)] px-6 py-14">
      <div className="mx-auto max-w-6xl">
        <div className="grid grid-cols-2 gap-10 md:grid-cols-4">
          {stats.map((stat, i) => (
            <motion.div
              key={stat.label}
              initial={{ opacity: 0, y: 16 }}
              whileInView={{ opacity: 1, y: 0 }}
              viewport={{ once: true, margin: "-40px" }}
              transition={{ delay: i * 0.08, duration: 0.6, ease: [0.16, 1, 0.3, 1] }}
              className="text-center"
            >
              <div className="fl-serif text-[44px] leading-none text-[var(--paper)] md:text-[52px]">
                {stat.value}
              </div>
              <div className="fl-mono mt-3 text-[10px] uppercase tracking-[0.12em] text-[var(--ink-30)]">
                {stat.label}
              </div>
            </motion.div>
          ))}
        </div>
      </div>
    </section>
  );
}
