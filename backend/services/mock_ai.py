import traceback

from .category_detector import detect_category
from .platform_detector import detect_platform
from .product_scraper import scrape_product
from .scoring_engine import run_scoring
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


def _safe_optional_int(val):
    if val is None or val == "":
        return None
    try:
        return int(str(val).replace(".", "").replace(",", ""))
    except Exception:
        return None


def _parse_price_val(price_str: str) -> float:
    try:
        return float(
            price_str
            .replace(" TL", "")
            .replace("₺", "")
            .replace(".", "")
            .replace(",", ".")
            .strip()
        )
    except Exception:
        return 0.0


def _extract_review_texts(reviews) -> list[str]:
    """Accept list[str] or list[dict], always return list[str] for scoring."""
    texts = []
    for r in (reviews or []):
        if isinstance(r, dict):
            t = r.get("text") or ""
        else:
            t = str(r)
        if t and len(t.strip()) > 5:
            texts.append(t.strip())
    return texts


DEMO_ERROR = "Ürün verileri güvenilir şekilde alınamadı. Lütfen farklı bir ürün linki deneyin."
UNSUPPORTED_SITE_ERROR = "Bu site şu anda desteklenmiyor. Trendyol, Hepsiburada veya Amazon Türkiye linki deneyin."

_VALID_DECISIONS = {"ALINABİLİR", "DİKKATLİ İNCELE", "BEKLE"}


async def generate_analysis(url: str, include_reviews: bool = False):
    print(f"[ANALYZE] incoming url = {url}")

    platform = detect_platform(url)
    print(f"[ANALYZE] detected platform = {platform}")
    if platform not in {"trendyol", "hepsiburada", "amazon_tr"}:
        raise ValueError(UNSUPPORTED_SITE_ERROR)

    try:
        extracted_data = await scrape_product(url)
    except Exception as e:
        print("[ANALYZE] scrape_product raised exception:")
        traceback.print_exc()
        raise ValueError(f"Ürün sayfası yüklenemedi: {e}")

    reviews_raw = extracted_data.get("reviews") or []
    review_texts = _extract_review_texts(reviews_raw)
    reviews_loaded = len(reviews_raw)

    print(f"[ANALYZE] productName    = {extracted_data.get('productName')!r}")
    print(f"[ANALYZE] price          = {extracted_data.get('price')!r}")
    print(f"[ANALYZE] image          = {'YES' if extracted_data.get('image') else 'NO'}")
    print(f"[ANALYZE] rating         = {extracted_data.get('rating')}")
    print(f"[ANALYZE] reviewCount    = {extracted_data.get('reviewCount')}")
    print(f"[ANALYZE] reviewsLoaded  = {reviews_loaded}")
    print(f"[ANALYZE] reviewsSource  = {extracted_data.get('reviewsSource', 'none')}")
    print(f"[ANALYZE] ratingDist     = {extracted_data.get('ratingDistribution')}")
    print(f"[ANALYZE] dataSource     = {extracted_data.get('dataSource')}")

    product_name_raw = extracted_data.get("productName")
    image_raw = extracted_data.get("image")
    price_raw = extracted_data.get("price")

    if not product_name_raw or _safe_str(product_name_raw).lower() in {
        "ürün adı alınamadı",
        "urun adi alinamadi",
        "your connection was interrupted",
    }:
        raise ValueError(DEMO_ERROR)
    if not price_raw:
        raise ValueError(DEMO_ERROR)
    if extracted_data.get("rating") is None:
        raise ValueError(DEMO_ERROR)

    # Reject unsafe count sources
    ds = extracted_data.get("dataSource") or {}
    if ds.get("reviewCount") in {"regex", "body_regex"}:
        print("[COUNT SOURCE] rejecting unsafe reviewCount source")
        extracted_data["reviewCount"] = None
    if ds.get("questionCount") in {"regex", "body_regex"}:
        print("[COUNT SOURCE] rejecting unsafe questionCount source")
        extracted_data["questionCount"] = None

    product_name = _safe_str(product_name_raw, "Ürün adı alınamadı")
    brand = _safe_str(extracted_data.get("brand"))
    image = (
        image_raw
        if isinstance(image_raw, str) and image_raw.strip().startswith("http")
        else None
    )
    price_str = _safe_str(price_raw)
    rating = _safe_float(extracted_data.get("rating"))
    review_count = _safe_optional_int(extracted_data.get("reviewCount"))
    question_count = _safe_optional_int(extracted_data.get("questionCount"))
    seller_score_raw = extracted_data.get("sellerScore")
    seller_score: float | None = _safe_float(seller_score_raw) if seller_score_raw is not None else None
    reviews_source = extracted_data.get("reviewsSource", "none")
    rating_distribution = extracted_data.get("ratingDistribution")

    # Build reviewStats from scraper output or construct a safe fallback
    review_stats_raw = extracted_data.get("reviewStats") or {}
    review_stats = {
        "reviewCount": review_stats_raw.get("reviewCount", review_count),
        "reviewsLoaded": review_stats_raw.get("reviewsLoaded", reviews_loaded),
        "dedupedCount": review_stats_raw.get("dedupedCount", reviews_loaded),
        "completed": review_stats_raw.get("completed", False),
        "maxReviews": review_stats_raw.get("maxReviews", 0),
        "source": review_stats_raw.get("source", reviews_source),
        "reason": review_stats_raw.get("reason", "unknown"),
    }
    if review_stats_raw.get("error"):
        review_stats["error"] = review_stats_raw["error"]
    if review_stats_raw.get("apiTotalCount") is not None:
        review_stats["apiTotalCount"] = review_stats_raw["apiTotalCount"]
    if review_stats_raw.get("platformLimitReached"):
        review_stats["platformLimitReached"] = True

    if rating <= 0:
        raise ValueError(DEMO_ERROR)

    price_val = _parse_price_val(price_str)

    # Category detection
    display_category = _safe_str(extracted_data.get("category"))
    if not display_category or display_category == "Genel":
        cat_display, _ = detect_category(
            product_name=product_name,
            slug_keywords=extracted_data.get("slugKeywords", []),
            breadcrumb=_safe_str(extracted_data.get("category")),
            brand=brand,
        )
        display_category = cat_display if cat_display else "Genel"

    # Scrape alternatives from the SAME platform
    try:
        better_alternatives = await get_alternatives(
            display_category, product_name, price_val,
            brand=brand, platform=platform,
        )
    except Exception as e:
        print(f"Alternatives error: {e}")
        better_alternatives = []

    # Extract numeric alternative prices for scoring
    alternative_prices: list[float] = []
    for alt in (better_alternatives or []):
        alt_price_str = _safe_str(alt.get("price"))
        if alt_price_str:
            pv = _parse_price_val(alt_price_str)
            if pv > 0:
                alternative_prices.append(pv)

    # Run data-driven scoring using plain text reviews
    scores = run_scoring(
        rating=rating if rating > 0 else None,
        review_count=review_count,
        seller_score=seller_score,
        price_val=price_val if price_val > 0 else None,
        reviews=review_texts,
        rating_distribution=rating_distribution,
        alternative_prices=alternative_prices,
        category=display_category,
    )

    fake_review_risk = scores.get("fakeReviewRisk")
    return_risk = scores.get("returnRisk")
    trust_score = scores.get("trustScore")
    sentiment_score = scores.get("sentimentScore")
    price_performance = scores.get("pricePerformance")
    final_decision = scores.get("finalDecision", "DİKKATLİ İNCELE")
    confidence_level = scores.get("confidenceLevel", "LOW_CONFIDENCE")
    data_warning = scores.get("dataWarning")
    data_quality = scores.get("dataQuality") or {}
    scoring_version = scores.get("scoringVersion", "confidence-v2")

    print(f"[SCORE] decision={final_decision!r} trust={trust_score} fake={fake_review_risk} "
          f"sentiment={sentiment_score} pricePerf={price_performance} confidence={confidence_level}")

    if final_decision not in _VALID_DECISIONS:
        final_decision = "DİKKATLİ İNCELE"

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

    clean_alternatives = []
    source_url = _safe_str(extracted_data.get("sourceUrl"), url)
    for alt in (better_alternatives or []):
        alt_image = alt.get("image")
        alt_url = _safe_str(alt.get("url"))
        alt_price = _safe_str(alt.get("price"))
        if not alt_url or alt_url == source_url or not alt_price:
            continue
        clean_alternatives.append({
            "name": _safe_str(alt.get("name"), "Ürün"),
            "price": alt_price,
            "image": alt_image if isinstance(alt_image, str) and alt_image.startswith("http") else None,
            "url": alt_url,
            "reason": _safe_str(alt.get("reason"), "Aynı kategoriden alternatif ürün."),
            "isDirectProductUrl": bool(alt.get("isDirectProductUrl", False)),
        })

    response = {
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
        "sourceUrl": source_url,
        "sourcePlatform": _safe_str(extracted_data.get("sourcePlatform"), "Web"),
        "fakeReviewRisk": fake_review_risk,
        "returnRisk": return_risk,
        "returnProbability": return_risk,
        "trustScore": trust_score,
        "sentimentScore": sentiment_score,
        "pricePerformance": price_performance,
        "finalDecision": final_decision,
        "analysis": analysis_text,
        "shoppingBehavior": shopping_behavior,
        "alternativeProducts": clean_alternatives,
        "betterAlternatives": clean_alternatives,
        "dataSource": extracted_data.get("dataSource") or {},
        "dataQuality": data_quality,
        "confidenceLevel": confidence_level,
        "dataWarning": data_warning,
        "reviewsLoaded": reviews_loaded,
        "reviewsSource": reviews_source,
        "reviewStats": review_stats,
        "scoringVersion": scoring_version,
    }

    # Only include full review objects when explicitly requested
    if include_reviews:
        response["reviews"] = reviews_raw

    return response
