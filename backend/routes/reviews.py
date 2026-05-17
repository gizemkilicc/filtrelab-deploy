import os
import traceback

from fastapi import APIRouter
from fastapi.responses import JSONResponse

from models.response_model import ReviewRequest, ReviewsExportRequest
from services.product_scraper import scrape_product

router = APIRouter()


def _default_max_reviews() -> int:
    return int(os.getenv("MAX_REVIEWS", "1000"))


def _build_review_stats(data: dict, max_reviews: int) -> dict:
    raw = data.get("reviewStats") or {}
    stats = {
        "reviewCount": raw.get("reviewCount", data.get("reviewCount")),
        "reviewsLoaded": raw.get("reviewsLoaded", len(data.get("reviews") or [])),
        "dedupedCount": raw.get("dedupedCount", len(data.get("reviews") or [])),
        "completed": raw.get("completed", False),
        "maxReviews": raw.get("maxReviews", max_reviews),
        "source": raw.get("source", data.get("reviewsSource", "none")),
        "reason": raw.get("reason", "unknown"),
    }
    if raw.get("error"):
        stats["error"] = raw["error"]
    elif stats["reviewsLoaded"] == 0:
        stats["error"] = "reviews_could_not_be_loaded"
    if raw.get("apiTotalCount") is not None:
        stats["apiTotalCount"] = raw["apiTotalCount"]
    if raw.get("platformLimitReached"):
        stats["platformLimitReached"] = True
    return stats


@router.post("/reviews")
async def get_reviews(request: ReviewRequest):
    """
    Fetch and return all available reviews for a product URL.
    Uses MAX_REVIEWS env var as default; can be overridden per request.
    """
    max_reviews = request.maxReviews if request.maxReviews else _default_max_reviews()
    try:
        data = await scrape_product(request.url, max_reviews=max_reviews)
        reviews = data.get("reviews") or []
        review_stats = _build_review_stats(data, max_reviews)

        return {
            "success": True,
            "productName": data.get("productName"),
            "reviewStats": review_stats,
            "reviews": reviews,
        }
    except Exception as e:
        print("[reviews] Unhandled exception:")
        traceback.print_exc()
        return JSONResponse(
            status_code=500,
            content={
                "success": False,
                "error": str(e),
                "reviewStats": {
                    "reviewsLoaded": 0,
                    "error": "scraping_failed",
                },
                "reviews": [],
            },
        )


@router.post("/reviews/export")
async def export_reviews(request: ReviewsExportRequest):
    """
    AI-team export endpoint. Returns a clean, stable review dataset.

    Reviews are returned in platform default order.
    Deduplication uses review ID when available, otherwise review text prefix.
    """
    max_reviews = request.maxReviews if request.maxReviews else _default_max_reviews()
    try:
        data = await scrape_product(request.url, max_reviews=max_reviews)
        reviews = data.get("reviews") or []
        review_stats = _build_review_stats(data, max_reviews)

        return {
            "product": {
                "name": data.get("productName"),
                "brand": data.get("brand"),
                "platform": data.get("sourcePlatform"),
                "url": request.url,
            },
            "reviews": reviews,
            "reviewStats": review_stats,
        }
    except Exception as e:
        print("[reviews/export] Unhandled exception:")
        traceback.print_exc()
        return JSONResponse(
            status_code=500,
            content={
                "success": False,
                "error": str(e),
                "product": {"url": request.url},
                "reviews": [],
                "reviewStats": {
                    "reviewsLoaded": 0,
                    "error": "scraping_failed",
                },
            },
        )
