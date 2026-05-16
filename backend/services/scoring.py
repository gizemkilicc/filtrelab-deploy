def calculate_scores(
    rating: float,
    review_count: int,
    question_count: int,
    seller_score: float,
    price_val: float,
    alternatives: list,
    category: str,
):
    rating = float(rating or 0)
    review_count = int(review_count or 0)
    question_count = int(question_count or 0)
    seller_score = float(seller_score or 0)

    # ── 1. Trust Score ──────────────────────────────────────────────────────
    rating_contribution = (rating / 5.0) * 70 if rating > 0 else 0

    if review_count >= 10000:
        review_contribution = 20
    elif review_count >= 1000:
        review_contribution = 15
    elif review_count >= 100:
        review_contribution = 10
    else:
        review_contribution = 3

    seller_contribution = 10 if seller_score >= 8.5 else 0

    trust_score = min(100, int(rating_contribution + review_contribution + seller_contribution))

    # ── 2. Fake Review Risk ─────────────────────────────────────────────────
    fake_risk = 50

    if review_count >= 10000:
        fake_risk -= 25
    elif review_count >= 1000:
        fake_risk -= 15

    if rating >= 4.9 and review_count < 100:
        fake_risk += 25
    elif 4.0 <= rating <= 4.7:
        fake_risk -= 10

    if seller_score >= 8.5:
        fake_risk -= 10

    fake_review_risk = max(5, min(100, fake_risk))

    # ── 3. Price Performance ────────────────────────────────────────────────
    alt_prices = []
    if alternatives:
        for alt in alternatives:
            try:
                p_str = (
                    str(alt.get("price", ""))
                    .replace(" TL", "")
                    .replace("₺", "")
                    .replace(".", "")
                    .replace(",", ".")
                    .strip()
                )
                if p_str:
                    alt_prices.append(float(p_str))
            except Exception:
                continue

    if alt_prices and price_val and price_val > 0:
        avg_alt = sum(alt_prices) / len(alt_prices)
        ratio = avg_alt / price_val
        price_performance = round(min(9.8, max(3.0, ratio * 7.0)), 1)
    elif rating >= 4.5:
        price_performance = 8.5
    elif rating >= 4.0:
        price_performance = 7.0
    else:
        price_performance = 5.0

    # ── 4. Sentiment Score ──────────────────────────────────────────────────
    sentiment_score = round(rating * 2, 1) if rating else 0.0

    # ── 5. Return Risk ──────────────────────────────────────────────────────
    if rating >= 4.4 and review_count >= 500:
        return_risk = "Düşük"
    elif rating >= 4.0:
        return_risk = "Orta"
    elif rating > 0:
        return_risk = "Yüksek"
    else:
        return_risk = "Orta"  # unknown rating — don't punish unfairly

    # ── 6. Final Decision ───────────────────────────────────────────────────
    alinabilir = (
        rating >= 4.4
        and review_count >= 500
        and trust_score >= 70
        and fake_review_risk <= 45
        and return_risk == "Düşük"
    )
    onerilmez = rating > 0 and (
        rating < 3.8
        or trust_score < 45
        or fake_review_risk >= 70
        or return_risk == "Yüksek"
    )

    if alinabilir:
        final_decision = "ALINABİLİR"
    elif onerilmez:
        final_decision = "ÖNERİLMEZ"
    else:
        final_decision = "BEKLE"

    print(
        f"[SCORING] rating={rating} reviewCount={review_count} sellerScore={seller_score} "
        f"→ trustScore={trust_score} fakeRisk={fake_review_risk} "
        f"returnRisk={return_risk} decision={final_decision}"
    )

    return {
        "trustScore": trust_score,
        "fakeReviewRisk": fake_review_risk,
        "sentimentScore": sentiment_score,
        "pricePerformance": price_performance,
        "returnRisk": return_risk,
        "finalDecision": final_decision,
    }
