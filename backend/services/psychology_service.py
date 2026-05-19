"""Shopping Psychology Engine (SYSTEM 2).

Kullanıcının gezinme/analiz geçmişinden alışveriş kişiliğini sezgisel olarak
çıkarır. Tamamen saf Python'dur: ağ/IO yapmaz, hızlıdır, deterministiktir ve
asla exception fırlatmaz — beklenmedik bir durumda güvenli varsayılan döner.

Girdi (history): her biri görüntülenen/analiz edilen bir ürünü temsil eden
sözlükler listesi. Beklenen alanlar (hepsi opsiyonel, eksik veriye toleranslı):
    category, brand, price, productName/name, productUrl/url,
    trustScore, viewCount

Çıktı:
    {
      shopping_personality,        # 6 kişilikten biri
      trust_sensitivity,           # 0-100
      impulsive_vs_analytical,     # 0=dürtüsel ... 100=analitik
      budget_behavior,             # etiket
      recommendation_strategy,     # öneri metni
      confidence_score             # 0-100
    }
"""

from collections import Counter
from typing import List, Optional

from .price_utils import parse_tr_price

# Olası alışveriş kişilikleri
_PERSONALITIES = (
    "Analytical Researcher",
    "Deal Hunter",
    "Premium Shopper",
    "Impulsive Buyer",
    "Trust-Focused Shopper",
    "Brand Loyalist",
)

# Kişiliğe göre öneri stratejisi metinleri
_STRATEGY = {
    "Analytical Researcher": "Detaylı karşılaştırma tabloları, uzun yorum "
        "analizleri ve teknik özellik kırılımları sun; aceleye getirme.",
    "Deal Hunter": "Fiyat düşüşü uyarıları, indirim rozetleri ve platformlar "
        "arası en ucuz fiyatı öne çıkar.",
    "Premium Shopper": "Üst segment ürünleri, marka güvenilirliğini ve kalite "
        "göstergelerini vurgula; fiyat ikincil planda kalsın.",
    "Impulsive Buyer": "Net ve hızlı bir karar (AL/BEKLE), öne çıkan tek bir "
        "alternatif ve sahte yorum uyarısıyla dürtüsel hatayı önle.",
    "Trust-Focused Shopper": "Güven skorunu, sahte yorum analizini ve satıcı "
        "puanını en görünür yere koy; şüpheli ürünlerde net uyar.",
    "Brand Loyalist": "Tercih edilen markanın diğer ürünlerini ve aynı "
        "markadan alternatifleri önceliklendir.",
}


# ── Güvenli yardımcılar ─────────────────────────────────────────────────────

def _to_float(value) -> Optional[float]:
    """Sayıya çevrilemeyen değerlerde None döndürür (asla hata vermez)."""
    if value is None:
        return None
    try:
        return float(value)
    except (TypeError, ValueError):
        return None


def _to_int(value, default: int = 1) -> int:
    try:
        return max(default, int(float(value)))
    except (TypeError, ValueError):
        return default


def _normalize_event(item) -> Optional[dict]:
    """Ham geçmiş öğesini standart sözlüğe çevirir; geçersizse None."""
    if not isinstance(item, dict):
        return None
    return {
        "category": str(item.get("category") or "").strip(),
        "brand": str(item.get("brand") or "").strip(),
        "price": parse_tr_price(item.get("price")),
        "name": str(item.get("productName") or item.get("name") or "").strip(),
        "url": str(item.get("productUrl") or item.get("url") or "").strip(),
        "trust": _to_float(item.get("trustScore")),
        "views": _to_int(item.get("viewCount"), default=1),
    }


def _empty_result() -> dict:
    """Veri yetersizken / hata durumunda dönen güvenli varsayılan."""
    return {
        "shopping_personality": "Analytical Researcher",
        "trust_sensitivity": 50,
        "impulsive_vs_analytical": 50,
        "budget_behavior": "Belirsiz",
        "recommendation_strategy": "Henüz yeterli gezinme verisi yok. Birkaç "
            "ürün analiz edildikçe kişiselleştirilmiş öneriler oluşturulur.",
        "confidence_score": 0,
    }


# ── Ana fonksiyon ───────────────────────────────────────────────────────────

def analyze_shopping_behavior(history: List) -> dict:
    """Gezinme geçmişinden alışveriş kişiliği profili çıkarır.

    Senkron ve saf-Python'dur; hızlıdır ve asla exception fırlatmaz.
    """
    try:
        events = [e for e in (_normalize_event(it) for it in (history or [])) if e]
        n = len(events)
        if n == 0:
            return _empty_result()

        # ── Sinyaller ──
        categories = Counter(e["category"] for e in events if e["category"])
        brands = Counter(e["brand"] for e in events if e["brand"])
        prices = [e["price"] for e in events if e["price"] and e["price"] > 0]
        trusts = [e["trust"] for e in events if e["trust"] is not None]

        # Tekrarlı ürün kontrolü (aynı ürüne birden çok bakış)
        keys = Counter(
            (e["url"] or e["name"]).lower()
            for e in events if (e["url"] or e["name"])
        )
        repeated_checks = sum(c - 1 for c in keys.values() if c > 1)
        # frontend açıkça viewCount sağladıysa onu da ekle
        repeated_checks += max(0, sum(e["views"] for e in events) - n)

        unique_categories = len(categories)
        brand_dominance = (brands.most_common(1)[0][1] / n) if brands else 0.0
        top_brand = brands.most_common(1)[0][0] if brands else ""

        avg_price = sum(prices) / len(prices) if prices else 0.0
        price_spread = (
            (max(prices) - min(prices)) / avg_price if avg_price > 0 else 0.0
        )
        avg_trust = sum(trusts) / len(trusts) if trusts else None

        # ── Kişilik skorlaması (her sinyal bir veya birkaç kişiliğe puan ekler) ──
        scores = {p: 0.0 for p in _PERSONALITIES}

        # Brand Loyalist — tek marka baskın
        if brand_dominance >= 0.6:
            scores["Brand Loyalist"] += 3.0
        elif brand_dominance >= 0.4:
            scores["Brand Loyalist"] += 1.5

        # Analytical Researcher — çok ürün + tekrar kontrol + kategori çeşitliliği
        if n >= 5:
            scores["Analytical Researcher"] += 1.5
        if repeated_checks >= 2:
            scores["Analytical Researcher"] += 2.0
        if unique_categories >= 3:
            scores["Analytical Researcher"] += 1.0

        # Impulsive Buyer — az ürün, tekrar yok, dar çeşitlilik
        if n <= 3 and repeated_checks == 0:
            scores["Impulsive Buyer"] += 2.5
        if unique_categories <= 1 and n <= 3:
            scores["Impulsive Buyer"] += 1.0

        # Deal Hunter — geniş fiyat aralığı taraması + çok ürün karşılaştırma
        if price_spread >= 0.8 and n >= 4:
            scores["Deal Hunter"] += 2.5
        if n >= 6:
            scores["Deal Hunter"] += 1.0

        # Premium Shopper — yüksek ve tutarlı fiyat bandı
        if prices and avg_price >= 1500 and price_spread < 0.5:
            high_share = sum(1 for p in prices if p >= avg_price) / len(prices)
            if high_share >= 0.5:
                scores["Premium Shopper"] += 2.5

        # Trust-Focused Shopper — yüksek güven skoruna yönelir / tekrar inceler
        if avg_trust is not None:
            if avg_trust >= 70:
                scores["Trust-Focused Shopper"] += 2.5
            elif avg_trust >= 55:
                scores["Trust-Focused Shopper"] += 1.0
            if repeated_checks >= 1:
                scores["Trust-Focused Shopper"] += 1.0

        # En yüksek skorlu kişilik
        personality, best_score = max(scores.items(), key=lambda kv: kv[1])
        if best_score <= 0:
            personality = "Analytical Researcher"

        # ── Türev metrikler ──
        # Güven hassasiyeti: tekrar inceleme + çeşitlilik + güven verisi
        trust_sensitivity = 35 + repeated_checks * 12 + unique_categories * 4
        if avg_trust is not None:
            trust_sensitivity += 15
        trust_sensitivity = max(0, min(100, round(trust_sensitivity)))

        # Dürtüsel ↔ analitik ekseni (0=dürtüsel, 100=analitik)
        analytical = 50 + repeated_checks * 12 + (n - 3) * 4 + unique_categories * 3
        impulsive_vs_analytical = max(0, min(100, round(analytical)))

        # Bütçe davranışı
        if not prices:
            budget_behavior = "Belirsiz"
        elif price_spread >= 0.8:
            budget_behavior = "Geniş Fiyat Aralığı Tarayıcı"
        elif avg_price >= 2000:
            budget_behavior = "Premium Eğilimli"
        elif avg_price <= 400:
            budget_behavior = "Bütçe Odaklı"
        else:
            budget_behavior = "Dengeli Harcama"

        # Güven skoru: kazanan kişiliğin baskınlığı + veri yeterliliği
        total_score = sum(scores.values()) or 1.0
        dominance = best_score / total_score if best_score > 0 else 0.0
        data_factor = min(1.0, n / 6.0)
        confidence_score = round(min(95, dominance * 70 + data_factor * 25))

        strategy = _STRATEGY.get(personality, _STRATEGY["Analytical Researcher"])
        if personality == "Brand Loyalist" and top_brand:
            strategy = f"Tercih edilen marka '{top_brand}' — " + strategy

        return {
            "shopping_personality": personality,
            "trust_sensitivity": trust_sensitivity,
            "impulsive_vs_analytical": impulsive_vs_analytical,
            "budget_behavior": budget_behavior,
            "recommendation_strategy": strategy,
            "confidence_score": confidence_score,
        }
    except Exception as e:
        print(f"[psychology] Beklenmeyen hata, fallback döndürülüyor: {e}")
        return _empty_result()
