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
    <main className="min-h-screen bg-[#f8f7fa] dark:bg-[#05050a] text-[#191847] dark:text-white p-6 md:p-12">
      <div className="mx-auto max-w-6xl pt-8">
        <Link href="/" className="inline-flex items-center text-gray-500 hover:text-[#191847] dark:text-gray-400 dark:hover:text-white transition-colors mb-8">
          <ArrowLeft className="w-5 h-5 mr-2" />
          Ana Sayfaya Dön
        </Link>
        <h1 className="text-4xl font-black mb-3">Favori Listesi</h1>
        <p className="text-gray-700 dark:text-gray-300 mb-8">Beğendiğin ürünleri buradan tekrar inceleyebilirsin.</p>

        {message && <div className="rounded-3xl border border-black/10 dark:border-white/10 bg-white/80 dark:bg-white/5 p-6 text-gray-700 dark:text-gray-300">{message}</div>}

        <div className="grid grid-cols-1 md:grid-cols-2 gap-5">
          {items.map((item) => (
            <div key={item.id} className="rounded-3xl border border-black/10 dark:border-white/10 bg-white/80 dark:bg-white/5 p-5 flex gap-4">
              <div className="relative h-24 w-24 flex-shrink-0 overflow-hidden rounded-2xl bg-white">
                {isValidImageUrl(item.image) ? (
                  <Image src={item.image} alt={item.productName} fill className="object-contain p-2" sizes="96px" />
                ) : (
                  <div className="h-full w-full bg-white/10" />
                )}
              </div>
              <div className="min-w-0 flex-1">
                <h2 className="font-bold leading-tight mb-2">{item.productName}</h2>
                <p className="text-sm text-[var(--neon-blue)] font-bold">{item.price || "Fiyat yok"}</p>
                <div className="mt-3 flex flex-wrap gap-4 text-sm">
                  <Link href={item.productUrl || "#"} target="_blank" className="inline-flex items-center gap-2 text-[var(--neon-blue)] hover:opacity-80">
                    <ExternalLink className="h-4 w-4" />
                    Ürüne Git
                  </Link>
                  <button onClick={() => removeItem(item.id)} className="inline-flex items-center gap-2 text-red-600 dark:text-red-300 hover:text-red-700 dark:hover:text-red-200">
                    <Trash2 className="h-4 w-4" />
                    Sil
                  </button>
                </div>
              </div>
            </div>
          ))}
        </div>
      </div>
    </main>
  );
}
