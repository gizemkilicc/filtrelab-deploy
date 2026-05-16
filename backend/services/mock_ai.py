from .category_detector import detect_category
from .trendyol_scraper import scrape_trendyol_product
from .scoring import calculate_scores
from .text_generator import generate_explanations
from .alternative_scraper import get_alternatives


def _safe_str(val, default: str = "") -> str:
    if val is None:
        return default
    s = str(val).strip()
    return s if s else default


def _safe_float(val, default: float = 0.0) -> float:
    if val is None:
        return default
    try:
        return float(str(val).replace(",", "."))
    except Exception:
        return default


def _safe_int(val, default: int = 0) -> int:
    if val is None:
        return default
    try:
        return int(str(val).replace(".", "").replace(",", ""))
    except Exception:
        return default


async def generate_analysis(url: str):
    extracted_data = await scrape_trendyol_product(url)

    product_name = _safe_str(extracted_data.get("productName"), "Ürün adı alınamadı")
    brand = _safe_str(extracted_data.get("brand"))
    # image: only pass through if it's a real URL string
    raw_image = extracted_data.get("image")
    image = (
        raw_image
        if isinstance(raw_image, str) and raw_image.strip().startswith("http")
        else None
    )
    price_str = _safe_str(extracted_data.get("price"))
    rating = _safe_float(extracted_data.get("rating"))
    review_count = _safe_int(extracted_data.get("reviewCount"))
    question_count = _safe_int(extracted_data.get("questionCount"))
    seller_score = _safe_float(extracted_data.get("sellerScore"))

    # Parse numeric price for scoring
    price_val = 0.0
    if price_str:
        try:
            price_val = float(
                price_str
                .replace(" TL", "")
                .replace("₺", "")
                .replace(".", "")
                .replace(",", ".")
                .strip()
            )
        except Exception:
            price_val = 0.0

    # Detect category
    display_category = _safe_str(extracted_data.get("category"))
    if not display_category or display_category == "Genel":
        cat_enum, _ = detect_category(url, extracted_data.get("slugKeywords", []))
        category_map = {
            "kozmetik": "Kozmetik / Cilt Bakımı",
            "elektronik": "Elektronik / Kulaklık",
            "laptop": "Bilgisayar / Laptop",
            "telefon": "Akıllı Telefon",
            "ayakkabi": "Giyim / Ayakkabı",
            "canta": "Aksesuar / Çanta",
            "saat": "Aksesuar / Saat",
            "kahve": "Elektrikli Ev Aletleri / Kahve Makinesi",
        }
        display_category = category_map.get(cat_enum, "Genel")

    # Scrape alternatives
    try:
        better_alternatives = await get_alternatives(display_category, product_name, price_val)
    except Exception as e:
        print(f"Alternatives error: {e}")
        better_alternatives = []

    # Calculate scores
    try:
        scores = calculate_scores(
            rating, review_count, question_count, seller_score,
            price_val, better_alternatives, display_category
        )
    except Exception as e:
        print(f"Scoring error: {e}")
        scores = {}

    fake_review_risk = _safe_int(scores.get("fakeReviewRisk"), 30)
    return_risk = _safe_str(scores.get("returnRisk"), "Orta")
    trust_score = _safe_int(scores.get("trustScore"), 0)
    sentiment_score = _safe_float(scores.get("sentimentScore"), 5.0)
    price_performance = _safe_float(scores.get("pricePerformance"), 5.0)
    final_decision = _safe_str(scores.get("finalDecision"), "BEKLE")

    # Generate text explanations
    try:
        explanations = generate_explanations(display_category, {
            "fakeReviewRisk": fake_review_risk,
            "returnRisk": return_risk,
            "trustScore": trust_score,
            "sentimentScore": sentiment_score,
            "pricePerformance": price_performance,
            "finalDecision": final_decision,
        })
    except Exception as e:
        print(f"Text generation error: {e}")
        explanations = {}

    analysis_text = _safe_str(
        explanations.get("decisionReason"),
        "Bu ürün verilerine göre genel değerlendirme tamamlandı."
    )
    if final_decision == "ÖNERİLMEZ":
        extra = _safe_str(explanations.get("fakeReviewExplanation"))
        if extra:
            analysis_text += " " + extra

    shopping_behavior = _safe_str(
        explanations.get("psychologyWarning"),
        "Bu ürünü satın almadan önce fiyat, yorum ve alternatifleri karşılaştırmanız önerilir."
    )

    # Normalize alternatives: ensure valid image URLs only
    clean_alternatives = []
    for alt in (better_alternatives or []):
        alt_image = alt.get("image")
        clean_alternatives.append({
            "name": _safe_str(alt.get("name"), "Ürün"),
            "price": _safe_str(alt.get("price")),
            "image": alt_image if isinstance(alt_image, str) and alt_image.startswith("http") else None,
            "url": _safe_str(alt.get("url")),
            "reason": _safe_str(alt.get("reason"), "Aynı kategoriden alternatif ürün."),
            "isDirectProductUrl": bool(alt.get("isDirectProductUrl", False)),
        })

    return {
        "success": True,
        "productName": product_name,
        "brand": brand,
        "category": display_category,
        "price": price_str,
        "image": image,
        "rating": rating,
        "reviewCount": review_count,
        "questionCount": question_count,
        "sellerScore": seller_score,
        "sourceUrl": _safe_str(extracted_data.get("sourceUrl"), url),
        "sourcePlatform": _safe_str(extracted_data.get("sourcePlatform"), "Trendyol"),
        "fakeReviewRisk": fake_review_risk,
        "returnRisk": return_risk,
        "returnProbability": return_risk,
        "trustScore": trust_score,
        "sentimentScore": round(sentiment_score, 1),
        "pricePerformance": round(price_performance, 1),
        "finalDecision": final_decision,
        "analysis": analysis_text,
        "shoppingBehavior": shopping_behavior,
        "alternativeProducts": clean_alternatives,
        "betterAlternatives": clean_alternatives,
        "dataSource": extracted_data.get("dataSource") or {},
    }
