"""
Scraper router.

Selects the right platform-specific scraper based on the URL,
falling back to the generic scraper for unknown sites.

All scrapers return the same dict schema.
"""

from .platform_detector import detect_platform, platform_display_name
from .trendyol_scraper import scrape_trendyol_product
from .hepsiburada_scraper import scrape_hepsiburada_product
from .amazon_scraper import scrape_amazon_product
from .generic_scraper import scrape_generic_product
from .data_quality import normalize_scraper_result


async def scrape_product(url: str, max_reviews: int | None = None) -> dict:
    """
    Route a product URL to the appropriate scraper.
    Never raises — returns a safe partial result on failure.
    max_reviews overrides the env-based default when provided.
    """
    platform = detect_platform(url)
    print(f"[scraper_router] platform={platform!r}  url={url[:80]!r}")

    try:
        if platform == "trendyol":
            return normalize_scraper_result(
                await scrape_trendyol_product(url, max_reviews=max_reviews),
                url, platform_display_name(platform)
            )
        elif platform == "hepsiburada":
            return normalize_scraper_result(
                await scrape_hepsiburada_product(url, max_reviews=max_reviews),
                url, platform_display_name(platform)
            )
        elif platform == "amazon_tr":
            return normalize_scraper_result(
                await scrape_amazon_product(url, max_reviews=max_reviews),
                url, platform_display_name(platform)
            )
        else:
            result = await scrape_generic_product(url)
            result["sourcePlatform"] = platform_display_name(platform)
            return normalize_scraper_result(result, url, platform_display_name(platform))
    except Exception as e:
        print(f"[scraper_router] scraper failed for {platform!r}: {e}")
        return normalize_scraper_result({
            "productName": None,
            "brand": None,
            "category": "Genel",
            "price": None,
            "image": None,
            "rating": None,
            "reviewCount": None,
            "questionCount": None,
            "sellerScore": None,
            "sourceUrl": url,
            "sourcePlatform": platform_display_name(platform),
            "slugKeywords": [],
            "dataSource": {"error": str(e)},
            "reviews": [],
            "reviewsLoaded": 0,
            "reviewsSource": "error",
            "reviewStats": {
                "reviewCount": None,
                "reviewsLoaded": 0,
                "dedupedCount": 0,
                "completed": False,
                "maxReviews": max_reviews or 0,
                "source": "error",
                "reason": "scraper_failed",
                "error": str(e),
            },
        }, url, platform_display_name(platform))
