from typing import Any

REQUIRED_SCRAPER_KEYS = {
    "productName": None,
    "brand": None,
    "category": "Genel",
    "price": None,
    "image": None,
    "rating": None,
    "reviewCount": None,
    "questionCount": None,
    "sellerScore": None,
    "sourceUrl": "",
    "sourcePlatform": "Web",
    "slugKeywords": [],
    "dataSource": {},
    "dataQuality": {},
    "reviews": [],
    "reviewsLoaded": 0,
    "reviewsSource": "none",
    "ratingDistribution": None,
}

SOURCE_QUALITY = {
    "jsonld": "high",
    "embedded": "high",
    "state": "high",
    "script": "high",
    "meta": "medium",
    "meta_og": "medium",
    "itemprop": "medium",
    "dom": "medium",
    "js": "medium",
    "regex": "low",
    "body_regex": "low",
    "fallback": "low",
}


def _source_quality(source: Any, value: Any) -> str:
    if value is None or value == "":
        return "missing"
    source_text = str(source or "").lower()
    for key, quality in SOURCE_QUALITY.items():
        if key in source_text:
            return quality
    return "low"


def normalize_scraper_result(result: dict[str, Any] | None, url: str = "", platform: str = "Web") -> dict[str, Any]:
    normalized = dict(REQUIRED_SCRAPER_KEYS)
    if result:
        normalized.update(result)

    normalized["sourceUrl"] = normalized.get("sourceUrl") or url
    normalized["sourcePlatform"] = normalized.get("sourcePlatform") or platform
    normalized["dataSource"] = normalized.get("dataSource") or {}

    data_source = normalized["dataSource"]
    data_quality = normalized.get("dataQuality") or {}
    for field in ("price", "reviewCount", "questionCount"):
        quality = data_quality.get(field) or _source_quality(data_source.get(field), normalized.get(field))
        data_quality[field] = quality
        if quality == "low":
            print(f"[DATA WARNING] {field} source is low confidence.")

    normalized["dataQuality"] = data_quality
    return normalized
