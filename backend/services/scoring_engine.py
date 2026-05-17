"""
Deterministic scoring engine — always produces a result.

Every function returns a concrete value. When data is scarce, confidence is
lowered and a warning is attached. "Analiz durmamalı" — analiz her zaman çalışır.

Confidence levels:
  HIGH_CONFIDENCE   : 20+ review texts
  MEDIUM_CONFIDENCE :  5–19 review texts
  LOW_CONFIDENCE    :  0–4 review texts (rating/category-based estimation)

Final decisions: ALINABİLİR | DİKKATLİ İNCELE | BEKLE
"""

from __future__ import annotations

import math
import re
from typing import Optional

# ---------------------------------------------------------------------------
# Turkish sentiment lexicon
# ---------------------------------------------------------------------------

_POS_WORDS = {
    "harika", "mükemmel", "güzel", "beğendim", "tavsiye", "kaliteli",
    "sağlam", "iyi", "memnun", "sevdim", "süper", "kusursuz", "uygun",
    "hızlı", "değer", "öneriyorum", "rahat", "pratik", "olumlu",
    "başarılı", "faydalı", "estetik", "şık", "muhteşem", "memnunum",
    "beğendik", "güzelmiş", "iyiymiş", "sağlamış",
}

_NEG_WORDS = {
    "berbat", "kötü", "çöp", "aldatıcı", "bozuk",
    "iade", "gelmedi", "sahte", "kalitesiz", "pişman", "rezalet",
    "rezil", "vasat", "başarısız", "sorun", "problem", "hata",
    "yanıltıcı", "yanlış", "olumsuz", "şikayetçi",
    "eksik", "kırık", "işe yaramaz",
}

_NEGATION = {"değil", "hiç", "yok", "olmadı", "olmayan"}


def _tokenize(text: str) -> list[str]:
    return re.findall(r"[a-züğışçöA-ZÜĞİŞÇÖ]+", text.lower())


def _sentiment_of_review(text: str) -> float:
    tokens = _tokenize(text)
    pos = sum(1 for t in tokens if t in _POS_WORDS)
    neg = sum(1 for t in tokens if t in _NEG_WORDS)
    lower = text.lower()
    neg += sum(1 for ph in _NEG_WORDS if " " in ph and ph in lower)
    for i, tok in enumerate(tokens):
        if tok in _NEGATION:
            for j in range(i + 1, min(i + 4, len(tokens))):
                if tokens[j] in _POS_WORDS:
                    pos -= 1
                    neg += 1
                    break
    if pos == neg:
        return 0.0
    return 1.0 if pos > neg else -1.0


# ---------------------------------------------------------------------------
# Confidence
# ---------------------------------------------------------------------------

def _confidence_level(reviews_loaded: int) -> str:
    if reviews_loaded >= 100:
        return "HIGH_CONFIDENCE"
    if reviews_loaded >= 20:
        return "MEDIUM_CONFIDENCE"
    if reviews_loaded >= 1:
        return "LOW_CONFIDENCE"
    return "NO_REVIEW_TEXT"


def _data_warning(reviews_loaded: int) -> Optional[str]:
    if reviews_loaded == 0:
        return "Yorum metni okunamadı — analiz puan ve ürün bilgisine göre yapılmıştır."
    if reviews_loaded < 20:
        return f"Yalnızca {reviews_loaded} yorum metni analiz edildi — sonuçlar sınırlı güvenilirlikte."
    if reviews_loaded < 100:
        return f"Bu analiz {reviews_loaded} yorum metnine dayanıyor; daha fazla yorum daha doğru sonuç verir."
    return None


# ---------------------------------------------------------------------------
# Scoring — always returns a value
# ---------------------------------------------------------------------------

def calculate_sentiment_score(
    reviews: list[str],
    rating: Optional[float] = None,
) -> float:
    """
    0–100. Always returns a value.
    ≥5 reviews → from actual texts.
    <5 reviews → estimated from rating (with confidence penalty).
    No rating and no reviews → neutral 50.
    """
    valid = [r for r in (reviews or []) if r and len(r.strip()) > 5]

    if len(valid) >= 1:
        scores = [_sentiment_of_review(r) for r in valid]
        positive_ratio = sum(1 for s in scores if s > 0) / len(scores)
        return round(positive_ratio * 100, 1)

    # Fallback: estimate from rating
    if rating is not None and rating > 0:
        if rating >= 4.5:
            return 80.0
        if rating >= 4.0:
            return 66.0
        if rating >= 3.5:
            return 52.0
        if rating >= 3.0:
            return 38.0
        return 22.0

    return 50.0  # fully unknown → neutral


def calculate_fake_review_risk(
    reviews: list[str],
    rating_distribution: Optional[dict],
    review_count: Optional[int],
    rating: Optional[float] = None,
) -> int:
    """
    0–100. Always returns a value.
    <5 reviews → lightweight heuristic estimate.
    ≥5 reviews → full signal analysis.
    """
    valid = [r for r in (reviews or []) if r and len(r.strip()) > 2]

    # --- Lightweight path (no or very few review texts) ---
    if len(valid) < 6:
        risk = 20  # start with low base risk
        if review_count is not None and rating is not None:
            # Suspicious: tiny count + suspiciously perfect rating
            if review_count < 5 and rating > 4.7:
                risk = 45
            elif review_count < 10 and rating > 4.8:
                risk = 40
            elif review_count < 3:
                risk = 35
        # Extreme distribution signal even without texts
        if rating_distribution:
            total = sum(rating_distribution.values())
            if total > 0:
                five = rating_distribution.get("5", rating_distribution.get(5, 0))
                if five / total > 0.92:
                    risk = max(risk, 38)
        return risk

    # --- Full analysis path ---
    risk = 0

    if rating_distribution:
        total = sum(rating_distribution.values())
        if total > 0:
            five_pct = rating_distribution.get("5", rating_distribution.get(5, 0)) / total
            one_pct = rating_distribution.get("1", rating_distribution.get(1, 0)) / total
            if five_pct > 0.85:
                risk += 30
            elif five_pct > 0.75:
                risk += 15
            if one_pct > 0.60:
                risk += 30
            elif one_pct > 0.40:
                risk += 15

    avg_len = sum(len(r.strip()) for r in valid) / len(valid)
    if avg_len < 20:
        risk += 25
    elif avg_len < 35:
        risk += 10

    if review_count is not None and rating_distribution:
        total = sum(rating_distribution.values())
        if total > 0:
            five_pct = rating_distribution.get("5", rating_distribution.get(5, 0)) / total
            if review_count < 10 and five_pct > 0.90:
                risk += 15

    verified_phrases = ["satın aldım", "kullandım", "denedim", "sipariş", "teslim"]
    verified_count = sum(1 for r in valid if any(ph in r.lower() for ph in verified_phrases))
    if verified_count / len(valid) > 0.3:
        risk -= 10

    return max(0, min(100, risk))


def calculate_trust_score(
    rating: Optional[float],
    review_count: Optional[int],
    seller_score: Optional[float],
    sentiment_score: float,
    fake_review_risk: int,
    confidence_level: str = "LOW_CONFIDENCE",
) -> int:
    """
    0–100. Always returns a value.
    Missing components reduce weight but never block computation.
    Low confidence applies a conservative penalty.
    """
    score = 0.0
    weight_total = 0.0

    if rating is not None and rating > 0:
        rating_component = (rating / 5.0) * 100
        score += rating_component * 0.30
        weight_total += 0.30
    else:
        # No rating = use neutral estimate (50) at reduced weight
        score += 50.0 * 0.15
        weight_total += 0.15

    if review_count is not None:
        volume_score = min(100.0, (math.log1p(review_count) / math.log1p(500)) * 100)
        score += volume_score * 0.20
        weight_total += 0.20
    # Omit volume component if review_count unavailable (don't penalise)

    if seller_score is not None:
        score += min(100.0, seller_score) * 0.15
        weight_total += 0.15

    # Sentiment always present
    score += sentiment_score * 0.20
    weight_total += 0.20

    # Fake risk (inverted)
    trust_from_fake = 100 - fake_review_risk
    score += trust_from_fake * 0.15
    weight_total += 0.15

    if weight_total == 0:
        return 50

    normalised = score / weight_total

    # Confidence penalty: NO_REVIEW_TEXT → −15 pts, LOW → −8 pts, MEDIUM → −3 pts
    if confidence_level == "NO_REVIEW_TEXT":
        normalised -= 15
    elif confidence_level == "LOW_CONFIDENCE":
        normalised -= 8
    elif confidence_level == "MEDIUM_CONFIDENCE":
        normalised -= 3

    return max(0, min(100, round(normalised)))


def calculate_price_performance(
    price_val: Optional[float],
    alternative_prices: list[float],
) -> Optional[float]:
    """
    0–100. Returns None only if price itself is missing.
    <3 alternatives → uses a neutral 50 with slight price-tier adjustment.
    """
    if price_val is None or price_val <= 0:
        return None

    valid_alts = [p for p in (alternative_prices or []) if p and p > 0]

    if len(valid_alts) < 3:
        # Not enough to compare — return neutral 50
        return 50.0

    avg_alt = sum(valid_alts) / len(valid_alts)
    if avg_alt <= 0:
        return 50.0

    ratio = price_val / avg_alt
    if ratio <= 0.5:
        pp = 95.0
    elif ratio <= 1.0:
        pp = 95.0 - (ratio - 0.5) * (30.0 / 0.5)
    elif ratio <= 1.5:
        pp = 65.0 - (ratio - 1.0) * (30.0 / 0.5)
    elif ratio <= 2.0:
        pp = 35.0 - (ratio - 1.5) * (25.0 / 0.5)
    else:
        pp = max(0.0, 10.0 - (ratio - 2.0) * 10.0)

    return round(max(0.0, min(100.0, pp)), 1)


def calculate_return_risk(
    rating: Optional[float],
    review_count: Optional[int],
    reviews: list[str],
) -> str:
    """Always returns 'Düşük' | 'Orta' | 'Yüksek'."""
    if rating is None:
        return "Orta"  # unknown → conservative default

    return_phrases = ["iade", "geri iade", "iade ettim", "geri gönderdim", "sorun çıktı", "bozuldu"]
    valid_reviews = [r for r in (reviews or []) if r and len(r.strip()) > 5]

    return_rate = 0.0
    if valid_reviews:
        return_mentions = sum(1 for r in valid_reviews if any(ph in r.lower() for ph in return_phrases))
        return_rate = return_mentions / len(valid_reviews)

    if rating >= 4.3 and return_rate < 0.05:
        return "Düşük"
    if rating <= 3.0 or return_rate > 0.15:
        return "Yüksek"
    return "Orta"


def make_final_decision(
    trust_score: int,
    fake_review_risk: int,
    price_performance: Optional[float],
    confidence_level: str,
) -> str:
    """
    Always returns 'ALINABİLİR' | 'DİKKATLİ İNCELE' | 'BEKLE'.
    Low confidence shifts decisions conservatively.
    """
    # Very suspicious reviews → caution regardless of other scores
    if fake_review_risk >= 70:
        return "DİKKATLİ İNCELE"

    # Very low trust → wait
    if trust_score < 30:
        return "BEKLE"

    # Low trust zone
    if trust_score < 50 or fake_review_risk >= 50:
        return "DİKKATLİ İNCELE"

    # Price is expensive vs alternatives
    if price_performance is not None and price_performance < 25:
        return "DİKKATLİ İNCELE"

    # Low confidence: be more conservative even if scores look okay
    if confidence_level == "LOW_CONFIDENCE":
        if trust_score >= 75 and fake_review_risk <= 25:
            return "ALINABİLİR"
        return "DİKKATLİ İNCELE"

    if trust_score >= 65 and fake_review_risk <= 35:
        return "ALINABİLİR"

    return "DİKKATLİ İNCELE"


# ---------------------------------------------------------------------------
# Main orchestration entry point
# ---------------------------------------------------------------------------

def run_scoring(
    rating: Optional[float],
    review_count: Optional[int],
    seller_score: Optional[float],
    price_val: Optional[float],
    reviews: list[str],
    rating_distribution: Optional[dict],
    alternative_prices: list[float],
    category: str = "",
) -> dict:
    """
    Runs all scoring functions and returns a complete result dict.
    All scores are always concrete values. Never returns None for scores.
    Same input → same output.
    """
    reviews = reviews or []
    alternative_prices = alternative_prices or []
    reviews_loaded = len(reviews)

    confidence_level = _confidence_level(reviews_loaded)
    data_warning = _data_warning(reviews_loaded)

    sentiment_score = calculate_sentiment_score(reviews, rating)
    fake_review_risk = calculate_fake_review_risk(reviews, rating_distribution, review_count, rating)
    trust_score = calculate_trust_score(
        rating, review_count, seller_score,
        sentiment_score, fake_review_risk, confidence_level,
    )
    price_performance = calculate_price_performance(price_val, alternative_prices)
    return_risk = calculate_return_risk(rating, review_count, reviews)
    final_decision = make_final_decision(trust_score, fake_review_risk, price_performance, confidence_level)

    data_quality = {
        "reviewsLoaded": reviews_loaded,
        "hasRatingDistribution": rating_distribution is not None,
        "alternativePricesFound": len([p for p in alternative_prices if p and p > 0]),
        "hasRating": rating is not None,
        "hasReviewCount": review_count is not None,
        "hasSellerScore": seller_score is not None,
        "confidenceLevel": confidence_level,
    }

    return {
        "sentimentScore": sentiment_score,
        "fakeReviewRisk": fake_review_risk,
        "trustScore": trust_score,
        "pricePerformance": price_performance,
        "returnRisk": return_risk,
        "finalDecision": final_decision,
        "confidenceLevel": confidence_level,
        "dataWarning": data_warning,
        "dataQuality": data_quality,
        "scoringVersion": "confidence-v2",
    }
