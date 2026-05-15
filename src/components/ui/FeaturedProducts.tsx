"use client";

import { motion, useMotionTemplate, useMotionValue } from "framer-motion";
import Image from "next/image";
import { featuredProducts, type Product } from "@/lib/mockProducts";
import { Sparkles, BrainCircuit } from "lucide-react";
import { useRouter } from "next/navigation";
import { MouseEvent } from "react";

export function FeaturedProducts() {
  const router = useRouter();

  const handleAnalyze = (url: string) => {
    router.push(`/dashboard?url=${encodeURIComponent(url)}`);
  };

  return (
    <section className="w-full max-w-7xl mx-auto mt-24 px-6 relative z-10">
      <div className="flex items-end justify-between mb-14">
        <div>
          <h2 className="text-4xl md:text-5xl font-medium tracking-tight mb-3 text-gray-900 drop-shadow-sm">
            AI <span className="font-semibold text-gray-400">Koleksiyonu</span>
          </h2>
          <p className="text-gray-500 font-light text-[17px] tracking-wide">FiltreLAB tarafından onaylanmış premium seçimler</p>
        </div>
        <button className="hidden md:flex items-center space-x-2 text-gray-600 hover:text-gray-900 transition-all group bg-white/70 px-6 py-2.5 rounded-full border border-white backdrop-blur-xl shadow-[inset_0_1px_3px_rgba(255,255,255,1),0_4px_15px_rgba(0,0,0,0.04)] hover:shadow-[0_8px_25px_rgba(0,0,0,0.08)] active:scale-[0.98]">
          <span className="font-medium text-[15px]">Tümünü Keşfet</span>
          <Sparkles className="w-4 h-4 group-hover:rotate-12 transition-transform" />
        </button>
      </div>

      <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-8">
        {featuredProducts.map((product, index) => (
          <ProductCard key={product.id} product={product} index={index} handleAnalyze={handleAnalyze} />
        ))}
      </div>
    </section>
  );
}

function ProductCard({ product, index, handleAnalyze }: { product: Product, index: number, handleAnalyze: (url: string) => void }) {
  const mouseX = useMotionValue(0);
  const mouseY = useMotionValue(0);

  function handleMouseMove({ currentTarget, clientX, clientY }: MouseEvent) {
    const { left, top } = currentTarget.getBoundingClientRect();
    mouseX.set(clientX - left);
    mouseY.set(clientY - top);
  }

  return (
    <motion.div
      initial={{ opacity: 0, y: 30 }}
      whileInView={{ opacity: 1, y: 0 }}
      viewport={{ once: true, margin: "-50px" }}
      transition={{ delay: index * 0.1, duration: 0.8, ease: [0.16, 1, 0.3, 1] }}
      className="relative group h-full"
      onMouseMove={handleMouseMove}
    >
      {/* Dynamic Apple-Style Soft Glow Hover Background */}
      <motion.div
        className="absolute -inset-px rounded-[2.5rem] opacity-0 group-hover:opacity-100 transition-opacity duration-700 will-change-transform pointer-events-none z-0"
        style={{
          background: useMotionTemplate`
            radial-gradient(
              400px circle at ${mouseX}px ${mouseY}px,
              rgba(255, 255, 255, 0.8) 0%,
              transparent 80%
            )
          `,
        }}
      />
      
      {/* High-Fidelity Layered Acrylic Card (Light Theme) */}
      <div className="liquid-glass gloss-overlay rounded-[2.5rem] p-4 overflow-hidden h-full flex flex-col relative z-10 transition-transform duration-700 group-hover:-translate-y-2 will-change-transform bg-white/50 backdrop-blur-3xl shadow-[0_12px_40px_rgba(0,0,0,0.04)] group-hover:shadow-[0_20px_60px_rgba(0,0,0,0.1)] border border-white">
        
        {/* Image Container with deep shadow */}
        <div className="relative w-full h-[22rem] rounded-[2rem] overflow-hidden mb-6 border border-white shadow-[0_8px_25px_rgba(0,0,0,0.06)] bg-gray-100">
          <Image 
            src={product.image} 
            alt={product.name} 
            fill 
            className="object-cover transition-transform duration-[1.5s] ease-out group-hover:scale-[1.08] will-change-transform"
          />
          
          {/* Subtle refraction layer over image */}
          <div className="absolute inset-0 bg-gradient-to-tr from-white/10 to-transparent pointer-events-none mix-blend-overlay" />
          
          {/* Top gloss over image */}
          <div className="absolute top-0 left-0 right-0 h-1/2 bg-gradient-to-b from-white/60 to-transparent pointer-events-none" />
          
          {/* AI Score Badge - Apple Style */}
          <div className="absolute top-4 left-4 bg-white/90 backdrop-blur-2xl px-4 py-2 rounded-full flex items-center space-x-2 border border-white shadow-[0_4px_15px_rgba(0,0,0,0.08),inset_0_2px_5px_rgba(255,255,255,1)]">
            <BrainCircuit className="w-4 h-4 text-pink-500 drop-shadow-sm" />
            <span className="text-[12px] font-bold text-gray-800 tracking-wide">{product.aiScore} Skor</span>
          </div>
        </div>

        {/* Product Info */}
        <div className="flex-1 flex flex-col justify-between px-2 pb-2 relative z-10">
          <div>
            <h3 className="text-[11px] font-bold text-gray-400 tracking-[0.2em] uppercase mb-2">{product.brand}</h3>
            <h2 className="text-[22px] font-semibold text-gray-900 mb-2 leading-tight drop-shadow-sm">{product.name}</h2>
          </div>
          <div className="flex items-center justify-between mt-6">
            <span className="text-2xl font-medium text-gray-900 drop-shadow-sm">{product.price}</span>
            
            {/* Analyze Action - Ultra Premium Floating Button */}
            <button 
              onClick={() => handleAnalyze(product.mockUrl)}
              className="bg-white/90 hover:bg-white border border-white backdrop-blur-xl text-gray-800 p-3.5 rounded-2xl transition-all duration-500 flex items-center justify-center group/btn relative overflow-hidden shadow-[0_4px_15px_rgba(0,0,0,0.06),inset_0_2px_4px_rgba(255,255,255,1)] hover:shadow-[0_10px_25px_rgba(0,0,0,0.12)] active:scale-95"
            >
              {/* Gloss sweep on hover */}
              <div className="absolute inset-0 bg-gradient-to-r from-transparent via-white to-transparent opacity-0 group-hover/btn:opacity-100 -translate-x-full group-hover/btn:translate-x-full transition-all duration-[0.8s] ease-out" />
              <Sparkles className="w-5 h-5 text-gray-700 group-hover/btn:rotate-12 transition-transform duration-500 relative z-10" />
            </button>
          </div>
        </div>
      </div>
    </motion.div>
  );
}
