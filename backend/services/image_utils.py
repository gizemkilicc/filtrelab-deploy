"""Shared image URL utilities used by all scrapers."""

_BAD = (
    "logo", "icon", "svg", "placeholder", "default",
    "blank", "spinner", "badge", "banner", "favicon",
    "tracking", "pixel", "1x1",
)


def is_valid_image_url(url: str | None) -> bool:
    if not url or not isinstance(url, str):
        return False
    u = url.strip()
    if not (u.startswith("http://") or u.startswith("https://")):
        return False
    ul = u.lower()
    if any(b in ul for b in _BAD):
        return False
    return True


def normalize_image_url(url: str | None, base_domain: str = "https://www.trendyol.com") -> str | None:
    """
    Normalise a raw image URL:
      - // → https://
      - /path → base_domain + /path
      - bare path → None
    Returns a valid absolute URL or None.
    """
    if not url or not isinstance(url, str):
        return None
    url = url.strip()

    # Protocol-relative
    if url.startswith("//"):
        url = "https:" + url
    # Absolute path
    elif url.startswith("/"):
        url = base_domain.rstrip("/") + url
    # Handle srcset single entry like "img.jpg 1x"
    elif not url.startswith("http") and " " not in url:
        return None

    # Strip srcset descriptor if present (e.g. "img.jpg 2x")
    if " " in url:
        url = url.split()[0]

    return url if is_valid_image_url(url) else None


def parse_srcset(srcset: str | None, base_domain: str = "") -> str | None:
    """
    Parse a srcset string and return the highest-resolution valid URL.
    Srcset entries are ordered low → high res, so we iterate in reverse.
    """
    if not srcset:
        return None
    candidates: list[str] = []
    for part in srcset.split(","):
        token = part.strip().split()[0]  # first token = URL, second = width/density descriptor
        if token:
            candidates.append(token)
    for raw in reversed(candidates):
        norm = normalize_image_url(raw, base_domain)
        if norm:
            return norm
    return None
