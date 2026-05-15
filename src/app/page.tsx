/* eslint-disable react-hooks/set-state-in-effect */
"use client";

import { motion } from "framer-motion";
import { Search, Zap, Droplets, Image as ImageIcon, Waves } from "lucide-react";
import Image from "next/image";
import { useState, useEffect } from "react";
import { useRouter } from "next/navigation";
import { Navbar } from "@/components/ui/Navbar";
import { FeaturedProducts } from "@/components/ui/FeaturedProducts";
import { Chatbot } from "@/components/ui/Chatbot";

export default function Home() {
  const [url, setUrl] = useState("");
  const router = useRouter();
  const [mounted, setMounted] = useState(false);
  const [particles, setParticles] = useState<Array<{top: string, left: string, animationDelay: string, animationDuration: string, size: string}>>([]);

  useEffect(() => {
    const newParticles = [...Array(15)].map(() => ({
      top: `${Math.random() * 100}%`,
      left: `${Math.random() * 100}%`,
      animationDelay: `${Math.random() * 5}s`,
      animationDuration: `${10 + Math.random() * 15}s`,
      size: `${2 + Math.random() * 3}px`
    }));
    setParticles(newParticles);
    setMounted(true);
  }, []);

  const handleAnalyze = (e: React.FormEvent) => {
    e.preventDefault();
    if (!url) return;
    router.push(`/dashboard?url=${encodeURIComponent(url)}`);
  };

  return (
    <main className="min-h-screen flex flex-col relative overflow-x-hidden selection:bg-[var(--neon-blue)] selection:text-white">
      
      {/* Immersive Light Studio Atmosphere */}
      <div className="fixed inset-0 bg-[#f8fafc] z-[-4]" />
      
      {/* AI Generated 3D Crystal Spheres Background */}
      <div className="fixed inset-0 z-[-3] pointer-events-none overflow-hidden flex items-center justify-center">
        <Image src="/images/crystal-bg.png" alt="Crystal Spheres Background" fill className="object-cover opacity-[0.85] scale-[1.15] animate-blob blur-[1px]" priority />
      </div>
      
      {/* Drifting Ambient Globs (Soft Pastel Lighting) */}
      <div className="fixed top-[-10%] left-[0%] w-[60%] h-[60%] bg-[radial-gradient(circle,rgba(236,72,153,0.06)_0%,transparent_60%)] rounded-full pointer-events-none z-[-2] animate-blob blur-[100px]" />
      <div className="fixed top-[20%] right-[-10%] w-[50%] h-[50%] bg-[radial-gradient(circle,rgba(14,165,233,0.06)_0%,transparent_60%)] rounded-full pointer-events-none z-[-2] animate-blob blur-[100px]" style={{ animationDelay: "3s", animationDuration: "25s" }} />

      {/* Floating Ambient Particles (Soft Light Motes) */}
      {mounted && (
        <div className="fixed inset-0 pointer-events-none z-[-1] overflow-hidden">
          {particles.map((style, i) => (
            <div 
              key={i}
              className="absolute bg-white rounded-full animate-particle shadow-[0_2px_8px_rgba(0,0,0,0.05)]"
              style={{
                top: style.top,
                left: style.left,
                width: style.size,
                height: style.size,
                animationDelay: style.animationDelay,
                animationDuration: style.animationDuration
              }}
            />
          ))}
        </div>
      )}
      
      <Navbar />

      {/* Cinematic Hero Section */}
      <section className="relative pt-44 pb-24 md:pt-52 md:pb-36 px-6 flex flex-col items-center justify-center text-center z-10 min-h-[90vh]">
        
        {/* Cinematic Floating 3D Rendered UI Cards */}
        <div className="absolute inset-0 overflow-hidden pointer-events-none z-[-1] flex items-center justify-center perspective-[1000px]">
          <div className="relative w-full max-w-[1000px] h-full animate-float-slow transform-gpu opacity-90">
            {/* We position the illustration slightly offset to frame the text nicely */}
            <div className="absolute top-[10%] right-[-10%] md:right-[-5%] w-[600px] h-[600px] opacity-80 mix-blend-darken rotate-[5deg]">
              <Image src="/images/ui-cards.png" alt="Floating UI Cards" fill className="object-contain" priority />
            </div>
          </div>
        </div>

        <motion.div
          initial={{ opacity: 0, scale: 0.98, y: 20 }}
          animate={{ opacity: 1, scale: 1, y: 0 }}
          transition={{ duration: 1, ease: [0.16, 1, 0.3, 1] }}
          className="max-w-4xl w-full flex flex-col items-center relative z-10"
        >
          {/* Subtle White Glow behind Title for Readability */}
          <div className="absolute top-1/2 left-1/2 -translate-x-1/2 -translate-y-1/2 w-[500px] h-[500px] bg-white opacity-60 blur-[100px] rounded-full pointer-events-none z-[-1]" />

          {/* Premium VisionOS Badge */}
          <motion.div
            initial={{ opacity: 0, y: -10 }}
            animate={{ opacity: 1, y: 0 }}
            transition={{ delay: 0.3, duration: 0.8 }}
            className="inline-flex items-center space-x-2 liquid-glass gloss-overlay rounded-full px-6 py-2.5 mb-10 shadow-[0_8px_25px_rgba(0,0,0,0.04)]"
          >
            <Waves className="w-4 h-4 text-pink-500 drop-shadow-sm" />
            <span className="text-[11px] font-bold text-gray-700 tracking-[0.25em] uppercase">Akıllı Stil Deneyimi</span>
          </motion.div>

          {/* Elegant, Refined Typography */}
          <h1 className="text-5xl md:text-6xl lg:text-[5.5rem] font-medium tracking-tight mb-8 leading-[1.1] text-gray-900 drop-shadow-sm">
            Geleceğin <br className="md:hidden" />
            <span className="font-semibold text-transparent bg-clip-text bg-gradient-to-br from-gray-900 via-gray-700 to-gray-400">Yansıması</span>
          </h1>
          
          <p className="text-lg md:text-xl text-gray-600 mb-14 max-w-2xl mx-auto font-light leading-relaxed tracking-wide">
            Yapay zeka ile stili yeniden keşfedin. <br className="hidden md:block"/> Premium alışverişin aydınlık boyutu.
          </p>

          {/* True Apple VisionOS Floating Glass Search Capsule (Light BG) */}
          <form onSubmit={handleAnalyze} className="relative w-full max-w-2xl mx-auto">
            <div className="relative flex items-center liquid-glass-heavy rounded-[3rem] p-2 transition-all duration-700 hover:shadow-[0_30px_60px_rgba(0,0,0,0.08),inset_0_2px_5px_rgba(255,255,255,1)] group">
              
              <div className="w-14 h-14 flex items-center justify-center rounded-full ml-2 opacity-50 group-focus-within:opacity-100 transition-opacity bg-white/60 shadow-[inset_0_1px_3px_rgba(255,255,255,1)]">
                <Search className="w-6 h-6 text-gray-700" />
              </div>
              
              <input
                type="url"
                placeholder="Analiz edilecek ürün linkini yapıştırın..."
                value={url}
                onChange={(e) => setUrl(e.target.value)}
                required
                className="flex-1 bg-transparent border-none outline-none text-gray-900 px-5 py-5 text-[17px] placeholder:text-gray-500 font-light"
              />
              
              <button
                type="submit"
                className="relative overflow-hidden bg-white backdrop-blur-xl border border-white text-gray-800 px-10 py-5 rounded-[2.5rem] font-semibold text-[15px] transition-all duration-500 hover:bg-gray-50 flex items-center shadow-[0_8px_20px_rgba(0,0,0,0.06),inset_0_2px_4px_rgba(255,255,255,1)] hover:shadow-[0_12px_30px_rgba(0,0,0,0.1)] active:scale-[0.98] group/btn"
              >
                {/* Intense Gloss reflection on hover */}
                <div className="absolute inset-0 bg-gradient-to-r from-transparent via-white/80 to-transparent opacity-0 group-hover/btn:opacity-100 -translate-x-full group-hover/btn:translate-x-full transition-all duration-700 ease-out" />
                <span className="relative z-10 flex items-center tracking-wide">
                  Analiz Et
                  <Zap className="w-4 h-4 ml-2 opacity-60 group-hover/btn:opacity-100 transition-opacity text-pink-500" />
                </span>
              </button>
            </div>
          </form>

        </motion.div>
      </section>

      {/* Featured Products */}
      <FeaturedProducts />

      {/* Spacing before footer */}
      <div className="h-40" />

      {/* Floating Chatbot */}
      <Chatbot />
    </main>
  );
}
