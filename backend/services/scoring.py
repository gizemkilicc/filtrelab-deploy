SCORING_VERSION = "deterministic-v1"


def calculate_scores(
    rating: float,
    review_count: int | None,
    question_count: int | None,
    seller_score: float,
    price_val: float,
    alternatives: list,
    category: str,
):
    if not rating or not price_val:
        raise ValueError("Insufficient reliable scoring data.")

    rating = float(rating or 0)
    review_count_value = int(review_count or 0)
    question_count_value = int(question_count or 0)
    seller_score = float(seller_score or 0)
    price_val = float(price_val or 0)

    # ── 1. Trust Score ──────────────────────────────────────────────────────
    rating_contribution = (rating / 5.0) * 70 if rating > 0 else 0

    if review_count_value >= 10000:
        review_contribution = 20
    elif review_count_value >= 1000:
        review_contribution = 15
    elif review_count_value >= 100:
        review_contribution = 10
    else:
        review_contribution = 0

    seller_contribution = 10 if seller_score >= 8.5 else 0

    trust_score = min(100, int(rating_contribution + review_contribution + seller_contribution))

    # ── 2. Fake Review Risk ─────────────────────────────────────────────────
    fake_risk = 55

    if review_count_value >= 10000:
        fake_risk -= 25
    elif review_count_value >= 1000:
        fake_risk -= 15
    elif review_count_value >= 100:
        fake_risk -= 8

    if rating >= 4.9 and review_count_value < 100:
        fake_risk += 25
    elif 4.0 <= rating <= 4.7:
        fake_risk -= 10

    if seller_score >= 8.5:
        fake_risk -= 10

    fake_review_risk = max(5, min(100, fake_risk))

    # ── 3. Price Performance ────────────────────────────────────────────────
    # Deterministic demo rule: do not use live alternative scrape output for scores.
    if rating >= 4.5:
        base_price_performance = 7.0
    elif rating >= 4.0:
        base_price_performance = 6.0
    else:
        base_price_performance = 4.5

    if price_val >= 3000:
        price_penalty = 1.0
    elif price_val >= 1000:
        price_penalty = 0.5
    else:
        price_penalty = 0.0
    price_performance = round(max(1.0, min(10.0, base_price_performance - price_penalty)), 1)

    # ── 4. Sentiment Score ──────────────────────────────────────────────────
    sentiment_score = round(rating * 2, 1) if rating else 0.0

    # ── 5. Return Risk ──────────────────────────────────────────────────────
    if rating >= 4.4 and review_count_value >= 500:
        return_risk = "Düşük"
    elif rating >= 4.0:
        return_risk = "Orta"
    elif rating > 0:
        return_risk = "Yüksek"
    else:
        return_risk = "Orta"  # unknown rating — don't punish unfairly

    # ── 6. Final Decision ───────────────────────────────────────────────────
    if trust_score < 50 or fake_review_risk > 65:
        final_decision = "ÖNERİLMEZ"
    elif trust_score >= 75 and price_performance >= 6 and fake_review_risk <= 35:
        final_decision = "ALINABİLİR"
    elif trust_score >= 50:
        final_decision = "BEKLE"
    else:
        final_decision = "ÖNERİLMEZ"

    scoring_inputs = {
        "rating": rating,
        "reviewCount": review_count,
        "questionCount": question_count,
        "sellerScore": seller_score,
        "price": price_val,
        "category": category,
        "reviewCountUsedForScore": review_count_value,
        "questionCountUsedForScore": question_count_value,
    }

    print(
        f"[SCORING] version={SCORING_VERSION} rating={rating} reviewCount={review_count} sellerScore={seller_score} "
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
        "scoringInputs": scoring_inputs,
        "scoringVersion": SCORING_VERSION,
    }
