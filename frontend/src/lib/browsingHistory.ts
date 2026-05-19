"use client";

/**
 * SYSTEM 2 — gezinme geçmişi takibi (localStorage tabanlı).
 *
 * Kullanıcının analiz ettiği ürünleri kaydeder; aynı ürüne tekrar bakılırsa
 * viewCount artırılır. Shopping Psychology motoru bu geçmişi kullanır.
 *
 * Tüm fonksiyonlar localStorage hatalarına karşı korumalıdır (try/catch) —
 * asla exception fırlatmaz, site çökmez.
 */

const KEY = "filtre_browsing_history";
const MAX_ITEMS = 30;

export type BrowsingItem = {
  category?: string;
  brand?: string;
  price?: string | null;
  productName?: string;
  productUrl?: string;
  trustScore?: number | null;
  viewCount: number;
  ts: number;
};

/** Kayıtlı gezinme geçmişini döndürür (hata olursa boş dizi). */
export function getBrowsingHistory(): BrowsingItem[] {
  try {
    const raw = localStorage.getItem(KEY);
    if (!raw) return [];
    const parsed = JSON.parse(raw);
    return Array.isArray(parsed) ? parsed : [];
  } catch {
    return [];
  }
}

/**
 * Bir ürünü geçmişe ekler (varsa viewCount artırır) ve güncel geçmişi döndürür.
 * Çağıran taraf dönen diziyi doğrudan kullanabilir.
 */
export function recordBrowsing(
  item: Omit<BrowsingItem, "viewCount" | "ts">
): BrowsingItem[] {
  try {
    const history = getBrowsingHistory();
    const key = (item.productUrl || item.productName || "").toLowerCase();
    const existing = key
      ? history.find(
          (h) => (h.productUrl || h.productName || "").toLowerCase() === key
        )
      : undefined;

    if (existing) {
      existing.viewCount += 1;
      existing.ts = Date.now();
    } else {
      history.push({ ...item, viewCount: 1, ts: Date.now() });
    }

    // En yeni MAX_ITEMS kaydı sakla
    const trimmed = history.sort((a, b) => b.ts - a.ts).slice(0, MAX_ITEMS);
    localStorage.setItem(KEY, JSON.stringify(trimmed));
    return trimmed;
  } catch {
    return getBrowsingHistory();
  }
}
