"""
Generic product scraper.

Works for any e-commerce site by extracting data from:
  1. JSON-LD Product schema
  2. Open Graph / Twitter meta tags
  3. Generic DOM selectors (h1, price patterns)
  4. Full body text regex

Returns the same dict schema as all other platform scrapers.
"""

import json
import re
import traceback
from urllib.parse import urlparse

from playwright.async_api import async_playwright

from .image_utils import is_valid_image_url, normalize_image_url, parse_srcset
from .price_utils import parse_price_to_string

_LAUNCH_ARGS = [
    "--headless=new",
    "--disable-blink-features=AutomationControlled",
    "--no-sandbox",
    "--disable-dev-shm-usage",
    "--disable-gpu",
    "--disable-setuid-sandbox",
    "--window-size=1280,900",
    "--ignore-certificate-errors",
]
_STEALTH_SCRIPT = """
    Object.defineProperty(navigator, 'webdriver', {get: () => undefined});
    Object.defineProperty(navigator, 'plugins', {get: () => [1, 2, 3, 4, 5]});
    Object.defineProperty(navigator, 'languages', {get: () => ['tr-TR', 'tr', 'en-US', 'en']});
    window.chrome = { runtime: {} };
"""

_EMPTY_RESULT = {
    "productName": None,
    "brand": None,
    "category": "Genel",
    "price": None,
    "image": None,
    "rating": None,
    "reviewCount": None,
    "questionCount": None,
    "sellerScore": None,
    "slugKeywords": [],
    "dataSource": {},
}


def _build_result(**kwargs) -> dict:
    r = dict(_EMPTY_RESULT)
    r.update(kwargs)
    return r


def _parse_review_count(text: str) -> int | None:
    for pattern in [
        r"([\d.]+)\s*Değerlendirme",
        r"([\d.]+)\s*Yorum",
        r"([\d]+)\s*yorum",
        r"([\d,]+)\s*review",
        r"([\d,]+)\s*rating",
    ]:
        m = re.search(pattern, text, re.IGNORECASE)
        if m:
            raw = m.group(1).replace(".", "").replace(",", "")
            if raw.isdigit():
                return int(raw)
    return None


def _extract_from_jsonld(data: dict) -> dict:
    """Extract product fields from a JSON-LD Product node."""
    out: dict = {}
    if data.get("@type") not in ("Product", "product"):
        return out

    if data.get("name"):
        out["productName"] = str(data["name"]).strip()

    brand = data.get("brand") or {}
    if isinstance(brand, dict) and brand.get("name"):
        out["brand"] = str(brand["name"]).strip()

    img_raw = data.get("image")
    if img_raw:
        candidates = img_raw if isinstance(img_raw, list) else [img_raw]
        for c in candidates:
            norm = normalize_image_url(str(c))
            if norm:
                out["image"] = norm
                break

    offers = data.get("offers") or {}
    if isinstance(offers, list):
        offers = offers[0] if offers else {}
    if isinstance(offers, dict):
        if offers.get("price"):
            out["price"] = parse_price_to_string(offers["price"])
        if not out.get("price") and offers.get("lowPrice"):
            out["price"] = parse_price_to_string(offers["lowPrice"])

    agg = data.get("aggregateRating") or {}
    if isinstance(agg, dict):
        if agg.get("ratingValue"):
            try:
                out["rating"] = float(str(agg["ratingValue"]).replace(",", "."))
            except Exception:
                pass
        if agg.get("reviewCount"):
            raw = str(agg["reviewCount"]).replace(".", "").replace(",", "")
            if raw.isdigit():
                out["reviewCount"] = int(raw)

    return out


async def scrape_generic_product(url: str) -> dict:
    parsed = urlparse(url)
    domain = parsed.netloc.lower()
    base_domain = f"{parsed.scheme}://{parsed.netloc}"

    product_name: str | None = None
    brand: str | None = None
    price: str | None = None
    image: str | None = None
    rating: float | None = None
    review_count: int | None = None
    category = "Genel"
    data_source: dict[str, str] = {}

    try:
        async with async_playwright() as p:
            browser = await p.chromium.launch(
                headless=True,
                args=_LAUNCH_ARGS,
            )
            context = await browser.new_context(
                user_agent=(
                    "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) "
                    "AppleWebKit/537.36 (KHTML, like Gecko) "
                    "Chrome/124.0.0.0 Safari/537.36"
                ),
                locale="tr-TR",
                viewport={"width": 1280, "height": 900},
                extra_http_headers={
                    "Accept-Language": "tr-TR,tr;q=0.9,en;q=0.8",
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
                    print(f"[generic_scraper] page load error: {e}")

            await page.wait_for_timeout(5000)

            # ── 1. JSON-LD ─────────────────────────────────────────────────
            try:
                for el in await page.query_selector_all('script[type="application/ld+json"]'):
                    try:
                        raw_text = await el.inner_text()
                        data = json.loads(raw_text)
                        nodes = data if isinstance(data, list) else [data]
                        for node in nodes:
                            extracted = _extract_from_jsonld(node)
                            if not extracted:
                                # Check @graph
                                for g in (node.get("@graph") or []):
                                    extracted = _extract_from_jsonld(g)
                                    if extracted:
                                        break
                            if extracted:
                                if not product_name and extracted.get("productName"):
                                    product_name = extracted["productName"]
                                    data_source["productName"] = "jsonld"
                                if not brand and extracted.get("brand"):
                                    brand = extracted["brand"]
                                    data_source["brand"] = "jsonld"
                                if not image and extracted.get("image"):
                                    image = extracted["image"]
                                    data_source["image"] = "jsonld"
                                if not price and extracted.get("price"):
                                    price = extracted["price"]
                                    data_source["price"] = "jsonld"
                                if not rating and extracted.get("rating"):
                                    rating = extracted["rating"]
                                    data_source["rating"] = "jsonld"
                                if not review_count and extracted.get("reviewCount"):
                                    review_count = extracted["reviewCount"]
                                    data_source["reviewCount"] = "jsonld"
                    except Exception:
                        continue
            except Exception:
                pass

            # ── 2. Meta tags ───────────────────────────────────────────────
            try:
                if not product_name:
                    for sel in ['meta[property="og:title"]', 'meta[name="twitter:title"]', "title"]:
                        el = await page.query_selector(sel)
                        if el:
                            c = await el.get_attribute("content") if sel.startswith("meta") else await el.inner_text()
                            if c and c.strip():
                                product_name = c.strip()
                                data_source["productName"] = "meta"
                                break

                if not image:
                    for sel in [
                        'meta[property="og:image"]',
                        'meta[property="og:image:secure_url"]',
                        'meta[name="twitter:image"]',
                        'meta[name="twitter:image:src"]',
                        'meta[itemprop="image"]',
                    ]:
                        el = await page.query_selector(sel)
                        if el:
                            c = await el.get_attribute("content") or await el.get_attribute("href") or ""
                            norm = normalize_image_url(c.strip(), base_domain)
                            if norm:
                                image = norm
                                data_source["image"] = "meta"
                                break

                if not price:
                    for sel in [
                        'meta[property="product:price:amount"]',
                        'meta[name="product:price:amount"]',
                        'meta[itemprop="price"]',
                    ]:
                        el = await page.query_selector(sel)
                        if el:
                            c = await el.get_attribute("content")
                            if c:
                                p = parse_price_to_string(c.strip())
                                if p:
                                    price = p
                                    data_source["price"] = "meta"
                                    break
            except Exception:
                pass

            # ── 3. Generic DOM ─────────────────────────────────────────────
            if not product_name:
                for sel in [
                    "[itemprop='name']",
                    "h1[class*='product']",
                    "h1[class*='title']",
                    "h1",
                ]:
                    try:
                        el = await page.query_selector(sel)
                        if el:
                            t = (await el.inner_text()).replace("\n", " ").strip()
                            if t and len(t) > 3:
                                product_name = t
                                data_source["productName"] = "dom"
                                break
                    except Exception:
                        continue

            if not price:
                for sel in [
                    "[itemprop='price']",
                    "[class*='price']",
                    "[class*='Price']",
                    "[data-testid*='price']",
                    "[data-test-id*='price']",
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
                # Try structured data attribute then common image selectors
                for sel in [
                    "[itemprop='image']",
                    "img[class*='product']",
                    "img[class*='main']",
                    "img[id*='product']",
                    ".product-image img",
                    ".product img",
                    "main img",
                ]:
                    try:
                        el = await page.query_selector(sel)
                        if el:
                            for attr in ("src", "data-src", "data-original", "content"):
                                v = await el.get_attribute(attr)
                                if v:
                                    norm = normalize_image_url(v.strip(), base_domain)
                                    if norm:
                                        image = norm
                                        data_source["image"] = "dom"
                                        break
                            if not image:
                                ss = await el.get_attribute("srcset")
                                img_from_ss = parse_srcset(ss, base_domain)
                                if img_from_ss:
                                    image = img_from_ss
                                    data_source["image"] = "dom_srcset"
                        if image:
                            break
                    except Exception:
                        continue

            if not rating:
                for sel in ["[itemprop='ratingValue']", "[class*='rating']", "[class*='Rating']"]:
                    try:
                        el = await page.query_selector(sel)
                        if el:
                            v = await el.get_attribute("content") or await el.inner_text()
                            m = re.search(r"\b([1-5][.,][0-9])\b", v)
                            if m:
                                rating = float(m.group(1).replace(",", "."))
                                data_source["rating"] = "dom"
                                break
                    except Exception:
                        continue

            if not review_count:
                for sel in ["[itemprop='reviewCount']", "[itemprop='ratingCount']"]:
                    try:
                        el = await page.query_selector(sel)
                        if el:
                            v = await el.get_attribute("content") or await el.inner_text()
                            raw = v.strip().replace(".", "").replace(",", "")
                            if raw.isdigit():
                                review_count = int(raw)
                                data_source["reviewCount"] = "dom"
                                break
                    except Exception:
                        continue

            # ── 4. Body regex (last resort) ─────────────────────────────────
            try:
                body = await page.inner_text("body")

                if not price:
                    m = re.search(r"([\d]{1,3}(?:\.[\d]{3})*,\d{2})\s*TL", body)
                    if m:
                        price = m.group(1) + " TL"
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
            except Exception:
                pass

            print(
                f"[generic_scraper] domain={domain} "
                f"name={product_name!r} price={price!r} "
                f"image={'YES' if image else 'NO'} rating={rating} "
                f"sources={data_source}"
            )
            await browser.close()

    except Exception as e:
        print(f"[generic_scraper] Playwright error:")
        traceback.print_exc()

    # Determine platform display name from domain
    platform = "Web"
    for keyword, name in [("trendyol", "Trendyol"), ("hepsiburada", "Hepsiburada"),
                          ("amazon", "Amazon"), ("n11", "N11"), ("pazarama", "Pazarama")]:
        if keyword in domain:
            platform = name
            break

    return {
        "productName": product_name,
        "brand": brand,
        "category": category,
        "price": price,
        "image": image,
        "rating": rating,
        "reviewCount": review_count,
        "questionCount": None,
        "sellerScore": None,
        "sourceUrl": url,
        "sourcePlatform": platform,
        "slugKeywords": [],
        "dataSource": data_source,
    }
