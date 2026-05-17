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
    color: "text-cyan-500 dark:text-cyan-400",
    bg: "bg-cyan-500/10",
    border: "border-cyan-500/15",
    href: "/price-tracking",
  },
  {
    icon: History,
    title: "Analiz Geçmişi",
    description: "Tüm analizlerin kayıtlı kalsın",
    color: "text-purple-500 dark:text-purple-400",
    bg: "bg-purple-500/10",
    border: "border-purple-500/15",
    href: "/history",
  },
  {
    icon: Heart,
    title: "Favori Listesi",
    description: "Beğendiğin ürünleri kaydet",
    color: "text-fuchsia-500 dark:text-fuchsia-400",
    bg: "bg-fuchsia-500/10",
    border: "border-fuchsia-500/15",
    href: "/favorites",
  },
  {
    icon: Bot,
    title: "Kişisel AI Önerileri",
    description: "Sana özel ürün tavsiyeleri",
    color: "text-emerald-500 dark:text-emerald-400",
    bg: "bg-emerald-500/10",
    border: "border-emerald-500/15",
    href: "/recommendations",
  },
];

export function PremiumCTA() {
  const [isAuthOpen, setIsAuthOpen] = useState(false);

  return (
    <>
      <section className="relative w-full overflow-hidden py-24 px-6">
        {/* Background decoration */}
        <div className="pointer-events-none absolute inset-0 -z-10">
          <div className="absolute inset-0 bg-gradient-to-b from-transparent via-purple-500/5 to-transparent dark:via-purple-500/10" />
          <div className="absolute left-1/2 top-1/2 h-[500px] w-[500px] -translate-x-1/2 -translate-y-1/2 rounded-full bg-purple-500/8 blur-3xl dark:bg-purple-500/15" />
        </div>

        <div className="mx-auto max-w-7xl">
          <div className="rounded-[2.5rem] border border-purple-500/15 dark:border-purple-500/20 bg-gradient-to-br from-purple-500/8 via-fuchsia-500/5 to-cyan-500/8 dark:from-purple-500/12 dark:via-fuchsia-500/8 dark:to-cyan-500/12 p-10 backdrop-blur-sm md:p-14">
            <div className="grid gap-12 lg:grid-cols-[1fr_1.1fr] lg:gap-16 lg:items-center">

              {/* Left — headline + CTA */}
              <motion.div
                initial={{ opacity: 0, x: -24 }}
                whileInView={{ opacity: 1, x: 0 }}
                viewport={{ once: true, margin: "-80px" }}
                transition={{ duration: 0.7, ease: [0.16, 1, 0.3, 1] }}
              >
                <span className="mb-4 inline-flex items-center gap-2 rounded-full border border-purple-500/20 bg-purple-500/10 px-4 py-1.5 text-xs font-semibold uppercase tracking-widest text-purple-500 dark:text-purple-300">
                  Ücretsiz · Sınırsız
                </span>

                <h2 className="mt-4 text-4xl font-black tracking-tight text-gray-900 dark:text-white md:text-5xl">
                  Hesabınla{" "}
                  <span className="bg-gradient-to-r from-purple-600 via-fuchsia-500 to-cyan-500 bg-clip-text text-transparent">
                    Daha Fazlasına
                  </span>{" "}
                  Ulaş
                </h2>

                <p className="mt-5 text-[16px] leading-7 text-gray-500 dark:text-gray-400">
                  Ücretsiz hesap oluşturarak fiyat takibi, analiz geçmişi ve kişisel AI önerileri gibi güçlü özelliklere erişim sağla.
                </p>

                <button
                  onClick={() => setIsAuthOpen(true)}
                  className="btn-holo group mt-8 inline-flex items-center gap-2.5 rounded-full px-7 py-3.5 text-[15px] font-semibold text-white"
                >
                  Ücretsiz Hesap Oluştur
                  <ArrowRight className="h-4 w-4 transition-transform duration-300 group-hover:translate-x-0.5" />
                </button>

                <p className="mt-3 text-xs text-gray-400 dark:text-gray-500">
                  Kredi kartı gerekmez · Reklam yok · Her zaman ücretsiz
                </p>
              </motion.div>

              {/* Right — feature cards grid */}
              <motion.div
                className="grid grid-cols-2 gap-4"
                initial={{ opacity: 0, x: 24 }}
                whileInView={{ opacity: 1, x: 0 }}
                viewport={{ once: true, margin: "-80px" }}
                transition={{ duration: 0.7, ease: [0.16, 1, 0.3, 1] }}
              >
                {features.map((feat, i) => (
                  <motion.div
                    key={feat.title}
                    initial={{ opacity: 0, y: 16 }}
                    whileInView={{ opacity: 1, y: 0 }}
                    viewport={{ once: true, margin: "-40px" }}
                    transition={{ delay: i * 0.08, duration: 0.6, ease: [0.16, 1, 0.3, 1] }}
                    className="contents"
                  >
                    <Link href={feat.href} className={`rounded-2xl border ${feat.border} ${feat.bg} p-5 transition-transform hover:-translate-y-0.5`}>
                      <div className={`mb-3 inline-flex h-10 w-10 items-center justify-center rounded-xl border ${feat.border} bg-white/60 dark:bg-white/5`}>
                        <feat.icon className={`h-4.5 w-4.5 ${feat.color}`} strokeWidth={1.8} />
                      </div>
                      <h3 className="mb-1 text-[15px] font-bold text-gray-900 dark:text-white">{feat.title}</h3>
                      <p className="text-xs leading-5 text-gray-500 dark:text-gray-400">{feat.description}</p>
                    </Link>
                  </motion.div>
                ))}
              </motion.div>
            </div>
          </div>
        </div>
      </section>

      <AuthModal isOpen={isAuthOpen} onClose={() => setIsAuthOpen(false)} />
    </>
  );
}
