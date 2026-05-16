import re
import json
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

# Image URL patterns that indicate logos/placeholders to reject
_BAD_IMAGE_PATTERNS = ("logo", "icon", "svg", "placeholder", "default", "blank", "spinner")
_GOOD_IMAGE_EXTS = (".jpg", ".jpeg", ".png", ".webp")


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
    # Accept any CDN image (Trendyol uses .jpg/.webp, but check broadly)
    return True


def _normalize_image_url(url: str) -> str | None:
    if not url:
        return None
    url = url.strip()
    if url.startswith("//"):
        url = "https:" + url
    elif url.startswith("/"):
        url = "https://www.trendyol.com" + url
    # Extract first URL from srcset (e.g. "img.jpg 1x, img@2x.jpg 2x")
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
    """Use JavaScript to find the best product image on the page."""
    try:
        result = await page.evaluate("""
            () => {
                // Priority 1: Trendyol CDN images (product images)
                const cdnImgs = Array.from(document.querySelectorAll('img'))
                    .filter(img => {
                        const src = img.src || img.getAttribute('data-src') || img.getAttribute('data-original') || '';
                        return (src.includes('ty-cdn') || src.includes('trendyol.com')) &&
                               !src.includes('logo') && !src.includes('icon') &&
                               (src.includes('.jpg') || src.includes('.webp') || src.includes('.png'));
                    })
                    .sort((a, b) => (b.naturalWidth || b.width || 0) - (a.naturalWidth || a.width || 0));

                if (cdnImgs.length > 0) {
                    const img = cdnImgs[0];
                    return img.src || img.getAttribute('data-src') || img.getAttribute('data-original');
                }

                // Priority 2: Any large image on page
                const allImgs = Array.from(document.querySelectorAll('img'))
                    .filter(img => {
                        const src = img.src || img.getAttribute('data-src') || '';
                        return src.startsWith('http') && !src.includes('logo') && !src.includes('icon');
                    })
                    .sort((a, b) => (b.naturalWidth || 0) - (a.naturalWidth || 0));

                if (allImgs.length > 0) {
                    const img = allImgs[0];
                    return img.src || img.getAttribute('data-src');
                }

                return null;
            }
        """)
        if result and _is_valid_image(result):
            return result
    except Exception as e:
        print(f"[scraper] JS image extraction error: {e}")
    return None


async def _extract_review_count_via_js(page) -> int | None:
    """Use JavaScript to find review count on the page."""
    try:
        result = await page.evaluate("""
            () => {
                // Look for elements containing 'Değerlendirme' or 'Yorum'
                const allEls = Array.from(document.querySelectorAll('*'));
                for (const el of allEls) {
                    if (el.children.length > 0) continue;  // leaf nodes only
                    const text = (el.textContent || '').trim();
                    const m = text.match(/^([\d.]+)\s*(Değerlendirme|Yorum)/);
                    if (m) return m[1].replace(/\./g, '');
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
    """Use JavaScript to find rating on page."""
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
    """Try multiple attributes on an element, return first non-empty value."""
    for attr in attrs:
        try:
            val = await el.get_attribute(attr)
            if val and val.strip():
                return val.strip()
        except Exception:
            continue
    return None


async def scrape_trendyol_product(url: str) -> dict:
    parsed_url = urlparse(url)
    domain = parsed_url.netloc.lower()
    path_segments = [seg for seg in parsed_url.path.strip("/").split("/") if seg]

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

    data_source = {
        "productName": "fallback",
        "price": "fallback",
        "image": "fallback",
        "rating": "fallback",
        "reviewCount": "fallback",
        "questionCount": "fallback",
        "sellerScore": "fallback",
    }

    # URL slug as initial fallback (name only, no fake data)
    if "trendyol.com" in domain and len(path_segments) >= 2:
        brand = beautify_turkish(path_segments[0])
        data_source["brand"] = "url_slug"
        slug_part = path_segments[1]
        if "-p-" in slug_part:
            slug_part = slug_part.split("-p-")[0]
        slug_keywords = slug_part.split("-")
        product_name = beautify_turkish(slug_part)

    try:
        async with async_playwright() as p:
            browser = await p.chromium.launch(headless=True)
            context = await browser.new_context(
                user_agent=(
                    "Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
                    "AppleWebKit/537.36 (KHTML, like Gecko) "
                    "Chrome/120.0.0.0 Safari/537.36"
                ),
                locale="tr-TR",
                viewport={"width": 1280, "height": 900},
            )
            page = await context.new_page()

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
                            # image can be string or list
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
            # Product name
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

            # Price
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

            # Image — try many selectors + data attributes
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
                                # Try srcset — pick first URL
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

            # Image — JavaScript fallback
            if not image or data_source["image"] == "fallback":
                js_img = await _extract_image_via_js(page)
                if js_img:
                    image = js_img
                    data_source["image"] = "js"

            # Rating
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

            # Review count — DOM
            if not review_count or data_source["reviewCount"] == "fallback":
                for sel in [
                    'a:has-text("Değerlendirme")',
                    'span:has-text("Değerlendirme")',
                    'div:has-text("Değerlendirme")',
                    'a:has-text("Yorum")',
                    '[class*="review"] [class*="count"]',
                    '[class*="rating"] [class*="count"]',
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

            # Review count — JavaScript fallback
            if not review_count or data_source["reviewCount"] == "fallback":
                rc_js = await _extract_review_count_via_js(page)
                if rc_js is not None:
                    review_count = rc_js
                    data_source["reviewCount"] = "js"

            # Question count
            if not question_count or data_source["questionCount"] == "fallback":
                for sel in [
                    'a:has-text("Soru-Cevap")',
                    'a:has-text("Soru")',
                    'span:has-text("Soru")',
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

            # Seller score
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

            # Category breadcrumb
            try:
                crumbs = await page.query_selector_all(".breadcrumb-item")
                if crumbs:
                    texts = [await c.inner_text() for c in crumbs]
                    category = " / ".join([t.strip() for t in texts if t.strip()])
            except Exception:
                pass

            # ── 4. Full body regex (last resort) ───────────────────────────
            needs_body = not price or not rating or not review_count or not question_count or not image
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

                    if not review_count or data_source["reviewCount"] == "fallback":
                        rc = parse_review_count(body_text)
                        if rc is not None:
                            review_count = rc
                            data_source["reviewCount"] = "regex"

                    if not question_count or data_source["questionCount"] == "fallback":
                        qc = parse_question_count(body_text)
                        if qc is not None:
                            question_count = qc
                            data_source["questionCount"] = "regex"

                except Exception:
                    pass

            # Print extraction results for debugging
            print(
                f"[scraper] name={product_name!r} brand={brand!r} "
                f"price={price!r} rating={rating} reviewCount={review_count} "
                f"image={'YES' if image else 'NONE'} sources={data_source}"
            )

            await browser.close()

    except Exception as e:
        print(f"[scraper] Playwright execution error: {e}")

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
    }
