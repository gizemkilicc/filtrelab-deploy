"use client";

import { useEffect, useState } from "react";
import Image from "next/image";
import Link from "next/link";
import { ArrowLeft, Trash2 } from "lucide-react";
import { deleteAnalysisHistory, getAnalysisHistory, type SavedProduct } from "@/lib/apiClient";

function isValidImageUrl(url: unknown): url is string {
  return typeof url === "string" && (url.startsWith("http://") || url.startsWith("https://"));
}

function verdictColor(decision: string | null | undefined): string {
  const d = (decision || "").toLocaleUpperCase("tr-TR");
  if (d.includes("ALINAB") || d.includes("ÖNER")) return "var(--verdict-buy)";
  if (d.includes("DİKKAT") || d.includes("KARARSIZ") || d.includes("ORTA")) return "var(--verdict-caution)";
  if (d.includes("ALMA") || d.includes("UZAK") || d.includes("BEKLE")) return "var(--verdict-wait)";
  return "var(--ink-30)";
}

export default function HistoryPage() {
  const [items, setItems] = useState<SavedProduct[]>([]);
  const [message, setMessage] = useState("Yükleniyor...");

  const load = async () => {
    const response = await getAnalysisHistory();
    if (response.success) {
      setItems(response.data.items);
      setMessage(response.data.items.length ? "" : "Henüz analiz geçmişiniz yok.");
    } else {
      setMessage(response.error);
    }
  };

  useEffect(() => {
    const timer = window.setTimeout(() => {
      void load();
    }, 0);
    return () => window.clearTimeout(timer);
  }, []);

  const removeItem = async (id: number) => {
    const response = await deleteAnalysisHistory(id);
    if (response.success) {
      setItems((current) => current.filter((item) => item.id !== id));
    } else {
      setMessage(response.error);
    }
  };

  return (
    <main className="fl-page px-6 py-14 md:px-12">
      <div className="mx-auto max-w-5xl">
        <Link href="/" className="fl-link mb-10 inline-flex items-center fl-mono text-[11px] uppercase tracking-[0.14em]">
          <ArrowLeft className="mr-2 h-4 w-4" />
          Ana Sayfaya Dön
        </Link>

        <p className="fl-kicker mb-3">EVRE · ANALİZ ARŞİVİ</p>
        <h1 className="fl-serif text-[56px] leading-[1.02] text-[var(--paper)]">Analiz Geçmişi</h1>
        <p className="fl-sans mt-3 text-[15px] text-[var(--ink-30)]">
          Daha önce analiz ettiğin ürünler burada saklanır.
        </p>

        {message && (
          <div className="mt-10 fl-card p-6 fl-sans text-[14px] text-[var(--ink-30)]">{message}</div>
        )}

        {items.length > 0 && (
          <div className="mt-10 border-b border-[var(--ink-70)]">
            {items.map((item) => (
              <div key={item.id} className="fl-row flex items-center gap-5 px-2 py-5">
                <div className="relative h-20 w-20 flex-shrink-0 overflow-hidden border border-[var(--ink-70)] bg-[var(--bg-deep)]">
                  {isValidImageUrl(item.image) ? (
                    <Image src={item.image} alt={item.productName} fill className="object-contain p-2" sizes="80px" />
                  ) : (
                    <div className="flex h-full w-full items-center justify-center fl-mono text-[9px] uppercase tracking-[0.1em] text-[var(--ink-50)]">
                      Görsel Yok
                    </div>
                  )}
                </div>

                <div className="min-w-0 flex-1">
                  <h2 className="fl-serif italic text-[21px] leading-snug text-[var(--paper)]">
                    {item.productName}
                  </h2>
                  <div className="mt-2 flex flex-wrap items-center gap-3">
                    <span className="fl-mono text-[13px] text-[var(--brass)]">
                      {item.price || "FİYAT YOK"}
                    </span>
                    <span
                      className="fl-pill"
                      style={{ color: verdictColor(item.finalDecision) }}
                    >
                      {item.finalDecision || "KARAR YOK"}
                    </span>
                    <span className="fl-mono text-[11px] uppercase tracking-[0.1em] text-[var(--ink-30)]">
                      Güven: {item.trustScore ?? "—"}
                    </span>
                  </div>
                </div>

                <button
                  onClick={() => removeItem(item.id)}
                  aria-label="Sil"
                  className="flex flex-shrink-0 items-center justify-center rounded-[3px] border border-[var(--border-strong)] p-2 text-[var(--ink-30)] transition-colors hover:border-[var(--verdict-caution)] hover:text-[var(--verdict-caution)]"
                >
                  <Trash2 className="h-4 w-4" />
                </button>
              </div>
            ))}
          </div>
        )}
      </div>
    </main>
  );
}
