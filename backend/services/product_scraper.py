"""
Scraper router.

Selects the right platform-specific scraper based on the URL,
falling back to the generic scraper for unknown sites.

All scrapers return the same dict schema.
"""

from .platform_detector import detect_platform, platform_display_name
from .trendyol_scraper import scrape_trendyol_product
from .hepsiburada_scraper import scrape_hepsiburada_product
from .generic_scraper import scrape_generic_product


async def scrape_product(url: str) -> dict:
    """
    Route a product URL to the appropriate scraper.
    Never raises — returns a safe partial result on failure.
    """
    platform = detect_platform(url)
    print(f"[scraper_router] platform={platform!r}  url={url[:80]!r}")

    try:
        if platform == "trendyol":
            return await scrape_trendyol_product(url)
        elif platform == "hepsiburada":
            return await scrape_hepsiburada_product(url)
        else:
            # amazon_tr, n11, pazarama, ciceksepeti, generic → generic scraper
            result = await scrape_generic_product(url)
            # Override platform name with correct display name
            result["sourcePlatform"] = platform_display_name(platform)
            return result
    except Exception as e:
        print(f"[scraper_router] scraper failed for {platform!r}: {e}")
        return {
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
        }
