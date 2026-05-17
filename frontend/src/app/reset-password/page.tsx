"use client";

import { Suspense, useState } from "react";
import { useSearchParams } from "next/navigation";
import { KeyRound, Sparkles } from "lucide-react";
import { resetPassword } from "@/lib/apiClient";

function ResetPasswordForm() {
  const searchParams = useSearchParams();
  const token = searchParams.get("token") || "";
  const [newPassword, setNewPassword] = useState("");
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [successMsg, setSuccessMsg] = useState<string | null>(null);

  const handleSubmit = async (event: React.FormEvent) => {
    event.preventDefault();
    setError(null);
    setSuccessMsg(null);

    if (!token) {
      setError("Sıfırlama bağlantısı geçersiz.");
      return;
    }

    setLoading(true);
    try {
      const res = await resetPassword(token, newPassword);
      if (res.success) {
        setSuccessMsg(res.message);
        setNewPassword("");
      } else {
        setError(res.error);
      }
    } finally {
      setLoading(false);
    }
  };

  return (
    <main className="min-h-screen flex items-center justify-center p-4 bg-[var(--soft-white)]">
      <div className="relative w-full max-w-md liquid-glass-heavy gloss-overlay rounded-[2.5rem] p-8 shadow-[0_25px_60px_rgba(0,0,0,0.08)] overflow-hidden border border-white">
        <div className="absolute inset-0 bg-gradient-to-tr from-pink-500/5 via-white/50 to-blue-500/5 pointer-events-none" />

        <div className="text-center mb-8 relative z-10">
          <div className="mx-auto w-14 h-14 bg-white/80 backdrop-blur-md rounded-[1rem] flex items-center justify-center mb-4 border border-white shadow-[inset_0_2px_5px_rgba(255,255,255,1),0_4px_10px_rgba(0,0,0,0.06)]">
            <KeyRound className="w-6 h-6 text-gray-700 drop-shadow-sm" />
          </div>
          <h1 className="text-2xl font-semibold tracking-tight text-gray-900 drop-shadow-sm">
            Yeni Şifre Belirle
          </h1>
          <p className="text-gray-500 font-light text-[17px] tracking-wide mt-2">
            FiltreLAB hesabınız için yeni parolanızı girin.
          </p>
        </div>

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

        <form className="space-y-4 relative z-10" onSubmit={handleSubmit}>
          <div>
            <label className="block text-[11px] font-semibold text-gray-500 mb-1.5 ml-1 tracking-widest uppercase">
              Yeni Şifre
            </label>
            <input
              type="password"
              placeholder="••••••••"
              value={newPassword}
              onChange={(e) => setNewPassword(e.target.value)}
              required
              minLength={6}
              className="w-full bg-white/60 border border-white rounded-xl px-4 py-3.5 text-gray-900 placeholder:text-gray-400 focus:outline-none focus:border-white focus:bg-white transition-all shadow-[inset_0_1px_3px_rgba(0,0,0,0.02)] font-light text-[15px]"
            />
          </div>

          <button
            type="submit"
            disabled={loading}
            className="w-full relative group overflow-hidden rounded-xl mt-6 border border-white shadow-[0_4px_15px_rgba(0,0,0,0.05),inset_0_2px_4px_rgba(255,255,255,1)] transition-all active:scale-[0.98] bg-white/80 hover:bg-white backdrop-blur-md disabled:opacity-60 disabled:cursor-not-allowed"
          >
            <div className="absolute inset-0 bg-gradient-to-r from-transparent via-white to-transparent opacity-0 group-hover:opacity-100 -translate-x-full group-hover:translate-x-full transition-all duration-700 ease-out" />
            <div className="relative px-4 py-3.5 flex items-center justify-center font-medium text-gray-800 text-[15px]">
              {loading ? "Lütfen bekleyin..." : "Şifreyi Güncelle"}
              {!loading && <Sparkles className="w-4 h-4 ml-2 opacity-80" />}
            </div>
          </button>
        </form>
      </div>
    </main>
  );
}

export default function ResetPasswordPage() {
  return (
    <Suspense fallback={null}>
      <ResetPasswordForm />
    </Suspense>
  );
}
