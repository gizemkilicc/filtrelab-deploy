from .category_detector import detect_category
from .trendyol_scraper import scrape_trendyol_product
from .scoring import calculate_scores
from .text_generator import generate_explanations
from .alternative_scraper import get_alternatives


async def generate_analysis(url: str):
    extracted_data = await scrape_trendyol_product(url)

    product_name = extracted_data.get("productName") or "Ürün adı alınamadı"
    brand = extracted_data.get("brand") or ""
    image = extracted_data.get("image") or None
    price_str = extracted_data.get("price") or ""
    rating = extracted_data.get("rating") or 0
    review_count = extracted_data.get("reviewCount") or 0
    question_count = extracted_data.get("questionCount") or 0
    seller_score = extracted_data.get("sellerScore") or 0

    price_val = 0.0
    if price_str:
        try:
            p_str = (
                str(price_str)
                .replace(" TL", "")
                .replace("₺", "")
                .replace(".", "")
                .replace(",", ".")
                .strip()
            )
            price_val = float(p_str)
        except Exception:
            price_val = 0.0

    display_category = extracted_data.get("category")
    if not display_category or display_category == "Genel":
        cat_enum, _ = detect_category(url, extracted_data.get("slugKeywords", []))

        if cat_enum == "kozmetik":
            display_category = "Kozmetik / Cilt Bakımı"
        elif cat_enum == "elektronik":
            display_category = "Elektronik / Kulaklık"
        elif cat_enum == "laptop":
            display_category = "Bilgisayar / Laptop"
        elif cat_enum == "telefon":
            display_category = "Akıllı Telefon"
        elif cat_enum == "ayakkabi":
            display_category = "Giyim / Ayakkabı"
        elif cat_enum == "canta":
            display_category = "Aksesuar / Çanta"
        elif cat_enum == "saat":
            display_category = "Aksesuar / Saat"
        elif cat_enum == "kahve":
            display_category = "Elektrikli Ev Aletleri / Kahve Makinesi"
        else:
            display_category = "Genel"

    try:
        better_alternatives = await get_alternatives(
            display_category,
            product_name,
            price_val
        )
    except Exception:
        better_alternatives = []

    try:
        scores = calculate_scores(
            rating,
            review_count,
            question_count,
            seller_score,
            price_val,
            better_alternatives,
            display_category
        )
    except Exception:
        scores = {}

    fake_review_risk = scores.get("fakeReviewRisk", 0)
    return_risk = scores.get("returnRisk", "Orta")
    trust_score = scores.get("trustScore", 0)
    sentiment_score = scores.get("sentimentScore", 0)
    price_performance = scores.get("pricePerformance", 0)
    final_decision = scores.get("finalDecision", "BEKLE")

    try:
        explanations = generate_explanations(display_category, {
            "fakeReviewRisk": fake_review_risk,
            "returnRisk": return_risk,
            "trustScore": trust_score,
            "sentimentScore": sentiment_score,
            "pricePerformance": price_performance,
            "finalDecision": final_decision,
        })
    except Exception:
        explanations = {}

    analysis_text = explanations.get(
        "decisionReason",
        "Bu ürün verilerine göre genel değerlendirme tamamlandı."
    )

    if final_decision == "ÖNERİLMEZ":
        analysis_text += " " + explanations.get("fakeReviewExplanation", "")

    shopping_behavior = explanations.get(
        "psychologyWarning",
        "Bu ürünü satın almadan önce fiyat, yorum ve alternatifleri karşılaştırmanız önerilir."
    )

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
        "sourceUrl": extracted_data.get("sourceUrl", url),
        "sourcePlatform": extracted_data.get("sourcePlatform", "Trendyol"),
        "fakeReviewRisk": fake_review_risk,
        "returnRisk": return_risk,
        "returnProbability": return_risk,
        "trustScore": trust_score,
        "sentimentScore": sentiment_score,
        "pricePerformance": price_performance,
        "finalDecision": final_decision,
        "analysis": analysis_text,
        "shoppingBehavior": shopping_behavior,
        "alternativeProducts": better_alternatives,
        "betterAlternatives": better_alternatives,
        "dataSource": extracted_data.get("dataSource", {})
    }