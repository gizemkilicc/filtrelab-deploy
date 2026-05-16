"use client";

import { motion, AnimatePresence } from "framer-motion";
import { X, Sparkles, Fingerprint } from "lucide-react";
import { useState, useEffect } from "react";
import { createPortal } from "react-dom";
import { registerUser, loginUser, forgotPassword } from "@/lib/apiClient";

interface AuthModalProps {
  isOpen: boolean;
  onClose: () => void;
}

type Mode = "login" | "register" | "forgot";

export function AuthModal({ isOpen, onClose }: AuthModalProps) {
  const [mode, setMode] = useState<Mode>("login");
  const [mounted, setMounted] = useState(false);

  // Form fields
  const [name, setName] = useState("");
  const [email, setEmail] = useState("");
  const [password, setPassword] = useState("");

  // UI state
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [successMsg, setSuccessMsg] = useState<string | null>(null);

  useEffect(() => {
    setMounted(true);
  }, []);

  // Reset state when modal opens or mode changes
  useEffect(() => {
    setError(null);
    setSuccessMsg(null);
    setName("");
    setEmail("");
    setPassword("");
  }, [mode, isOpen]);

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    setError(null);
    setSuccessMsg(null);
    setLoading(true);

    try {
      if (mode === "register") {
        const res = await registerUser(name, email, password);
        if (res.success) {
          setSuccessMsg(res.message);
        } else {
          setError(res.error);
        }
      } else if (mode === "login") {
        const res = await loginUser(email, password);
        if (res.success) {
          if (res.message) {
            // Email not verified — still let them in but warn
            setSuccessMsg(`Giriş başarılı! ${res.message}`);
            setTimeout(() => onClose(), 2000);
          } else {
            onClose();
          }
        } else {
          setError(res.error);
        }
      } else if (mode === "forgot") {
        const res = await forgotPassword(email);
        if (res.success) {
          setSuccessMsg(res.message);
        } else {
          setError(res.error);
        }
      }
    } finally {
      setLoading(false);
    }
  };

  if (!mounted) return null;

  const title =
    mode === "login"
      ? "FiltreLAB'a Giriş Yap"
      : mode === "register"
      ? "Yeni Hesap Oluştur"
      : "Şifremi Unuttum";

  const submitLabel =
    mode === "login"
      ? "Giriş Yap"
      : mode === "register"
      ? "Kayıt Ol"
      : "Sıfırlama Bağlantısı Gönder";

  return createPortal(
    <AnimatePresence>
      {isOpen && (
        <div className="fixed inset-0 z-[100] flex items-center justify-center p-4">
          {/* Blurred backdrop */}
          <motion.div
            initial={{ opacity: 0 }}
            animate={{ opacity: 1 }}
            exit={{ opacity: 0 }}
            onClick={onClose}
            className="absolute inset-0 bg-white/40 backdrop-blur-xl"
          />

          {/* Modal */}
          <motion.div
            initial={{ opacity: 0, scale: 0.95, y: 10 }}
            animate={{ opacity: 1, scale: 1, y: 0 }}
            exit={{ opacity: 0, scale: 0.95, y: 10 }}
            transition={{ type: "spring", damping: 25, stiffness: 300 }}
            className="relative w-full max-w-md liquid-glass-heavy gloss-overlay rounded-[2.5rem] p-8 shadow-[0_25px_60px_rgba(0,0,0,0.08)] overflow-hidden border border-white"
          >
            <div className="absolute inset-0 bg-gradient-to-tr from-pink-500/5 via-white/50 to-blue-500/5 pointer-events-none" />

            {/* Close */}
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
                {title}
              </h2>
              <p className="text-gray-500 font-light text-[17px] tracking-wide mt-2">
                FiltreLAB tarafından onaylanmış premium seçimler.
              </p>
            </div>

            {/* Feedback messages */}
            {error && (
              <div className="mb-4 relative z-10 px-4 py-3 rounded-xl bg-red-50 border border-red-200 text-red-700 text-sm">
                {error}
              </div>
            )}
            {successMsg && (
              <div className="mb-4 relative z-10 px-4 py-3 rounded-xl bg-green-50 border border-green-200 text-green-700 text-sm">
                {successMsg}
              </div>
            )}

            {/* Form */}
            <form className="space-y-4 relative z-10" onSubmit={handleSubmit}>
              {mode === "register" && (
                <div>
                  <label className="block text-[11px] font-semibold text-gray-500 mb-1.5 ml-1 tracking-widest uppercase">
                    Ad Soyad
                  </label>
                  <input
                    type="text"
                    placeholder="Jane Doe"
                    value={name}
                    onChange={(e) => setName(e.target.value)}
                    required
                    className="w-full bg-white/60 border border-white rounded-xl px-4 py-3.5 text-gray-900 placeholder:text-gray-400 focus:outline-none focus:border-white focus:bg-white transition-all shadow-[inset_0_1px_3px_rgba(0,0,0,0.02)] font-light text-[15px]"
                  />
                </div>
              )}

              <div>
                <label className="block text-[11px] font-semibold text-gray-500 mb-1.5 ml-1 tracking-widest uppercase">
                  E-Posta
                </label>
                <input
                  type="email"
                  placeholder="ornek@mail.com"
                  value={email}
                  onChange={(e) => setEmail(e.target.value)}
                  required
                  className="w-full bg-white/60 border border-white rounded-xl px-4 py-3.5 text-gray-900 placeholder:text-gray-400 focus:outline-none focus:border-white focus:bg-white transition-all shadow-[inset_0_1px_3px_rgba(0,0,0,0.02)] font-light text-[15px]"
                />
              </div>

              {mode !== "forgot" && (
                <div>
                  <label className="block text-[11px] font-semibold text-gray-500 mb-1.5 ml-1 tracking-widest uppercase">
                    Şifre
                  </label>
                  <input
                    type="password"
                    placeholder="••••••••"
                    value={password}
                    onChange={(e) => setPassword(e.target.value)}
                    required
                    minLength={6}
                    className="w-full bg-white/60 border border-white rounded-xl px-4 py-3.5 text-gray-900 placeholder:text-gray-400 focus:outline-none focus:border-white focus:bg-white transition-all shadow-[inset_0_1px_3px_rgba(0,0,0,0.02)] font-light text-[15px]"
                  />
                </div>
              )}

              {/* Forgot password link inside login */}
              {mode === "login" && (
                <div className="text-right">
                  <button
                    type="button"
                    onClick={() => setMode("forgot")}
                    className="text-[12px] text-gray-400 hover:text-gray-700 transition-colors underline underline-offset-2 decoration-gray-300"
                  >
                    Şifremi unuttum
                  </button>
                </div>
              )}

              <button
                type="submit"
                disabled={loading}
                className="w-full relative group overflow-hidden rounded-xl mt-6 border border-white shadow-[0_4px_15px_rgba(0,0,0,0.05),inset_0_2px_4px_rgba(255,255,255,1)] transition-all active:scale-[0.98] bg-white/80 hover:bg-white backdrop-blur-md disabled:opacity-60 disabled:cursor-not-allowed"
              >
                <div className="absolute inset-0 bg-gradient-to-r from-transparent via-white to-transparent opacity-0 group-hover:opacity-100 -translate-x-full group-hover:translate-x-full transition-all duration-700 ease-out" />
                <div className="relative px-4 py-3.5 flex items-center justify-center font-medium text-gray-800 text-[15px]">
                  {loading ? "Lütfen bekleyin..." : submitLabel}
                  {!loading && <Sparkles className="w-4 h-4 ml-2 opacity-80" />}
                </div>
              </button>
            </form>

            {/* Toggle Login / Register / Back */}
            <div className="mt-6 text-center relative z-10 space-y-2">
              {mode === "forgot" ? (
                <button
                  onClick={() => setMode("login")}
                  className="text-[13px] text-gray-500 hover:text-gray-900 transition-colors font-light"
                >
                  ← Giriş ekranına dön
                </button>
              ) : (
                <button
                  onClick={() => setMode(mode === "login" ? "register" : "login")}
                  className="text-[13px] text-gray-500 hover:text-gray-900 transition-colors font-light"
                >
                  {mode === "login" ? "Hesabınız yok mu? " : "Zaten hesabınız var mı? "}
                  <span className="font-medium underline underline-offset-4 decoration-gray-300 hover:decoration-gray-500">
                    {mode === "login" ? "Kayıt Ol" : "Giriş Yap"}
                  </span>
                </button>
              )}
            </div>
          </motion.div>
        </div>
      )}
    </AnimatePresence>,
    document.body
  );
}
