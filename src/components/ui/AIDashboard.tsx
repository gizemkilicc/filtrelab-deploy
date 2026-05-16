"use client";

import { motion } from "framer-motion";
import { ShieldCheck, AlertCircle, MessageSquareText, Sparkles, RefreshCw, ScanSearch } from "lucide-react";
import Image from "next/image";

export function AIDashboard() {
  return (
    <section className="relative z-20 w-full max-w-[1200px] mx-auto px-6 py-12 md:py-24">
      
      <div className="flex flex-col md:flex-row items-end justify-between mb-10">
        <div>
          <h2 className="text-3xl md:text-4xl font-semibold tracking-tight text-gray-900 drop-shadow-sm mb-2">
            Akıllı <span className="font-light">Analizler</span>
          </h2>
          <p className="text-gray-500 font-light text-[17px] tracking-wide">
            Yapay zeka ile riskleri minimize edin.
          </p>
        </div>
      </div>

      <div className="grid grid-cols-1 md:grid-cols-3 gap-6">
        
        {/* Güven Skoru */}
        <motion.div 
          initial={{ opacity: 0, y: 20 }}
          whileInView={{ opacity: 1, y: 0 }}
          viewport={{ once: true }}
          className="bento-glass p-8 flex flex-col items-center justify-center text-center relative group"
        >
          <div className="w-16 h-16 rounded-2xl bg-gradient-to-tr from-blue-500 to-purple-500 flex items-center justify-center mb-6 shadow-lg shadow-blue-500/20">
            <ShieldCheck className="w-8 h-8 text-white" />
          </div>
          <h3 className="text-gray-500 font-medium tracking-widest text-[11px] uppercase mb-1">AI Güven Skoru</h3>
          <div className="flex items-baseline space-x-1 mb-2">
            <span className="text-6xl font-bold tracking-tighter text-gray-900">98</span>
            <span className="text-xl font-medium text-gray-400">/100</span>
          </div>
        </motion.div>

        {/* Yorum Analizi & Sahte Yorum Tespiti */}
        <motion.div 
          initial={{ opacity: 0, y: 20 }}
          whileInView={{ opacity: 1, y: 0 }}
          viewport={{ once: true }}
          transition={{ delay: 0.1 }}
          className="bento-glass p-8 md:col-span-2 relative group"
        >
          <div className="flex justify-between items-center mb-8 relative z-10">
            <div className="flex items-center space-x-3">
              <div className="w-10 h-10 rounded-xl bg-purple-100 flex items-center justify-center">
                <MessageSquareText className="w-5 h-5 text-purple-600" />
              </div>
              <div>
                <h3 className="text-gray-900 font-semibold text-[17px]">Kapsamlı Yorum Analizi</h3>
                <p className="text-gray-500 text-[13px] font-light">12,450 yorum yapay zeka ile filtrelendi.</p>
              </div>
            </div>
            
            {/* Sahte Yorum Badge */}
            <div className="flex items-center space-x-2 bg-rose-50 border border-rose-100 px-3 py-1.5 rounded-full">
              <ScanSearch className="w-4 h-4 text-rose-500" />
              <span className="text-[12px] font-medium text-rose-600">%4 Sahte Yorum Temizlendi</span>
            </div>
          </div>

          <div className="space-y-5">
            <div>
              <div className="flex justify-between text-[13px] font-medium mb-1.5">
                <span className="text-gray-700">Pozitif Eğilim</span>
                <span className="text-green-600">85%</span>
              </div>
              <div className="w-full bg-white/50 h-2.5 rounded-full overflow-hidden border border-white/80">
                <motion.div initial={{ width: 0 }} whileInView={{ width: "85%" }} transition={{ duration: 1.5 }} className="h-full bg-gradient-to-r from-green-400 to-emerald-500 rounded-full" />
              </div>
            </div>
            <div>
              <div className="flex justify-between text-[13px] font-medium mb-1.5">
                <span className="text-gray-700">Negatif Sinyaller</span>
                <span className="text-rose-500">3%</span>
              </div>
              <div className="w-full bg-white/50 h-2.5 rounded-full overflow-hidden border border-white/80">
                <motion.div initial={{ width: 0 }} whileInView={{ width: "3%" }} transition={{ duration: 1.5, delay: 0.2 }} className="h-full bg-gradient-to-r from-rose-300 to-rose-400 rounded-full" />
              </div>
            </div>
          </div>
        </motion.div>

        {/* İade Risk Tahmini */}
        <motion.div 
          initial={{ opacity: 0, y: 20 }}
          whileInView={{ opacity: 1, y: 0 }}
          viewport={{ once: true }}
          transition={{ delay: 0.2 }}
          className="bento-glass p-8 relative group"
        >
          <div className="w-10 h-10 rounded-xl bg-orange-50 flex items-center justify-center border border-orange-100 mb-6">
            <RefreshCw className="w-5 h-5 text-orange-500" />
          </div>
          <h3 className="text-gray-900 font-semibold text-[17px] mb-2">İade Risk Tahmini</h3>
          <div className="flex items-end space-x-2 mb-2">
            <span className="text-4xl font-bold tracking-tight text-gray-900">Düşük</span>
          </div>
          <p className="text-[14px] text-gray-600 font-light">
            Beden uyuşmazlığı riski minimum düzeyde. Kendi bedeninizi alabilirsiniz.
          </p>
        </motion.div>

        {/* AI Alışveriş Asistanı */}
        <motion.div 
          initial={{ opacity: 0, y: 20 }}
          whileInView={{ opacity: 1, y: 0 }}
          viewport={{ once: true }}
          transition={{ delay: 0.3 }}
          className="bento-glass p-8 md:col-span-2 relative flex items-center bg-gradient-to-br from-white/80 to-purple-50/50"
        >
          <div className="flex-1 pr-6">
            <h3 className="text-gray-900 font-bold text-2xl mb-2 flex items-center">
              <Sparkles className="w-6 h-6 mr-2 text-purple-500" />
              AI Alışveriş Asistanı
            </h3>
            <p className="text-gray-600 leading-relaxed font-light text-[15px] mb-6">
              Bütçenizi, tarzınızı ve yorumları analiz ederek size en uygun alternatifi önerir. Emin olamadığınızda asistanınıza sorun.
            </p>
            <button className="bg-gray-900 text-white px-6 py-2.5 rounded-full text-[14px] font-medium hover:bg-gray-800 transition-colors shadow-lg shadow-gray-900/20">
              Asistanı Başlat
            </button>
          </div>
          <div className="w-[150px] h-[150px] relative shrink-0">
             <div className="absolute inset-0 bg-purple-200 rounded-full blur-2xl opacity-50 animate-pulse" />
             <div className="absolute inset-2 bg-gradient-to-tr from-blue-400 to-purple-500 rounded-full flex items-center justify-center shadow-inner">
               <Sparkles className="w-12 h-12 text-white opacity-80" />
             </div>
          </div>
        </motion.div>

      </div>
    </section>
  );
}
