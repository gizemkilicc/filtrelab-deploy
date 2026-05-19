"""
Hepsiburada product scraper.

Extraction priority:
  1. JSON-LD → embedded state → meta tags → DOM → regex

Reviews strategy (in order):
  0. Directly captured response bodies (page.on("response") async handler)
  1. Re-fetch from captured URL with pagination
  2. Known API endpoint templates with pagination
  3. Scroll + trigger XHR then retry
  4. BeautifulSoup DOM parse of rendered page
"""

import json
import os
import re
import traceback
import asyncio
import random
from urllib.parse import urlparse, urlencode, urlunparse, parse_qsl

from bs4 import BeautifulSoup
from playwright.async_api import async_playwright

from .image_utils import normalize_image_url, parse_srcset
from .price_utils import parse_tr_price
from .review_analytics import compute_review_analytics

_MAX_REVIEWS = int(os.getenv("MAX_REVIEWS", "1000"))
_HB_PAGE_SIZE = 20   # Use 20 — works reliably across all HB API variants
_BASE = "https://www.hepsiburada.com"
_UA = (
    "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) "
    "AppleWebKit/537.36 (KHTML, like Gecko) "
    "Chrome/124.0.0.0 Safari/537.36"
)
_LAUNCH_ARGS = [
    "--headless=new",
    "--disable-blink-features=AutomationControlled",
    "--no-sandbox",
    "--disable-dev-shm-usage",
    "--disable-gpu",
    "--disable-setuid-sandbox",
    "--window-size=1440,900",
    "--ignore-certificate-errors",
    "--lang=tr-TR",
]
_STEALTH_SCRIPT = """
    Object.defineProperty(navigator, 'webdriver', {get: () => undefined});
    Object.defineProperty(navigator, 'plugins', {get: () => [1, 2, 3, 4, 5]});
    Object.defineProperty(navigator, 'languages', {get: () => ['tr-TR', 'tr', 'en-US', 'en']});
    window.chrome = { runtime: {} };
"""
_NAME_SUFFIXES = (
    " değerlendirmeleri", " yorumları", " incelemeleri",
    " reviews", " yorumlari", " degerlendirmeleri",
)

_BAD_SELLER_KEYWORDS = (
    "other-seller", "othersellers", "diger-satici",
    "merchant-list", "seller-list", "other-merchants",
    "other-offers", "marketplace-offers",
    "diger-saticilar", "diger-saticilar-listesi",
    "other-sellers", "seller-card",
)

# JS snippet injected into any price evaluate() call to skip "Diğer satıcılar"
_JS_BAD_CONTAINER_FN = """
    const BAD = %s;
    function inBadContainer(el) {
        let node = el.parentElement, d = 0;
        while (node && d++ < 12) {
            const cls = (node.className || '').toLowerCase();
            const id  = (node.id  || '').toLowerCase();
            const tid = (node.getAttribute ? node.getAttribute('data-test-id') || '' : '').toLowerCase();
            if (BAD.some(k => cls.includes(k) || id.includes(k) || tid.includes(k))) return true;
            const txt = (node.innerText || node.textContent || '').toLowerCase();
            if (txt.length < 1400 && (
                txt.includes('diğer satıcılar') ||
                txt.includes('diger saticilar') ||
                txt.includes('tümünü gör') ||
                txt.includes('tumunu gor') ||
                txt.includes('ürüne git') ||
                txt.includes('urune git')
            )) return true;
            node = node.parentElement;
        }
        return false;
    }
""" % str(list(_BAD_SELLER_KEYWORDS))


def _calculate_review_limit(total_review_count: int | None) -> int:
    """
    Compute how many reviews to fetch based on the product's total count.
    Provides sufficient AI analysis sample without over-fetching.
    """
    if total_review_count is None or total_review_count <= 0:
        return 50
    if total_review_count <= 100:
        return total_review_count
    if total_review_count <= 500:
        return min(200, total_review_count)
    if total_review_count <= 2000:
        return 400
    if total_review_count <= 10000:
        return 600
    return 1000  # 10,000+ review products (iPhone, popular items)


def _in_bad_container_bs4(el) -> bool:
    """Return True if a BS4 element lives inside a 'Diğer satıcılar' container."""
    node = el.parent
    depth = 0
    while node and depth < 12:
        cls_str = " ".join(node.get("class", [])).lower() if isinstance(node.get("class"), list) else str(node.get("class", "")).lower()
        id_str  = str(node.get("id", "")).lower()
        tid_str = str(node.get("data-test-id", "")).lower()
        if any(k in cls_str or k in id_str or k in tid_str for k in _BAD_SELLER_KEYWORDS):
            return True
        node = node.parent
        depth += 1
    return False


async def _is_bad_price_element(el) -> bool:
    """Playwright-side mirror of inBadContainer for Python selector fallbacks."""
    try:
        return bool(await el.evaluate(
            """(el, bad) => {
                let node = el.parentElement, d = 0;
                while (node && d++ < 12) {
                    const cls = (node.className || '').toLowerCase();
                    const id = (node.id || '').toLowerCase();
                    const tid = (node.getAttribute ? node.getAttribute('data-test-id') || '' : '').toLowerCase();
                    if (bad.some(k => cls.includes(k) || id.includes(k) || tid.includes(k))) return true;
                    const txt = (node.innerText || node.textContent || '').toLowerCase();
                    if (txt.length < 1400 && (
                        txt.includes('diğer satıcılar') ||
                        txt.includes('diger saticilar') ||
                        txt.includes('tümünü gör') ||
                        txt.includes('tumunu gor') ||
                        txt.includes('ürüne git') ||
                        txt.includes('urune git')
                    )) return true;
                    node = node.parentElement;
                }
                return false;
            }""",
            list(_BAD_SELLER_KEYWORDS),
        ))
    except Exception:
        return False


# ─── Helpers ────────────────────────────────────────────────────────────────

def _extract_hb_product_id(url: str) -> str | None:
    """Extract Hepsiburada product identifier from URL path."""
    # Pattern: -p-HBCV00003T5BVC or -pm-HBV00000S9MSLZ
    m = re.search(r"-p[m]?-([A-Z0-9]{8,})", url, re.IGNORECASE)
    if m:
        return m.group(1).upper()
    # HBA-style segment
    m = re.search(r"/(HBA\w+)", url, re.IGNORECASE)
    if m:
        return m.group(1).upper()
    return None


def _clean(s: str | None) -> str | None:
    if not s:
        return None
    s = s.strip()
    sl = s.lower()
    for suf in _NAME_SUFFIXES:
        if sl.endswith(suf):
            s = s[: len(s) - len(suf)].strip()
            break
    return s if s else None


def _parse_review_count(text: str) -> int | None:
    for pattern in [
        r"([\d.]+)\s*Değerlendirme",
        r"([\d.]+)\s*değerlendirme",
        r"([\d.]+)\s*Yorum",
        r"([\d.]+)\s*yorum",
        r"([\d,]+)\s*review",
        r"\((\d[\d.]*)\)",
    ]:
        m = re.search(pattern, text, re.IGNORECASE)
        if m:
            raw = m.group(1).replace(".", "").replace(",", "")
            if raw.isdigit():
                return int(raw)
    return None


_HB_PRICE_RE = re.compile(
    r"(\d{1,3}(?:[.,]\d{3})*(?:[.,]\d{1,2})?|\d+(?:[.,]\d{1,2})?)\s*(?:TL|₺)",
    re.IGNORECASE,
)
_HB_BAD_PRICE_CONTEXT_RE = re.compile(r"taksit|ayda|kargo|kupon|puan|kazanç|kazanc", re.IGNORECASE)


def _extract_hb_price_value(raw) -> float | None:
    """
    Extract a single safe current product price from Hepsiburada text.
    Some HB nodes contain old price + sale price + installment numbers together;
    parsing that whole text creates huge bogus values. Split candidates first.
    """
    if raw is None:
        return None
    text = str(raw).strip()
    if not text:
        return None

    candidates: list[tuple[float, str]] = []
    for match in _HB_PRICE_RE.finditer(text):
        start = max(0, match.start() - 32)
        end = min(len(text), match.end() + 32)
        context = text[start:end]
        if _HB_BAD_PRICE_CONTEXT_RE.search(context):
            continue
        value = parse_tr_price(match.group(1))
        if value and 5 < value < 500_000:
            candidates.append((value, match.group(1)))

    if candidates:
        if len(candidates) > 1:
            max_value = max(value for value, _ in candidates)
            # Drop tiny coupon/discount amounts mixed into the same container.
            candidates = [(value, raw) for value, raw in candidates if value >= max_value * 0.35]
        # Discounted/current price is lower than the crossed old price when both
        # are present in the same HB price container.
        return min(value for value, _ in candidates)

    # Accept plain numeric source only when it is a short single value, not a
    # whole container text with several numbers merged together.
    compact = re.sub(r"\s+", "", text)
    if len(compact) <= 16:
        if re.fullmatch(r"\d+\.\d{1,2}", compact):
            value = float(compact)
            if 5 < value < 500_000:
                return value
        value = parse_tr_price(text)
        if value and 5 < value < 500_000:
            return value
    return None


def _format_hb_price(raw) -> str | None:
    if isinstance(raw, (int, float)):
        value = float(raw)
    else:
        value = _extract_hb_price_value(raw)
    if not value:
        return None
    int_part = int(value)
    decimals = round((value - int_part) * 100)
    int_str = f"{int_part:,}".replace(",", ".")
    if decimals > 0:
        return f"{int_str},{decimals:02d} TL"
    return f"{int_str} TL"


def _is_review_url(url: str) -> bool:
    low = url.lower()
    return (
        "hepsiburada.com" in low
        and any(k in low for k in ("review", "comment", "usercontent", "rating", "degerlendirme", "yorum"))
    )


# ─── Review body parser ──────────────────────────────────────────────────────

def _parse_hb_reviews_from_body(body: object, product_name: str | None = None) -> tuple[list[dict], int | None]:
    """
    Parse Hepsiburada review JSON from any known response format.
    Returns (review_list, total_count_if_available).
    """
    if not isinstance(body, dict):
        return [], None

    total: int | None = None

    # Locate the review list in common container paths
    review_list = None
    container_paths = [
        ["approvedUserContents"],
        ["reviews"],
        ["comments"],
        ["result", "reviews"],
        ["result", "comments"],
        ["data", "reviews"],
        ["data", "comments"],
        ["result", "content"],
        ["data", "content"],
        ["content"],
        ["items"],
        ["elements"],
    ]

    def _get(node, keys: list[str]):
        for k in keys:
            if not isinstance(node, dict):
                return None
            node = node.get(k) or next((v for ck, v in node.items() if ck.lower() == k.lower()), None)
        return node

    for path in container_paths:
        candidate = _get(body, path)
        if isinstance(candidate, list) and candidate:
            review_list = candidate
            print(f"[HB REVIEWS DEBUG] found list at path={'.'.join(path)!r} count={len(candidate)}")
            break

    # Try to find total
    for key in ("total", "totalCount", "totalElements", "count", "pageInfo"):
        v = body.get(key)
        if isinstance(v, int) and v > 0:
            total = v
            break
        if isinstance(v, dict):
            for sk in ("total", "totalCount", "count"):
                sv = v.get(sk)
                if isinstance(sv, int) and sv > 0:
                    total = sv
                    break

    if not review_list:
        return [], total

    text_keys = ("content", "comment", "text", "reviewText", "description", "body")
    rating_keys = ("star", "rate", "rating", "starCount", "ratingValue", "score")
    user_keys = ("displayName", "userFullName", "userName", "user", "nickName", "name")
    date_keys = ("createdDate", "date", "reviewDate", "updatedDate", "publishDate")

    def _first(d: dict, keys: tuple) -> str | None:
        low = {k.lower(): v for k, v in d.items()}
        for key in keys:
            val = low.get(key.lower())
            if val is not None:
                if isinstance(val, dict):
                    # dig one level for nested user objects
                    for sk in ("displayName", "userName", "name", "fullName"):
                        inner = val.get(sk)
                        if isinstance(inner, str) and inner.strip():
                            return inner.strip()
                elif isinstance(val, (str, int, float)):
                    return str(val).strip()
        return None

    reviews: list[dict] = []
    for item in review_list:
        if not isinstance(item, dict):
            continue

        text = _first(item, text_keys) or ""
        text = re.sub(r"\s+", " ", text).strip()
        if len(text) < 5:
            continue

        # Skip entries that look like product name / UI noise
        if product_name and text[:80].lower() == product_name[:80].lower():
            continue

        rating_raw = _first(item, rating_keys)
        rating: int | None = None
        if rating_raw is not None:
            try:
                r = round(float(str(rating_raw).replace(",", ".")))
                if 1 <= r <= 5:
                    rating = r
            except Exception:
                pass

        user_str = _first(item, user_keys)
        date_str = _first(item, date_keys)
        rev_id = str(item.get("id") or item.get("reviewId") or item.get("contentId") or "")

        reviews.append({
            "id": rev_id,
            "text": text,
            "rating": rating,
            "date": date_str,
            "user": user_str,
            "source": "hepsiburada_reviews_api",
        })

    return reviews, total


# ─── Response capture ────────────────────────────────────────────────────────

def _setup_hb_response_capture(page) -> tuple[list[str], dict]:
    """
    Intercept Hepsiburada review API responses and capture JSON bodies.
    Returns (captured_urls, captured_bodies).
    """
    captured_urls: list[str] = []
    captured_bodies: dict[str, object] = {}

    async def _handle_response(response) -> None:
        url = response.url
        if not _is_review_url(url):
            return
        if url not in captured_urls:
            captured_urls.append(url)

        status = response.status
        print(f"[HB RESPONSE] url={url[:120]}")
        print(f"[HB RESPONSE] status={status}")

        if status != 200:
            return

        try:
            content_type = response.headers.get("content-type", "")
            if "json" not in content_type.lower():
                return

            try:
                body = await response.json()
            except Exception:
                raw = await response.text()
                body = json.loads(raw)

            if isinstance(body, dict):
                print(f"[HB RESPONSE] topKeys={list(body.keys())[:15]}")
            print(f"[HB RESPONSE] preview={json.dumps(body, ensure_ascii=False)[:400]}")
            captured_bodies[url] = body

        except Exception as e:
            print(f"[HB RESPONSE] body read failed url={url[:80]} err={e}")

    def _on_request(request) -> None:
        if _is_review_url(request.url) and request.url not in captured_urls:
            captured_urls.append(request.url)

    page.on("request", _on_request)
    page.on("response", _handle_response)
    return captured_urls, captured_bodies


# ─── Pagination helpers ──────────────────────────────────────────────────────

def _normalise_hb_endpoint(url: str, page_num: int, page_size: int = _HB_PAGE_SIZE) -> str:
    """Replace / add pageNumber and pageSize params in a HB review URL."""
    parsed = urlparse(url)
    params = [
        (k, v) for k, v in parse_qsl(parsed.query, keep_blank_values=True)
        if k.lower() not in {"pagenumber", "page", "pagesize", "size", "offset", "skip"}
    ]
    # Detect param naming convention from original URL
    orig_keys = [k.lower() for k, _ in parse_qsl(parsed.query)]
    if "offset" in orig_keys or "skip" in orig_keys:
        params.append(("offset", str((page_num - 1) * page_size)))
        params.append(("limit", str(page_size)))
    else:
        params.append(("pageNumber", str(page_num)))
        params.append(("pageSize", str(page_size)))
    return urlunparse(parsed._replace(query=urlencode(params, doseq=True)))


async def _hb_refetch(page, url: str) -> tuple[object, int]:
    """Re-fetch a URL from within the page context (inherits cookies/session)."""
    try:
        result = await page.evaluate(
            """(endpoint) => fetch(endpoint, {
                headers: {
                    "Accept": "application/json, text/plain, */*",
                    "Accept-Language": "tr-TR,tr;q=0.9,en;q=0.8",
                }
            })
            .then(r => r.json().then(data => [r.status, data]).catch(() => [r.status, null]))
            .catch(() => [0, null])""",
            url,
        )
        if result and isinstance(result, list) and len(result) == 2:
            return result[1], int(result[0] or 0)
    except Exception as e:
        print(f"[HB REVIEWS] re-fetch error url={url[:80]} err={e}")
    return None, 0


async def _hb_paginate(
    page,
    base_url: str,
    first_body: object | None,
    max_reviews: int,
    product_name: str | None = None,
) -> tuple[list[dict], bool, str]:
    """
    Paginate from base_url. If first_body is provided it is used as page 1
    without a network request.
    Returns (reviews, completed, reason).
    """
    all_reviews: list[dict] = []
    seen: set[str] = set()
    reason = "no_more_pages"
    consecutive_empty = 0

    for page_num in range(1, 2000):
        if len(all_reviews) >= max_reviews:
            reason = "maxReviews_reached"
            break

        if page_num == 1 and first_body is not None:
            body = first_body
            status = 200
        else:
            url = _normalise_hb_endpoint(base_url, page_num)
            body, status = await _hb_refetch(page, url)

        if status in (403, 429):
            print(f"[HB REVIEWS] page={page_num} status={status} rate_limited")
            reason = "rate_limited"
            break

        if not body:
            consecutive_empty += 1
            if consecutive_empty >= 2:
                reason = "no_more_pages"
                break
            page_num_next = page_num + 1
            continue

        page_reviews, total = _parse_hb_reviews_from_body(body, product_name)
        loaded = len(page_reviews)
        print(f"[HB REVIEWS] page={page_num} loaded={loaded} total={len(all_reviews)}")

        if loaded == 0:
            consecutive_empty += 1
            if consecutive_empty >= 2:
                reason = "no_more_pages"
                break
        else:
            consecutive_empty = 0
            for r in page_reviews:
                key = r["id"] if r["id"] else r["text"][:80]
                if key not in seen:
                    seen.add(key)
                    all_reviews.append(r)
                    if len(all_reviews) >= max_reviews:
                        break

        if len(all_reviews) >= max_reviews:
            reason = "maxReviews_reached"
            break

        await asyncio.sleep(random.uniform(0.3, 0.8))

    completed = reason == "no_more_pages"
    print(f"[HB REVIEWS] totalLoaded={len(all_reviews)} completed={completed} reason={reason}")
    return all_reviews, completed, reason


# ─── BS4 DOM fallback ────────────────────────────────────────────────────────

def _parse_hb_reviews_from_dom(html: str, product_name: str | None = None) -> list[dict]:
    """Parse review cards from fully rendered Hepsiburada HTML via BS4."""
    soup = BeautifulSoup(html, "html.parser")
    reviews: list[dict] = []

    containers = (
        soup.select('[class*="ReviewCard"], [class*="reviewCard"]')
        or soup.select('[class*="CommentItem"], [class*="commentItem"]')
        or soup.select('[data-testid*="review"], [data-test-id*="review"]')
        or soup.select('[class*="ReviewWrapper"], [class*="reviewWrapper"]')
    )

    text_sels = (
        '[class*="ReviewText"]',
        '[class*="reviewText"]',
        '[class*="ReviewContent"]',
        '[class*="reviewContent"]',
        '[class*="ReviewDescription"]',
        '[class*="commentDescription"]',
        '[class*="comment-description"]',
        '[class*="review-description"]',
    )
    rating_sels = (
        '[class*="RatingStars"]',
        '[class*="ratingStars"]',
        '[class*="starRating"]',
        '[class*="StarRating"]',
        '[class*="rating-score"]',
    )

    for card in containers:
        text = ""
        for sel in text_sels:
            el = card.select_one(sel)
            if el:
                text = re.sub(r"\s+", " ", el.get_text(" ", strip=True)).strip()
                if len(text) >= 5:
                    break

        if len(text) < 5:
            continue
        if product_name and text[:80].lower() == product_name[:80].lower():
            continue

        rating: int | None = None
        for sel in rating_sels:
            el = card.select_one(sel)
            if el:
                rm = re.search(r"([1-5][.,][0-9]|[1-5])\s*[/üz]", el.get_text())
                if rm:
                    try:
                        rating = round(float(rm.group(1).replace(",", ".")))
                    except Exception:
                        pass
                    break

        date_el = card.select_one('[class*="date"], [class*="Date"], time')
        date = date_el.get_text(strip=True) if date_el else None

        user_el = card.select_one('[class*="userName"], [class*="UserName"], [class*="author"]')
        user = user_el.get_text(strip=True) if user_el else None

        reviews.append({
            "id": "",
            "text": text,
            "rating": rating,
            "date": date,
            "user": user,
            "source": "hepsiburada_dom",
        })

    return reviews


# ─── Master review extractor ─────────────────────────────────────────────────

async def _extract_reviews_hepsiburada(
    page,
    url: str,
    captured_urls: list[str],
    captured_bodies: dict,
    review_count: int | None,
    max_reviews: int = _MAX_REVIEWS,
    product_name: str | None = None,
) -> tuple[list[dict], dict | None, str, bool, str]:
    """
    Master review extractor for Hepsiburada.
    Returns (reviews, rating_dist, source, completed, reason).
    """
    print(f"[HB REVIEWS] ===== START =====")
    print(f"[HB REVIEWS] current url: {page.url}")
    product_id = _extract_hb_product_id(url)
    print(f"[HB REVIEWS] productId={product_id!r} knownReviewCount={review_count}")
    print(f"[HB REVIEWS] captured URLs={len(captured_urls)} bodies={len(captured_bodies)}")

    # ── Strategy 0: directly captured response bodies ────────────────────────
    for cap_url, body in captured_bodies.items():
        page_reviews, total = _parse_hb_reviews_from_body(body, product_name)
        print(f"[HB REVIEWS PARSED] count={len(page_reviews)} from url={cap_url[:100]}")
        if page_reviews:
            sample = [r.get("text", "")[:60] for r in page_reviews[:2]]
            print(f"[HB REVIEWS PARSED SAMPLE]={sample}")
            reviews, completed, reason = await _hb_paginate(
                page, cap_url, body, max_reviews, product_name
            )
            if reviews:
                return reviews, None, "intercepted_response", completed, reason
            deduped = page_reviews[:max_reviews]
            return deduped, None, "captured_response_page0", False, "pagination_failed"
        else:
            print(f"[HB REVIEWS PARSED] count=0 — debug:")
            print(f"[HB REVIEWS DEBUG] keys={list(body.keys())[:15] if isinstance(body, dict) else type(body)}")
            print(f"[HB REVIEWS DEBUG] preview={json.dumps(body, ensure_ascii=False)[:400]}")

    # ── Strategy 1: scroll to trigger XHR, then retry captured bodies ────────
    if not captured_bodies:
        print("[HB REVIEWS] no bodies captured — scrolling to trigger XHR")
        for pct in [0.3, 0.55, 0.75, 0.9, 1.0]:
            await page.evaluate(f"window.scrollTo(0, document.body.scrollHeight * {pct})")
            await page.wait_for_timeout(700)
        # Click "Tüm Değerlendirmeleri Gör" if present
        for sel in (
            'button:has-text("Tüm Değerlendirmeleri")',
            'a:has-text("Tüm Değerlendirmeleri")',
            'button:has-text("Yorumları Gör")',
            '[class*="review"] button:has-text("Tümünü")',
        ):
            try:
                el = await page.query_selector(sel)
                if el:
                    await el.scroll_into_view_if_needed()
                    await el.click()
                    await page.wait_for_timeout(2000)
                    print(f"[HB REVIEWS] clicked '{sel}'")
                    break
            except Exception:
                continue

        await page.wait_for_timeout(1500)
        print(f"[HB REVIEWS] after scroll: URLs={len(captured_urls)} bodies={len(captured_bodies)}")

        # Retry Strategy 0 after scroll
        for cap_url, body in captured_bodies.items():
            page_reviews, _ = _parse_hb_reviews_from_body(body, product_name)
            if page_reviews:
                sample = [r.get("text", "")[:60] for r in page_reviews[:2]]
                print(f"[HB REVIEWS PARSED SAMPLE (post-scroll)]={sample}")
                reviews, completed, reason = await _hb_paginate(
                    page, cap_url, body, max_reviews, product_name
                )
                if reviews:
                    return reviews, None, "intercepted_response_post_scroll", completed, reason

    # ── Strategy 2: known API endpoint templates ──────────────────────────────
    if product_id:
        templates = [
            # Hermes user-content gateway (most reliable)
            f"https://user-content-gw-hermes.hepsiburada.com/queryapi/v2/ApprovedUserContents/{product_id}?hasMedia=false&hasContent=true&offset=0&limit={_HB_PAGE_SIZE}&stars=0",
            # Standard review APIs
            f"https://www.hepsiburada.com/reviews/{product_id}?pageNumber=1&pageSize={_HB_PAGE_SIZE}",
            f"https://api.hepsiburada.com/ratings/reviews/products/{product_id}?page=1&pageSize={_HB_PAGE_SIZE}",
            f"https://www.hepsiburada.com/api/v1/reviews/{product_id}?page=1&size={_HB_PAGE_SIZE}",
            f"https://www.hepsiburada.com/api/review?sku={product_id}&page=1&size={_HB_PAGE_SIZE}",
        ]
        for tmpl in templates:
            print(f"[HB REVIEWS] trying template url={tmpl[:120]}")
            body, status = await _hb_refetch(page, tmpl)
            print(f"[HB REVIEWS] status={status}")
            if status == 200 and body:
                page_reviews, _ = _parse_hb_reviews_from_body(body, product_name)
                if page_reviews:
                    print(f"[HB REVIEWS] template works loaded={len(page_reviews)}")
                    reviews, completed, reason = await _hb_paginate(
                        page, tmpl, body, max_reviews, product_name
                    )
                    if reviews:
                        return reviews, None, "api_template", completed, reason

    # ── Strategy 2.5: navigate to -yorumlari page + BS4 + pagination ─────────
    print("[HB REVIEWS] Strategy 2.5: navigating to -yorumlari page")
    try:
        base_url_clean = url.split('?')[0].split('#')[0]
        # Transform: {slug}-pm-{id} → {slug}-yorumlari-pm-{id}
        # or:        {slug}-p-{id}  → {slug}-yorumlari-p-{id}
        review_page_url: str | None = None
        for sep in ('-pm-', '-p-'):
            if sep in base_url_clean:
                parts = base_url_clean.split(sep, 1)
                review_page_url = f"{parts[0]}-yorumlari{sep}{parts[1]}"
                break
        if not review_page_url:
            review_page_url = base_url_clean.rstrip('/') + '-yorumlari'

        print(f"[HB REVIEWS] yorumlar URL: {review_page_url}")
        try:
            await page.goto(review_page_url, wait_until="domcontentloaded", timeout=25000)
            await page.wait_for_timeout(2500)
            print(f"[HB REVIEWS] loaded: {page.url}")
        except Exception as nav_err:
            print(f"[HB REVIEWS] yorumlar navigation failed: {nav_err}")

        # Scroll to trigger lazy load
        for _ in range(8):
            await page.evaluate("window.scrollBy(0, 700)")
            await page.wait_for_timeout(450)

        html_yr = await page.content()
        print(f"[HB REVIEWS] yorumlar HTML length: {len(html_yr)}")
        yorumlar_reviews = _parse_hb_reviews_from_dom(html_yr, product_name)
        print(f"[HB REVIEWS] yorumlar page 1: {len(yorumlar_reviews)} reviews")

        if yorumlar_reviews:
            # Paginate: ?sayfa=2, ?sayfa=3, ...
            all_yr_reviews = list(yorumlar_reviews)
            base_yr_url = page.url.split('?')[0]
            for page_num in range(2, 50):
                if len(all_yr_reviews) >= max_reviews:
                    break
                next_url = f"{base_yr_url}?sayfa={page_num}"
                try:
                    await page.goto(next_url, wait_until="domcontentloaded", timeout=15000)
                    await page.wait_for_timeout(1200)
                    for _ in range(4):
                        await page.evaluate("window.scrollBy(0, 600)")
                        await page.wait_for_timeout(350)
                    html_p = await page.content()
                    pg_reviews = _parse_hb_reviews_from_dom(html_p, product_name)
                    if not pg_reviews:
                        print(f"[HB REVIEWS] yorumlar page {page_num}: no cards → stopping")
                        break
                    new_r = [r for r in pg_reviews
                             if not any(e['text'][:80] == r['text'][:80] for e in all_yr_reviews)]
                    if not new_r:
                        print(f"[HB REVIEWS] yorumlar page {page_num}: all duplicates → stopping")
                        break
                    all_yr_reviews.extend(new_r)
                    print(f"[HB REVIEWS] yorumlar page {page_num}: +{len(new_r)} (total {len(all_yr_reviews)})")
                    await page.wait_for_timeout(700)
                except Exception as pg_err:
                    print(f"[HB REVIEWS] yorumlar page {page_num} error: {pg_err}")
                    break

            print(f"[HB REVIEWS] Strategy 2.5 SUCCESS: {len(all_yr_reviews)} reviews")
            return all_yr_reviews[:max_reviews], None, "yorumlar_page", False, "yorumlar_page"
    except Exception as e:
        print(f"[HB REVIEWS] Strategy 2.5 failed: {e}")

    # ── Strategy 3: BS4 DOM parse of rendered page ───────────────────────────
    print("[HB REVIEWS] falling back to BS4 DOM parse")
    html = await page.content()
    dom_reviews = _parse_hb_reviews_from_dom(html, product_name)
    if dom_reviews:
        print(f"[HB REVIEWS] dom loaded={len(dom_reviews)}")
        return dom_reviews, None, "hepsiburada_dom", False, "dom_fallback"

    # Legacy JS DOM fallback (existing code)
    raw = await page.evaluate("""
        () => {
            const sels = [
                '[class*="ReviewText"]', '[class*="reviewText"]',
                '[class*="comment-text"]', '[class*="commentText"]',
                '[class*="ReviewContent"]', '[class*="reviewContent"]',
                '[class*="ReviewDescription"]', '.review-description',
            ];
            const texts = new Set();
            for (const sel of sels) {
                for (const el of document.querySelectorAll(sel)) {
                    const t = el.children.length === 0
                        ? (el.textContent || '').trim()
                        : (el.firstChild?.textContent || '').trim();
                    if (t.length > 15) texts.add(t);
                }
            }
            return Array.from(texts).slice(0, 50);
        }
    """)
    js_texts = [t for t in (raw or []) if isinstance(t, str) and len(t.strip()) > 5]
    if js_texts:
        js_reviews = [
            {"id": "", "text": t, "rating": None, "date": None, "user": None, "source": "hepsiburada_dom_js"}
            for t in js_texts
        ]
        print(f"[HB REVIEWS] js-dom loaded={len(js_reviews)}")
        return js_reviews, None, "hepsiburada_dom_js", False, "dom_js_fallback"

    if review_count and review_count > 0:
        print(f"[HB REVIEWS ERROR] reviewCount={review_count} exists but reviews could not be loaded")
    print("[HB REVIEWS] loaded=0 source=none")
    return [], None, "none", False, "no_reviews_found"


# ─── Main scraper ────────────────────────────────────────────────────────────

async def scrape_hepsiburada_product(url: str, max_reviews: int | None = None) -> dict:
    product_name: str | None = None
    brand: str | None = None
    price: str | None = None
    image: str | None = None
    rating: float | None = None
    review_count: int | None = None
    question_count: int | None = None
    category = "Genel"
    data_source: dict[str, str] = {}
    reviews: list[dict] = []
    rating_distribution: dict | None = None
    reviews_completed = False
    reviews_reason = "not_started"
    effective_max_reviews = max_reviews if max_reviews is not None else _MAX_REVIEWS

    try:
        async with async_playwright() as p:
            browser = await p.chromium.launch(headless=True, args=_LAUNCH_ARGS)
            context = await browser.new_context(
                user_agent=_UA,
                locale="tr-TR",
                viewport={"width": 1440, "height": 900},
                extra_http_headers={
                    "Accept-Language": "tr-TR,tr;q=0.9,en;q=0.8",
                    "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,image/avif,image/webp,*/*;q=0.8",
                },
            )
            await context.add_init_script(_STEALTH_SCRIPT)

            page = await context.new_page()

            # Set up review response capture BEFORE page load
            captured_urls, captured_bodies = _setup_hb_response_capture(page)

            try:
                await page.goto(url, wait_until="networkidle", timeout=45000)
            except Exception:
                try:
                    await page.goto(url, wait_until="domcontentloaded", timeout=30000)
                except Exception as e:
                    print(f"[hepsiburada] page load error: {e}")

            await page.wait_for_timeout(4000)

            # ── 1. JSON-LD ─────────────────────────────────────────────────
            try:
                for el in await page.query_selector_all('script[type="application/ld+json"]'):
                    try:
                        data = json.loads(await el.inner_text())
                        nodes = data if isinstance(data, list) else [data]
                        for node in nodes:
                            if not isinstance(node, dict) or node.get("@type") != "Product":
                                continue
                            if not product_name and node.get("name"):
                                product_name = str(node["name"]).strip()
                                data_source["productName"] = "jsonld"
                            b = node.get("brand") or {}
                            if not brand and isinstance(b, dict) and b.get("name"):
                                brand = str(b["name"]).strip()
                                data_source["brand"] = "jsonld"
                            img_raw = node.get("image")
                            if not image and img_raw:
                                for c in (img_raw if isinstance(img_raw, list) else [img_raw]):
                                    norm = normalize_image_url(str(c), _BASE)
                                    if norm:
                                        image = norm
                                        data_source["image"] = "jsonld"
                                        break
                            offers = node.get("offers") or {}
                            if isinstance(offers, list):
                                offers = offers[0] if offers else {}
                            if not price and isinstance(offers, dict) and offers.get("price"):
                                p = _format_hb_price(offers["price"])
                                if p:
                                    price = p
                                    data_source["price"] = "jsonld"
                            agg = node.get("aggregateRating") or {}
                            if isinstance(agg, dict):
                                if not rating and agg.get("ratingValue"):
                                    try:
                                        rating = float(str(agg["ratingValue"]).replace(",", "."))
                                        data_source["rating"] = "jsonld"
                                    except Exception:
                                        pass
                                if not review_count and agg.get("reviewCount"):
                                    raw_rc = str(agg["reviewCount"]).replace(".", "").replace(",", "")
                                    if raw_rc.isdigit():
                                        review_count = int(raw_rc)
                                        data_source["reviewCount"] = "jsonld"
                    except Exception:
                        continue
            except Exception:
                pass

            # ── 2. Open Graph / meta tags ──────────────────────────────────
            if not product_name:
                for sel in ['meta[property="og:title"]', 'meta[name="twitter:title"]']:
                    try:
                        el = await page.query_selector(sel)
                        if el:
                            c = await el.get_attribute("content")
                            if c and c.strip():
                                product_name = c.strip()
                                data_source["productName"] = "meta_og"
                                break
                    except Exception:
                        continue

            if not image:
                for sel in [
                    'meta[property="og:image"]',
                    'meta[property="og:image:secure_url"]',
                    'meta[name="twitter:image"]',
                ]:
                    try:
                        el = await page.query_selector(sel)
                        if el:
                            c = await el.get_attribute("content")
                            norm = normalize_image_url(c or "", _BASE)
                            if norm:
                                image = norm
                                data_source["image"] = "meta_og"
                                print(f"[HB-image] ✓ {sel}: {image[:80]}")
                                break
                            else:
                                print(f"[HB-image] {sel}: content={c!r} rejected")
                        else:
                            print(f"[HB-image] {sel}: element not found")
                    except Exception:
                        continue

            if not price:
                for sel in [
                    'meta[property="product:price:amount"]',
                    'meta[name="product:price:amount"]',
                ]:
                    try:
                        el = await page.query_selector(sel)
                        if el:
                            c = await el.get_attribute("content")
                            if c:
                                p = _format_hb_price(c.strip())
                                if p:
                                    price = p
                                    data_source["price"] = "meta_og"
                                    break
                    except Exception:
                        continue

            # ── 3. itemprop attributes ─────────────────────────────────────
            if not product_name:
                for sel in ["[itemprop='name']", "h1[itemprop='name']"]:
                    try:
                        el = await page.query_selector(sel)
                        if el:
                            t = _clean(await el.inner_text() or await el.get_attribute("content"))
                            if t and len(t) > 3:
                                product_name = t
                                data_source["productName"] = "itemprop"
                                break
                    except Exception:
                        continue

            if not image:
                for sel in ["[itemprop='image']", "img[itemprop='image']"]:
                    try:
                        el = await page.query_selector(sel)
                        if el:
                            for attr in ("src", "content", "data-src"):
                                v = await el.get_attribute(attr)
                                if v:
                                    norm = normalize_image_url(v.strip(), _BASE)
                                    if norm:
                                        image = norm
                                        data_source["image"] = "itemprop"
                                        break
                        if image:
                            break
                    except Exception:
                        continue

            if not rating:
                try:
                    el = await page.query_selector("[itemprop='ratingValue']")
                    if el:
                        v = await el.get_attribute("content") or await el.inner_text()
                        rating = float(v.strip().replace(",", "."))
                        data_source["rating"] = "itemprop"
                except Exception:
                    pass

            if not review_count:
                for sel in ["[itemprop='reviewCount']", "[itemprop='ratingCount']"]:
                    try:
                        el = await page.query_selector(sel)
                        if el:
                            v = await el.get_attribute("content") or await el.inner_text()
                            raw_v = v.strip().replace(".", "").replace(",", "")
                            if raw_v.isdigit():
                                review_count = int(raw_v)
                                data_source["reviewCount"] = "itemprop"
                    except Exception:
                        continue

            # ── 4. Hepsiburada-specific DOM selectors ──────────────────────
            if not product_name:
                for sel in [
                    "h1[data-test-id='product-name']",
                    "[data-test-id='product-name']",
                    "[data-testid='product-name']",
                    "h1.product-name",
                    "h1",
                ]:
                    try:
                        el = await page.query_selector(sel)
                        if el:
                            t = _clean((await el.inner_text()).replace("\n", " "))
                            if t and len(t) > 3:
                                product_name = t
                                data_source["productName"] = "dom"
                                break
                    except Exception:
                        continue

            if not price:
                try:
                    _dom_price = await page.evaluate("""
                        () => {
                            %s
                            const sels = [
                                "[data-test-id='price-current-price']",
                                "[data-test-id='price']",
                                "[data-testid='price']",
                                "[itemprop='price']",
                                "span[class*='price']",
                                "[class*='currentPrice']",
                                "[class*='priceValue']"
                            ];
                            for (const sel of sels) {
                                for (const el of document.querySelectorAll(sel)) {
                                    if (inBadContainer(el)) continue;
                                    const v = el.getAttribute('content') || el.innerText || '';
                                    if (v.trim().match(/\\d/)) return v.trim();
                                }
                            }
                            return null;
                        }
                    """ % _JS_BAD_CONTAINER_FN)
                    if _dom_price:
                        p = _format_hb_price(str(_dom_price))
                        if p:
                            price = p
                            data_source["price"] = "dom_filtered"
                            print(f"[scraper] hb price CHOSEN: src=dom_filtered value={price}")
                except Exception:
                    pass

            if not image:
                print(f"[HB-image] URL: {page.url}")
                print(f"[HB-image] json-ld/meta/itemprop all failed — trying DOM strategies")

                # Scroll first to trigger any lazy loading
                try:
                    await page.evaluate("window.scrollBy(0, 500)")
                    await page.wait_for_timeout(1500)
                except Exception:
                    pass

                # Strategy 4: DOM selectors — prefer productimages CDN URLs
                dom_selectors = [
                    "img#productImage",
                    "#productMainImage img",
                    'img[data-test-id="product-image"]',
                    'img[data-test-id*="product-image"]',
                    'img[class*="product-image"]',
                    'img[class*="ProductImage"]',
                    'img[class*="hermes-ProductImage"]',
                    'div[class*="image-gallery"] img',
                    'div[class*="product-detail"] img',
                    'div[id*="productMainImage"] img',
                    'main img[src*="productimages"]',
                    "section img",
                    "main img",
                ]
                for sel in dom_selectors:
                    try:
                        el = await page.query_selector(sel)
                        if el:
                            for attr in ("data-zoom-image", "data-src", "data-original", "src"):
                                v = await el.get_attribute(attr)
                                if v:
                                    # Prefer URLs that are known-good CDN
                                    if "productimages" in v.lower():
                                        norm = normalize_image_url(v.strip(), _BASE)
                                        if norm:
                                            image = norm
                                            data_source["image"] = "dom"
                                            print(f"[HB-image] ✓ STRATEGY 4 DOM {sel!r}: {image[:80]}")
                                            break
                            if not image:
                                for attr in ("data-zoom-image", "data-src", "data-original", "src"):
                                    v = await el.get_attribute(attr)
                                    if v:
                                        norm = normalize_image_url(v.strip(), _BASE)
                                        if norm:
                                            image = norm
                                            data_source["image"] = "dom"
                                            print(f"[HB-image] ✓ STRATEGY 4 DOM fallback {sel!r}: {image[:80]}")
                                            break
                            if not image:
                                ss = await el.get_attribute("srcset")
                                img_ss = parse_srcset(ss, _BASE)
                                if img_ss:
                                    image = img_ss
                                    data_source["image"] = "dom_srcset"
                                    print(f"[HB-image] ✓ STRATEGY 4 srcset {sel!r}: {image[:80]}")
                        if image:
                            break
                    except Exception:
                        continue

                # Strategy 5: scan all imgs for productimages CDN URL
                if not image:
                    try:
                        all_imgs = await page.query_selector_all("img")
                        print(f"[HB-image] strategy 5: scanning {len(all_imgs)} images")
                        for img_el in all_imgs[:50]:
                            for attr in ("src", "data-src", "data-original"):
                                v = await img_el.get_attribute(attr)
                                if v and "productimages" in v.lower():
                                    norm = normalize_image_url(v.strip(), _BASE)
                                    if norm:
                                        image = norm
                                        data_source["image"] = "scan"
                                        print(f"[HB-image] ✓ STRATEGY 5 scan: {image[:80]}")
                                        break
                            if image:
                                break
                    except Exception as e:
                        print(f"[HB-image] strategy 5 error: {e}")

            if not rating:
                for sel in [
                    "[data-test-id='rating']",
                    "[class*='rating-score']",
                    "[class*='ratingScore']",
                    "[class*='star-rating']",
                ]:
                    try:
                        el = await page.query_selector(sel)
                        if el:
                            t = await el.inner_text()
                            m = re.search(r"\b([1-5][.,][0-9])\b", t)
                            if m:
                                rating = float(m.group(1).replace(",", "."))
                                data_source["rating"] = "dom"
                                break
                    except Exception:
                        continue

            # ── Strategy 6: JS eval — CDN-prioritised, handles // URLs ──────
            if not image:
                print(f"[HB-image] strategy 6: JS eval")
                try:
                    result = await page.evaluate("""
                        () => {
                            const BAD = ['logo','icon','svg','placeholder','blank','spinner','badge','favicon'];
                            const CDN = 'productimages.hepsiburada.com';
                            function resolve(s) {
                                if (!s) return '';
                                if (s.startsWith('//')) return 'https:' + s;
                                return s;
                            }
                            const ok = s => {
                                const r = resolve(s);
                                return r && r.startsWith('http') && !BAD.some(b => r.toLowerCase().includes(b));
                            };
                            function bestSrc(img) {
                                for (const attr of ['data-zoom-image','data-src','data-lazy','data-original']) {
                                    const t = resolve(img.getAttribute(attr));
                                    if (ok(t)) return t;
                                }
                                const ss = img.getAttribute('srcset') || '';
                                if (ss) {
                                    const parts = ss.split(',').map(s => s.trim().split(/\\s+/)[0]).filter(Boolean);
                                    for (let i = parts.length - 1; i >= 0; i--) {
                                        const t = resolve(parts[i]);
                                        if (ok(t)) return t;
                                    }
                                }
                                const t = resolve(img.src);
                                return ok(t) ? t : null;
                            }
                            const imgs = Array.from(document.querySelectorAll('img'))
                                .map(img => ({ src: bestSrc(img), w: img.naturalWidth || 0 }))
                                .filter(r => r.src);
                            const cdn = imgs.filter(r => r.src.includes(CDN));
                            const pool = cdn.length > 0 ? cdn : imgs;
                            pool.sort((a, b) => b.w - a.w);
                            return pool.length > 0 ? pool[0].src : null;
                        }
                    """)
                    if result:
                        norm = normalize_image_url(str(result), _BASE)
                        if norm:
                            image = norm
                            data_source["image"] = "js"
                            print(f"[HB-image] ✓ STRATEGY 6 JS eval: {image[:80]}")
                        else:
                            print(f"[HB-image] strategy 6: result not normalizable: {str(result)[:80]}")
                    else:
                        print(f"[HB-image] strategy 6: JS eval returned None")
                except Exception as e:
                    print(f"[HB-image] strategy 6 error: {e}")

            # ── Strategy 7: regex scan of full HTML (last resort) ─────────
            if not image:
                print(f"[HB-image] strategy 7: regex scan of full HTML")
                try:
                    html_content = await page.content()
                    matches = re.findall(
                        r'https?://[^"\'>\s]*productimages[^"\'>\s]*\.(?:jpg|jpeg|png|webp)',
                        html_content, re.IGNORECASE,
                    )
                    if matches:
                        image = matches[0]
                        data_source["image"] = "regex"
                        print(f"[HB-image] ✓ STRATEGY 7 regex: {image[:80]}")
                    else:
                        print(f"[HB-image] strategy 7: no productimages URL in HTML")
                except Exception as e:
                    print(f"[HB-image] strategy 7 error: {e}")

            if not image:
                print(f"[HB-image] ✗ ALL STRATEGIES FAILED")
            print(f"[HB-image] FINAL: image={image!r} source={data_source.get('image')!r}")

            if not price:
                try:
                    _js_price2 = await page.evaluate("""
                        () => {
                            %s
                            const sels = [
                                '[data-test-id="price-current-price"]',
                                '[class*="currentPrice"]',
                                '[itemprop="price"]',
                                'span[class*="price-value"]',
                                'span[class*="product-price"]',
                            ];
                            for (const sel of sels) {
                                for (const el of document.querySelectorAll(sel)) {
                                    if (inBadContainer(el)) continue;
                                    const v = el.getAttribute('content') || el.innerText || '';
                                    if (v.trim().match(/\\d/)) return v.trim();
                                }
                            }
                            return null;
                        }
                    """ % _JS_BAD_CONTAINER_FN)
                    if _js_price2:
                        p = _format_hb_price(str(_js_price2))
                        if p:
                            price = p
                            data_source["price"] = "js_filtered"
                            print(f"[scraper] hb price CHOSEN: src=js_filtered value={price}")
                except Exception:
                    pass

            # ── Price fallback: multi-strategy with [HB-price] logging ──────
            if not price or (isinstance(price, str) and not price.strip()):
                _hb_price_float: float | None = None

                # 1) DOM: indirimli/güncel fiyat (önce bunlara bak)
                for _psel in (
                    'span[data-test-id="price-current-price"]',
                    'div[data-test-id="price-current-price"]',
                    'span[class*="current-price"]',
                    'span[class*="discounted-price"]',
                    'span[class*="sale-price"]',
                    'div[class*="product-price-current"]',
                ):
                    try:
                        for _el in await page.query_selector_all(_psel):
                            if await _is_bad_price_element(_el):
                                print(f"[HB-price] skip other-seller price {_psel}")
                                continue
                            _txt = await _el.inner_text()
                            _v = _extract_hb_price_value(_txt)
                            if _v and _v > 5:
                                _hb_price_float = _v
                                print(f"[HB-price] İNDİRİMLİ dom {_psel}: {_v}")
                                break
                        if _hb_price_float:
                            break
                    except Exception:
                        continue

                # 2) DOM: normal fiyat (fallback)
                if not _hb_price_float:
                    for _psel in (
                        'span[itemprop="price"]',
                        'span[class*="price-value"]',
                        'div[class*="priceContainer"] span',
                        '#offering-price',
                    ):
                        try:
                            for _el in await page.query_selector_all(_psel):
                                if await _is_bad_price_element(_el):
                                    print(f"[HB-price] skip other-seller price {_psel}")
                                    continue
                                _txt = await _el.inner_text()
                                _v = _extract_hb_price_value(_txt)
                                if _v and _v > 5:
                                    _hb_price_float = _v
                                    print(f"[HB-price] NORMAL dom {_psel}: {_v}")
                                    break
                            if _hb_price_float:
                                break
                        except Exception:
                            continue

                # 3) JSON-LD (lowPrice = indirimli önce, price = normal fallback)
                if not _hb_price_float:
                    try:
                        _hb_html_p = await page.content()
                        _hb_soup_p = BeautifulSoup(_hb_html_p, 'html.parser')
                        for script in _hb_soup_p.find_all('script', type='application/ld+json'):
                            try:
                                _d = json.loads(script.string or '{}')
                                for _item in (_d if isinstance(_d, list) else [_d]):
                                    _off = _item.get('offers', {})
                                    if isinstance(_off, list):
                                        _off = _off[0] if _off else {}
                                    _p = _off.get('lowPrice') or _off.get('price')
                                    if _p:
                                        _v = _extract_hb_price_value(_p)
                                        if _v:
                                            _hb_price_float = _v
                                            print(f"[HB-price] json-ld: {_v}")
                                            break
                            except Exception:
                                continue
                            if _hb_price_float:
                                break
                    except Exception as e:
                        print(f"[HB-price] json-ld error: {e}")

                # 4) Meta tag
                if not _hb_price_float:
                    try:
                        _meta_el = await page.query_selector('meta[property="product:price:amount"]')
                        if _meta_el:
                            _mc = await _meta_el.get_attribute('content')
                            _v = _extract_hb_price_value(_mc)
                            if _v:
                                _hb_price_float = _v
                                print(f"[HB-price] meta: {_v}")
                    except Exception:
                        pass

                # 5) Regex scan of full HTML
                if not _hb_price_float:
                    try:
                        _hb_html_p2 = await page.content()
                        _rx_matches = re.findall(r'"price"\s*:\s*"?(\d+[.,]?\d*)"?', _hb_html_p2)
                        for _rm in _rx_matches:
                            _v = _extract_hb_price_value(_rm)
                            if _v and 5 < _v < 500_000:
                                _hb_price_float = _v
                                print(f"[HB-price] regex: {_v}")
                                break
                    except Exception as e:
                        print(f"[HB-price] regex error: {e}")

                if _hb_price_float:
                    price = _format_hb_price(_hb_price_float) or f"{_hb_price_float:g} TL"
                    data_source["price"] = "hb_fallback"
                else:
                    print("[HB-price] ✗ ALL STRATEGIES FAILED")

                print(f"[HB-price] FINAL: {price!r}")

            # Final sanity: never let a merged/malformed HB price reach the UI.
            if price:
                safe_price = _format_hb_price(price)
                if safe_price:
                    if safe_price != price:
                        print(f"[HB-price] sanitized malformed price {price!r} -> {safe_price!r}")
                    price = safe_price
                else:
                    print(f"[HB-price] rejected unsafe price: {price!r}")
                    price = None
                    data_source.pop("price", None)

            # ── Dynamic review limit ───────────────────────────────────────
            # If caller did not pass an explicit max_reviews, compute it from
            # the product's actual review count so we fetch a good sample size.
            if max_reviews is None:
                if not review_count:
                    # Last-chance: parse review count from DOM if JSON-LD missed it
                    try:
                        _rc_html = await page.content()
                        _rc_soup = BeautifulSoup(_rc_html, 'html.parser')
                        for _rc_sel in (
                            '[data-test-id="ratingAndReviewCount"]',
                            'span[class*="ratingCount"]',
                            'a[href*="-yorumlari"]',
                            'div[class*="hermes-RatingPointBox"]',
                        ):
                            _rc_el = _rc_soup.select_one(_rc_sel)
                            if _rc_el:
                                _rc_txt = _rc_el.get_text(strip=True).replace('.', '').replace(',', '')
                                _rc_m = re.search(r'(\d+)', _rc_txt)
                                if _rc_m:
                                    _rc_val = int(_rc_m.group(1))
                                    if _rc_val > 0:
                                        review_count = _rc_val
                                        data_source.setdefault("reviewCount", "dom_rc")
                                        break
                    except Exception:
                        pass
                effective_max_reviews = _calculate_review_limit(review_count)
                print(f"[scraper] hb total_reviews={review_count or 0}, review_limit={effective_max_reviews}")

            # ── 6. Reviews ─────────────────────────────────────────────────
            if effective_max_reviews > 0:
                try:
                    reviews, rating_distribution, reviews_source, reviews_completed, reviews_reason = (
                        await _extract_reviews_hepsiburada(
                            page, url, captured_urls, captured_bodies,
                            review_count, effective_max_reviews, product_name
                        )
                    )
                    data_source["reviews"] = reviews_source
                except Exception as e:
                    print(f"[hepsiburada] review extraction error: {e}")
                    traceback.print_exc()
                    reviews, rating_distribution = [], None
                    reviews_completed, reviews_reason = False, "extraction_error"
                    data_source["reviews"] = "error"
            else:
                reviews_reason = "not_requested"
                data_source["reviews"] = "none"

            # HTML ile ek yorum çekme (BeautifulSoup merge) - Hepsiburada
            try:
                try:
                    await page.evaluate("window.scrollTo(0, document.body.scrollHeight)")
                    await page.wait_for_timeout(2000)
                    for sel in (
                        'a[href*="-yorumlari"]',
                        'button:has-text("Değerlendirmeler")',
                        'a:has-text("Tüm Değerlendirmeler")',
                        '[data-test-id="reviews-tab"]',
                    ):
                        try:
                            el = await page.query_selector(sel)
                            if el:
                                await el.click()
                                await page.wait_for_timeout(3000)
                                break
                        except Exception:
                            continue
                    for _ in range(5):
                        await page.evaluate("window.scrollBy(0, 800)")
                        await page.wait_for_timeout(800)
                except Exception as scroll_err:
                    print(f"[scraper] scroll/tab error: {scroll_err}")

                html_content = await page.content()
                soup_reviews = BeautifulSoup(html_content, 'html.parser')
                html_reviews: list[str] = []

                _hb_review_selectors = [
                    {'class': lambda x: bool(x) and 'hermes-ReviewCard-module' in (' '.join(x) if isinstance(x, list) else x)},
                    {'class': lambda x: bool(x) and 'review-text' in (' '.join(x) if isinstance(x, list) else x)},
                    {'class': lambda x: bool(x) and 'comment-content' in (' '.join(x) if isinstance(x, list) else x)},
                    {'class': lambda x: bool(x) and 'user-review' in (' '.join(x) if isinstance(x, list) else x)},
                    {'class': lambda x: bool(x) and 'review-card' in (' '.join(x) if isinstance(x, list) else x)},
                    {'itemprop': 'reviewBody'},
                    {'data-test-id': 'review-content'},
                    {'data-test-id': 'review-card-text'},
                ]
                for selector in _hb_review_selectors:
                    elements = soup_reviews.find_all(True, selector)
                    for el in elements:
                        text = el.get_text(strip=True, separator=' ')
                        if text and 10 < len(text) < 2000:
                            html_reviews.append(text[:500])
                    if html_reviews:
                        print(f"[scraper] hepsiburada selector matched: {selector}, found={len(html_reviews)}")
                        break

                # JSON-LD review fallback
                if len(html_reviews) < 5:
                    for script in soup_reviews.find_all('script', type='application/ld+json'):
                        try:
                            data = json.loads(script.string or '{}')
                            items = data if isinstance(data, list) else [data]
                            for item in items:
                                reviews_field = item.get('review') or item.get('reviews') or []
                                if isinstance(reviews_field, dict):
                                    reviews_field = [reviews_field]
                                for r in reviews_field:
                                    body = r.get('reviewBody') or r.get('description')
                                    if body and len(body) > 10:
                                        html_reviews.append(body[:500])
                        except Exception:
                            continue

                html_reviews = (
                    list(dict.fromkeys(html_reviews))[:max(50, effective_max_reviews)]
                    if effective_max_reviews > 0 else []
                )
                print(f"[scraper] hepsiburada html_reviews_found={len(html_reviews)}")

                existing_texts = {r.get('text', '')[:80] for r in reviews if isinstance(r, dict)}
                added_html_reviews = 0
                for hr in html_reviews:
                    if hr[:80] not in existing_texts:
                        reviews.append({
                            'id': f'hb_html_{len(reviews)}',
                            'text': hr,
                            'rating': None,
                            'date': None,
                            'user': None,
                            'source': 'html',
                        })
                        existing_texts.add(hr[:80])
                        added_html_reviews += 1
                        if len(reviews) >= effective_max_reviews:
                            break
                if added_html_reviews:
                    if data_source.get("reviews") in {"none", "", None}:
                        data_source["reviews"] = "html"
                    if reviews_reason in {"no_reviews_found", "not_started", "not_requested"}:
                        reviews_reason = "html_fallback"
                print(f"[scraper] hepsiburada after html merge: total reviews={len(reviews)}")
            except Exception as e:
                print(f"[scraper] Hepsiburada HTML parse error: {e}")

            # ── 7. Body regex (last resort) ────────────────────────────────
            try:
                body_text = await page.inner_text("body")

                if not price:
                    m = re.search(r"([\d]{1,3}(?:\.[\d]{3})*,\d{2})\s*TL", body_text)
                    if m:
                        price = m.group(1) + " TL"
                        data_source["price"] = "regex"

                if not rating:
                    m = re.search(r"\b([1-5][.,][0-9])\b", body_text)
                    if m:
                        rating = float(m.group(1).replace(",", "."))
                        data_source["rating"] = "regex"

                if not review_count:
                    rc = _parse_review_count(body_text)
                    if rc is not None:
                        review_count = rc
                        data_source["reviewCount"] = "regex"

                if not product_name:
                    m = re.search(r'<title>([^<]{5,120})</title>', await page.content())
                    if m:
                        t = m.group(1).strip().split(" | ")[0].split(" - ")[0]
                        if t and len(t) > 3:
                            product_name = t
                            data_source["productName"] = "regex_title"

                bc_match = re.search(r"Hepsiburada\s*›\s*([^›\n]+?)(?:\s*›|$)", body_text)
                if bc_match:
                    category = bc_match.group(1).strip()

            except Exception:
                pass

            print(
                f"[hepsiburada] name={product_name!r} brand={brand!r} "
                f"price={price!r} rating={rating} rc={review_count} "
                f"reviews_loaded={len(reviews)} image={'YES' if image else 'NO'}"
            )
            await browser.close()

    except Exception as e:
        print(f"[hepsiburada] Playwright error:")
        traceback.print_exc()

    reviews_loaded = len(reviews)
    review_analytics = compute_review_analytics(reviews, rating_distribution, effective_max_reviews)

    if reviews_loaded > 0:
        review_confidence = "OK"
    elif review_count and review_count > 0:
        review_confidence = "REVIEW_TEXT_MISSING"
    else:
        review_confidence = "NO_REVIEWS"

    review_stats = {
        "reviewCount": review_count,
        "reviewsLoaded": reviews_loaded,
        "dedupedCount": reviews_loaded,
        "completed": reviews_completed,
        "maxReviews": effective_max_reviews,
        "source": data_source.get("reviews", "none"),
        "reason": reviews_reason,
        "confidence": review_confidence,
        "starDistribution": review_analytics["starDistribution"],
        "loadedByStar": review_analytics["loadedByStar"],
        "sampleReviews": review_analytics["sampleReviews"],
    }
    if reviews_loaded == 0 and reviews_reason not in ("no_reviews_found", "not_started"):
        review_stats["error"] = "reviews_could_not_be_loaded"

    return {
        "productName": product_name,
        "brand": brand,
        "category": category,
        "price": price,
        "image": image,
        "rating": rating,
        "reviewCount": review_count,
        "questionCount": question_count,
        "sellerScore": None,
        "sourceUrl": url,
        "sourcePlatform": "Hepsiburada",
        "slugKeywords": [],
        "dataSource": data_source,
        "reviews": reviews,
        "reviewsLoaded": reviews_loaded,
        "reviewsSource": data_source.get("reviews", "none"),
        "ratingDistribution": rating_distribution,
        "reviewStats": review_stats,
    }
