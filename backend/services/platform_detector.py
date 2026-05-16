"""Detect which e-commerce platform a URL belongs to."""

from urllib.parse import urlparse


def detect_platform(url: str) -> str:
    """
    Returns one of:
      "trendyol" | "hepsiburada" | "amazon_tr" | "n11" |
      "pazarama" | "ciceksepeti" | "generic"
    """
    if not url:
        return "generic"
    try:
        host = urlparse(url).netloc.lower()
        # strip www. prefix
        host = host.removeprefix("www.")
    except Exception:
        return "generic"

    if "trendyol.com" in host:
        return "trendyol"
    if "hepsiburada.com" in host:
        return "hepsiburada"
    if "amazon.com.tr" in host or "amazon.tr" in host:
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

    return "generic"


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
