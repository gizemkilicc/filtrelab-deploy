/* eslint-disable react-hooks/set-state-in-effect */
"use client";

import { motion, AnimatePresence } from "framer-motion";
import { X, Sparkles, Fingerprint } from "lucide-react";
import { useState, useEffect } from "react";
import { createPortal } from "react-dom";

interface AuthModalProps {
  isOpen: boolean;
  onClose: () => void;
}

export function AuthModal({ isOpen, onClose }: AuthModalProps) {
  const [isLogin, setIsLogin] = useState(true);
  const [mounted, setMounted] = useState(false);

  useEffect(() => {
    setMounted(true);
  }, []);

  if (!mounted) return null;

  return createPortal(
    <AnimatePresence>
      {isOpen && (
        <div className="fixed inset-0 z-[100] flex items-center justify-center p-4">
          {/* Light Studio blurred backdrop */}
          <motion.div
            initial={{ opacity: 0 }}
            animate={{ opacity: 1 }}
            exit={{ opacity: 0 }}
            onClick={onClose}
            className="absolute inset-0 bg-white/40 backdrop-blur-xl"
          />

          {/* Elegant Crystal VisionOS Modal */}
          <motion.div
            initial={{ opacity: 0, scale: 0.95, y: 10 }}
            animate={{ opacity: 1, scale: 1, y: 0 }}
            exit={{ opacity: 0, scale: 0.95, y: 10 }}
            transition={{ type: "spring", damping: 25, stiffness: 300 }}
            className="relative w-full max-w-md liquid-glass-heavy gloss-overlay rounded-[2.5rem] p-8 shadow-[0_25px_60px_rgba(0,0,0,0.08)] overflow-hidden border border-white"
          >
            {/* Subtle pastel pink/blue inner glow */}
            <div className="absolute inset-0 bg-gradient-to-tr from-pink-500/5 via-white/50 to-blue-500/5 pointer-events-none" />

            {/* Close Button */}
            <button 
              onClick={onClose}
              className="absolute top-5 right-5 text-gray-400 hover:text-gray-900 transition-all hover:scale-110 z-20 bg-white/50 hover:bg-white p-2.5 rounded-full backdrop-blur-md border border-white/80 shadow-[inset_0_1px_2px_rgba(255,255,255,1),0_2px_4px_rgba(0,0,0,0.05)]"
            >
              <X className="w-4 h-4" />
            </button>

            {/* Header */}
            <div className="text-center mb-8 relative z-10">
              <div className="mx-auto w-14 h-14 bg-white/80 backdrop-blur-md rounded-[1rem] flex items-center justify-center mb-4 border border-white shadow-[inset_0_2px_5px_rgba(255,255,255,1),0_4px_10px_rgba(0,0,0,0.06)]">
                <Fingerprint className="w-6 h-6 text-gray-700 drop-shadow-sm" />
              </div>
              <h2 className="text-2xl font-semibold tracking-tight text-gray-900 drop-shadow-sm">
                {isLogin ? "FiltreLAB'a Giriş Yap" : "Yeni Hesap Oluştur"}
              </h2>
              <p className="text-gray-500 font-light text-[17px] tracking-wide mt-2">FiltreLAB tarafından onaylanmış premium seçimler.</p>
            </div>

            {/* Form */}
            <form className="space-y-4 relative z-10" onSubmit={(e) => e.preventDefault()}>
              {!isLogin && (
                <div>
                  <label className="block text-[11px] font-semibold text-gray-500 mb-1.5 ml-1 tracking-widest uppercase">Ad Soyad</label>
                  <input 
                    type="text" 
                    placeholder="Jane Doe"
                    className="w-full bg-white/60 border border-white rounded-xl px-4 py-3.5 text-gray-900 placeholder:text-gray-400 focus:outline-none focus:border-white focus:bg-white transition-all shadow-[inset_0_1px_3px_rgba(0,0,0,0.02)] font-light text-[15px]"
                  />
                </div>
              )}
              <div>
                <label className="block text-[11px] font-semibold text-gray-500 mb-1.5 ml-1 tracking-widest uppercase">E-Posta</label>
                <input 
                  type="email" 
                  placeholder="ornek@mail.com"
                  className="w-full bg-white/60 border border-white rounded-xl px-4 py-3.5 text-gray-900 placeholder:text-gray-400 focus:outline-none focus:border-white focus:bg-white transition-all shadow-[inset_0_1px_3px_rgba(0,0,0,0.02)] font-light text-[15px]"
                />
              </div>
              <div>
                <label className="block text-[11px] font-semibold text-gray-500 mb-1.5 ml-1 tracking-widest uppercase">Şifre</label>
                <input 
                  type="password" 
                  placeholder="••••••••"
                  className="w-full bg-white/60 border border-white rounded-xl px-4 py-3.5 text-gray-900 placeholder:text-gray-400 focus:outline-none focus:border-white focus:bg-white transition-all shadow-[inset_0_1px_3px_rgba(0,0,0,0.02)] font-light text-[15px]"
                />
              </div>


              {/* Soft White Soft Button */}
              <button className="w-full relative group overflow-hidden rounded-xl mt-6 border border-white shadow-[0_4px_15px_rgba(0,0,0,0.05),inset_0_2px_4px_rgba(255,255,255,1)] transition-all active:scale-[0.98] bg-white/80 hover:bg-white backdrop-blur-md">
                <div className="absolute inset-0 bg-gradient-to-r from-transparent via-white to-transparent opacity-0 group-hover:opacity-100 -translate-x-full group-hover:translate-x-full transition-all duration-700 ease-out" />
                <div className="relative px-4 py-3.5 flex items-center justify-center font-medium text-gray-800 text-[15px]">
                  {isLogin ? "Giriş Yap" : "Kayıt Ol"}
                  <Sparkles className="w-4 h-4 ml-2 opacity-80" />
                </div>
              </button>
            </form>

            {/* Toggle Login/Register */}
            <div className="mt-6 text-center relative z-10">
              <button 
                onClick={() => setIsLogin(!isLogin)}
                className="text-[13px] text-gray-500 hover:text-gray-900 transition-colors font-light"
              >
                {isLogin ? "Hesabınız yok mu? " : "Zaten hesabınız var mı? "}
                <span className="font-medium underline underline-offset-4 decoration-gray-300 hover:decoration-gray-500">
                  {isLogin ? "Kayıt Ol" : "Giriş Yap"}
                </span>
              </button>
            </div>

          </motion.div>
        </div>
      )}
    </AnimatePresence>,
    document.body
  );
}
