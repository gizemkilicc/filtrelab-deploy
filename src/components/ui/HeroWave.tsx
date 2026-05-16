"use client";

import { motion, useReducedMotion } from "framer-motion";
import Image from "next/image";
import type { CSSProperties } from "react";
import {
  ArrowRight,
  Package,
  Search,
  ShieldCheck,
  ShoppingCart,
  Sparkles,
  Star,
} from "lucide-react";

const trustSignals = [
  ["4D signals", "Price, trust, fit"],
  ["Live cart AI", "Ranks every option"],
  ["Zero clutter", "Premium decisions"],
];

const floatingSignals = [
  { Icon: Package, className: "left-[10%] top-[24%]", delay: "0s" },
  { Icon: Star, className: "left-[30%] top-[78%]", delay: "1.2s" },
  { Icon: Sparkles, className: "right-[16%] top-[15%]", delay: ".7s" },
  { Icon: ShieldCheck, className: "right-[8%] bottom-[18%]", delay: "1.8s" },
];

function FloatingSignals() {
  return (
    <div className="pointer-events-none absolute inset-0 z-10 hidden sm:block" aria-hidden="true">
      {floatingSignals.map(({ Icon, className, delay }) => (
        <div
          key={className}
          className={`hero-float absolute ${className} grid h-10 w-10 place-items-center rounded-full border border-white/15 bg-white/[0.07] text-white/70 shadow-[0_12px_36px_rgba(56,189,248,0.16)]`}
          style={{ animationDelay: delay }}
        >
          <Icon className="h-4 w-4" strokeWidth={1.5} />
        </div>
      ))}
    </div>
  );
}

function ProductFlow() {
  return (
    <div className="pointer-events-none absolute inset-0 z-20 hidden overflow-hidden md:block" aria-hidden="true">
      <svg
        className="absolute left-[4%] top-1/2 h-[360px] w-[66%] -translate-y-1/2 opacity-60"
        viewBox="0 0 900 360"
        fill="none"
      >
        <path
          d="M12 190 C182 76 318 286 456 186 C596 86 716 164 888 176"
          stroke="url(#flowGradient)"
          strokeWidth="1.4"
          strokeDasharray="10 18"
        />
        <defs>
          <linearGradient id="flowGradient" x1="0" y1="0" x2="900" y2="0">
            <stop stopColor="#22d3ee" stopOpacity="0" />
            <stop offset=".34" stopColor="#a78bfa" />
            <stop offset=".72" stopColor="#f0abfc" />
            <stop offset="1" stopColor="#93c5fd" stopOpacity=".85" />
          </linearGradient>
        </defs>
      </svg>

      {[0, 1, 2].map((item) => (
        <div
          key={item}
          className="hero-flow absolute left-[-12%] top-1/2 grid h-11 w-11 place-items-center rounded-2xl border border-white/20 bg-white/10 text-cyan-100 shadow-[0_14px_38px_rgba(34,211,238,0.16)]"
          style={{ animationDelay: `${item * 1.45}s` }}
        >
          <Package className="h-5 w-5" strokeWidth={1.6} />
        </div>
      ))}
    </div>
  );
}

const scanItems = [
  { delay: "0s", path: "scan-product-left", Icon: Package },
  { delay: "0s", path: "scan-product-right", Icon: ShieldCheck },
  { delay: "6s", path: "scan-product-left", Icon: Star },
  { delay: "6s", path: "scan-product-right", Icon: Sparkles },
];

function ProductScanStream() {
  return (
    <div className="pointer-events-none absolute inset-0 z-[65] hidden md:block" aria-hidden="true">
      {scanItems.map(({ delay, path, Icon }, index) => (
        <div
          key={index}
          className={`scan-product ${path} absolute left-1/2 top-1/2 grid h-12 w-12 place-items-center rounded-2xl border border-white/28 bg-white/14 text-white shadow-[inset_0_1px_0_rgba(255,255,255,0.55),0_16px_36px_rgba(34,211,238,0.18)]`}
          style={{ animationDelay: delay } as CSSProperties}
        >
          <Icon className="h-5 w-5" strokeWidth={1.5} />
            <span
              className="scan-spark absolute inset-[-6px] rounded-3xl border border-cyan-100/20"
              style={{ animationDelay: delay }}
            />
        </div>
      ))}
    </div>
  );
}

function FilterLenses() {
  return (
    <div className="pointer-events-none absolute inset-[-56px] z-[70] hidden md:block" aria-hidden="true">
      {[0, 1].map((item) => (
        <div
          key={item}
          className="filter-lens absolute left-1/2 top-1/2 h-24 w-24 overflow-hidden rounded-[1.65rem] border border-white/35 bg-white/18 shadow-[inset_0_1px_0_rgba(255,255,255,0.7),0_18px_42px_rgba(37,99,235,0.28)]"
          style={{
            "--lens-angle": `${item * 180 + 8}deg`,
            "--lens-counter": `${-(item * 180 + 8)}deg`,
            "--lens-radius": "230px",
          } as CSSProperties}
        >
          <Image
            src="/images/product-discovery-orbit.png"
            alt=""
            fill
            sizes="96px"
            className="filter-lens-image object-cover object-center opacity-95"
          />
          <div className="absolute inset-0 bg-gradient-to-br from-white/32 via-transparent to-cyan-300/20" />
          <div className="absolute inset-x-3 top-3 h-px bg-gradient-to-r from-transparent via-white/80 to-transparent" />
          <div className="filter-lens-ring absolute inset-[-10px] rounded-[2rem] border border-cyan-100/20" />
        </div>
      ))}
    </div>
  );
}

function GlassCart() {
  const prefersReducedMotion = useReducedMotion();

  return (
    <motion.div
      className="relative z-30 mx-auto mt-12 h-[330px] w-full max-w-[420px] md:mt-0 lg:max-w-[500px]"
      initial={prefersReducedMotion ? false : { opacity: 0, x: 46 }}
      animate={prefersReducedMotion ? undefined : { opacity: 1, x: 0 }}
      transition={{ duration: 0.75, ease: "easeOut" }}
    >
      <ProductScanStream />
      <FilterLenses />

      <div className="absolute inset-x-10 bottom-0 h-16 rounded-[100%] bg-cyan-300/16 blur-2xl" />
      <div className="absolute inset-0 z-20 overflow-hidden rounded-[2rem] border border-white/30 bg-white/[0.11] shadow-[inset_0_1px_0_rgba(255,255,255,0.68),inset_0_-24px_48px_rgba(8,13,35,0.24),0_30px_80px_rgba(37,99,235,0.24)]">
        <div className="absolute inset-0 bg-[linear-gradient(135deg,rgba(255,255,255,.38)_0%,rgba(255,255,255,.09)_30%,rgba(125,211,252,.16)_52%,rgba(217,70,239,.15)_100%)]" />
        <div className="absolute inset-x-0 top-0 h-1/2 bg-[radial-gradient(ellipse_at_top,rgba(255,255,255,.58),transparent_62%)]" />
        <div className="absolute -left-20 top-8 h-56 w-40 rotate-[-18deg] rounded-full bg-white/18 blur-xl" />
        <div className="absolute right-8 top-8 h-24 w-24 rounded-full border border-white/18 bg-white/[0.05]" />
        <div className="absolute left-8 right-8 top-7 h-px bg-gradient-to-r from-transparent via-white/85 to-transparent" />
        <div className="absolute left-12 top-12 h-2 w-28 rounded-full bg-white/28" />
        <div className="absolute left-12 top-20 h-1.5 w-16 rounded-full bg-cyan-100/22" />
        <div className="absolute bottom-8 right-10 grid grid-cols-2 gap-2 opacity-70">
          {[0, 1, 2, 3].map((item) => (
            <span
              key={item}
              className="h-8 w-8 rounded-xl border border-white/15 bg-white/[0.06]"
            />
          ))}
        </div>

        <div className="absolute inset-0 grid place-items-center">
          <div className="relative grid h-56 w-56 place-items-center rounded-[2rem] border border-white/28 bg-white/[0.1] shadow-[inset_0_1px_0_rgba(255,255,255,0.5),inset_0_-18px_34px_rgba(10,15,40,0.3),0_18px_55px_rgba(8,13,35,0.24),0_0_48px_rgba(168,85,247,0.18)] md:h-64 md:w-64">
            <div className="absolute inset-0 rounded-[2rem] bg-[linear-gradient(145deg,rgba(255,255,255,.28),transparent_42%,rgba(34,211,238,.12))]" />
            <div className="absolute left-5 right-5 top-5 h-px bg-gradient-to-r from-transparent via-white/72 to-transparent" />
            <div className="absolute inset-5 rounded-[1.65rem] border border-cyan-200/20" />
            <div className="absolute inset-9 rounded-[1.3rem] border border-white/12 bg-black/5" />
            <div className="absolute bottom-7 left-8 flex gap-2">
              <span className="h-2.5 w-2.5 rounded-full bg-cyan-100/60" />
              <span className="h-2.5 w-2.5 rounded-full bg-fuchsia-100/50" />
              <span className="h-2.5 w-2.5 rounded-full bg-white/40" />
            </div>
            <div className="absolute -right-4 -top-4 h-16 w-16 rounded-2xl border border-white/18 bg-white/[0.08] shadow-[inset_0_1px_0_rgba(255,255,255,0.35)]" />
            <ShoppingCart
              className="relative z-10 h-28 w-28 text-white/90 drop-shadow-[0_0_26px_rgba(125,211,252,0.72)] md:h-32 md:w-32"
              strokeWidth={1.08}
            />
            <div className="absolute left-1/2 top-1/2 h-24 w-36 -translate-x-1/2 -translate-y-1/2 rounded-[2rem] bg-cyan-200/10 blur-2xl" />
          </div>
        </div>
      </div>
      <div className="pointer-events-none absolute inset-0 z-50 rounded-[2rem] border border-white/12" />
    </motion.div>
  );
}

export function HeroWave() {
  const prefersReducedMotion = useReducedMotion();

  return (
    <section className="relative min-h-screen w-full overflow-hidden bg-[#05010f] px-5 pb-16 pt-28 text-white sm:px-8 lg:px-12">
      <div className="absolute inset-0 bg-[radial-gradient(circle_at_18%_14%,rgba(147,51,234,.38),transparent_30%),radial-gradient(circle_at_76%_22%,rgba(37,99,235,.34),transparent_28%),radial-gradient(circle_at_52%_92%,rgba(6,182,212,.18),transparent_34%),linear-gradient(135deg,#060014_0%,#0b1036_48%,#10031d_100%)]" />
      <div className="absolute inset-0 bg-[linear-gradient(rgba(255,255,255,.045)_1px,transparent_1px),linear-gradient(90deg,rgba(255,255,255,.045)_1px,transparent_1px)] bg-[size:72px_72px] opacity-16 [mask-image:radial-gradient(circle_at_center,black,transparent_72%)]" />
      <div className="absolute -left-20 top-20 h-72 w-72 rounded-full bg-fuchsia-500/22 blur-3xl" />
      <div className="absolute right-0 top-1/4 h-80 w-80 rounded-full bg-blue-500/20 blur-3xl" />

      <FloatingSignals />

      <div className="absolute inset-x-0 top-[15%] z-0 select-none text-center">
        <motion.h1
          className="text-[18vw] font-black leading-none tracking-normal text-transparent opacity-45 [background:linear-gradient(180deg,rgba(255,255,255,.28),rgba(125,211,252,.08)_44%,rgba(217,70,239,.02))] bg-clip-text"
          initial={prefersReducedMotion ? false : { opacity: 0, y: 20 }}
          animate={prefersReducedMotion ? undefined : { opacity: 0.45, y: 0 }}
          transition={{ duration: 0.75, ease: "easeOut" }}
        >
          FiltreLAB
        </motion.h1>
      </div>

      <div className="relative z-30 mx-auto grid min-h-[calc(100vh-7rem)] max-w-7xl items-center gap-10 lg:grid-cols-[1.02fr_.98fr]">
        <motion.div
          className="max-w-3xl pt-10 text-center lg:text-left"
          initial={prefersReducedMotion ? false : { opacity: 0, y: 20 }}
          animate={prefersReducedMotion ? undefined : { opacity: 1, y: 0 }}
          transition={{ duration: 0.7, ease: "easeOut" }}
        >
          <div className="mx-auto mb-7 inline-flex items-center gap-2 rounded-full border border-white/15 bg-white/[0.07] px-4 py-2 text-xs font-medium text-cyan-100 shadow-[0_12px_34px_rgba(125,211,252,0.13)] lg:mx-0">
            <Sparkles className="h-3.5 w-3.5 text-fuchsia-200" />
            VisionOS-grade shopping intelligence
          </div>

          <h2 className="text-5xl font-black leading-[0.92] tracking-normal text-white drop-shadow-[0_0_28px_rgba(255,255,255,0.12)] sm:text-7xl lg:text-8xl">
            Filtre LAB
          </h2>

          <p className="mx-auto mt-7 max-w-2xl text-base leading-8 text-slate-200/76 sm:text-lg lg:mx-0">
            Yapay zekayla filtreli alışveriş
          </p>

          <div className="mt-9 flex flex-col items-center gap-3 sm:flex-row lg:justify-start">
            <button className="group inline-flex h-12 items-center justify-center gap-2 rounded-full bg-white px-6 text-sm font-semibold text-[#09031a] shadow-[0_18px_48px_rgba(255,255,255,0.14)] transition hover:bg-cyan-50 active:scale-[0.98]">
              Start filtering
              <ArrowRight className="h-4 w-4 transition group-hover:translate-x-0.5" />
            </button>
            <button className="inline-flex h-12 items-center justify-center gap-2 rounded-full border border-white/15 bg-white/[0.06] px-6 text-sm font-semibold text-white shadow-[0_18px_42px_rgba(99,102,241,0.14)] transition hover:border-cyan-200/40 hover:bg-white/[0.1] active:scale-[0.98]">
              <Search className="h-4 w-4 text-cyan-200" />
              Explore assistant
            </button>
          </div>

          <div className="mt-10 grid max-w-2xl grid-cols-1 gap-3 sm:grid-cols-3">
            {trustSignals.map(([value, label]) => (
              <div
                key={value}
                className="rounded-2xl border border-white/10 bg-white/[0.055] px-4 py-3 text-left shadow-[inset_0_1px_0_rgba(255,255,255,0.14)]"
              >
                <div className="text-sm font-semibold text-white">{value}</div>
                <div className="mt-1 text-[11px] text-slate-300/70">{label}</div>
              </div>
            ))}
          </div>
        </motion.div>

        <div className="relative">
          <div className="absolute left-1/2 top-1/2 h-[500px] w-[500px] -translate-x-1/2 -translate-y-1/2 rounded-full border border-white/10 bg-[conic-gradient(from_180deg,rgba(34,211,238,.14),rgba(168,85,247,.16),rgba(244,114,182,.1),rgba(34,211,238,.14))] opacity-60" />
          <GlassCart />
        </div>
      </div>

      <div className="pointer-events-none absolute inset-x-0 bottom-0 h-44 bg-gradient-to-t from-[#05010f] via-[#05010f]/80 to-transparent" />
    </section>
  );
}
