"use client";

import { useEffect, useState } from "react";
import Link from "next/link";
import { ArrowLeft, Bot } from "lucide-react";
import { getRecommendations, type Recommendation } from "@/lib/apiClient";

export default function RecommendationsPage() {
  const [items, setItems] = useState<Recommendation[]>([]);
  const [message, setMessage] = useState("Yükleniyor...");

  useEffect(() => {
    const timer = window.setTimeout(() => {
      const load = async () => {
      const response = await getRecommendations();
      if (response.success) {
        setItems(response.data.recommendations);
        setMessage(response.data.message || (response.data.recommendations.length ? "" : "Henüz öneri oluşturmak için yeterli veri yok."));
      } else {
        setMessage(response.error);
      }
      };
      void load();
    }, 0);
    return () => window.clearTimeout(timer);
  }, []);

  return (
    <main className="min-h-screen bg-[#f8f7fa] dark:bg-[#05050a] text-[#191847] dark:text-white p-6 md:p-12">
      <div className="mx-auto max-w-5xl pt-8">
        <Link href="/" className="inline-flex items-center text-gray-500 hover:text-[#191847] dark:text-gray-400 dark:hover:text-white transition-colors mb-8">
          <ArrowLeft className="w-5 h-5 mr-2" />
          Ana Sayfaya Dön
        </Link>
        <h1 className="text-4xl font-black mb-3">Kişisel AI Önerileri</h1>
        <p className="text-gray-700 dark:text-gray-300 mb-8">Favorilerin, analiz geçmişin ve fiyat takiplerin üzerinden gerçek veriye dayalı öneriler.</p>

        {message && <div className="rounded-3xl border border-black/10 dark:border-white/10 bg-white/80 dark:bg-white/5 p-6 text-gray-700 dark:text-gray-300">{message}</div>}

        <div className="grid grid-cols-1 gap-5">
          {items.map((item, index) => (
            <div key={`${item.title}-${index}`} className="rounded-3xl border border-black/10 dark:border-white/10 bg-white/80 dark:bg-white/5 p-6">
              <div className="mb-3 inline-flex h-10 w-10 items-center justify-center rounded-2xl border border-emerald-400/20 bg-emerald-400/10">
                <Bot className="h-5 w-5 text-emerald-300" />
              </div>
              <h2 className="text-xl font-bold mb-2">{item.title}</h2>
              <p className="text-gray-700 dark:text-gray-300 leading-relaxed">{item.description}</p>
              {item.source?.productName && (
                <p className="mt-4 rounded-2xl border border-black/10 dark:border-white/10 bg-white/70 dark:bg-black/20 px-4 py-3 text-sm text-gray-500 dark:text-gray-400">
                  Kaynak ürün: <span className="text-[#191847] dark:text-white">{item.source.productName}</span>
                </p>
              )}
            </div>
          ))}
        </div>
      </div>
    </main>
  );
}
