"use client";

import { useEffect, useState } from "react";
import Image from "next/image";
import Link from "next/link";
import { ExternalLink, AlertTriangle, CheckCircle2, XCircle, Loader2, TrendingDown, TrendingUp } from "lucide-react";

const API_URL = process.env.NEXT_PUBLIC_API_URL || "http://127.0.0.1:8000";

// ─── Types ───────────────────────────────────────────────────────────────────

interface PlatformMatch {
  platform: string;
  found: boolean;
  product_name: string | null;
  product_url: string | null;
  image_url: string | null;
  price: number | null;
  price_str: string | null;
  confidence: "high" | "medium" | "low" | "not_found";
  match_score: number | null;
  not_found_reason: string | null;
  variant_warning: string | null;
}

interface CrossPlatformResult {
  source_platform: string;
  source_product_name: string;
  source_price: number;
  matches: PlatformMatch[];
  // legacy
  cheapest_platform: string | null;
  price_difference_max: number | null;
  // new
  cheapest_price: number | null;
  most_expensive_platform: string | null;
  most_expensive_price: number | null;
  source_rank: number | null;
  total_platforms_with_price: number;
  is_source_cheapest: boolean;
  is_source_most_expensive: boolean;
  savings_amount: number | null;
  savings_percentage: number | null;
  comparison_message: string | null;
}

interface CrossPlatformPricesProps {
  sourcePlatform: string;
  productName: string;
  brand: string;
  priceStr: string;
  sourceUrl?: string | null;
  sourceImage?: string | null;
}

// ─── Platform config ─────────────────────────────────────────────────────────

const PLATFORM_CONFIG: Record<string, { name: string; accentColor: string; badgeClass: string }> = {
  trendyol: {
    name: "Trendyol",
    accentColor: "#F27A1A",
    badgeClass: "bg-orange-100 dark:bg-orange-900/30 text-orange-700 dark:text-orange-300 border-orange-200 dark:border-orange-700/40",
  },
  amazon_tr: {
    name: "Amazon TR",
    accentColor: "#FF9900",
    badgeClass: "bg-yellow-100 dark:bg-yellow-900/30 text-yellow-700 dark:text-yellow-300 border-yellow-200 dark:border-yellow-700/40",
  },
  hepsiburada: {
    name: "Hepsiburada",
    accentColor: "#FF6000",
    badgeClass: "bg-red-100 dark:bg-red-900/30 text-red-700 dark:text-red-300 border-red-200 dark:border-red-700/40",
  },
};

const CONFIDENCE_LABEL: Record<string, string> = {
  high: "Yüksek güven",
  medium: "Orta güven",
  low: "Düşük güven",
  not_found: "",
};

// ─── Helpers ─────────────────────────────────────────────────────────────────

function normalizePlatform(name: string): string {
  const n = (name || "").toLowerCase().trim();
  if (n.includes("trendyol")) return "trendyol";
  if (n.includes("hepsiburada")) return "hepsiburada";
  if (n.includes("amazon")) return "amazon_tr";
  return n;
}

function parsePriceFloat(priceStr: string): number {
  const cleaned = (priceStr || "").replace(/[TL₺\s]/g, "").trim();
  if (!cleaned) return 0;

  if (cleaned.includes(",") && cleaned.includes(".")) {
    // Turkish: "118.999,00" — dot=thousands, comma=decimal
    return parseFloat(cleaned.replace(/\./g, "").replace(",", ".")) || 0;
  }
  if (cleaned.includes(",")) {
    const afterComma = cleaned.slice(cleaned.lastIndexOf(",") + 1);
    if (afterComma.length === 3) {
      // Thousands comma: "118,999" → 118999
      return parseFloat(cleaned.replace(",", "")) || 0;
    }
    // Decimal comma: "118,90" → 118.9
    return parseFloat(cleaned.replace(",", ".")) || 0;
  }
  if (cleaned.includes(".")) {
    const afterDot = cleaned.slice(cleaned.lastIndexOf(".") + 1);
    if (afterDot.length === 3) {
      // Thousands dot: "118.999" → 118999
      return parseFloat(cleaned.replace(".", "")) || 0;
    }
    // Decimal dot: "118.90" → 118.9
    return parseFloat(cleaned) || 0;
  }
  return parseFloat(cleaned) || 0;
}

function formatPrice(val: number): string {
  return val.toLocaleString("tr-TR", { minimumFractionDigits: 0, maximumFractionDigits: 0 }) + " TL";
}

function isValidImage(url: unknown): url is string {
  return typeof url === "string" && (url.startsWith("http://") || url.startsWith("https://"));
}

// ─── PlatformCard ─────────────────────────────────────────────────────────────

function PlatformCard({
  platformKey,
  isSource,
  sourcePrice,
  sourceName,
  sourceUrl,
  sourceImage,
  match,
  cheapestPlatform,
  mostExpensivePlatform,
}: {
  platformKey: string;
  isSource: boolean;
  sourcePrice: number;
  sourceName: string;
  sourceUrl?: string | null;
  sourceImage?: string | null;
  match?: PlatformMatch;
  cheapestPlatform: string | null;
  mostExpensivePlatform: string | null;
}) {
  const cfg = PLATFORM_CONFIG[platformKey] ?? {
    name: platformKey,
    accentColor: "#888",
    badgeClass: "bg-gray-100 text-gray-700 border-gray-200",
  };
  const isCheapest = cheapestPlatform === platformKey;
  const isMostExpensive = mostExpensivePlatform === platformKey && mostExpensivePlatform !== cheapestPlatform;

  // Unified product data: source card uses props, target card uses match
  const productName  = isSource ? sourceName       : (match?.product_name ?? null);
  const productUrl   = isSource ? (sourceUrl ?? null) : (match?.product_url ?? null);
  const productImage = isSource ? (sourceImage ?? null) : (match?.image_url ?? null);
  const priceDisplay = isSource
    ? formatPrice(sourcePrice)
    : (match?.price_str || (match?.price ? formatPrice(match.price) : null));
  const found = isSource || (match?.found ?? false);

  // Price diff relative to source (target cards only)
  let priceDiffLabel: string | null = null;
  let priceDiffPositive = false;
  if (!isSource && match?.found && match.price && sourcePrice > 0) {
    const diff = match.price - sourcePrice;
    if (Math.abs(diff) > 1) {
      priceDiffPositive = diff < 0;
      priceDiffLabel = (diff < 0 ? "−" : "+") + formatPrice(Math.abs(diff));
    }
  }

  // Platform badge — clickable when there's a product URL
  const badgeEl = (
    <span className={`text-xs font-bold px-2.5 py-1 rounded-full border ${cfg.badgeClass}`}>
      {cfg.name}
    </span>
  );
  const platformBadge = productUrl ? (
    <Link href={productUrl} target="_blank" rel="noopener noreferrer" className="hover:opacity-80 transition-opacity">
      {badgeEl}
    </Link>
  ) : badgeEl;

  return (
    <div
      className={`relative rounded-2xl border p-4 flex flex-col gap-3 transition-all ${
        isCheapest
          ? "border-green-400/50 dark:border-green-500/40 bg-green-50/60 dark:bg-green-950/20 shadow-sm"
          : isMostExpensive
          ? "border-red-400/50 dark:border-red-500/40 bg-red-50/40 dark:bg-red-950/10"
          : "border-black/10 dark:border-white/10 bg-white/60 dark:bg-white/5"
      }`}
    >
      {/* Header row: platform badge + status tags */}
      <div className="flex items-center justify-between gap-2">
        {platformBadge}
        <div className="flex gap-1.5 flex-wrap justify-end">
          {isSource && (
            <span className="text-xs px-2 py-0.5 rounded-full bg-blue-100 dark:bg-blue-900/30 text-blue-700 dark:text-blue-300 border border-blue-200 dark:border-blue-700/40 font-medium whitespace-nowrap">
              Şu an
            </span>
          )}
          {isCheapest && (
            <span className="text-xs px-2 py-0.5 rounded-full bg-green-100 dark:bg-green-900/30 text-green-700 dark:text-green-300 border border-green-200 dark:border-green-700/40 font-bold flex items-center gap-1 whitespace-nowrap">
              <TrendingDown className="w-3 h-3" /> En Ucuz
            </span>
          )}
          {isMostExpensive && (
            <span className="text-xs px-2 py-0.5 rounded-full bg-red-100 dark:bg-red-900/30 text-red-700 dark:text-red-300 border border-red-200 dark:border-red-700/40 font-bold flex items-center gap-1 whitespace-nowrap">
              <TrendingUp className="w-3 h-3" /> En Pahalı
            </span>
          )}
        </div>
      </div>

      {found ? (
        <>
          {/* Product image */}
          {isValidImage(productImage) && (
            <div className="relative w-full h-20 rounded-lg overflow-hidden bg-white dark:bg-neutral-800">
              <Image
                src={productImage}
                alt={productName || ""}
                fill
                className="object-contain p-1"
                sizes="200px"
              />
            </div>
          )}

          {/* Product name — clickable when URL available */}
          {productName && (
            productUrl ? (
              <Link
                href={productUrl}
                target="_blank"
                rel="noopener noreferrer"
                className="text-xs text-gray-600 dark:text-gray-400 line-clamp-2 leading-snug hover:underline"
              >
                {productName}
              </Link>
            ) : (
              <p className="text-xs text-gray-600 dark:text-gray-400 line-clamp-2 leading-snug">
                {productName}
              </p>
            )
          )}

          {/* Price row */}
          <div className="flex items-end gap-2">
            <span className="text-xl font-black" style={{ color: cfg.accentColor }}>
              {priceDisplay ?? "—"}
            </span>
            {priceDiffLabel && (
              <span
                className={`text-xs font-semibold mb-0.5 ${
                  priceDiffPositive ? "text-green-600 dark:text-green-400" : "text-red-600 dark:text-red-400"
                }`}
              >
                {priceDiffLabel}
              </span>
            )}
          </div>

          {/* Confidence indicator + Ürüne Git button */}
          <div className="flex items-center justify-between mt-auto gap-2">
            {!isSource && match?.confidence && match.confidence !== "not_found" && (
              <div className="flex items-center gap-1 shrink-0">
                {match.confidence === "high" ? (
                  <CheckCircle2 className="w-3.5 h-3.5 text-green-500" />
                ) : (
                  <AlertTriangle className="w-3.5 h-3.5 text-yellow-500" />
                )}
                <span className="text-xs text-gray-500 dark:text-gray-400">
                  {CONFIDENCE_LABEL[match.confidence]}
                </span>
              </div>
            )}
            {productUrl && (
              <Link
                href={productUrl}
                target="_blank"
                rel="noopener noreferrer"
                className="ml-auto flex items-center gap-1 text-xs font-bold px-3 py-1.5 rounded-lg border transition-colors hover:opacity-80"
                style={{
                  color: cfg.accentColor,
                  borderColor: cfg.accentColor + "44",
                  backgroundColor: cfg.accentColor + "12",
                }}
              >
                <ExternalLink className="w-3 h-3" />
                Ürüne Git
              </Link>
            )}
          </div>

          {/* Variant warning (soft match) or generic low-confidence note */}
          {!isSource && match?.variant_warning && (
            <p className="text-xs text-yellow-600 dark:text-yellow-400 flex items-start gap-1 mt-1">
              <AlertTriangle className="w-3 h-3 flex-shrink-0 mt-0.5" />
              <span>Bu tam varyant satılmıyor: {match.variant_warning}. Benzer ürün gösteriliyor.</span>
            </p>
          )}
          {!isSource && match?.confidence === "low" && !match?.variant_warning && (
            <p className="text-xs text-yellow-600 dark:text-yellow-400 flex items-center gap-1 mt-1">
              <AlertTriangle className="w-3 h-3 flex-shrink-0" />
              Ürün farklı olabilir — kontrol edin
            </p>
          )}
        </>
      ) : (
        <div className="flex flex-col items-center justify-center gap-2 py-4 text-center">
          <XCircle className="w-8 h-8 text-gray-300 dark:text-gray-600" />
          <p className="text-sm text-gray-500 dark:text-gray-400">
            {match?.not_found_reason ?? "Bu platformda bulunamadı"}
          </p>
        </div>
      )}
    </div>
  );
}

// ─── Main component ───────────────────────────────────────────────────────────

export function CrossPlatformPrices({
  sourcePlatform,
  productName,
  brand,
  priceStr,
  sourceUrl,
  sourceImage,
}: CrossPlatformPricesProps) {
  const [data, setData] = useState<CrossPlatformResult | null>(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);

  const sourcePriceFromProp = parsePriceFloat(priceStr || "");
  const normalizedSource = normalizePlatform(sourcePlatform);

  // After data loads, prefer backend source_price (already a float) when prop
  // couldn't be parsed (e.g. "118.999 TL" dot-only format before the fix).
  // data?.source_price is the float the backend received from the frontend, so
  // it's only better when it was passed correctly.  Fall back to prop.
  const sourcePrice = (data?.source_price && data.source_price > 0)
    ? data.source_price
    : sourcePriceFromProp;

  useEffect(() => {
    if (!productName || !normalizedSource) {
      setLoading(false);
      return;
    }

    setLoading(true);
    setError(null);

    // Distinguish real timeout aborts from cleanup aborts.
    // Cleanup-caused aborts must NOT show an error.
    const isTimeoutAbort = { value: false };
    const controller = new AbortController();
    const timeout = setTimeout(() => {
      isTimeoutAbort.value = true;
      controller.abort();
    }, 90000);

    const price = parsePriceFloat(priceStr || "");

    (async () => {
      try {
        const res = await fetch(`${API_URL}/cross-platform-compare`, {
          method: "POST",
          headers: { "Content-Type": "application/json" },
          body: JSON.stringify({
            source_platform: normalizedSource,
            product_name: productName,
            brand: brand || "",
            price,
          }),
          signal: controller.signal,
        });
        clearTimeout(timeout);
        if (!res.ok) throw new Error(`HTTP ${res.status}`);
        const json = await res.json();
        if (json.error) throw new Error(json.error);
        setError(null);
        setData(json as CrossPlatformResult);
      } catch (e: unknown) {
        clearTimeout(timeout);
        if ((e as Error)?.name === "AbortError") {
          if (isTimeoutAbort.value) {
            setError("Karşılaştırma zaman aşımına uğradı (90s).");
          }
          // Cleanup abort → silently stop
        } else {
          setError("Platform karşılaştırması yüklenemedi.");
        }
      } finally {
        setLoading(false);
      }
    })();

    return () => {
      clearTimeout(timeout);
      controller.abort();
    };
  }, [normalizedSource, productName, brand, priceStr]); // eslint-disable-line react-hooks/exhaustive-deps

  // Source first, then the two target platforms
  const allPlatforms = ["trendyol", "hepsiburada", "amazon_tr"];
  const orderedPlatforms = [
    normalizedSource,
    ...allPlatforms.filter((p) => p !== normalizedSource),
  ];

  const matchByPlatform = Object.fromEntries(
    (data?.matches ?? []).map((m) => [m.platform, m])
  );

  // Summary line helpers
  const cheapestCfg   = data?.cheapest_platform ? PLATFORM_CONFIG[data.cheapest_platform] : null;
  const cheapestMatch = data?.cheapest_platform ? matchByPlatform[data.cheapest_platform] : null;
  const cheapestUrl   = data?.cheapest_platform === normalizedSource
    ? (sourceUrl ?? null)
    : (cheapestMatch?.product_url ?? null);

  const mostExpensiveCfg   = data?.most_expensive_platform ? PLATFORM_CONFIG[data.most_expensive_platform] : null;
  const mostExpensiveMatch = data?.most_expensive_platform ? matchByPlatform[data.most_expensive_platform] : null;
  const mostExpensiveUrl   = data?.most_expensive_platform === normalizedSource
    ? (sourceUrl ?? null)
    : (mostExpensiveMatch?.product_url ?? null);

  return (
    <div className="mt-10 pt-8 border-t border-white/10">
      {/* Header */}
      <h3 className="text-xl font-bold mb-2 flex items-center gap-2">
        <TrendingDown className="text-green-400" />
        Platform Fiyat Karşılaştırması
      </h3>

      {/* Summary — bidirectional */}
      {data && data.total_platforms_with_price >= 2 && data.price_difference_max != null && data.price_difference_max > 1 && (
        <div className="mb-5">
          {data.is_source_cheapest ? (
            /* User is on the cheapest platform */
            <div className="flex items-start gap-2 rounded-xl border border-green-300 dark:border-green-700/50 bg-green-50 dark:bg-green-950/25 px-4 py-3 text-sm text-green-800 dark:text-green-200">
              <CheckCircle2 className="w-4 h-4 mt-0.5 shrink-0 text-green-600 dark:text-green-400" />
              <span>
                <strong>İyi haber!</strong> Şu an baktığınız platform en ucuzu.
                {data.savings_amount != null && data.savings_amount > 0 && (
                  <>
                    {" "}Diğer platformlardan{" "}
                    <strong className="text-green-700 dark:text-green-300">
                      {formatPrice(data.savings_amount)}
                      {data.savings_percentage != null && ` (%${data.savings_percentage.toFixed(1)})`}
                    </strong>{" "}daha ucuz.
                  </>
                )}
              </span>
            </div>
          ) : (
            /* User is paying more — show cheapest alternative */
            <div className="flex items-start gap-2 rounded-xl border border-amber-300 dark:border-amber-700/50 bg-amber-50 dark:bg-amber-950/25 px-4 py-3 text-sm text-amber-900 dark:text-amber-200">
              <AlertTriangle className="w-4 h-4 mt-0.5 shrink-0 text-amber-600 dark:text-amber-400" />
              <span>
                <strong>Dikkat!</strong>{" "}
                {cheapestCfg && (
                  cheapestUrl ? (
                    <Link
                      href={cheapestUrl}
                      target="_blank"
                      rel="noopener noreferrer"
                      className="font-bold underline underline-offset-2 hover:opacity-80"
                      style={{ color: cheapestCfg.accentColor }}
                    >
                      {cheapestCfg.name} <ExternalLink className="inline w-3 h-3 mb-0.5" />
                    </Link>
                  ) : (
                    <strong style={{ color: cheapestCfg.accentColor }}>{cheapestCfg.name}</strong>
                  )
                )}{" "}platformunda{" "}
                {data.savings_amount != null && (
                  <strong className="text-red-600 dark:text-red-400">
                    {formatPrice(Math.abs(data.savings_amount))}
                    {data.savings_percentage != null && ` (%${Math.abs(data.savings_percentage).toFixed(1)})`}
                  </strong>
                )}{" "}daha ucuz!
              </span>
            </div>
          )}

          {/* Price ranking row */}
          {data.cheapest_platform && data.most_expensive_platform && data.cheapest_platform !== data.most_expensive_platform && (
            <div className="flex flex-wrap gap-x-5 gap-y-1 mt-2 px-1 text-xs text-gray-500 dark:text-gray-400">
              <span>
                En ucuz:{" "}
                <strong className="text-green-700 dark:text-green-400">
                  {PLATFORM_CONFIG[data.cheapest_platform]?.name ?? data.cheapest_platform}
                </strong>
                {data.cheapest_price != null && <> — {formatPrice(data.cheapest_price)}</>}
              </span>
              <span>
                En pahalı:{" "}
                <strong className="text-red-700 dark:text-red-400">
                  {PLATFORM_CONFIG[data.most_expensive_platform]?.name ?? data.most_expensive_platform}
                </strong>
                {data.most_expensive_price != null && <> — {formatPrice(data.most_expensive_price)}</>}
              </span>
            </div>
          )}
        </div>
      )}
      {data && data.total_platforms_with_price >= 2 && data.price_difference_max !== null && data.price_difference_max <= 1 && (
        <p className="text-sm mb-5 text-gray-500 dark:text-gray-400">
          Platformlar arasında anlamlı fiyat farkı yok.
        </p>
      )}

      {/* Loading */}
      {loading && (
        <div className="flex items-center gap-3 py-8 text-gray-500 dark:text-gray-400">
          <Loader2 className="w-5 h-5 animate-spin" />
          <span className="text-sm">Diğer platformlarda aranıyor… (30–60 sn sürebilir)</span>
        </div>
      )}

      {/* Error — only when no data to show */}
      {!loading && error && !data && (
        <p className="text-sm text-red-500 dark:text-red-400 py-4">{error}</p>
      )}

      {/* Platform cards */}
      {!loading && data && (
        <div className="grid grid-cols-1 sm:grid-cols-3 gap-4">
          {orderedPlatforms.map((platformKey) => {
            const isSource = platformKey === normalizedSource;
            return (
              <PlatformCard
                key={platformKey}
                platformKey={platformKey}
                isSource={isSource}
                sourcePrice={sourcePrice}
                sourceName={productName}
                sourceUrl={sourceUrl}
                sourceImage={sourceImage}
                match={matchByPlatform[platformKey]}
                cheapestPlatform={data.cheapest_platform}
                mostExpensivePlatform={data.most_expensive_platform ?? null}
              />
            );
          })}
        </div>
      )}
    </div>
  );
}
