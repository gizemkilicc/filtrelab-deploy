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
  className?: string;
}

// ─── Platform config ─────────────────────────────────────────────────────────

const PLATFORM_CONFIG: Record<string, { name: string }> = {
  trendyol: { name: "Trendyol" },
  amazon_tr: { name: "Amazon TR" },
  hepsiburada: { name: "Hepsiburada" },
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
  const cfg = PLATFORM_CONFIG[platformKey] ?? { name: platformKey };
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

  const borderColor = isCheapest
    ? "var(--verdict-buy)"
    : isMostExpensive
    ? "var(--verdict-caution)"
    : "var(--ink-70)";

  // Platform badge — clickable when there's a product URL
  const badgeEl = (
    <span className="fl-mono text-[12px] uppercase tracking-[0.1em] text-[var(--paper)]">
      {cfg.name}
    </span>
  );
  const platformBadge = productUrl ? (
    <Link href={productUrl} target="_blank" rel="noopener noreferrer" className="transition-opacity hover:opacity-70">
      {badgeEl}
    </Link>
  ) : badgeEl;

  return (
    <div
      className="relative flex min-w-0 flex-1 flex-col gap-3 rounded-[4px] border p-4"
      style={{ borderColor, background: "var(--surface)" }}
    >
      {/* Header row: platform badge + status tags */}
      <div className="flex items-center justify-between gap-2">
        {platformBadge}
        <div className="flex flex-wrap justify-end gap-1.5">
          {isSource && (
            <span className="fl-mono text-[9px] uppercase tracking-[0.1em] text-[var(--ink-30)]">
              Şu an
            </span>
          )}
          {isCheapest && (
            <span
              className="flex items-center gap-1 fl-mono text-[9px] uppercase tracking-[0.1em]"
              style={{ color: "var(--verdict-buy)" }}
            >
              <TrendingDown className="h-3 w-3" /> En Ucuz
            </span>
          )}
          {isMostExpensive && (
            <span
              className="flex items-center gap-1 fl-mono text-[9px] uppercase tracking-[0.1em]"
              style={{ color: "var(--verdict-caution)" }}
            >
              <TrendingUp className="h-3 w-3" /> En Pahalı
            </span>
          )}
        </div>
      </div>

      {found ? (
        <>
          {/* Product image */}
          {isValidImage(productImage) && (
            <div className="relative mx-auto h-20 w-20 overflow-hidden border border-[var(--ink-70)] bg-[var(--bg-deep)]">
              <Image
                src={productImage}
                alt={productName || ""}
                fill
                className="object-contain p-1"
                sizes="80px"
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
                className="fl-sans text-[12px] leading-snug text-[var(--ink-30)] line-clamp-2 hover:text-[var(--brass)]"
              >
                {productName}
              </Link>
            ) : (
              <p className="fl-sans text-[12px] leading-snug text-[var(--ink-30)] line-clamp-2">
                {productName}
              </p>
            )
          )}

          {/* Price row */}
          <div className="flex flex-col gap-1">
            <span className="fl-serif text-[28px] leading-tight text-[var(--brass)]">
              {priceDisplay ?? "—"}
            </span>
            {priceDiffLabel && (
              <span
                className="fl-mono text-[11px]"
                style={{ color: priceDiffPositive ? "var(--verdict-buy)" : NEGATIVE_RED }}
              >
                {priceDiffLabel}
              </span>
            )}
          </div>

          {/* Confidence indicator + Ürüne Git button */}
          <div className="mt-auto flex flex-col items-stretch gap-2">
            {!isSource && match?.confidence && match.confidence !== "not_found" && (
              <div className="flex shrink-0 items-center gap-1">
                {match.confidence === "high" ? (
                  <CheckCircle2 className="h-3.5 w-3.5" style={{ color: "var(--verdict-buy)" }} />
                ) : (
                  <AlertTriangle className="h-3.5 w-3.5" style={{ color: "var(--verdict-caution)" }} />
                )}
                <span className="fl-mono text-[10px] uppercase tracking-[0.08em] text-[var(--ink-30)]">
                  {CONFIDENCE_LABEL[match.confidence]}
                </span>
              </div>
            )}
            {productUrl && (
              <Link
                href={productUrl}
                target="_blank"
                rel="noopener noreferrer"
                className="flex w-full items-center justify-center gap-1.5 rounded-[3px] border border-[var(--border-strong)] px-3 py-2 fl-mono text-[10px] uppercase tracking-[0.1em] text-[var(--ink-10)] transition-colors hover:border-[var(--brass)] hover:text-[var(--brass)]"
              >
                <ExternalLink className="h-3 w-3" />
                Ürüne Git
              </Link>
            )}
          </div>

          {/* Variant warning (soft match) or generic low-confidence note */}
          {!isSource && match?.variant_warning && (
            <p className="mt-1 flex items-start gap-1 fl-sans text-[11px]" style={{ color: "var(--verdict-caution)" }}>
              <AlertTriangle className="mt-0.5 h-3 w-3 flex-shrink-0" />
              <span>Bu tam varyant satılmıyor: {match.variant_warning}. Benzer ürün gösteriliyor.</span>
            </p>
          )}
          {!isSource && match?.confidence === "low" && !match?.variant_warning && (
            <p className="mt-1 flex items-center gap-1 fl-sans text-[11px]" style={{ color: "var(--verdict-caution)" }}>
              <AlertTriangle className="h-3 w-3 flex-shrink-0" />
              Ürün farklı olabilir — kontrol edin
            </p>
          )}
        </>
      ) : (
        <div className="flex flex-col items-center justify-center gap-2 py-4 text-center">
          <XCircle className="h-8 w-8 text-[var(--ink-50)]" />
          <p className="fl-sans text-[13px] text-[var(--ink-30)]">
            {match?.not_found_reason ?? "Bu platformda bulunamadı"}
          </p>
        </div>
      )}
    </div>
  );
}

const NEGATIVE_RED = "#9c5b4d";

// ─── Main component ───────────────────────────────────────────────────────────

export function CrossPlatformPrices({
  sourcePlatform,
  productName,
  brand,
  priceStr,
  sourceUrl,
  sourceImage,
  className,
}: CrossPlatformPricesProps) {
  const [data, setData] = useState<CrossPlatformResult | null>(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);

  const sourcePriceFromProp = parsePriceFloat(priceStr || "");
  const normalizedSource = normalizePlatform(sourcePlatform);

  // After data loads, prefer backend source_price (already a float) when prop
  // couldn't be parsed (e.g. "118.999 TL" dot-only format before the fix).
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

  return (
    <div className={className ?? "fl-divider mt-10 pt-8"}>
      {/* Header */}
      <p className="fl-kicker mb-3">EVRE · PLATFORM FİYAT KARŞILAŞTIRMASI</p>

      {/* Summary — bidirectional */}
      {data && data.total_platforms_with_price >= 2 && data.price_difference_max != null && data.price_difference_max > 1 && (
        <div className="mb-5">
          {data.is_source_cheapest ? (
            /* User is on the cheapest platform */
            <div
              className="flex items-start gap-2 rounded-[3px] border px-4 py-3 fl-sans text-[13px]"
              style={{ borderColor: "var(--verdict-buy)", color: "var(--verdict-buy)" }}
            >
              <CheckCircle2 className="mt-0.5 h-4 w-4 shrink-0" />
              <span>
                <strong>İyi haber!</strong> Şu an baktığınız platform en ucuzu.
                {data.savings_amount != null && data.savings_amount > 0 && (
                  <>
                    {" "}Diğer platformlardan{" "}
                    <strong>
                      {formatPrice(data.savings_amount)}
                      {data.savings_percentage != null && ` (%${data.savings_percentage.toFixed(1)})`}
                    </strong>{" "}daha ucuz.
                  </>
                )}
              </span>
            </div>
          ) : (
            /* User is paying more — show cheapest alternative */
            <div
              className="flex items-start gap-2 rounded-[3px] border px-4 py-3 fl-sans text-[13px]"
              style={{ borderColor: "var(--verdict-caution)", color: "var(--verdict-caution)" }}
            >
              <AlertTriangle className="mt-0.5 h-4 w-4 shrink-0" />
              <span>
                <strong>Dikkat!</strong>{" "}
                {cheapestCfg && (
                  cheapestUrl ? (
                    <Link
                      href={cheapestUrl}
                      target="_blank"
                      rel="noopener noreferrer"
                      className="font-bold underline underline-offset-2 hover:opacity-80"
                    >
                      {cheapestCfg.name} <ExternalLink className="mb-0.5 inline h-3 w-3" />
                    </Link>
                  ) : (
                    <strong>{cheapestCfg.name}</strong>
                  )
                )}{" "}platformunda{" "}
                {data.savings_amount != null && (
                  <strong>
                    {formatPrice(Math.abs(data.savings_amount))}
                    {data.savings_percentage != null && ` (%${Math.abs(data.savings_percentage).toFixed(1)})`}
                  </strong>
                )}{" "}daha ucuz!
              </span>
            </div>
          )}

          {/* Price ranking row */}
          {data.cheapest_platform && data.most_expensive_platform && data.cheapest_platform !== data.most_expensive_platform && (
            <div className="mt-2 flex flex-wrap gap-x-5 gap-y-1 px-1 fl-mono text-[10px] uppercase tracking-[0.08em] text-[var(--ink-30)]">
              <span>
                En ucuz:{" "}
                <strong style={{ color: "var(--verdict-buy)" }}>
                  {PLATFORM_CONFIG[data.cheapest_platform]?.name ?? data.cheapest_platform}
                </strong>
                {data.cheapest_price != null && <> — {formatPrice(data.cheapest_price)}</>}
              </span>
              <span>
                En pahalı:{" "}
                <strong style={{ color: "var(--verdict-caution)" }}>
                  {PLATFORM_CONFIG[data.most_expensive_platform]?.name ?? data.most_expensive_platform}
                </strong>
                {data.most_expensive_price != null && <> — {formatPrice(data.most_expensive_price)}</>}
              </span>
            </div>
          )}
        </div>
      )}
      {data && data.total_platforms_with_price >= 2 && data.price_difference_max !== null && data.price_difference_max <= 1 && (
        <p className="mb-5 fl-sans text-[13px] text-[var(--ink-30)]">
          Platformlar arasında anlamlı fiyat farkı yok.
        </p>
      )}

      {/* Loading */}
      {loading && (
        <div className="flex items-center gap-3 py-8 text-[var(--ink-30)]">
          <Loader2 className="h-4 w-4 animate-spin text-[var(--brass)]" />
          <span className="fl-mono text-[11px] uppercase tracking-[0.1em]">
            Diğer platformlarda aranıyor… (30–60 sn sürebilir)
          </span>
        </div>
      )}

      {/* Error — only when no data to show */}
      {!loading && error && !data && (
        <p className="py-4 fl-sans text-[13px]" style={{ color: NEGATIVE_RED }}>{error}</p>
      )}

      {/* Platform cards */}
      {!loading && data && (
        <div className="overflow-visible pb-2">
          <div className="flex flex-nowrap gap-3">
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
        </div>
      )}
    </div>
  );
}
