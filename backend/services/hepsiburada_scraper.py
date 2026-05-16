"""
Hepsiburada-specific product scraper.

Extraction priority:
  1. JSON-LD Product
  2. Open Graph / Twitter meta tags
  3. itemprop attributes
  4. Hepsiburada-specific CSS selectors
  5. JavaScript DOM evaluation
  6. Body text regex (last resort)
"""

import json
import re
import traceback

from playwright.async_api import async_playwright

from .image_utils import is_valid_image_url, normalize_image_url, parse_srcset
from .price_utils import parse_price_to_string

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
    "--disable-infobars",
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


def _clean(s: str | None) -> str | None:
    if not s:
        return None
    s = s.strip()
    # Strip known noise suffixes from product names
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


async def scrape_hepsiburada_product(url: str) -> dict:
    product_name: str | None = None
    brand: str | None = None
    price: str | None = None
    image: str | None = None
    rating: float | None = None
    review_count: int | None = None
    question_count: int | None = None
    category = "Genel"
    data_source: dict[str, str] = {}

    try:
        async with async_playwright() as p:
            browser = await p.chromium.launch(
                headless=True,
                args=_LAUNCH_ARGS,
            )
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

            try:
                await page.goto(url, wait_until="networkidle", timeout=45000)
            except Exception:
                try:
                    await page.goto(url, wait_until="domcontentloaded", timeout=30000)
                except Exception as e:
                    print(f"[hepsiburada] page load error: {e}")

            # Wait for JS rendering
            await page.wait_for_timeout(5000)

            # ── 1. JSON-LD ─────────────────────────────────────────────────
            try:
                for el in await page.query_selector_all('script[type="application/ld+json"]'):
                    try:
                        raw_text = await el.inner_text()
                        data = json.loads(raw_text)
                        nodes = data if isinstance(data, list) else [data]
                        for node in nodes:
                            if not isinstance(node, dict):
                                continue
                            if node.get("@type") != "Product":
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
                                candidates = img_raw if isinstance(img_raw, list) else [img_raw]
                                for c in candidates:
                                    norm = normalize_image_url(str(c), _BASE)
                                    if norm:
                                        image = norm
                                        data_source["image"] = "jsonld"
                                        break

                            offers = node.get("offers") or {}
                            if isinstance(offers, list):
                                offers = offers[0] if offers else {}
                            if not price and isinstance(offers, dict) and offers.get("price"):
                                p = parse_price_to_string(offers["price"])
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
                                    raw = str(agg["reviewCount"]).replace(".", "").replace(",", "")
                                    if raw.isdigit():
                                        review_count = int(raw)
                                        data_source["reviewCount"] = "jsonld"
                    except Exception:
                        continue
            except Exception:
                pass

            # ── 2. Open Graph / Twitter meta tags ──────────────────────────
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
                    'meta[name="twitter:image:src"]',
                ]:
                    try:
                        el = await page.query_selector(sel)
                        if el:
                            c = await el.get_attribute("content")
                            norm = normalize_image_url(c or "", _BASE)
                            if norm:
                                image = norm
                                data_source["image"] = "meta_og"
                                break
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
                                p = parse_price_to_string(c.strip())
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
                            raw = v.strip().replace(".", "").replace(",", "")
                            if raw.isdigit():
                                review_count = int(raw)
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
                for sel in [
                    "[data-test-id='price-current-price']",
                    "[data-test-id='price']",
                    "[data-testid='price']",
                    "[itemprop='price']",
                    "span[class*='price']",
                    "div[class*='price']",
                    "[class*='currentPrice']",
                    "[class*='current-price']",
                    "[class*='priceValue']",
                ]:
                    try:
                        el = await page.query_selector(sel)
                        if el:
                            raw = await el.get_attribute("content") or await el.inner_text()
                            p = parse_price_to_string(raw.strip())
                            if p:
                                price = p
                                data_source["price"] = "dom"
                                break
                    except Exception:
                        continue

            if not image:
                for sel in [
                    "img[class*='product-main']",
                    "img[class*='ProductImage']",
                    "img[class*='productImage']",
                    "[class*='gallery'] img",
                    "[class*='product-image'] img",
                    "img[class*='image']",
                    "main img",
                ]:
                    try:
                        el = await page.query_selector(sel)
                        if el:
                            for attr in ("src", "data-src", "data-original"):
                                v = await el.get_attribute(attr)
                                if v:
                                    norm = normalize_image_url(v.strip(), _BASE)
                                    if norm:
                                        image = norm
                                        data_source["image"] = "dom"
                                        break
                            if not image:
                                ss = await el.get_attribute("srcset")
                                img_ss = parse_srcset(ss, _BASE)
                                if img_ss:
                                    image = img_ss
                                    data_source["image"] = "dom_srcset"
                        if image:
                            break
                    except Exception:
                        continue

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

            # ── 5. JavaScript DOM evaluation ───────────────────────────────
            if not image:
                try:
                    result = await page.evaluate("""
                        () => {
                            const BAD = ['logo', 'icon', 'svg', 'placeholder', 'blank', 'spinner', 'badge', 'favicon'];
                            const ok = s => s && s.startsWith('http') && !BAD.some(b => s.toLowerCase().includes(b));

                            const imgs = Array.from(document.querySelectorAll('img'))
                                .map(img => {
                                    const ss = img.getAttribute('srcset') || '';
                                    if (ss) {
                                        const tokens = ss.split(',').map(s => s.trim().split(/\\s+/)[0]).filter(Boolean);
                                        for (let i = tokens.length - 1; i >= 0; i--) {
                                            const t = tokens[i].startsWith('//') ? 'https:' + tokens[i] : tokens[i];
                                            if (ok(t)) return { img, src: t };
                                        }
                                    }
                                    const src = img.src || img.getAttribute('data-src') || '';
                                    return { img, src };
                                })
                                .filter(({ src }) => ok(src))
                                .sort((a, b) => (b.img.naturalWidth || 0) - (a.img.naturalWidth || 0));
                            return imgs.length > 0 ? imgs[0].src : null;
                        }
                    """)
                    if result:
                        norm = normalize_image_url(str(result), _BASE)
                        if norm:
                            image = norm
                            data_source["image"] = "js"
                except Exception as e:
                    print(f"[hepsiburada] JS image error: {e}")

            if not price:
                try:
                    result_price = await page.evaluate("""
                        () => {
                            const sels = [
                                '[data-test-id="price-current-price"]',
                                '[data-test-id="price"]',
                                '[class*="currentPrice"]',
                                '[class*="priceValue"]',
                                '[itemprop="price"]',
                            ];
                            for (const sel of sels) {
                                const el = document.querySelector(sel);
                                if (el) {
                                    const v = el.getAttribute('content') || el.innerText;
                                    if (v && v.trim()) return v.trim();
                                }
                            }
                            return null;
                        }
                    """)
                    if result_price:
                        p = parse_price_to_string(str(result_price))
                        if p:
                            price = p
                            data_source["price"] = "js"
                except Exception as e:
                    print(f"[hepsiburada] JS price error: {e}")

            # ── 6. Body regex (last resort) ────────────────────────────────
            try:
                body = await page.inner_text("body")

                if not price:
                    m = re.search(r"([\d]{1,3}(?:\.[\d]{3})*,\d{2})\s*TL", body)
                    if m:
                        price = m.group(1) + " TL"
                        data_source["price"] = "regex"
                    if not price:
                        m = re.search(r"₺\s*([\d.,]+)", body)
                        if m:
                            p = parse_price_to_string(m.group(1))
                            if p:
                                price = p
                                data_source["price"] = "regex"

                if not rating:
                    m = re.search(r"\b([1-5][.,][0-9])\b", body)
                    if m:
                        rating = float(m.group(1).replace(",", "."))
                        data_source["rating"] = "regex"

                if not review_count:
                    rc = _parse_review_count(body)
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

                # Breadcrumb → category
                bc_match = re.search(r"Hepsiburada\s*›\s*([^›\n]+?)(?:\s*›|$)", body)
                if bc_match:
                    category = bc_match.group(1).strip()

            except Exception:
                pass

            print(
                f"[hepsiburada] name={product_name!r} brand={brand!r} "
                f"price={price!r} rating={rating} rc={review_count} "
                f"image={'YES' if image else 'NO'} sources={data_source}"
            )
            await browser.close()

    except Exception as e:
        print(f"[hepsiburada] Playwright error:")
        traceback.print_exc()

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
    }
