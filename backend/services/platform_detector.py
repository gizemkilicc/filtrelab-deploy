"""Detect which e-commerce platform a URL belongs to."""

from urllib.parse import urlparse


def detect_platform(url: str) -> str:
    """
    Returns one of:
      "trendyol" | "hepsiburada" | "amazon_tr" | "n11" |
      "pazarama" | "ciceksepeti" | "generic"

    Handles URLs with or without the https:// scheme prefix.
    """
    if not url or not isinstance(url, str):
        return "generic"

    url_stripped = url.strip()

    # Add scheme if missing so urlparse can extract netloc correctly
    url_for_parse = url_stripped
    if not url_for_parse.startswith(("http://", "https://")):
        url_for_parse = "https://" + url_for_parse

    try:
        host = urlparse(url_for_parse).netloc.lower()
        host = host.removeprefix("www.").removeprefix("m.").removeprefix("mobile.")
    except Exception:
        host = ""

    # Primary: match via parsed hostname
    if "trendyol.com" in host:
        print(f"[platform-detect] {host} → trendyol")
        return "trendyol"
    if "hepsiburada.com" in host:
        print(f"[platform-detect] {host} → hepsiburada")
        return "hepsiburada"
    if "amazon.com.tr" in host or "amazon.tr" in host:
        print(f"[platform-detect] {host} → amazon_tr")
        return "amazon_tr"
    if "n11.com" in host:
        return "n11"
    if "pazarama.com" in host:
        return "pazarama"
    if "ciceksepeti.com" in host:
        return "ciceksepeti"
    if "gittigidiyor.com" in host:
        return "gittigidiyor"
    if "morhipo.com" in host:
        return "morhipo"

    # Fallback: search in the raw URL string (handles edge cases)
    url_lower = url_stripped.lower()
    if "trendyol.com" in url_lower:
        print(f"[platform-detect] fallback string match → trendyol")
        return "trendyol"
    if "hepsiburada.com" in url_lower:
        print(f"[platform-detect] fallback string match → hepsiburada")
        return "hepsiburada"
    if "amazon.com.tr" in url_lower or "amazon.tr" in url_lower:
        print(f"[platform-detect] fallback string match → amazon_tr")
        return "amazon_tr"

    print(f"[platform-detect] ✗ unknown host={host!r}")
    return "generic"


def normalize_url(url: str) -> str:
    """
    Ensure the URL has an https:// scheme.
    Does NOT strip tracking parameters — call clean_url for that.
    """
    url = (url or "").strip()
    if url and not url.startswith(("http://", "https://")):
        url = "https://" + url
    return url


def clean_url(url: str, platform: str) -> str:
    """
    Strip unnecessary tracking parameters from the URL for a cleaner scrape.
    Returns the original URL unchanged on any error.
    """
    from urllib.parse import urlparse, urlunparse
    import re as _re

    try:
        url = normalize_url(url)
        parsed = urlparse(url)

        if platform == "amazon_tr":
            # Keep only /dp/ASIN — removes ref=, tracking, etc.
            m = _re.search(r"/dp/([A-Z0-9]{10})", parsed.path, _re.IGNORECASE)
            if m:
                clean_path = f"/dp/{m.group(1)}"
                cleaned = urlunparse((parsed.scheme, parsed.netloc, clean_path, "", "", ""))
                print(f"[url-clean] amazon_tr: {cleaned}")
                return cleaned

        elif platform == "trendyol":
            # Keep boutiqueId / merchantId query params if present
            from urllib.parse import parse_qs, urlencode
            qs = parse_qs(parsed.query)
            keep = {k: v for k, v in qs.items() if k in ("boutiqueId", "merchantId")}
            new_query = urlencode(keep, doseq=True) if keep else ""
            cleaned = urlunparse((parsed.scheme, parsed.netloc, parsed.path, "", new_query, ""))
            print(f"[url-clean] trendyol: {cleaned}")
            return cleaned

        elif platform == "hepsiburada":
            # Drop all query params
            cleaned = urlunparse((parsed.scheme, parsed.netloc, parsed.path, "", "", ""))
            print(f"[url-clean] hepsiburada: {cleaned}")
            return cleaned

    except Exception as e:
        print(f"[url-clean] error: {e}")

    return url


# Human-readable platform display names
PLATFORM_NAMES: dict[str, str] = {
    "trendyol": "Trendyol",
    "hepsiburada": "Hepsiburada",
    "amazon_tr": "Amazon Türkiye",
    "n11": "N11",
    "pazarama": "Pazarama",
    "ciceksepeti": "ÇiçekSepeti",
    "gittigidiyor": "GittiGidiyor",
    "morhipo": "Morhipo",
    "generic": "Web",
}


def platform_display_name(platform: str) -> str:
    return PLATFORM_NAMES.get(platform, "Web")
