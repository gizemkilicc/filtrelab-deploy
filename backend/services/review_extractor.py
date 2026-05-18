import asyncio
import json
import re
from html import unescape
from urllib.parse import urlparse

from playwright.async_api import async_playwright, TimeoutError as PlaywrightTimeoutError

from .review_analytics import compute_review_analytics


_KEYWORDS = (
    "review", "reviews", "comment", "comments", "rating", "ratings",
    "yorum", "degerlendirme", "değerlendirme", "product-reviews",
)
_TEXT_KEYS = ("text", "comment", "reviewText", "content", "message", "rvwTxt", "description")
_RATING_KEYS = ("rating", "star", "stars", "rate", "score", "ratingValue")
_USER_KEYS = ("user", "nickname", "customerName", "userName", "name", "author")
_DATE_KEYS = ("date", "createdDate", "reviewDate", "commentDate", "createdAt")
_BAD_TEXT_FRAGMENTS = (
    "çerez", "cookie", "sepete ekle", "kargo", "taksit", "favori",
    "değerlendirme yap", "yorum yaz", "ürün açıklaması", "satıcı",
    "kampanya", "gizlilik", "aydınlatma metni", "tüm yorumlar",
    "yorumları incele", "yorumlari incele", "kullanıcılar beğeniyor",
    "kullanicilar begeniyor", "tarafından gönderilecektir", "tarafindan gonderilecektir",
    "kullanma amacı", "kullanma amaci", "ürün güvenliği", "urun guvenligi",
    "ek özellik", "ek ozellik", "hacim", "refill", "alkol içermez",
)
_LAUNCH_ARGS = [
    "--headless=new",
    "--disable-blink-features=AutomationControlled",
    "--no-sandbox",
    "--disable-dev-shm-usage",
    "--disable-gpu",
    "--window-size=1366,900",
    "--ignore-certificate-errors",
]
_STEALTH = """
    Object.defineProperty(navigator, 'webdriver', {get: () => undefined});
    Object.defineProperty(navigator, 'plugins', {get: () => [1, 2, 3, 4, 5]});
    Object.defineProperty(navigator, 'languages', {get: () => ['tr-TR', 'tr', 'en-US', 'en']});
    window.chrome = { runtime: {} };
"""


def _norm_space(value: str | None) -> str:
    text = unescape(str(value or ""))
    text = re.sub(r"Devamını Oku|Devamini Oku|Read more", " ", text, flags=re.IGNORECASE)
    return re.sub(r"\s+", " ", text).strip()


def _is_probable_review_text(text: str) -> bool:
    text = _norm_space(text)
    if len(text) < 20 or len(text) > 2500:
        return False
    low = text.lower()
    if any(fragment in low for fragment in _BAD_TEXT_FRAGMENTS):
        return False
    if re.fullmatch(r"[A-ZÇĞİÖŞÜ]\*\*.*\d{4}", text.strip()):
        return False
    if re.fullmatch(r"[\d.,]+\s+Değerlendirme\s+[\d.,]+\s+Yorum", text.strip(), flags=re.IGNORECASE):
        return False
    if len(set(low.split())) < 4:
        return False
    return bool(re.search(r"[a-zA-ZğüşöçıİĞÜŞÖÇ]", text))


def _parse_rating(value) -> int | None:
    if value is None:
        return None
    if isinstance(value, dict):
        for key in _RATING_KEYS:
            if key in value:
                return _parse_rating(value.get(key))
        return None
    try:
        match = re.search(r"([1-5])(?:[.,]\d+)?", str(value))
        if match:
            rating = int(match.group(1))
            return rating if 1 <= rating <= 5 else None
    except Exception:
        return None
    return None


def _find_first(obj, keys: tuple[str, ...]):
    if not isinstance(obj, dict):
        return None
    lowered = {str(k).lower(): v for k, v in obj.items()}
    for key in keys:
        if key.lower() in lowered:
            value = lowered[key.lower()]
            if isinstance(value, (str, int, float)):
                return value
            if isinstance(value, dict):
                nested = _find_first(value, keys)
                if nested is not None:
                    return nested
    return None


def _review_from_dict(obj: dict, source: str) -> dict | None:
    text = None
    for key in _TEXT_KEYS:
        if key in obj:
            value = obj.get(key)
            if isinstance(value, str) and _is_probable_review_text(value):
                text = _norm_space(value)
                break
    if not text:
        lowered = {str(k).lower(): v for k, v in obj.items()}
        for key in _TEXT_KEYS:
            value = lowered.get(key.lower())
            if isinstance(value, str) and _is_probable_review_text(value):
                text = _norm_space(value)
                break
    if not text:
        return None

    user = _find_first(obj, _USER_KEYS)
    date = _find_first(obj, _DATE_KEYS)
    return {
        "id": str(obj.get("id") or obj.get("reviewId") or obj.get("commentId") or ""),
        "text": text,
        "rating": _parse_rating(_find_first(obj, _RATING_KEYS)),
        "user": _norm_space(user) if user is not None else None,
        "date": _norm_space(date) if date is not None else None,
        "source": source,
    }


def _collect_reviews_recursive(obj, source: str, out: list[dict], max_nodes: int = 12000):
    stack = [obj]
    seen_nodes = 0
    while stack and seen_nodes < max_nodes:
        seen_nodes += 1
        current = stack.pop()
        if isinstance(current, dict):
            review = _review_from_dict(current, source)
            if review:
                out.append(review)
            for value in current.values():
                if isinstance(value, (dict, list)):
                    stack.append(value)
        elif isinstance(current, list):
            stack.extend(current)


def _dedupe_reviews(reviews: list[dict], max_reviews: int) -> list[dict]:
    deduped: list[dict] = []
    seen: set[str] = set()
    for review in reviews:
        text = _norm_space(review.get("text"))
        if not _is_probable_review_text(text):
            continue
        key = re.sub(r"\W+", "", text.lower())[:180]
        if key in seen:
            continue
        seen.add(key)
        clean = dict(review)
        clean["text"] = text
        deduped.append(clean)
        if len(deduped) >= max_reviews:
            break
    return deduped


def _balanced_reviews(reviews: list[dict], max_reviews: int) -> list[dict]:
    if len(reviews) <= max_reviews:
        return reviews
    by_star: dict[int, list[dict]] = {star: [] for star in range(1, 6)}
    unknown: list[dict] = []
    for review in reviews:
        rating = review.get("rating")
        if isinstance(rating, int) and 1 <= rating <= 5:
            by_star[rating].append(review)
        else:
            unknown.append(review)
    balanced: list[dict] = []
    order = [1, 2, 3, 4, 5]
    while len(balanced) < max_reviews and any(by_star.values()):
        for star in order:
            if by_star[star] and len(balanced) < max_reviews:
                balanced.append(by_star[star].pop(0))
    for review in unknown:
        if len(balanced) >= max_reviews:
            break
        balanced.append(review)
    return balanced


def _stats(reviews: list[dict], source: str, max_reviews: int, reason: str = "ok", error: str | None = None) -> dict:
    analytics = compute_review_analytics(reviews, None, max_reviews)
    stats = {
        "reviewCount": None,
        "reviewsLoaded": len(reviews),
        "dedupedCount": len(reviews),
        "completed": len(reviews) < max_reviews,
        "maxReviews": max_reviews,
        "source": source,
        "reason": reason,
        "starDistribution": analytics["starDistribution"],
        "loadedByStar": analytics["loadedByStar"],
        "sampleReviews": analytics["sampleReviews"],
    }
    if error:
        stats["error"] = error
    return stats


def _log_summary(counts: dict[str, int], reviews: list[dict], source: str):
    positive = next((r.get("text", "")[:140] for r in reviews if (r.get("rating") or 0) >= 4), "")
    negative = next((r.get("text", "")[:140] for r in reviews if (r.get("rating") or 0) <= 2), "")
    print(f"[REVIEWS] network={counts.get('network', 0)}")
    print(f"[REVIEWS] embedded_json={counts.get('embedded_json', 0)}")
    print(f"[REVIEWS] dom={counts.get('dom', 0)}")
    print(f"[REVIEWS] html={counts.get('html', 0)}")
    print(f"[REVIEWS] totalLoaded={len(reviews)}")
    print(f"[REVIEWS] deduped={len(reviews)}")
    print(f"[REVIEWS] source={source}")
    print(f"[REVIEWS] samplePositive={positive!r}")
    print(f"[REVIEWS] sampleNegative={negative!r}")


async def _click_review_area(page, platform: str):
    selectors = [
        'text=/Değerlendirme|Değerlendirmeler|Yorumlar|Müşteri Yorumları|Ürün Yorumları/i',
        '[data-testid*="review"]',
        '[data-test-id*="review"]',
        '[class*="review-tab"]',
        '[class*="comment-tab"]',
        'a[href*="yorum"]',
        'a[href*="review"]',
    ]
    if platform == "amazon_tr":
        selectors = [
            'a[data-hook="see-all-reviews-link-foot"]',
            'a[href*="product-reviews"]',
            'text=/Tüm değerlendirmeleri|Tüm yorumları|See all reviews/i',
        ] + selectors
    for selector in selectors:
        try:
            locator = page.locator(selector).first
            if await locator.count() > 0:
                await locator.click(timeout=2500)
                await page.wait_for_timeout(1500)
                return
        except Exception:
            continue


async def _scroll_like_user(page):
    for _ in range(5):
        await page.mouse.wheel(0, 900)
        await page.wait_for_timeout(900)
    for selector in [
        'text=/Daha fazla göster|Daha fazla yorum|Tümünü göster|Devamını oku|Show more/i',
        'button[class*="more"]',
        '[class*="show-more"]',
    ]:
        try:
            locator = page.locator(selector).first
            if await locator.count() > 0:
                await locator.click(timeout=2000)
                await page.wait_for_timeout(800)
        except Exception:
            continue


def _extract_json_blobs_from_html(html: str) -> list:
    blobs = []
    for pattern in [
        r'<script[^>]+id=["\']__NEXT_DATA__["\'][^>]*>(.*?)</script>',
        r'<script[^>]+type=["\']application/ld\+json["\'][^>]*>(.*?)</script>',
    ]:
        for match in re.finditer(pattern, html, flags=re.DOTALL | re.IGNORECASE):
            raw = unescape(match.group(1)).strip()
            try:
                blobs.append(json.loads(raw))
            except Exception:
                pass
    for marker in ("INITIAL_STATE", "__INITIAL_STATE__", "window.__INITIAL_STATE__", "dataLayer"):
        idx = html.find(marker)
        if idx == -1:
            continue
        segment = html[idx: idx + 350000]
        for match in re.finditer(r"(\{.*?\}|\[.*?\])\s*(?:;|</script>)", segment, flags=re.DOTALL):
            raw = match.group(1)
            if len(raw) < 40:
                continue
            try:
                blobs.append(json.loads(raw))
                break
            except Exception:
                continue
    return blobs


async def _extract_dom_reviews(page) -> list[dict]:
    raw = await page.evaluate("""
        () => {
            const selectors = [
                '[data-test-id*="review"]',
                '[data-testid*="review"]',
                '[class*="review"]',
                '[class*="comment"]',
                '[class*="yorum"]'
            ];
            const nodes = Array.from(document.querySelectorAll(selectors.join(','))).slice(0, 600);
            return nodes.map((node) => {
                const text = (node.innerText || node.textContent || '').replace(/\\s+/g, ' ').trim();
                const ratingText = (node.getAttribute('aria-label') || text || '').match(/([1-5])\\s*(?:yıldız|star)|([1-5])\\s*\\/\\s*5/i);
                const rating = ratingText ? parseInt(ratingText[1] || ratingText[2], 10) : null;
                return { text, rating };
            });
        }
    """)
    reviews = []
    for item in raw or []:
        text = item.get("text") if isinstance(item, dict) else ""
        if _is_probable_review_text(text):
            reviews.append({
                "id": "",
                "text": _norm_space(text),
                "rating": _parse_rating(item.get("rating")) if isinstance(item, dict) else None,
                "user": None,
                "date": None,
                "source": "dom",
            })
    return reviews


def _extract_html_reviews(html: str) -> list[dict]:
    reviews = []
    for match in re.finditer(r"[^<>]{20,700}(?:yorum|memnun|beğen|tavsiye|kalite|ürün|kargo)[^<>]{0,700}", html, flags=re.IGNORECASE):
        text = re.sub(r"<[^>]+>", " ", match.group(0))
        text = _norm_space(text)
        if _is_probable_review_text(text):
            reviews.append({"id": "", "text": text, "rating": None, "user": None, "date": None, "source": "html"})
    return reviews


def _amazon_reviews_url(url: str) -> str | None:
    match = re.search(r"/(?:dp|gp/product)/([A-Z0-9]{10})", url)
    if not match:
        return None
    parsed = urlparse(url)
    host = parsed.netloc or "www.amazon.com.tr"
    return f"https://{host}/product-reviews/{match.group(1)}?reviewerType=all_reviews"


async def extract_reviews(url: str, platform: str, max_reviews: int = 1000) -> dict:
    max_reviews = max(1, min(int(max_reviews or 1000), 1000))
    counts = {"network": 0, "embedded_json": 0, "dom": 0, "html": 0}
    network_reviews: list[dict] = []
    embedded_reviews: list[dict] = []
    dom_reviews: list[dict] = []
    html_reviews: list[dict] = []
    source = "none"
    reason = "no_reviews_found"
    error = None

    try:
        async with async_playwright() as p:
            browser = await p.chromium.launch(headless=True, args=_LAUNCH_ARGS)
            context = await browser.new_context(
                user_agent=(
                    "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) "
                    "AppleWebKit/537.36 (KHTML, like Gecko) "
                    "Chrome/124.0.0.0 Safari/537.36"
                ),
                locale="tr-TR",
                viewport={"width": 1366, "height": 900},
                extra_http_headers={"Accept-Language": "tr-TR,tr;q=0.9,en;q=0.8"},
            )
            await context.add_init_script(_STEALTH)
            page = await context.new_page()
            tasks: list[asyncio.Task] = []

            async def handle_response(response):
                response_url = response.url.lower()
                if not any(keyword in response_url for keyword in _KEYWORDS):
                    return
                if response.status >= 400:
                    return
                try:
                    content_type = (response.headers or {}).get("content-type", "")
                    if "json" not in content_type and not response_url.endswith(".json"):
                        return
                    payload = await response.json()
                    collected: list[dict] = []
                    _collect_reviews_recursive(payload, "network", collected)
                    network_reviews.extend(collected)
                except Exception:
                    return

            page.on("response", lambda response: tasks.append(asyncio.create_task(handle_response(response))))

            target_url = _amazon_reviews_url(url) if platform == "amazon_tr" else url
            try:
                await page.goto(target_url or url, wait_until="domcontentloaded", timeout=45000)
            except PlaywrightTimeoutError:
                await page.goto(target_url or url, wait_until="load", timeout=20000)

            await page.wait_for_timeout(2500)
            if platform != "amazon_tr":
                await _click_review_area(page, platform)
            await _scroll_like_user(page)
            if tasks:
                await asyncio.gather(*tasks[:40], return_exceptions=True)

            try:
                title = (await page.title()).lower()
                body_preview = (await page.inner_text("body"))[:800].lower()
                if any(marker in title or marker in body_preview for marker in ("captcha", "robot", "bot check", "enter the characters")):
                    error = "bot_protection"
                    reason = "bot_protection"
            except Exception:
                pass

            html = await page.content()
            for blob in _extract_json_blobs_from_html(html):
                _collect_reviews_recursive(blob, "embedded_json", embedded_reviews)
            dom_reviews = await _extract_dom_reviews(page)
            html_reviews = _extract_html_reviews(html)
            await browser.close()

    except Exception as exc:
        print(f"[REVIEWS] extractor_error={exc}")
        error = error or "extractor_error"
        reason = "extractor_error"

    counts["network"] = len(network_reviews)
    counts["embedded_json"] = len(embedded_reviews)
    counts["dom"] = len(dom_reviews)
    counts["html"] = len(html_reviews)

    candidates = [
        ("network", network_reviews),
        ("embedded_json", embedded_reviews),
        ("dom", dom_reviews),
        ("html", html_reviews),
    ]
    if platform == "amazon_tr":
        candidates = [("dom", dom_reviews), ("network", network_reviews), ("embedded_json", embedded_reviews), ("html", html_reviews)]

    selected_source, selected_reviews = max(candidates, key=lambda item: len(_dedupe_reviews(item[1], max_reviews)))
    reviews = _balanced_reviews(_dedupe_reviews(selected_reviews, max_reviews), max_reviews)
    if reviews:
        source = selected_source
        reason = "ok"
    elif error == "bot_protection":
        source = "none"
        reason = "bot_protection"
    elif any(counts.values()):
        reason = "filtered_out"

    _log_summary(counts, reviews, source)
    return {
        "reviews": reviews,
        "reviewsLoaded": len(reviews),
        "reviewsSource": source,
        "reviewStats": _stats(reviews, source, max_reviews, reason=reason, error=error),
    }
