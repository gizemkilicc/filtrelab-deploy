"use client";

/* ============================================================
   FiltreLAB — Corridor
   Full cinematic landing: Hero + 6 scroll-driven alcoves, with a
   left progress rail, brand strip, and a hidden transparency panel
   (type "filtre" to open). The corridor explains the 6-step
   analysis on a sample product; the Hero URL box runs the real
   analysis on /dashboard.
   ============================================================ */

import { useEffect, useState } from "react";
import { Hero } from "./Hero";
import {
  AlcoveWelcome,
  AlcoveField,
  AlcoveMirrors,
  AlcoveReturns,
  AlcoveScale,
  AlcoveCourt,
  PRODUCT,
  type Verdict,
  type Confidence,
} from "./Alcoves";
import { useCinema } from "./useCinema";
import "./corridor.css";

// Fixed demo verdict for the explainer corridor.
const VERDICT: Verdict = "CAUTION";
const CONFIDENCE: Confidence = "MEDIUM";

const STEPS = [
  { i: 1, t: "Linki Tanıma" },
  { i: 2, t: "Yorum Analizi" },
  { i: 3, t: "Sahte Yorum Kontrolü" },
  { i: 4, t: "İade Riski" },
  { i: 5, t: "Fiyat Karşılaştırması" },
  { i: 6, t: "Nihai Karar" },
];

function Rail({ active, onJump }: { active: number; onJump: (i: number) => void }) {
  return (
    <nav className="rail" aria-label="Alcove progress">
      {STEPS.map((s) => (
        <a
          key={s.i}
          className={`rail__step ${active === s.i ? "is-active" : ""}`}
          onClick={() => onJump(s.i)}
        >
          <span className="num">{String(s.i).padStart(2, "0")}</span>
          <span className="tick"></span>
          <span>{s.t}</span>
        </a>
      ))}
    </nav>
  );
}

function Brand() {
  return (
    <div className="brand">
      <b>FiltreLAB</b>
      <span>· akıllı alışveriş asistanı</span>
    </div>
  );
}

function DataMode({ open, onClose }: { open: boolean; onClose: () => void }) {
  if (!open) return null;
  return (
    <div className="data-mode visible">
      <div className="data-mode__panel">
        <button className="data-mode__close" onClick={onClose}>
          Kapat · ESC
        </button>
        <h3>Verinin arkasında ne var?</h3>
        <p>· ileri seviye kullanıcılar için şeffaflık paneli</p>

        <div className="data-mode__row">
          <span>Veri kaynağı</span>
          <span>Trendyol · ürün ID 9484017</span>
          <b>tam</b>
        </div>
        <div className="data-mode__row">
          <span>Son güncelleme</span>
          <span>19.05.2026 · 03:14</span>
          <b>26 dk önce</b>
        </div>
        <div className="data-mode__row">
          <span>Taranan yorum</span>
          <span>
            {PRODUCT.reviews} / {PRODUCT.reviews} yorum
          </span>
          <b>%100</b>
        </div>
        <div className="data-mode__row">
          <span>Çapraz karşılaştırma</span>
          <span>Hepsiburada ✓ · Amazon ✓ · İdefix ✗</span>
          <b>2/3</b>
        </div>
        <div className="data-mode__row">
          <span>Sahte yorum modeli</span>
          <span>%87 doğruluk · {PRODUCT.reviews} yorumda doğrulanmış</span>
          <b>aktif</b>
        </div>
        <div className="data-mode__row">
          <span>Güven seviyesi</span>
          <span>0.71 · düşük güven eşiği 0.55</span>
          <b>geçer</b>
        </div>
      </div>
    </div>
  );
}

export function Corridor() {
  const [active, setActive] = useState(0);
  const [dataMode, setDataMode] = useState(false);

  useCinema();

  // intersection observer to track current alcove
  useEffect(() => {
    const sections = document.querySelectorAll(".alcove, .hero");
    if (!sections.length) return;
    const obs = new IntersectionObserver(
      (entries) => {
        const visible = entries.filter((e) => e.isIntersecting);
        if (!visible.length) return;
        const best = visible.reduce((a, b) =>
          b.intersectionRatio > a.intersectionRatio ? b : a
        );
        const label = best.target.getAttribute("data-screen-label") || "";
        const num = parseInt(label.slice(0, 2), 10);
        if (!isNaN(num)) setActive(num);
      },
      { threshold: [0.35, 0.55, 0.75] }
    );
    sections.forEach((s) => obs.observe(s));
    return () => obs.disconnect();
  }, []);

  // f-i-l-t-r-e gesture → open transparency panel
  useEffect(() => {
    let buf = "";
    const handler = (e: KeyboardEvent) => {
      if (e.key === "Escape") {
        setDataMode(false);
        return;
      }
      if (e.key.length !== 1) return;
      buf = (buf + e.key.toLowerCase()).slice(-6);
      if (buf === "filtre") setDataMode(true);
    };
    window.addEventListener("keydown", handler);
    return () => window.removeEventListener("keydown", handler);
  }, []);

  const jumpTo = (i: number) => {
    const el = document.querySelectorAll<HTMLElement>(".alcove")[i - 1];
    if (el) {
      if (window.__lenis) window.__lenis.scrollTo(el, { duration: 1.4 });
      else window.scrollTo({ top: el.offsetTop, behavior: "smooth" });
    }
  };

  return (
    <>
      {active > 0 && <Brand />}
      {active > 0 && <Rail active={active} onJump={jumpTo} />}

      <main className="corridor">
        <Hero />
        <AlcoveWelcome />
        <AlcoveField />
        <AlcoveMirrors />
        <AlcoveReturns />
        <AlcoveScale />
        <AlcoveCourt verdict={VERDICT} confidence={CONFIDENCE} />
      </main>

      <DataMode open={dataMode} onClose={() => setDataMode(false)} />
    </>
  );
}
