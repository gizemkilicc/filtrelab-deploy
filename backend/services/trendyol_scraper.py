import os
import re
import json
import asyncio
from urllib.parse import urlparse
from playwright.async_api import async_playwright

TR_MAP = {
    "canlandirici": "Canlandırıcı", "gozenek": "Gözenek", "sikilastirici": "Sıkılaştırıcı",
    "urun": "Ürün", "gunes": "Güneş", "yuz": "Yüz", "sac": "Saç", "bakim": "Bakım",
    "kadin": "Kadın", "erkek": "Erkek", "ayakkabi": "Ayakkabı", "canta": "Çanta",
    "telefon": "Telefon", "kulaklik": "Kulaklık", "bilgisayar": "Bilgisayar",
    "oyuncu": "Oyuncu", "makinesi": "Makinesi", "asit": "Asit", "tonik": "Tonik",
    "glikolik": "Glikolik", "serum": "Serum", "krem": "Krem", "losyon": "Losyon",
    "nemlendirici": "Nemlendirici", "temizleyici": "Temizleyici",
}

_BAD_IMAGE_PATTERNS = ("logo", "icon", "svg", "placeholder", "default", "blank", "spinner", "badge", "banner", "favicon")

_PAGE_SIZE = 50
_MAX_REVIEWS = int(os.getenv("MAX_REVIEWS", "1000"))

_ENDPOINT_TEMPLATES = [
    "https://public.trendyol.com/discovery-web-productgw-service/api/ratings/{pid}?storefrontId=1&culture=tr-TR",
    "https://public-mdc.trendyol.com/discovery-web-productgw-service/api/ratings/{pid}?storefrontId=1&culture=tr-TR",
    "https://public-sdc.trendyol.com/discovery-web-productgw-service/api/ratings/{pid}?storefrontId=1&culture=tr-TR",
    "https://public.trendyol.com/discovery-web-websfxproductreviews-santral/api/product-reviews/{pid}?storefrontId=1&culture=tr-TR",
]


def beautify_turkish(text: str) -> str:
    words = text.split("-")
    beautified = []
    for word in words:
        lower_word = word.lower()
        beautified.append(TR_MAP.get(lower_word, word.capitalize()))
    return " ".join(beautified)


def format_price_turkish(value) -> str:
    try:
        s = str(value).replace(" TL", "").replace("₺", "").strip()
        if "," in s:
            float_val = float(s.replace(".", "").replace(",", "."))
        else:
            float_val = float(s)
        int_part = int(float_val)
        dec_part = round((float_val - int_part) * 100)
        int_str = f"{int_part:,}".replace(",", ".")
        return f"{int_str},{dec_part:02d} TL" if dec_part > 0 else f"{int_str} TL"
    except Exception:
        return str(value)


def _is_valid_image(url: str | None) -> bool:
    if not url or not isinstance(url, str):
        return False
    url = url.strip()
    if not (url.startswith("http://") or url.startswith("https://") or url.startswith("//")):
        return False
    url_lower = url.lower()
    if any(bad in url_lower for bad in _BAD_IMAGE_PATTERNS):
        return False
    return True


def _normalize_image_url(url: str) -> str | None:
    if not url:
        return None
    url = url.strip()
    if url.startswith("//"):
        url = "https:" + url
    elif url.startswith("/"):
        url = "https://www.trendyol.com" + url
    if " " in url and not url.startswith("http"):
        url = url.split(" ")[0]
    return url if _is_valid_image(url) else None


def parse_review_count(text: str) -> int | None:
    for pattern in [
        r'([\d.]+)\s*Değerlendirme',
        r'([\d.]+)\s*Yorum',
        r'([\d]+)\s*yorum',
    ]:
        m = re.search(pattern, text)
        if m:
            raw = m.group(1).replace(".", "")
            if raw.isdigit():
                return int(raw)
    return None


def parse_question_count(text: str) -> int | None:
    for pattern in [
        r'([\d.]+)\s*Soru-Cevap',
        r'([\d.]+)\s*Soru',
    ]:
        m = re.search(pattern, text)
        if m:
            raw = m.group(1).replace(".", "")
            if raw.isdigit():
                return int(raw)
    return None


async def _extract_image_via_js(page) -> str | None:
    try:
        result = await page.evaluate("""
            () => {
                const BAD = ['logo', 'icon', 'svg', 'placeholder', 'blank', 'spinner', 'badge', 'banner'];
                const isBad = src => BAD.some(b => src.toLowerCase().includes(b));
                const isGood = src => src && src.startsWith('http') && !isBad(src);

                function bestSrc(img) {
                    const ss = img.getAttribute('srcset') || '';
                    if (ss) {
                        const tokens = ss.split(',').map(s => s.trim().split(/\\s+/)[0]).filter(Boolean);
                        for (let i = tokens.length - 1; i >= 0; i--) {
                            let t = tokens[i];
                            if (!t.startsWith('http')) t = 'https:' + t;
                            if (isGood(t)) return t;
                        }
                    }
                    for (const attr of ['src', 'data-src', 'data-original', 'data-lazy-src', 'data-zoom-image']) {
                        let v = img.getAttribute(attr) || '';
                        if (!v) continue;
                        if (v.startsWith('//')) v = 'https:' + v;
                        if (v.startsWith('/')) v = 'https://www.trendyol.com' + v;
                        if (isGood(v)) return v;
                    }
                    return null;
                }

                const containers = [
                    '.product-image-container img',
                    '.gallery-container img',
                    '.base-product-image img',
                    '.product-slide img',
                    '.slick-active img',
                    '[class*="product-img"] img',
                    '[class*="gallery"] img',
                ];
                for (const sel of containers) {
                    const imgs = Array.from(document.querySelectorAll(sel));
                    for (const img of imgs) {
                        const src = bestSrc(img);
                        if (src && (src.includes('.jpg') || src.includes('.webp') || src.includes('.png'))) return src;
                    }
                }

                const cdnImgs = Array.from(document.querySelectorAll('img'))
                    .map(img => ({ img, src: bestSrc(img) }))
                    .filter(({ src }) => src && (
                        src.includes('ty-cdn') || src.includes('dsmcdn') ||
                        src.includes('trendyol') || src.includes('cdn')
                    ) && !isBad(src))
                    .sort((a, b) => (b.img.naturalWidth || b.img.width || 0) - (a.img.naturalWidth || a.img.width || 0));

                if (cdnImgs.length > 0) return cdnImgs[0].src;

                const allImgs = Array.from(document.querySelectorAll('img'))
                    .map(img => ({ img, src: bestSrc(img) }))
                    .filter(({ src }) => isGood(src))
                    .sort((a, b) => (b.img.naturalWidth || 0) - (a.img.naturalWidth || 0));

                return allImgs.length > 0 ? allImgs[0].src : null;
            }
        """)
        if result:
            norm = _normalize_image_url(str(result))
            if norm:
                return norm
    except Exception as e:
        print(f"[scraper] JS image extraction error: {e}")
    return None


async def _extract_review_count_via_js(page) -> int | None:
    try:
        result = await page.evaluate("""
            () => {
                const containers = Array.from(document.querySelectorAll([
                    '.rating-line-count',
                    '.rvw-cnt-tx',
                    '.reviewCount',
                    '.ratingCount',
                    '[class*="rating-line"]',
                    '[class*="review-count"]',
                    '[class*="rating-count"]'
                ].join(',')));

                for (const el of containers) {
                    const text = (el.textContent || '').replace(/\\s+/g, ' ').trim();
                    const m = text.match(/(?:^|\\b)([\\d.]+)\\s*(Değerlendirme|Yorum)(?:\\b|$)/i);
                    if (m) return m[1].replace(/\\./g, '');
                }
                return null;
            }
        """)
        if result and str(result).isdigit():
            return int(result)
    except Exception as e:
        print(f"[scraper] JS review count extraction error: {e}")
    return None


async def _extract_rating_via_js(page) -> float | None:
    try:
        result = await page.evaluate("""
            () => {
                const allEls = Array.from(document.querySelectorAll('*'));
                for (const el of allEls) {
                    if (el.children.length > 0) continue;
                    const text = (el.textContent || '').trim();
                    const m = text.match(/^([1-5][.,][0-9])$/);
                    if (m) return m[1].replace(',', '.');
                }
                return null;
            }
        """)
        if result:
            return float(str(result))
    except Exception as e:
        print(f"[scraper] JS rating extraction error: {e}")
    return None


async def _try_get_attr(el, *attrs) -> str | None:
    for attr in attrs:
        try:
            val = await el.get_attribute(attr)
            if val and val.strip():
                return val.strip()
        except Exception:
            continue
    return None


def _extract_product_id(url: str) -> str | None:
    m = re.search(r"-p-(\d+)", url)
    return m.group(1) if m else None


def _parse_review_body(body: dict) -> tuple[list[dict], dict | None, dict]:
    """
    Parse one page of API response.
    Returns (review_objects, rating_distribution, pagination_meta).

    pagination_meta keys (present only when found in response):
      totalCount   – total reviews on the platform for this product
      totalPages   – total number of pages
      currentPage  – page index returned by the API
      hasNextPage  – bool hint from the API
    """
    result_data = body.get("result") or body
    comments_raw = (
        result_data.get("comments")
        or result_data.get("reviews")
        or result_data.get("productReviews")
        or body.get("comments")
        or []
    )
    reviews: list[dict] = []
    for c in (comments_raw or []):
        text = (
            c.get("text") or c.get("content") or
            c.get("reviewText") or c.get("rvwTxt") or
            c.get("comment") or ""
        )
        if not isinstance(text, str) or len(text.strip()) <= 5:
            continue

        raw_id = c.get("id") or c.get("reviewId") or c.get("commentId") or ""
        raw_rating = (
            c.get("rate") or c.get("rating") or c.get("star") or
            c.get("starCount") or c.get("ratingScore")
        )
        raw_date = (
            c.get("createdDate") or c.get("date") or c.get("reviewDate") or
            c.get("userReviewDate") or c.get("lastModifiedDate")
        )
        raw_user = (
            c.get("userFullName") or c.get("userName") or
            c.get("displayName") or c.get("userDisplayName")
        )

        reviews.append({
            "id": str(raw_id) if raw_id else "",
            "text": text.strip(),
            "rating": int(raw_rating) if raw_rating is not None else None,
            "date": str(raw_date) if raw_date else None,
            "user": str(raw_user) if raw_user else None,
            "source": "trendyol_reviews_api",
        })

    dist_raw = (
        (result_data.get("ratingScore") or {}).get("distribution")
        or result_data.get("distribution")
        or {}
    )
    rating_dist = (
        {str(k): int(v) for k, v in dist_raw.items()}
        if isinstance(dist_raw, dict) and len(dist_raw) >= 2 else None
    )

    # ── Pagination metadata ───────────────────────────────────────────────────
    pagination: dict = {}
    for field in ("totalCount", "total", "totalElements", "totalResults", "commentCount"):
        val = result_data.get(field)
        if val is not None:
            try:
                pagination["totalCount"] = int(val)
            except (TypeError, ValueError):
                pass
            break

    for field in ("totalPages", "totalPage", "pageCount"):
        val = result_data.get(field)
        if val is not None:
            try:
                pagination["totalPages"] = int(val)
            except (TypeError, ValueError):
                pass
            break

    for field in ("currentPage", "page", "pageNumber"):
        val = result_data.get(field)
        if val is not None:
            try:
                pagination["currentPage"] = int(val)
            except (TypeError, ValueError):
                pass
            break

    # hasNextPage: some APIs return explicit boolean, others infer from last=false
    has_next = result_data.get("hasNextPage") or result_data.get("hasNext")
    last_page = result_data.get("last")  # Spring-style: last=true means final page
    if has_next is not None:
        pagination["hasNextPage"] = bool(has_next)
    elif last_page is not None:
        pagination["hasNextPage"] = not bool(last_page)

    return reviews, rating_dist, pagination


def _setup_request_capture(page) -> list[str]:
    captured: list[str] = []

    def _on_request(request) -> None:
        url = request.url
        if not any(kw in url for kw in ["rating", "review", "comment", "degerlendirme"]):
            return
        if not any(d in url for d in ["trendyol.com", "public.", "public-mdc", "public-sdc"]):
            return
        if url not in captured:
            captured.append(url)
            print(f"[REVIEWS] intercepted request url={url}")

    page.on("request", _on_request)
    return captured


def _strip_page_params(url: str) -> str:
    url = re.sub(r"[&?]page=\d+", "", url)
    url = re.sub(r"[&?]size=\d+", "", url)
    url = re.sub(r"[&?]pageSize=\d+", "", url)
    if "?" not in url and "&" in url:
        url = url.replace("&", "?", 1)
    return url


def _build_page_url(base_url: str, page_num: int, size: int) -> str:
    sep = "&" if "?" in base_url else "?"
    return f"{base_url}{sep}page={page_num}&size={size}"


async def _refetch_with_status(page, url: str) -> tuple[dict | None, int]:
    try:
        result = await page.evaluate(
            """(endpoint) => fetch(endpoint, {
                headers: {
                    "Accept": "application/json, text/plain, */*",
                    "Accept-Language": "tr-TR,tr;q=0.9,en;q=0.8",
                }
            })
            .then(r => r.json()
                .then(data => [r.status, data])
                .catch(() => [r.status, null])
            )
            .catch(() => [0, null])""",
            url,
        )
        if result and isinstance(result, list) and len(result) == 2:
            return result[1], int(result[0] or 0)
        return None, 0
    except Exception as e:
        print(f"[REVIEWS] re-fetch failed url={url[:80]} error={e}")
        return None, 0


async def _fetch_all_pages(
    page,
    base_url: str,
    review_count: int | None,
    max_reviews: int,
) -> tuple[list[dict], dict | None, bool, str, int | None]:
    """
    Paginate from page=0, collecting review objects until max_reviews or no more data.
    Returns (reviews, rating_distribution, completed, reason, api_total_count).

    completed=True  → stopped because all reviews were loaded (no more exist)
    completed=False → stopped early (maxReviews_reached, rate_limited, platform_limit, etc.)

    Reasons:
      no_more_pages        – API returned empty pages; loaded count matches api total
      maxReviews_reached   – hit our own MAX_REVIEWS cap
      rate_limited         – 403/429
      empty_response       – no body at all
      duplicate_loop       – API looped/repeated pages (detected via all-duplicate page)
      platform_limit_reached – API stopped early despite reporting more reviews
      pagination_incomplete  – API said no more pages but totalCount > loaded
    """
    all_reviews: list[dict] = []
    seen: set[str] = set()
    rating_dist: dict | None = None
    reason = "no_more_pages"
    api_total_count: int | None = None
    api_total_pages: int | None = None

    target = min(review_count if review_count else max_reviews, max_reviews)

    if review_count:
        print(f"[REVIEWS] reviewCount={review_count}")
    print(f"[REVIEWS] maxReviews={max_reviews}")

    # ── Probe for larger page size (100) ────────────────────────────────────
    actual_page_size = _PAGE_SIZE
    probe_url_100 = _build_page_url(base_url, 0, 100)
    probe_body_100, probe_status_100 = await _refetch_with_status(page, probe_url_100)
    if probe_status_100 == 200 and probe_body_100:
        probe_reviews_100, _, probe_meta_100 = _parse_review_body(probe_body_100)
        if len(probe_reviews_100) > _PAGE_SIZE:
            actual_page_size = 100
            print(f"[REVIEWS] pageSize=100 supported, switching")
        if probe_meta_100.get("totalCount") is not None:
            api_total_count = probe_meta_100["totalCount"]
        if probe_meta_100.get("totalPages") is not None:
            api_total_pages = probe_meta_100["totalPages"]
        if api_total_count:
            print(f"[REVIEWS] API totalCount={api_total_count} totalPages={api_total_pages}")

    page_num = 0
    consecutive_empty = 0

    while len(all_reviews) < target:
        url = _build_page_url(base_url, page_num, actual_page_size)
        body, status = await _refetch_with_status(page, url)

        if status in (403, 429):
            print(f"[REVIEWS] page={page_num} status={status} rate_limited — stopping with {len(all_reviews)} reviews")
            reason = "rate_limited"
            break

        if not body:
            print(f"[REVIEWS] page={page_num} status={status or 'no-body'} — stopping")
            reason = "empty_response"
            break

        page_reviews, page_dist, page_meta = _parse_review_body(body)
        loaded_this_page = len(page_reviews)

        # Update pagination metadata from first page that has it
        if page_meta.get("totalCount") is not None and api_total_count is None:
            api_total_count = page_meta["totalCount"]
            api_total_pages = page_meta.get("totalPages")
            print(f"[REVIEWS] API totalCount={api_total_count} totalPages={api_total_pages}")

        if page_dist and not rating_dist:
            rating_dist = page_dist

        # Build log line with all available metadata
        meta_log = f"page={page_num} loaded={loaded_this_page} total={len(all_reviews)}"
        if page_meta.get("currentPage") is not None:
            meta_log += f" apiCurrentPage={page_meta['currentPage']}"
        if page_meta.get("totalPages") is not None:
            meta_log += f" apiTotalPages={page_meta['totalPages']}"
        if page_meta.get("totalCount") is not None:
            meta_log += f" apiTotalCount={page_meta['totalCount']}"
        if page_meta.get("hasNextPage") is not None:
            meta_log += f" hasNextPage={page_meta['hasNextPage']}"
        print(f"[REVIEWS] {meta_log}")

        if not page_reviews:
            consecutive_empty += 1
            # Detect platform limit: API says more reviews exist but sent empty page
            if api_total_count is not None and len(all_reviews) < api_total_count:
                print(
                    f"[REVIEWS WARNING] platform limit reached: "
                    f"apiTotalCount={api_total_count} but got empty page={page_num} "
                    f"with only {len(all_reviews)} loaded"
                )
                reason = "platform_limit_reached"
                break
            if consecutive_empty >= 2:
                reason = "no_more_pages"
                break
            page_num += 1
            continue

        consecutive_empty = 0
        added = 0
        for r in page_reviews:
            dedup_key = r["id"] if r["id"] else r["text"][:80]
            if dedup_key not in seen:
                seen.add(dedup_key)
                all_reviews.append(r)
                added += 1

        if added == 0:
            # All items were duplicates — API is looping (hidden pagination ceiling)
            if api_total_count is not None and len(all_reviews) < api_total_count:
                print(
                    f"[REVIEWS WARNING] platform limit reached (duplicate loop): "
                    f"apiTotalCount={api_total_count} but all items on page={page_num} already seen, "
                    f"loaded={len(all_reviews)}"
                )
                reason = "platform_limit_reached"
            else:
                reason = "duplicate_loop"
            break

        if len(all_reviews) >= target:
            reason = "maxReviews_reached"
            break

        # hasNextPage=False from API → stop (but check api total first)
        if page_meta.get("hasNextPage") is False:
            reason = "no_more_pages"
            break

        page_num += 1
        await asyncio.sleep(0.1)

    total = len(all_reviews)

    # ── Final completion assessment ──────────────────────────────────────────
    # If we stopped with "no_more_pages" but API says totalCount > loaded → incomplete
    if reason == "no_more_pages" and api_total_count is not None and total < api_total_count:
        print(
            f"[REVIEWS WARNING] pagination_incomplete: "
            f"apiTotalCount={api_total_count} > loaded={total} "
            f"(platform likely caps accessible pages)"
        )
        reason = "pagination_incomplete"

    completed = reason == "no_more_pages"

    print(f"[REVIEWS] totalLoaded={total}")
    print(f"[REVIEWS] deduped={total}")
    if api_total_count is not None:
        print(f"[REVIEWS] apiTotalCount={api_total_count}")
    print(f"[REVIEWS] completed={completed}")
    print(f"[REVIEWS] reason={reason}")

    return all_reviews, rating_dist, completed, reason, api_total_count


async def _find_working_endpoint(page, product_id: str) -> str | None:
    for template in _ENDPOINT_TEMPLATES:
        base_url = template.format(pid=product_id)
        probe_url = _build_page_url(base_url, 0, _PAGE_SIZE)
        print(f"[REVIEWS] endpoint tried={probe_url}")
        body, status = await _refetch_with_status(page, probe_url)
        if status == 200 and body:
            reviews, _, meta = _parse_review_body(body)
            print(f"[REVIEWS] status={status} loaded={len(reviews)} meta={meta}")
            if reviews:
                return base_url
        else:
            print(f"[REVIEWS] status={status or 'failed'}")
    return None


async def _extract_reviews_trendyol(
    page,
    captured_urls: list[str],
    product_id: str | None,
    review_count: int | None,
    max_reviews: int,
) -> tuple[list[dict], dict | None, str, bool, str, int | None]:
    """
    Master review extractor with full pagination.
    Returns (reviews, rating_distribution, source, completed, reason, api_total_count).
    """
    print(f"[REVIEWS] productId={product_id!r} knownReviewCount={review_count}")
    print(f"[REVIEWS] intercepted {len(captured_urls)} candidate URLs")

    # ── Strategy 1: intercepted URLs → strip page params → paginate ─────────
    for captured in captured_urls[:5]:
        base_url = _strip_page_params(captured)
        probe_url = _build_page_url(base_url, 0, _PAGE_SIZE)
        body, status = await _refetch_with_status(page, probe_url)
        if status == 200 and body:
            probe_reviews, _, _ = _parse_review_body(body)
            if probe_reviews:
                print(f"[REVIEWS] using intercepted base_url={base_url[:80]}")
                reviews, dist, completed, reason, api_total = await _fetch_all_pages(
                    page, base_url, review_count, max_reviews
                )
                if reviews:
                    source = "intercepted_rate_limited" if reason == "rate_limited" else "intercepted"
                    return reviews, dist, source, completed, reason, api_total

    # ── Strategy 2: known endpoint templates → paginate ──────────────────────
    if product_id:
        base_url = await _find_working_endpoint(page, product_id)
        if base_url:
            reviews, dist, completed, reason, api_total = await _fetch_all_pages(
                page, base_url, review_count, max_reviews
            )
            if reviews:
                source = "api_rate_limited" if reason == "rate_limited" else "trendyol_reviews_api"
                return reviews, dist, source, completed, reason, api_total

    # ── Strategy 3: DOM fallback (single page, no pagination) ────────────────
    tab_selectors = [
        'button:has-text("Değerlendirmeler")',
        'a:has-text("Değerlendirmeler")',
        '[class*="review-tab"]',
        '[class*="ReviewTab"]',
        'a[href*="degerlendirmeler"]',
        'a[href*="yorumlar"]',
        '[data-testid*="review"]',
        '[class*="tab"]:has-text("Yorum")',
    ]
    for sel in tab_selectors:
        try:
            el = await page.query_selector(sel)
            if el:
                await el.scroll_into_view_if_needed()
                await el.click()
                await page.wait_for_timeout(2000)
                print(f"[REVIEWS] clicked tab sel={sel!r}")
                break
        except Exception:
            continue

    for pct in [0.5, 0.7, 0.85, 1.0]:
        await page.evaluate(f"window.scrollTo(0, document.body.scrollHeight * {pct})")
        await page.wait_for_timeout(600)

    raw = await page.evaluate("""
        () => {
            const sels = [
                '.pr-rvw-c .rvw-txt', '.pr-rvw-c',
                '.review-card .description',
                '[class*="rvw-txt"]', '[class*="reviewText"]',
                '[class*="review-text"]', '[class*="ReviewContent"]',
                '[class*="comment-text"]', '[class*="commentText"]',
                '.productComments p',
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
            return Array.from(texts);
        }
    """)
    dom_texts = [r for r in (raw or []) if isinstance(r, str) and len(r.strip()) > 5]
    dom_reviews: list[dict] = [
        {"id": "", "text": t, "rating": None, "date": None, "user": None, "source": "trendyol_dom"}
        for t in dom_texts
    ]

    dist_raw = await page.evaluate("""
        () => {
            const dist = {};
            for (const el of document.querySelectorAll(
                '[class*="rating-bar"],[class*="ratingBar"],[class*="star-count"],[class*="starCount"]'
            )) {
                const m = (el.textContent || '').match(/(\\d)\\s*[Yy]ıldız[^\\d]*(\\d+)/);
                if (m) dist[m[1]] = parseInt(m[2], 10);
            }
            if (Object.keys(dist).length < 2) {
                for (const el of document.querySelectorAll('[aria-label]')) {
                    const m = (el.getAttribute('aria-label') || '').match(/(\\d)\\s*[Yy]ıldız[^\\d]*(\\d+)/);
                    if (m) dist[m[1]] = parseInt(m[2], 10);
                }
            }
            return Object.keys(dist).length >= 2 ? dist : null;
        }
    """)
    rating_dist = (
        {str(k): int(v) for k, v in dist_raw.items()}
        if isinstance(dist_raw, dict) and len(dist_raw) >= 2 else None
    )

    print(f"[REVIEWS] loaded={len(dom_reviews)} source=dom")
    if review_count and review_count > 0 and not dom_reviews:
        print(f"[REVIEWS ERROR] reviewCount={review_count} exists but no reviews loaded via any strategy")

    if dom_reviews:
        return dom_reviews, rating_dist, "dom", False, "dom_fallback", None
    return [], rating_dist, "none", False, "no_reviews_found", None


async def scrape_trendyol_product(url: str, max_reviews: int | None = None) -> dict:
    parsed_url = urlparse(url)
    domain = parsed_url.netloc.lower()
    path_segments = [seg for seg in parsed_url.path.strip("/").split("/") if seg]

    effective_max_reviews = max_reviews if max_reviews is not None else _MAX_REVIEWS

    product_name = None
    brand = None
    price = None
    image = None
    rating = None
    review_count = None
    question_count = None
    seller_score = None
    category = "Genel"
    slug_keywords = []
    reviews: list[dict] = []
    rating_distribution: dict | None = None

    data_source = {
        "productName": "fallback",
        "price": "fallback",
        "image": "fallback",
        "rating": "fallback",
        "reviewCount": "fallback",
        "questionCount": "fallback",
        "sellerScore": "fallback",
    }

    if "trendyol.com" in domain and len(path_segments) >= 2:
        brand = beautify_turkish(path_segments[0])
        data_source["brand"] = "url_slug"
        slug_part = path_segments[1]
        if "-p-" in slug_part:
            slug_part = slug_part.split("-p-")[0]
        slug_keywords = slug_part.split("-")
        product_name = beautify_turkish(slug_part)

    reviews_completed = False
    reviews_reason = "not_started"

    try:
        async with async_playwright() as p:
            browser = await p.chromium.launch(
                headless=True,
                args=[
                    "--headless=new",
                    "--disable-blink-features=AutomationControlled",
                    "--no-sandbox",
                    "--disable-dev-shm-usage",
                    "--disable-gpu",
                    "--window-size=1280,900",
                    "--ignore-certificate-errors",
                ],
            )
            context = await browser.new_context(
                user_agent=(
                    "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) "
                    "AppleWebKit/537.36 (KHTML, like Gecko) "
                    "Chrome/124.0.0.0 Safari/537.36"
                ),
                locale="tr-TR",
                viewport={"width": 1280, "height": 900},
                extra_http_headers={"Accept-Language": "tr-TR,tr;q=0.9,en;q=0.8"},
            )
            await context.add_init_script("""
                Object.defineProperty(navigator, 'webdriver', {get: () => undefined});
                Object.defineProperty(navigator, 'plugins', {get: () => [1, 2, 3, 4, 5]});
                Object.defineProperty(navigator, 'languages', {get: () => ['tr-TR', 'tr', 'en-US', 'en']});
                window.chrome = { runtime: {} };
            """)
            page = await context.new_page()
            captured_urls = _setup_request_capture(page)

            try:
                await page.goto(url, wait_until="networkidle", timeout=45000)
            except Exception:
                try:
                    await page.goto(url, wait_until="domcontentloaded", timeout=30000)
                except Exception as e:
                    print(f"[scraper] Page load error: {e}")

            await page.wait_for_timeout(3000)

            # ── 1. JSON-LD ─────────────────────────────────────────────────
            try:
                for el in await page.query_selector_all('script[type="application/ld+json"]'):
                    try:
                        raw = await el.inner_text()
                        data = json.loads(raw)
                        items = data if isinstance(data, list) else [data]
                        for item in items:
                            if item.get("@type") not in ("Product", "product"):
                                continue
                            if not product_name and item.get("name"):
                                product_name = item["name"].strip()
                                data_source["productName"] = "jsonld"
                            if not brand and item.get("brand", {}).get("name"):
                                brand = item["brand"]["name"].strip()
                                data_source["brand"] = "jsonld"
                            if not image and item.get("image"):
                                img_raw = item["image"]
                                candidates = img_raw if isinstance(img_raw, list) else [img_raw]
                                for c in candidates:
                                    norm = _normalize_image_url(str(c))
                                    if norm:
                                        image = norm
                                        data_source["image"] = "jsonld"
                                        break
                            offers = item.get("offers") or {}
                            if isinstance(offers, list):
                                offers = offers[0] if offers else {}
                            if not price and offers.get("price"):
                                price = format_price_turkish(offers["price"])
                                data_source["price"] = "jsonld"
                            agg = item.get("aggregateRating") or {}
                            if not rating and agg.get("ratingValue"):
                                rating = float(str(agg["ratingValue"]).replace(",", "."))
                                data_source["rating"] = "jsonld"
                            if not review_count and agg.get("reviewCount"):
                                rc_raw = str(agg["reviewCount"]).replace(".", "")
                                if rc_raw.isdigit():
                                    review_count = int(rc_raw)
                                    data_source["reviewCount"] = "jsonld"
                    except Exception:
                        continue
            except Exception:
                pass

            # ── 2. Meta tags ───────────────────────────────────────────────
            try:
                if not product_name:
                    el = await page.query_selector('meta[property="og:title"]')
                    if el:
                        c = await el.get_attribute("content")
                        if c:
                            product_name = c.strip()
                            data_source["productName"] = "meta"

                if not image:
                    for sel in [
                        'meta[property="og:image"]',
                        'meta[name="twitter:image"]',
                        'meta[name="twitter:image:src"]',
                    ]:
                        el = await page.query_selector(sel)
                        if el:
                            c = await el.get_attribute("content")
                            norm = _normalize_image_url(c)
                            if norm:
                                image = norm
                                data_source["image"] = "meta"
                                break

                if not price:
                    el = await page.query_selector('meta[property="product:price:amount"]')
                    if el:
                        c = await el.get_attribute("content")
                        if c:
                            price = format_price_turkish(c.strip())
                            data_source["price"] = "meta"
            except Exception:
                pass

            # ── 3. DOM selectors ───────────────────────────────────────────
            if not product_name or data_source["productName"] == "fallback":
                for sel in [
                    "h1.pr-new-br",
                    '[data-testid*="product-title"]',
                    "h1.product-name",
                    ".product-name h1",
                    "h1",
                ]:
                    try:
                        el = await page.query_selector(sel)
                        if el:
                            text = (await el.inner_text()).replace("\n", " ").strip()
                            if text and len(text) > 5:
                                product_name = text
                                data_source["productName"] = "dom"
                                brand_inner = await el.query_selector("a, span")
                                if brand_inner:
                                    b = (await brand_inner.inner_text()).strip()
                                    if b:
                                        brand = b
                                        data_source["brand"] = "dom"
                                break
                    except Exception:
                        continue

            if not price or data_source["price"] == "fallback":
                for sel in [
                    ".prc-dsc",
                    ".prc-slg",
                    ".product-price-container",
                    '[data-testid*="price"]',
                    ".pr-bx-nm",
                    ".prc-box-dscntd",
                ]:
                    try:
                        el = await page.query_selector(sel)
                        if el:
                            p_text = (await el.inner_text()).strip()
                            if p_text:
                                clean = p_text.replace(" TL", "").replace("₺", "").strip()
                                price = format_price_turkish(clean)
                                data_source["price"] = "dom"
                                break
                    except Exception:
                        continue

            if not image or data_source["image"] == "fallback":
                img_selectors = [
                    ".product-image-container img",
                    ".gallery-container img",
                    ".base-product-image img",
                    ".product-slide img",
                    ".slick-active img",
                    ".photo-carousel img",
                    '[class*="product-img"] img',
                    '[class*="gallery"] img',
                    'img[class*="detail"]',
                    'img[class*="product"]',
                ]
                for sel in img_selectors:
                    try:
                        el = await page.query_selector(sel)
                        if el:
                            src = await _try_get_attr(el, "src", "data-src", "data-original", "data-lazy-src")
                            if not src:
                                ss = await el.get_attribute("srcset")
                                if ss:
                                    src = ss.split(",")[0].strip().split(" ")[0]
                            norm = _normalize_image_url(src)
                            if norm:
                                image = norm
                                data_source["image"] = "dom"
                                break
                    except Exception:
                        continue

            if not image or data_source["image"] == "fallback":
                js_img = await _extract_image_via_js(page)
                if js_img:
                    image = js_img
                    data_source["image"] = "js"

            if not rating or data_source["rating"] == "fallback":
                for sel in [".rating-score", ".ratings", '[class*="rating"]', ".ratingScore"]:
                    try:
                        el = await page.query_selector(sel)
                        if el:
                            r_text = await el.inner_text()
                            r_match = re.search(r"\b([1-5][.,][0-9])\b", r_text)
                            if r_match:
                                rating = float(r_match.group(1).replace(",", "."))
                                data_source["rating"] = "dom"
                                break
                    except Exception:
                        continue

            if not rating or data_source["rating"] == "fallback":
                r_js = await _extract_rating_via_js(page)
                if r_js:
                    rating = r_js
                    data_source["rating"] = "js"

            if not review_count or data_source["reviewCount"] == "fallback":
                for sel in [
                    ".rating-line-count",
                    ".rvw-cnt-tx",
                    ".reviewCount",
                    ".ratingCount",
                    '[class*="rating-line"]',
                    '[class*="review-count"]',
                    '[class*="rating-count"]',
                ]:
                    try:
                        el = await page.query_selector(sel)
                        if el:
                            rev_text = await el.inner_text()
                            rc = parse_review_count(rev_text)
                            if rc is not None:
                                review_count = rc
                                data_source["reviewCount"] = "dom"
                                break
                    except Exception:
                        continue

            if not review_count or data_source["reviewCount"] == "fallback":
                rc_js = await _extract_review_count_via_js(page)
                if rc_js is not None:
                    review_count = rc_js
                    data_source["reviewCount"] = "js"

            if not question_count or data_source["questionCount"] == "fallback":
                for sel in [
                    '[data-testid*="question"]',
                    '[class*="question-count"]',
                    '[class*="answered-question"]',
                ]:
                    try:
                        el = await page.query_selector(sel)
                        if el:
                            q_text = await el.inner_text()
                            qc = parse_question_count(q_text)
                            if qc is not None:
                                question_count = qc
                                data_source["questionCount"] = "dom"
                                break
                    except Exception:
                        continue

            try:
                s_el = await page.query_selector(
                    '.seller-store-score, [data-testid="seller-score"]'
                )
                if s_el:
                    s_text = await s_el.inner_text()
                    s_match = re.search(r"(\d+[.,]\d+)", s_text)
                    if s_match:
                        seller_score = float(s_match.group(1).replace(",", "."))
                        data_source["sellerScore"] = "dom"
            except Exception:
                pass

            question_count = None
            data_source["questionCount"] = "fallback"

            try:
                crumbs = await page.query_selector_all(".breadcrumb-item")
                if crumbs:
                    texts = [await c.inner_text() for c in crumbs]
                    category = " / ".join([t.strip() for t in texts if t.strip()])
            except Exception:
                pass

            # ── 4. Reviews ─────────────────────────────────────────────────
            product_id = _extract_product_id(url)
            (
                reviews, rating_distribution, reviews_source,
                reviews_completed, reviews_reason, reviews_api_total,
            ) = await _extract_reviews_trendyol(
                page, captured_urls, product_id, review_count, effective_max_reviews
            )
            data_source["reviews"] = reviews_source

            # ── 5. Full body regex (last resort for product data) ───────────
            needs_body = not price or not rating or not image
            if needs_body:
                try:
                    body_text = await page.inner_text("body")

                    if not price or data_source["price"] == "fallback":
                        m = re.search(r"([\d]{1,3}(?:\.[\d]{3})*,\d{2})\s*TL", body_text)
                        if m:
                            price = m.group(1) + " TL"
                            data_source["price"] = "regex"

                    if not rating or data_source["rating"] == "fallback":
                        m = re.search(r"\b([1-5][.,][0-9])\b", body_text)
                        if m:
                            rating = float(m.group(1).replace(",", "."))
                            data_source["rating"] = "regex"

                except Exception:
                    pass

            if data_source.get("reviewCount") in {"regex", "body_regex", "fallback"}:
                if review_count is not None:
                    print(f"[COUNT SOURCE] rejected reviewCount={review_count} source={data_source.get('reviewCount')}")
                review_count = None
                data_source["reviewCount"] = "fallback"
            if data_source.get("questionCount") in {"regex", "body_regex", "fallback"}:
                question_count = None
                data_source["questionCount"] = "fallback"

            print(f"[COUNT SOURCE] reviewCount={review_count} source={data_source.get('reviewCount')}")
            print(f"[COUNT SOURCE] questionCount={question_count} source={data_source.get('questionCount')}")
            print(
                f"[scraper] name={product_name!r} brand={brand!r} "
                f"price={price!r} rating={rating} reviewCount={review_count} "
                f"image={'YES' if image else 'NONE'} sources={data_source}"
            )

            await browser.close()

    except Exception as e:
        print(f"[scraper] Playwright execution error: {e}")

    reviews_loaded = len(reviews)

    # Transparent warning for platform-capped pagination
    if reviews_reason in ("platform_limit_reached", "pagination_incomplete"):
        platform_cap = reviews_api_total or review_count
        print(
            f"[REVIEWS WARNING] platform limit reached: "
            f"apiTotalCount={reviews_api_total} reviewCount={review_count} "
            f"loaded={reviews_loaded} reason={reviews_reason}"
        )

    review_stats = {
        "reviewCount": review_count,
        "reviewsLoaded": reviews_loaded,
        "dedupedCount": reviews_loaded,
        "completed": reviews_completed,
        "maxReviews": effective_max_reviews,
        "source": data_source.get("reviews", "none"),
        "reason": reviews_reason,
    }
    if reviews_api_total is not None:
        review_stats["apiTotalCount"] = reviews_api_total
    if reviews_reason in ("platform_limit_reached", "pagination_incomplete"):
        review_stats["platformLimitReached"] = True
    if reviews_loaded == 0 and reviews_reason not in ("no_reviews_found", "not_started"):
        review_stats["error"] = "reviews_could_not_be_loaded"

    return {
        "sourceUrl": url,
        "sourcePlatform": "Trendyol" if "trendyol" in domain else "Web",
        "productName": product_name,
        "brand": brand,
        "category": category,
        "price": price,
        "image": image,
        "rating": rating,
        "reviewCount": review_count,
        "questionCount": question_count,
        "sellerScore": seller_score,
        "slugKeywords": slug_keywords,
        "dataSource": data_source,
        "reviews": reviews,
        "reviewsLoaded": reviews_loaded,
        "reviewsSource": data_source.get("reviews", "none"),
        "ratingDistribution": rating_distribution,
        "reviewStats": review_stats,
    }
