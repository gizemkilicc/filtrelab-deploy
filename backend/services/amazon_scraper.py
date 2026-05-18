"""
Amazon.com.tr scraper.

Uses JSON-LD and embedded page state for product data.
Reviews are NOT extracted — Amazon's bot-protection blocks review API calls
from headless browsers without valid session cookies.
"""

import re
import json
from urllib.parse import urlparse
from playwright.async_api import async_playwright


def _extract_asin(url: str) -> str | None:
    """Extract ASIN from Amazon URL: /dp/B08XYZ or /gp/product/B08XYZ"""
    m = re.search(r"/(?:dp|gp/product)/([A-Z0-9]{10})", url)
    return m.group(1) if m else None


def _format_price(value) -> str | None:
    try:
        s = str(value).strip()
        # Remove currency symbols
        s = re.sub(r"[₺TL$€£\s]", "", s).strip()
        # Turkish format: 1.234,56 → keep as-is formatted
        if re.match(r"^\d{1,3}(?:\.\d{3})*,\d{2}$", s):
            return s + " TL"
        # Plain number
        f = float(s.replace(",", "."))
        int_part = int(f)
        dec_part = round((f - int_part) * 100)
        int_str = f"{int_part:,}".replace(",", ".")
        return f"{int_str},{dec_part:02d} TL" if dec_part > 0 else f"{int_str} TL"
    except Exception:
        return None


async def scrape_amazon_product(url: str, max_reviews: int | None = None) -> dict:
    parsed_url = urlparse(url)
    domain = parsed_url.netloc.lower()

    asin = _extract_asin(url)
    product_name = None
    brand = None
    price = None
    image = None
    rating = None
    review_count = None
    category = "Genel"
    slug_keywords = []

    data_source: dict = {
        "productName": "fallback",
        "price": "fallback",
        "image": "fallback",
        "rating": "fallback",
        "reviewCount": "fallback",
        "questionCount": "fallback",
        "sellerScore": "fallback",
    }

    print(f"[AMAZON] asin={asin!r} url={url[:80]!r}")

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

            try:
                await page.goto(url, wait_until="networkidle", timeout=45000)
            except Exception:
                try:
                    await page.goto(url, wait_until="domcontentloaded", timeout=30000)
                except Exception as e:
                    print(f"[AMAZON] page load error: {e}")

            await page.wait_for_timeout(3000)

            # ── 1. JSON-LD ──────────────────────────────────────────────────
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
                                img = item["image"]
                                if isinstance(img, list):
                                    img = img[0]
                                if isinstance(img, str) and img.startswith("http"):
                                    image = img
                                    data_source["image"] = "jsonld"
                            offers = item.get("offers") or {}
                            if isinstance(offers, list):
                                offers = offers[0] if offers else {}
                            if not price and offers.get("price"):
                                formatted = _format_price(offers["price"])
                                if formatted:
                                    price = formatted
                                    data_source["price"] = "jsonld"
                            agg = item.get("aggregateRating") or {}
                            if not rating and agg.get("ratingValue"):
                                try:
                                    rating = float(str(agg["ratingValue"]).replace(",", "."))
                                    data_source["rating"] = "jsonld"
                                except Exception:
                                    pass
                            if not review_count and agg.get("reviewCount"):
                                rc_raw = str(agg["reviewCount"]).replace(".", "").replace(",", "")
                                if rc_raw.isdigit():
                                    review_count = int(rc_raw)
                                    data_source["reviewCount"] = "jsonld"
                    except Exception:
                        continue
            except Exception:
                pass

            # ── 2. Meta tags ────────────────────────────────────────────────
            try:
                if not product_name:
                    for sel in ['meta[name="title"]', 'meta[property="og:title"]']:
                        el = await page.query_selector(sel)
                        if el:
                            c = await el.get_attribute("content")
                            if c and len(c.strip()) > 3:
                                product_name = c.strip()
                                data_source["productName"] = "meta"
                                break
                if not image:
                    for sel in ['meta[property="og:image"]', 'meta[name="twitter:image"]']:
                        el = await page.query_selector(sel)
                        if el:
                            c = await el.get_attribute("content")
                            if c and c.startswith("http"):
                                image = c.strip()
                                data_source["image"] = "meta"
                                break
            except Exception:
                pass

            # ── 3. DOM selectors ────────────────────────────────────────────
            if not product_name or data_source["productName"] == "fallback":
                for sel in ["#productTitle", "h1.a-size-large", "h1"]:
                    try:
                        el = await page.query_selector(sel)
                        if el:
                            text = (await el.inner_text()).strip()
                            if text and len(text) > 3:
                                product_name = text
                                data_source["productName"] = "dom"
                                break
                    except Exception:
                        continue

            if not price or data_source["price"] == "fallback":
                for sel in [
                    ".a-price-whole",
                    "#priceblock_ourprice",
                    "#priceblock_dealprice",
                    ".a-offscreen",
                    '[data-a-color="price"] .a-offscreen',
                    "#corePrice_feature_div .a-price .a-offscreen",
                ]:
                    try:
                        el = await page.query_selector(sel)
                        if el:
                            p_text = (await el.inner_text()).strip()
                            if p_text:
                                formatted = _format_price(p_text)
                                if formatted:
                                    price = formatted
                                    data_source["price"] = "dom"
                                    break
                    except Exception:
                        continue

            if not image or data_source["image"] == "fallback":
                for sel in [
                    "#imgTagWrapperId img",
                    "#landingImage",
                    "#main-image",
                    "#ebooks-img-canvas img",
                    ".a-dynamic-image",
                ]:
                    try:
                        el = await page.query_selector(sel)
                        if el:
                            src = await el.get_attribute("src")
                            if not src or "placeholder" in src.lower():
                                src = await el.get_attribute("data-old-hires") or await el.get_attribute("data-a-dynamic-image")
                            if src and src.startswith("http"):
                                # data-a-dynamic-image is a JSON map of {url: [w, h]}
                                if src.startswith("{"):
                                    try:
                                        img_map = json.loads(src)
                                        # Pick the largest image
                                        best = max(img_map, key=lambda u: img_map[u][0] if img_map[u] else 0)
                                        src = best
                                    except Exception:
                                        pass
                                if src and src.startswith("http"):
                                    image = src
                                    data_source["image"] = "dom"
                                    break
                    except Exception:
                        continue

            if not rating or data_source["rating"] == "fallback":
                for sel in [
                    "#acrPopover .a-icon-alt",
                    "#averageCustomerReviews .a-icon-alt",
                    '[data-hook="rating-out-of-text"]',
                    ".a-star-medium .a-icon-alt",
                ]:
                    try:
                        el = await page.query_selector(sel)
                        if el:
                            r_text = (await el.inner_text()).strip()
                            m = re.search(r"([1-5][.,][0-9])", r_text)
                            if m:
                                rating = float(m.group(1).replace(",", "."))
                                data_source["rating"] = "dom"
                                break
                    except Exception:
                        continue

            if not review_count or data_source["reviewCount"] == "fallback":
                for sel in [
                    "#acrCustomerReviewText",
                    '[data-hook="total-review-count"]',
                    "#customerReviews .a-link-normal",
                ]:
                    try:
                        el = await page.query_selector(sel)
                        if el:
                            rc_text = (await el.inner_text()).strip()
                            m = re.search(r"([\d.,]+)", rc_text)
                            if m:
                                rc_raw = m.group(1).replace(".", "").replace(",", "")
                                if rc_raw.isdigit():
                                    review_count = int(rc_raw)
                                    data_source["reviewCount"] = "dom"
                                    break
                    except Exception:
                        continue

            # ── 4. Bot protection check ─────────────────────────────────────
            try:
                page_title = await page.title()
                body_text = (await page.inner_text("body"))[:500]
                is_blocked = (
                    "robot" in page_title.lower()
                    or "captcha" in page_title.lower()
                    or "bot check" in page_title.lower()
                    or "sorry, we just need to make sure" in body_text.lower()
                    or "enter the characters you see" in body_text.lower()
                )
                if is_blocked:
                    print("[AMAZON] BOT PROTECTION DETECTED — product data may be incomplete")
                    data_source["botProtection"] = True
            except Exception:
                pass

            # ── 5. Slug fallback for name ───────────────────────────────────
            if not product_name:
                path = parsed_url.path
                slug = path.strip("/").split("/")[-1] if "/" in path else path.strip("/")
                if slug and slug != "dp":
                    slug_keywords = slug.replace("-", " ").split()
                    product_name = slug.replace("-", " ").title()
                    data_source["productName"] = "slug"

            print(
                f"[AMAZON] name={product_name!r} brand={brand!r} "
                f"price={price!r} rating={rating} reviewCount={review_count} "
                f"image={'YES' if image else 'NONE'} asin={asin!r}"
            )
            print(f"[REVIEWS] amazon asin={asin!r} — review text extraction skipped (bot protection)")
            print(f"[REVIEWS] loaded=0 source=bot_protection_skipped")

            await browser.close()

    except Exception as e:
        print(f"[AMAZON] playwright error: {e}")

    review_stats = {
        "reviewCount": review_count,
        "reviewsLoaded": 0,
        "dedupedCount": 0,
        "completed": False,
        "maxReviews": max_reviews or 0,
        "source": "bot_protection_skipped",
        "reason": "bot_protection",
        "error": "reviews_could_not_be_loaded",
        "starDistribution": None,
        "loadedByStar": {str(s): 0 for s in range(1, 6)},
        "sampleReviews": [],
    }

    return {
        "sourceUrl": url,
        "sourcePlatform": "Amazon",
        "productName": product_name,
        "brand": brand,
        "category": category,
        "price": price,
        "image": image,
        "rating": rating,
        "reviewCount": review_count,
        "questionCount": None,
        "sellerScore": None,
        "slugKeywords": slug_keywords,
        "dataSource": data_source,
        "reviews": [],
        "reviewsLoaded": 0,
        "reviewsSource": "bot_protection_skipped",
        "ratingDistribution": None,
        "reviewStats": review_stats,
    }
