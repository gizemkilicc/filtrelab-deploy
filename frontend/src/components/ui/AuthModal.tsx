"use client";

import { motion, AnimatePresence } from "framer-motion";
import { X } from "lucide-react";
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
  const [mounted] = useState(() => typeof document !== "undefined");

  // Form fields
  const [firstName, setFirstName] = useState("");
  const [lastName, setLastName] = useState("");
  const [email, setEmail] = useState("");
  const [password, setPassword] = useState("");

  // UI state
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [successMsg, setSuccessMsg] = useState<string | null>(null);

  // Reset state when modal opens or mode changes
  useEffect(() => {
    const timer = window.setTimeout(() => {
      setError(null);
      setSuccessMsg(null);
      setFirstName("");
      setLastName("");
      setEmail("");
      setPassword("");
    }, 0);
    return () => window.clearTimeout(timer);
  }, [mode, isOpen]);

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    setError(null);
    setSuccessMsg(null);
    setLoading(true);

    try {
      if (mode === "register") {
        const res = await registerUser(firstName, lastName, email, password);
        if (res.success) {
          setSuccessMsg(res.message);
        } else {
          setError(res.error);
        }
      } else if (mode === "login") {
        const res = await loginUser(email, password);
        if (res.success) {
          if (res.message) {
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
      ? "Giriş Yap"
      : mode === "register"
      ? "Yeni Hesap Oluştur"
      : "Şifremi Unuttum";

  const submitLabel =
    mode === "login"
      ? "Giriş Yap"
      : mode === "register"
      ? "Kayıt Ol"
      : "Sıfırlama Bağlantısı Gönder";

  const labelClass = "block fl-mono text-[10px] uppercase tracking-[0.16em] text-[var(--ink-30)] mb-2";

  return createPortal(
    <AnimatePresence>
      {isOpen && (
        <div className="fixed inset-0 z-[100] flex items-center justify-center p-4">
          {/* Backdrop */}
          <motion.div
            initial={{ opacity: 0 }}
            animate={{ opacity: 1 }}
            exit={{ opacity: 0 }}
            onClick={onClose}
            className="absolute inset-0"
            style={{ background: "rgba(5,4,3,0.78)", backdropFilter: "blur(6px)" }}
          />

          {/* Modal */}
          <motion.div
            initial={{ opacity: 0, scale: 0.96, y: 12 }}
            animate={{ opacity: 1, scale: 1, y: 0 }}
            exit={{ opacity: 0, scale: 0.96, y: 12 }}
            transition={{ duration: 0.5, ease: [0.16, 1, 0.3, 1] }}
            className="relative w-full max-w-md rounded-[5px] p-9 overflow-hidden"
            style={{
              background: "var(--bg-raised)",
              border: "1px solid var(--border-strong)",
            }}
          >
            {/* Close */}
            <button
              onClick={onClose}
              aria-label="Kapat"
              className="absolute top-5 right-5 flex items-center justify-center w-9 h-9 rounded-[3px] border border-[var(--border-strong)] text-[var(--ink-30)] transition-colors hover:border-[var(--brass)] hover:text-[var(--brass)]"
            >
              <X className="w-4 h-4" />
            </button>

            {/* Header */}
            <div className="mb-8">
              <p className="fl-kicker mb-3">EVRE · KİMLİK DOĞRULAMA</p>
              <h2 className="fl-serif text-[40px] leading-[1.05] text-[var(--paper)]">{title}</h2>
              <p className="fl-sans text-[14px] text-[var(--ink-30)] mt-3">
                FiltreLAB tarafından onaylanmış premium seçimler.
              </p>
            </div>

            {/* Feedback messages */}
            {error && (
              <div className="mb-5 px-4 py-3 rounded-[3px] border border-[var(--verdict-caution)] fl-sans text-[13px] text-[var(--verdict-caution)]">
                {error}
              </div>
            )}
            {successMsg && (
              <div className="mb-5 px-4 py-3 rounded-[3px] border border-[var(--verdict-buy)] fl-sans text-[13px] text-[var(--verdict-buy)]">
                {successMsg}
              </div>
            )}

            {/* Form */}
            <form className="space-y-5" onSubmit={handleSubmit}>
              {mode === "register" && (
                <div className="grid grid-cols-2 gap-3">
                  <div>
                    <label className={labelClass}>Ad</label>
                    <input
                      type="text"
                      placeholder="Jane"
                      value={firstName}
                      onChange={(e) => setFirstName(e.target.value)}
                      required
                      className="fl-input"
                    />
                  </div>
                  <div>
                    <label className={labelClass}>Soyad</label>
                    <input
                      type="text"
                      placeholder="Doe"
                      value={lastName}
                      onChange={(e) => setLastName(e.target.value)}
                      required
                      className="fl-input"
                    />
                  </div>
                </div>
              )}

              <div>
                <label className={labelClass}>E-Posta</label>
                <input
                  type="email"
                  placeholder="ornek@mail.com"
                  value={email}
                  onChange={(e) => setEmail(e.target.value)}
                  required
                  className="fl-input"
                />
              </div>

              {mode !== "forgot" && (
                <div>
                  <label className={labelClass}>Şifre</label>
                  <input
                    type="password"
                    placeholder="••••••••"
                    value={password}
                    onChange={(e) => setPassword(e.target.value)}
                    required
                    minLength={6}
                    className="fl-input"
                  />
                </div>
              )}

              {mode === "login" && (
                <div className="text-right">
                  <button
                    type="button"
                    onClick={() => setMode("forgot")}
                    className="fl-mono text-[11px] uppercase tracking-[0.1em] text-[var(--ink-30)] transition-colors hover:text-[var(--brass)]"
                  >
                    Şifremi unuttum
                  </button>
                </div>
              )}

              <button type="submit" disabled={loading} className="fl-btn fl-btn-primary w-full">
                {loading ? "Lütfen bekleyin..." : submitLabel}
              </button>
            </form>

            {/* Toggle Login / Register / Back */}
            <div className="mt-6 text-center">
              {mode === "forgot" ? (
                <button
                  onClick={() => setMode("login")}
                  className="fl-sans text-[13px] text-[var(--ink-30)] transition-colors hover:text-[var(--paper)]"
                >
                  ← Giriş ekranına dön
                </button>
              ) : (
                <button
                  onClick={() => setMode(mode === "login" ? "register" : "login")}
                  className="fl-sans text-[13px] text-[var(--ink-30)] transition-colors hover:text-[var(--paper)]"
                >
                  {mode === "login" ? "Hesabınız yok mu? " : "Zaten hesabınız var mı? "}
                  <span className="text-[var(--brass)]">
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
