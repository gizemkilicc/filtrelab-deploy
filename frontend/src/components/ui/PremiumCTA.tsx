"use client";

import { motion } from "framer-motion";
import { Bell, History, Heart, Bot, ArrowRight } from "lucide-react";
import { useState } from "react";
import { AuthModal } from "./AuthModal";
import Link from "next/link";

const features = [
  {
    icon: Bell,
    title: "Fiyat Takibi",
    description: "Ürün ucuzlayınca sana haber verelim",
    href: "/price-tracking",
  },
  {
    icon: History,
    title: "Analiz Geçmişi",
    description: "Tüm analizlerin kayıtlı kalsın",
    href: "/history",
  },
  {
    icon: Heart,
    title: "Favori Listesi",
    description: "Beğendiğin ürünleri kaydet",
    href: "/favorites",
  },
  {
    icon: Bot,
    title: "Kişisel AI Önerileri",
    description: "Sana özel ürün tavsiyeleri",
    href: "/recommendations",
  },
];

export function PremiumCTA() {
  const [isAuthOpen, setIsAuthOpen] = useState(false);

  return (
    <>
      <section className="w-full px-6 py-24">
        <div className="mx-auto max-w-6xl">
          <div className="fl-card p-10 md:p-14">
            <div className="grid gap-12 lg:grid-cols-[1fr_1.1fr] lg:items-center lg:gap-16">
              {/* Left — headline + CTA */}
              <motion.div
                initial={{ opacity: 0, y: 20 }}
                whileInView={{ opacity: 1, y: 0 }}
                viewport={{ once: true, margin: "-80px" }}
                transition={{ duration: 0.7, ease: [0.16, 1, 0.3, 1] }}
              >
                <p className="fl-kicker">ÜCRETSİZ · SINIRSIZ</p>

                <h2 className="fl-serif mt-5 text-[40px] leading-[1.04] text-[var(--paper)] md:text-[52px]">
                  Hesabınla <span className="italic text-[var(--brass)]">daha fazlasına</span> ulaş
                </h2>

                <p className="fl-sans mt-5 text-[15px] leading-relaxed text-[var(--ink-30)]">
                  Ücretsiz hesap oluşturarak fiyat takibi, analiz geçmişi ve kişisel AI önerileri
                  gibi güçlü özelliklere erişim sağla.
                </p>

                <button onClick={() => setIsAuthOpen(true)} className="fl-btn fl-btn-primary mt-8">
                  Ücretsiz Hesap Oluştur
                  <ArrowRight className="h-4 w-4" />
                </button>

                <p className="fl-mono mt-4 text-[10px] uppercase tracking-[0.1em] text-[var(--ink-30)]">
                  Kredi kartı gerekmez · Reklam yok · Her zaman ücretsiz
                </p>
              </motion.div>

              {/* Right — feature cards grid */}
              <motion.div
                className="grid grid-cols-2 gap-4"
                initial={{ opacity: 0, y: 20 }}
                whileInView={{ opacity: 1, y: 0 }}
                viewport={{ once: true, margin: "-80px" }}
                transition={{ duration: 0.7, ease: [0.16, 1, 0.3, 1] }}
              >
                {features.map((feat) => {
                  const Icon = feat.icon;
                  return (
                    <Link
                      key={feat.title}
                      href={feat.href}
                      className="rounded-[3px] border border-[var(--ink-70)] p-5 transition-colors hover:border-[var(--brass-deep)]"
                    >
                      <Icon className="mb-4 h-5 w-5 text-[var(--brass)]" strokeWidth={1.8} />
                      <h3 className="fl-serif text-[18px] text-[var(--paper)]">{feat.title}</h3>
                      <p className="fl-sans mt-1 text-[12px] leading-relaxed text-[var(--ink-30)]">
                        {feat.description}
                      </p>
                    </Link>
                  );
                })}
              </motion.div>
            </div>
          </div>
        </div>
      </section>

      <AuthModal isOpen={isAuthOpen} onClose={() => setIsAuthOpen(false)} />
    </>
  );
}
