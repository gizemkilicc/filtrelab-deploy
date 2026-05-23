"use client";

/* ============================================================
   FiltreLAB · useCinema
   GSAP + ScrollTrigger + Lenis orchestration for the corridor.
   The corridor IS the camera: as the user scrolls, each alcove
   choreographs its own dolly + parallax. Runs once on mount and
   tears everything down on unmount (SPA-safe).
   ============================================================ */

import { useEffect } from "react";
import { gsap } from "gsap";
import { ScrollTrigger } from "gsap/ScrollTrigger";
import Lenis from "lenis";

declare global {
  interface Window {
    __lenis?: Lenis;
  }
}

export function useCinema() {
  useEffect(() => {
    gsap.registerPlugin(ScrollTrigger);

    // honor reduced motion — keep static composition
    const reduced = window.matchMedia("(prefers-reduced-motion: reduce)").matches;

    let lenis: Lenis | null = null;
    let lenisTick: ((time: number) => void) | null = null;
    const extraTweens: gsap.core.Tween[] = [];

    // ---- Lenis smooth scroll -----------------------------------
    if (!reduced) {
      lenis = new Lenis({
        duration: 1.15,
        easing: (t: number) => Math.min(1, 1.001 - Math.pow(2, -10 * t)), // ease-out-expo
        smoothWheel: true,
        wheelMultiplier: 1.0,
      });
      lenis.on("scroll", ScrollTrigger.update);
      lenisTick = (time: number) => lenis?.raf(time * 1000);
      gsap.ticker.add(lenisTick);
      gsap.ticker.lagSmoothing(0);
      window.__lenis = lenis;
    }

    // ---- continuous dust layer ---------------------------------
    const teardownDust = addDustLayer();

    // ---- HERO: title fades, column lifts, vignette deepens ------
    const hero = document.querySelector(".hero");
    if (hero) {
      const tl = gsap.timeline({
        scrollTrigger: { trigger: hero, start: "top top", end: "bottom top", scrub: 1.1 },
      });
      tl.to(".hero__title", { y: -80, opacity: 0.0, ease: "power2.in" }, 0);
      tl.to(".hero__deck", { y: -40, opacity: 0.0 }, 0);
      tl.to(".hero__kicker", { y: -20, opacity: 0.0 }, 0);
      tl.to(".paste-rig", { y: -20, opacity: 0.0 }, 0.1);
      tl.to(".hero__trust", { y: -20, opacity: 0.0 }, 0.1);
      tl.to(".hero__column", { y: -180, opacity: 0.0, ease: "power2.in" }, 0.05);
      tl.to(".hero__motes", { opacity: 0.3 }, 0);
      tl.to(".hero__cone", { opacity: 0.35 }, 0);
      tl.to(".hero__floor", { opacity: 0 }, 0);
    }

    // ---- ALCOVE 1 · vitrine dollies forward, ticket slides up ----
    cinemaAlcove(".alcove--welcome", (sec) => {
      const vit = sec.querySelector(".vitrine__column");
      const tk = sec.querySelector(".ticket");
      const cap = sec.querySelector(".alcove__caption");
      if (vit) {
        gsap.fromTo(
          vit,
          { scale: 0.78, y: 40, filter: "blur(2px)" },
          { scale: 1.04, y: -10, filter: "blur(0px)", ease: "none", scrollTrigger: stEnter(sec, 1.1) }
        );
      }
      if (tk) {
        gsap.fromTo(
          tk,
          { y: 120, rotate: -10, opacity: 0 },
          { y: 0, rotate: -3.5, opacity: 1, ease: "power2.out", scrollTrigger: stReveal(sec) }
        );
      }
      if (cap) parallaxOnSection(cap, sec, -28);
      sec.querySelectorAll(".particles span").forEach((p) => {
        gsap.to(p, {
          y: gsap.utils.random(-80, 80),
          x: gsap.utils.random(-40, 40),
          ease: "none",
          scrollTrigger: stThrough(sec),
        });
      });
    });

    // ---- ALCOVE 2 · astrolabe rings spin, cards orbit ------------
    cinemaAlcove(".alcove--field", (sec) => {
      sec.querySelectorAll(".astrolabe__ring").forEach((r, i) => {
        gsap.to(r, {
          rotation: (i % 2 === 0 ? 1 : -1) * (40 + i * 15),
          ease: "none",
          scrollTrigger: stThrough(sec, 1.2),
        });
      });
      const core = sec.querySelector(".astrolabe__core");
      if (core) {
        gsap.fromTo(
          core,
          { scale: 0.6, opacity: 0 },
          { scale: 1, opacity: 1, ease: "power2.out", scrollTrigger: stReveal(sec) }
        );
      }
      const cap = sec.querySelector(".alcove__caption");
      if (cap) parallaxOnSection(cap, sec, -32);
    });

    // ---- ALCOVE 3 · mirrors emerge, the cracked one ignites ------
    cinemaAlcove(".alcove--mirrors", (sec) => {
      gsap.from(sec.querySelectorAll(".mirror"), {
        opacity: 0,
        y: 40,
        scale: 0.92,
        stagger: { each: 0.04, from: "random" },
        ease: "power2.out",
        scrollTrigger: stReveal(sec),
      });
      const cracked = sec.querySelector(".mirror--cracked");
      if (cracked) {
        gsap.fromTo(cracked, { scale: 0.96 }, { scale: 1.18, ease: "none", scrollTrigger: stThrough(sec, 1.2) });
        gsap.fromTo(cracked, { "--glow": 0.4 }, { "--glow": 1.2, ease: "none", scrollTrigger: stThrough(sec) });
      }
      const flag = sec.querySelector(".bot-flag");
      if (flag) {
        gsap.from(flag, { x: 80, opacity: 0, ease: "power2.out", scrollTrigger: stReveal(sec, 0.7) });
      }
      const cap = sec.querySelector(".alcove__caption");
      if (cap) parallaxOnSection(cap, sec, -28);
    });

    // ---- ALCOVE 4 · tunnel perspective deepens, belt rushes ------
    cinemaAlcove(".alcove--returns", (sec) => {
      const belt = sec.querySelector(".belt");
      if (belt) {
        gsap.fromTo(belt, { rotateX: 48, y: 40 }, { rotateX: 64, y: -20, ease: "none", scrollTrigger: stThrough(sec, 1.3) });
      }
      const walls = sec.querySelector(".tunnel__walls");
      if (walls) {
        gsap.to(walls, { backgroundPositionY: "+=120px", ease: "none", scrollTrigger: stThrough(sec) });
      }
      const cap = sec.querySelector(".alcove__caption");
      if (cap) parallaxOnSection(cap, sec, -28);
    });

    // ---- ALCOVE 5 · brass scale settles into its tilt ------------
    cinemaAlcove(".alcove--scale", (sec) => {
      const beam = sec.querySelector(".scale__beam");
      const left = sec.querySelector(".pan--left");
      const right = sec.querySelector(".pan--right");
      if (beam) gsap.fromTo(beam, { rotation: 0 }, { rotation: -6, ease: "power2.out", scrollTrigger: stReveal(sec, 0.95) });
      if (left) gsap.fromTo(left, { y: 0 }, { y: 44, ease: "power2.out", scrollTrigger: stReveal(sec, 0.95) });
      if (right) gsap.fromTo(right, { y: 0 }, { y: -44, ease: "power2.out", scrollTrigger: stReveal(sec, 0.95) });
      const cap = sec.querySelector(".alcove__caption");
      if (cap) parallaxOnSection(cap, sec, -28);
    });

    // ---- ALCOVE 6 · doors dolly forward; chosen one breathes -----
    cinemaAlcove(".alcove--court", (sec) => {
      const doors = sec.querySelector(".doors");
      if (doors) {
        gsap.fromTo(
          doors,
          { scale: 0.84, y: 80, filter: "brightness(0.6)" },
          { scale: 1, y: 0, filter: "brightness(1)", ease: "power2.out", scrollTrigger: stReveal(sec, 1.0) }
        );
      }
      const active = sec.querySelector(".door--active");
      if (active) {
        extraTweens.push(
          gsap.to(active, { y: -8, ease: "sine.inOut", repeat: -1, yoyo: true, duration: 4 })
        );
      }
      const cap = sec.querySelector(".alcove__caption");
      if (cap) parallaxOnSection(cap, sec, -28);
    });

    // ---- corridor "depth" CSS variable driven by total scroll ----
    ScrollTrigger.create({
      trigger: document.body,
      start: "top top",
      end: "bottom bottom",
      onUpdate: (self) => {
        document.documentElement.style.setProperty("--corridor-depth", self.progress.toFixed(3));
      },
    });

    ScrollTrigger.refresh();

    // when verdict swaps the active door, recompute trigger positions
    const obs = new MutationObserver(() => ScrollTrigger.refresh());
    document.querySelectorAll(".alcove--court").forEach((el) =>
      obs.observe(el, { attributes: true, subtree: true, attributeFilter: ["class"] })
    );

    // ---- cleanup -----------------------------------------------
    return () => {
      obs.disconnect();
      ScrollTrigger.getAll().forEach((st) => st.kill());
      extraTweens.forEach((tw) => tw.kill());
      teardownDust();
      if (lenisTick) gsap.ticker.remove(lenisTick);
      if (lenis) lenis.destroy();
      if (window.__lenis === lenis) delete window.__lenis;
      document.documentElement.style.removeProperty("--corridor-depth");
    };
  }, []);
}

// ---- helpers --------------------------------------------------------

function cinemaAlcove(selector: string, fn: (sec: Element) => void) {
  const sec = document.querySelector(selector);
  if (sec) fn(sec);
}

function stThrough(sec: Element, scrub?: number): ScrollTrigger.Vars {
  return { trigger: sec, start: "top bottom", end: "bottom top", scrub: scrub ?? true };
}
function stReveal(sec: Element, scrub?: number): ScrollTrigger.Vars {
  return { trigger: sec, start: "top 78%", end: "top 30%", scrub: scrub ?? true };
}
function stEnter(sec: Element, scrub?: number): ScrollTrigger.Vars {
  return { trigger: sec, start: "top 90%", end: "top 10%", scrub: scrub ?? true };
}

function parallaxOnSection(el: Element, sec: Element, amount: number) {
  gsap.fromTo(el, { y: -amount }, { y: amount, ease: "none", scrollTrigger: stThrough(sec) });
}

// continuous dust layer — fixed canvas behind everything. Returns a teardown.
function addDustLayer(): () => void {
  if (document.querySelector(".dust-layer")) return () => {};
  const canvas = document.createElement("canvas");
  canvas.className = "dust-layer";
  Object.assign(canvas.style, {
    position: "fixed",
    inset: "0",
    pointerEvents: "none",
    zIndex: "1",
    opacity: "0.35",
    mixBlendMode: "screen",
  });
  document.body.appendChild(canvas);

  const ctx = canvas.getContext("2d");
  const dpr = Math.min(window.devicePixelRatio || 1, 2);
  let w = 0;
  let h = 0;
  let motes: { x: number; y: number; r: number; vy: number; vx: number; a: number }[] = [];
  let rafId = 0;

  function resize() {
    w = canvas.width = window.innerWidth * dpr;
    h = canvas.height = window.innerHeight * dpr;
    canvas.style.width = window.innerWidth + "px";
    canvas.style.height = window.innerHeight + "px";
    motes = [];
    const n = Math.floor((window.innerWidth * window.innerHeight) / 24000);
    for (let i = 0; i < n; i++) {
      motes.push({
        x: Math.random() * w,
        y: Math.random() * h,
        r: (0.5 + Math.random() * 1.6) * dpr,
        vy: (-0.05 - Math.random() * 0.12) * dpr,
        vx: (Math.random() - 0.5) * 0.04 * dpr,
        a: 0.15 + Math.random() * 0.4,
      });
    }
  }
  resize();
  window.addEventListener("resize", resize);

  function tick() {
    if (!ctx) return;
    ctx.clearRect(0, 0, w, h);
    const depth = parseFloat(
      getComputedStyle(document.documentElement).getPropertyValue("--corridor-depth") || "0"
    );
    const r = 247 - depth * 30;
    const g = 240 - depth * 60;
    const b = 220 - depth * 140;
    for (const m of motes) {
      m.x += m.vx;
      m.y += m.vy;
      if (m.y < -10) {
        m.y = h + 10;
        m.x = Math.random() * w;
      }
      if (m.x < -10) m.x = w + 10;
      if (m.x > w + 10) m.x = -10;
      ctx.beginPath();
      ctx.fillStyle = `rgba(${r | 0}, ${g | 0}, ${b | 0}, ${m.a})`;
      ctx.arc(m.x, m.y, m.r, 0, Math.PI * 2);
      ctx.fill();
    }
    rafId = requestAnimationFrame(tick);
  }
  tick();

  return () => {
    cancelAnimationFrame(rafId);
    window.removeEventListener("resize", resize);
    canvas.remove();
  };
}
