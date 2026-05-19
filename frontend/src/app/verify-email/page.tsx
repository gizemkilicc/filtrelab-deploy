"use client";

import { Suspense, useEffect, useState } from "react";
import { useSearchParams, useRouter } from "next/navigation";
import { CheckCircle, XCircle, Loader2, Mail } from "lucide-react";
import { verifyEmailToken } from "@/lib/apiClient";

function VerifyEmailContent() {
  const searchParams = useSearchParams();
  const router = useRouter();
  const token = searchParams.get("token") || "";

  const [status, setStatus] = useState<"loading" | "success" | "error" | "no-token">(
    token ? "loading" : "no-token"
  );
  const [message, setMessage] = useState("");

  useEffect(() => {
    if (!token) return;

    verifyEmailToken(token).then((res) => {
      if (res.success) {
        setStatus("success");
        setMessage(res.message || "E-posta adresiniz başarıyla doğrulandı.");
      } else {
        setStatus("error");
        setMessage(res.error || "Doğrulama bağlantısı geçersiz veya süresi dolmuş.");
      }
    });
  }, [token]);

  return (
    <main className="min-h-screen flex items-center justify-center p-4 bg-[var(--soft-white)]">
      <div className="relative w-full max-w-md liquid-glass-heavy gloss-overlay rounded-[2.5rem] p-8 shadow-[0_25px_60px_rgba(0,0,0,0.08)] overflow-hidden border border-white">
        <div className="absolute inset-0 bg-gradient-to-tr from-pink-500/5 via-white/50 to-blue-500/5 pointer-events-none" />

        <div className="text-center relative z-10">
          {status === "loading" && (
            <>
              <div className="mx-auto w-14 h-14 bg-white/80 backdrop-blur-md rounded-[1rem] flex items-center justify-center mb-4 border border-white shadow-[inset_0_2px_5px_rgba(255,255,255,1),0_4px_10px_rgba(0,0,0,0.06)]">
                <Loader2 className="w-6 h-6 text-gray-500 animate-spin" />
              </div>
              <h1 className="text-2xl font-semibold tracking-tight text-gray-900 mb-2">
                Doğrulanıyor...
              </h1>
              <p className="text-gray-500 font-light text-[15px]">
                E-posta adresiniz doğrulanıyor, lütfen bekleyin.
              </p>
            </>
          )}

          {status === "success" && (
            <>
              <div className="mx-auto w-14 h-14 bg-green-50 backdrop-blur-md rounded-[1rem] flex items-center justify-center mb-4 border border-green-100 shadow-[inset_0_2px_5px_rgba(255,255,255,1),0_4px_10px_rgba(0,0,0,0.06)]">
                <CheckCircle className="w-6 h-6 text-green-600" />
              </div>
              <h1 className="text-2xl font-semibold tracking-tight text-gray-900 mb-2">
                E-posta Doğrulandı
              </h1>
              <p className="text-gray-600 font-light text-[15px] mb-6">{message}</p>
              <button
                onClick={() => router.push("/")}
                className="w-full relative group overflow-hidden rounded-xl border border-white shadow-[0_4px_15px_rgba(0,0,0,0.05),inset_0_2px_4px_rgba(255,255,255,1)] transition-all active:scale-[0.98] bg-white/80 hover:bg-white backdrop-blur-md px-4 py-3.5 font-medium text-gray-800 text-[15px]"
              >
                Giriş Yap
              </button>
            </>
          )}

          {status === "error" && (
            <>
              <div className="mx-auto w-14 h-14 bg-red-50 backdrop-blur-md rounded-[1rem] flex items-center justify-center mb-4 border border-red-100 shadow-[inset_0_2px_5px_rgba(255,255,255,1),0_4px_10px_rgba(0,0,0,0.06)]">
                <XCircle className="w-6 h-6 text-red-500" />
              </div>
              <h1 className="text-2xl font-semibold tracking-tight text-gray-900 mb-2">
                Doğrulama Başarısız
              </h1>
              <p className="text-gray-600 font-light text-[15px] mb-6">{message}</p>
              <button
                onClick={() => router.push("/")}
                className="w-full relative group overflow-hidden rounded-xl border border-white shadow-[0_4px_15px_rgba(0,0,0,0.05),inset_0_2px_4px_rgba(255,255,255,1)] transition-all active:scale-[0.98] bg-white/80 hover:bg-white backdrop-blur-md px-4 py-3.5 font-medium text-gray-800 text-[15px]"
              >
                Ana Sayfaya Dön
              </button>
            </>
          )}

          {status === "no-token" && (
            <>
              <div className="mx-auto w-14 h-14 bg-white/80 backdrop-blur-md rounded-[1rem] flex items-center justify-center mb-4 border border-white shadow-[inset_0_2px_5px_rgba(255,255,255,1),0_4px_10px_rgba(0,0,0,0.06)]">
                <Mail className="w-6 h-6 text-gray-500" />
              </div>
              <h1 className="text-2xl font-semibold tracking-tight text-gray-900 mb-2">
                Geçersiz Bağlantı
              </h1>
              <p className="text-gray-500 font-light text-[15px] mb-6">
                Doğrulama bağlantısı bulunamadı. Lütfen e-postanızdaki bağlantıyı kullanın.
              </p>
              <button
                onClick={() => router.push("/")}
                className="w-full relative group overflow-hidden rounded-xl border border-white shadow-[0_4px_15px_rgba(0,0,0,0.05),inset_0_2px_4px_rgba(255,255,255,1)] transition-all active:scale-[0.98] bg-white/80 hover:bg-white backdrop-blur-md px-4 py-3.5 font-medium text-gray-800 text-[15px]"
              >
                Ana Sayfaya Dön
              </button>
            </>
          )}
        </div>
      </div>
    </main>
  );
}

export default function VerifyEmailPage() {
  return (
    <Suspense fallback={null}>
      <VerifyEmailContent />
    </Suspense>
  );
}
