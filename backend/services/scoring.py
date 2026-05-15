def calculate_scores(rating: float, review_count: int, question_count: int, seller_score: float, price_val: float, alternatives: list, category: str):
    rating = rating or 0.0
    review_count = review_count or 0
    question_count = question_count or 0
    seller_score = seller_score or 0.0

    # 1. Trust Score
    # Base trust is 40. High rating adds up to 30. High reviews adds up to 15. Seller score adds up to 15.
    rating_factor = (rating / 5.0) * 30
    review_factor = min(15, (review_count / 1000.0) * 15)
    seller_factor = min(15, (seller_score / 10.0) * 15) if seller_score > 0 else 5 # slight bump if no score but exists
    
    trust_score = int(40 + rating_factor + review_factor + seller_factor)
    trust_score = min(100, max(0, trust_score))
    
    # 2. Fake Review Risk
    if rating > 4.7 and review_count < 50:
        fake_review_risk = 80 - review_count
    elif rating > 4.5 and review_count > 1000:
        fake_review_risk = max(5, 20 - int(question_count / 100))
    elif review_count == 0:
        fake_review_risk = 50 # Not enough data
    else:
        fake_review_risk = 30 + int((5.0 - rating) * 10)
        
    fake_review_risk = min(100, max(5, fake_review_risk))

    # 3. Price Performance
    avg_alt_price = price_val or 1.0
    if alternatives:
        try:
            alt_prices = []
            for alt in alternatives:
                p_str = alt["price"].replace(" TL", "").replace(".", "").replace(",", ".")
                alt_prices.append(float(p_str))
            if alt_prices:
                avg_alt_price = sum(alt_prices) / len(alt_prices)
        except:
            pass
            
    ratio = avg_alt_price / max(1, price_val) if price_val else 1.0
    price_performance = round(min(9.8, max(3.0, ratio * 7.0)), 1)
    
    # 4. Sentiment Score
    sentiment_score = round(rating * 2.0, 1) if rating else 5.0
    
    # 5. Return Risk
    if category and "giyim" in category.lower():
        base_return = 40 # clothing has higher return rates
    elif category and "elektronik" in category.lower():
        base_return = 20
    else:
        base_return = 10

    if rating >= 4.5 and review_count > 500:
        return_risk_val = base_return - 10
    elif rating <= 3.5:
        return_risk_val = base_return + 30
    else:
        return_risk_val = base_return + 10

    if return_risk_val < 20:
        return_risk = "Düşük"
    elif return_risk_val < 50:
        return_risk = "Orta"
    else:
        return_risk = "Yüksek"

    # 6. Final Decision
    if trust_score > 80 and return_risk == "Düşük" and fake_review_risk < 30:
        final_decision = "ALINABİLİR"
    elif trust_score < 50 or fake_review_risk > 70 or return_risk == "Yüksek":
        final_decision = "ÖNERİLMEZ"
    else:
        final_decision = "BEKLE"

    return {
        "trustScore": trust_score,
        "fakeReviewRisk": fake_review_risk,
        "sentimentScore": sentiment_score,
        "pricePerformance": price_performance,
        "returnRisk": return_risk,
        "finalDecision": final_decision
    }
