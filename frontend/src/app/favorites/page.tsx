"use client";

import { useEffect, useState } from "react";
import Image from "next/image";
import Link from "next/link";
import { ArrowLeft, ExternalLink, Trash2 } from "lucide-react";
import { deleteFavorite, getFavorites, type SavedProduct } from "@/lib/apiClient";

function isValidImageUrl(url: unknown): url is string {
  return typeof url === "string" && (url.startsWith("http://") || url.startsWith("https://"));
}

export default function FavoritesPage() {
  const [items, setItems] = useState<SavedProduct[]>([]);
  const [message, setMessage] = useState("Yükleniyor...");

  const load = async () => {
    const response = await getFavorites();
    if (response.success) {
      setItems(response.data.items);
      setMessage(response.data.items.length ? "" : "Henüz favori ürününüz yok.");
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
    const response = await deleteFavorite(id);
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

        <p className="fl-kicker mb-3">EVRE · FAVORİLER</p>
        <h1 className="fl-serif text-[56px] leading-[1.02] text-[var(--paper)]">Favori Listesi</h1>
        <p className="fl-sans mt-3 text-[15px] text-[var(--ink-30)]">
          Beğendiğin ürünleri buradan tekrar inceleyebilirsin.
        </p>

        {message && (
          <div className="mt-10 fl-card p-6 fl-sans text-[14px] text-[var(--ink-30)]">{message}</div>
        )}

        {items.length > 0 && (
          <div className="mt-10 border-b border-[var(--ink-70)]">
            {items.map((item) => (
              <div
                key={item.id}
                className="fl-row flex items-center gap-5 px-2 py-5"
              >
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
                  <p className="fl-mono mt-1.5 text-[13px] text-[var(--brass)]">
                    {item.price || "FİYAT YOK"}
                  </p>
                </div>

                <div className="flex flex-shrink-0 items-center gap-2">
                  <Link
                    href={item.productUrl || "#"}
                    target="_blank"
                    className="flex items-center gap-2 rounded-[3px] border border-[var(--border-strong)] px-3 py-2 fl-mono text-[11px] uppercase tracking-[0.1em] text-[var(--ink-10)] transition-colors hover:border-[var(--brass)] hover:text-[var(--brass)]"
                  >
                    <ExternalLink className="h-3.5 w-3.5" />
                    Ürüne Git
                  </Link>
                  <button
                    onClick={() => removeItem(item.id)}
                    aria-label="Sil"
                    className="flex items-center justify-center rounded-[3px] border border-[var(--border-strong)] p-2 text-[var(--ink-30)] transition-colors hover:border-[var(--verdict-caution)] hover:text-[var(--verdict-caution)]"
                  >
                    <Trash2 className="h-4 w-4" />
                  </button>
                </div>
              </div>
            ))}
          </div>
        )}
      </div>
    </main>
  );
}
