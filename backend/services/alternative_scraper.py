"""
Alternative product scraper — platform-aware.

Alternatives come from the SAME platform the user submitted a link for.
If the platform can't yield enough results, return what was found — never
cross to another platform.

Supported platforms: trendyol | hepsiburada | amazon_tr | n11 | generic
"""

import re as _re
import traceback
from urllib.parse import quote_plus

from playwright.async_api import async_playwright
from .product_type_extractor import extract_product_type

# ---------------------------------------------------------------------------
# Constants
# ---------------------------------------------------------------------------

_BAD_IMG = ("logo", "icon", "placeholder", "blank", "svg", "banner", "badge", "spinner", "favicon")

_LAUNCH_ARGS = [
    "--headless=new",
    "--disable-blink-features=AutomationControlled",
    "--no-sandbox",
    "--disable-dev-shm-usage",
    "--disable-gpu",
    "--window-size=1280,900",
    "--ignore-certificate-errors",
]
_STEALTH = """
    Object.defineProperty(navigator, 'webdriver', {get: () => undefined});
    Object.defineProperty(navigator, 'plugins', {get: () => [1,2,3,4,5]});
    Object.defineProperty(navigator, 'languages', {get: () => ['tr-TR','tr','en-US','en']});
    window.chrome = { runtime: {} };
"""

# Platform display names
_DISPLAY = {
    "trendyol":    "Trendyol",
    "hepsiburada": "Hepsiburada",
    "amazon_tr":   "Amazon TR",
    "n11":         "N11",
    "generic":     "Web",
}


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

def _is_valid_image(url: str | None) -> bool:
    if not url or not isinstance(url, str):
        return False
    u = url.strip().lower()
    if not u.startswith("http"):
        return False
    return not any(b in u for b in _BAD_IMG)


def _norm(text: str) -> str:
    tr = str.maketrans({
        "ı": "i", "İ": "i", "ö": "o", "Ö": "o",
        "ü": "u", "Ü": "u", "ş": "s", "Ş": "s",
        "ğ": "g", "Ğ": "g", "ç": "c", "Ç": "c",
    })
    return text.lower().translate(tr)


def _parse_price(raw: str) -> str:
    """Normalise a raw price string to 'X.XXX,XX TL' format."""
    if not raw:
        return ""
    raw = raw.strip()
    if "TL" in raw:
        return raw.split("TL")[0].strip() + " TL"
    if "₺" in raw:
        return raw.replace("₺", "").strip() + " TL"
    return raw


def _relevance_score(
    alt_name: str,
    base_name: str,
    category: str,
    required: list[str],
    forbidden: list[str],
    type_name: str,
    base_price: float,
    alt_price_str: str,
    has_image: bool = False,
) -> int:
    """
    +60  product type / required keyword found (mandatory — returns -1 if missing)
    -100 forbidden keyword found (instant reject)
    +20  category match
    +15  shared keywords with base product
    +10  price within 0.5×–2× of base price
    +5   image/metadata present
    Threshold: >= 70
    """
    name_n = _norm(alt_name)
    base_n = _norm(base_name)

    for kw in forbidden:
        if _norm(kw) in name_n:
            print(f"[alt] REJECT forbidden='{kw}': {alt_name[:55]!r}")
            return -100

    if required:
        if not any(_norm(kw) in name_n for kw in required):
            print(f"[alt] REJECT no-required: {alt_name[:55]!r}")
            return -1
    score = 60

    category_words = [w for w in _norm(category).replace("/", " ").split() if len(w) > 4]
    if category_words and any(w in name_n for w in category_words):
        score += 20

    shared_stop = {"icin", "ile", "ve", "the", "plus", "ultra", "yeni", "adet", "set"}
    base_words = {w for w in _re.findall(r"[a-z0-9]+", base_n) if len(w) > 3 and w not in shared_stop}
    alt_words = {w for w in _re.findall(r"[a-z0-9]+", name_n) if len(w) > 3 and w not in shared_stop}
    shared = base_words & alt_words
    if shared:
        score += min(15, len(shared) * 5)

    if base_price > 0 and alt_price_str:
        try:
            p = float(
                alt_price_str
                .replace(" TL", "").replace("₺", "")
                .replace(".", "").replace(",", ".").strip()
            )
            if 0.5 * base_price <= p <= 2.0 * base_price:
                score += 10
        except Exception:
            pass

    if has_image:
        score += 5

    return score


# ---------------------------------------------------------------------------
# Platform-specific search URL builders
# ---------------------------------------------------------------------------

def _search_url(platform: str, query: str) -> str:
    q = quote_plus(query)
    if platform == "trendyol":
        return f"https://www.trendyol.com/sr?q={q}"
    if platform == "hepsiburada":
        return f"https://www.hepsiburada.com/ara?q={q}"
    if platform == "amazon_tr":
        return f"https://www.amazon.com.tr/s?k={q}"
    if platform == "n11":
        return f"https://www.n11.com/arama?q={q}"
    # generic → trendyol as default
    return f"https://www.trendyol.com/sr?q={q}"


# ---------------------------------------------------------------------------
# Platform-specific result extractors (JavaScript-based for reliability)
# ---------------------------------------------------------------------------

_JS_TRENDYOL = """
() => Array.from(document.querySelectorAll(
    'a[data-testid="product-card"], a.product-card, a[href*="-p-"]'
)).slice(0, 30).map(a => {
    const img  = a.querySelector('img');
    const src  = img ? (img.src || img.getAttribute('data-src') || '') : '';
    const alt  = img ? (img.alt || '') : '';
    const nameEl = a.querySelector('span.product-name, [class="product-name"], [class*="product-name"]');
    const name = nameEl ? nameEl.textContent.trim() : alt;
    const prEl = a.querySelector('span.price-value, [class="price-value"], [class*="price-value"], [class*="prc-box-dscntd"]');
    const price = prEl ? prEl.textContent.replace(/\\s+/g,' ').trim() : '';
    return { href: a.href, name: name.substring(0,120), price, src };
}).filter(p => p.name && p.href.includes('-p-') && p.href.includes('trendyol.com'))
"""

_JS_HEPSIBURADA = """
() => {
    const TR_PRICE_RE = /\\d{1,3}(?:\\.\\d{3})*(?:,\\d{1,2})?\\s*(?:TL|₺)/i;
    const results = [];
    const seen = new Set();

    // Accept any hepsiburada.com link that looks like a product page
    const isProductLink = href =>
        href && href.includes('hepsiburada.com') &&
        (href.includes('-pm-') || href.includes('-p-'));

    const links = Array.from(document.querySelectorAll('a[href]'))
        .filter(a => isProductLink(a.href));

    for (const a of links) {
        const href = a.href || '';
        if (seen.has(href)) continue;
        seen.add(href);

        const img  = a.querySelector('img');
        const src  = img ? (img.src || img.getAttribute('data-src') || '') : '';
        const alt  = img ? (img.alt || '') : '';
        const title = a.getAttribute('title') || '';

        // Name: title attr → img alt → nearest heading text
        let name = (title || alt).trim();
        if (!name) {
            const card = a.closest('li, article, [class*="productCard"], [class*="product-card"]') || a.parentElement;
            if (card) {
                const h = card.querySelector('h2, h3, h4, [class*="title"], [class*="name"], [class*="product-name"]');
                if (h) name = h.textContent.trim();
            }
        }
        if (!name) name = a.textContent.trim().substring(0, 120);
        name = name.replace(/\\s+/g, ' ').substring(0, 120);
        if (!name || name.length < 3) continue;

        // Price extraction: explicit selectors → aria-label → content scan
        let price = '';
        const card = a.closest('li, article, [class*="productCard"], [class*="product-card"]') || a.parentElement;
        if (card) {
            // 1) Explicit data-test-id / class selectors (2024-2025 HB patterns)
            const PRICE_SELS = [
                '[data-test-id="price-current-price"]',
                '[data-test-id="price"]',
                '[class*="price-value"]',
                '[class*="priceContainer"] span',
                '[class*="product-price"]',
                '[class*="curr-price"]',
                '[class*="hbs-product-price"]',
                '[class*="currentPrice"]',
            ];
            for (const psel of PRICE_SELS) {
                const el = card.querySelector(psel);
                if (el) {
                    const t = el.textContent.trim().replace(/\\s+/g, ' ');
                    const m = t.match(TR_PRICE_RE);
                    if (m) { price = m[0]; break; }
                    // Also accept plain number followed by TL/₺ anywhere in text
                    if (/\\d/.test(t) && (t.includes('TL') || t.includes('₺'))) {
                        price = t.substring(0, 30); break;
                    }
                }
            }
            // 2) aria-label on any element (common HB pattern)
            if (!price) {
                const h2 = card.querySelector('[aria-label]');
                if (h2) {
                    const m = (h2.getAttribute('aria-label') || '').match(TR_PRICE_RE);
                    if (m) price = m[0];
                }
            }
            // 3) content-scan: leaf elements matching TR price RE
            if (!price) {
                const allEls = Array.from(card.querySelectorAll('*'));
                for (const el of allEls) {
                    if (el.children.length > 2) continue;
                    const t = el.textContent.trim();
                    if (TR_PRICE_RE.test(t)) {
                        const m = t.match(TR_PRICE_RE);
                        if (m) { price = m[0]; break; }
                    }
                }
            }
        }

        results.push({ href, name, price, src });
        if (results.length >= 30) break;
    }
    return results;
}
"""

_JS_AMAZON = """
() => Array.from(document.querySelectorAll(
    'div[data-component-type="s-search-result"]'
)).slice(0, 20).map(card => {
    const a    = card.querySelector('a.a-link-normal[href*="/dp/"]');
    const href = a ? a.href : '';
    const img  = card.querySelector('img.s-image');
    const src  = img ? img.src : '';
    const nameEl = card.querySelector('h2 span, span.a-text-normal');
    const name   = nameEl ? nameEl.textContent.trim().substring(0,120) : '';
    const prEl   = card.querySelector('span.a-price-whole');
    const price  = prEl ? prEl.textContent.trim() + ' TL' : '';
    return { href, name, price, src };
}).filter(p => p.name && p.href.includes('/dp/'))
"""

_JS_N11 = """
() => Array.from(document.querySelectorAll(
    'ul.prdList li.column, .productListContent li, li[class*="product"]'
)).slice(0, 25).map(li => {
    const a    = li.querySelector('a[href*="n11.com"]') || li.querySelector('a[href]');
    const href = a ? a.href : '';
    const img  = li.querySelector('img');
    const src  = img ? (img.src || img.getAttribute('data-src') || '') : '';
    const nameEl = li.querySelector('h3, h2, [class*="name"], [class*="title"]');
    const name   = nameEl ? nameEl.textContent.trim().substring(0,120) : (img ? img.alt : '');
    const prEl   = li.querySelector('[class*="price"], [class*="Price"]');
    const price  = prEl ? prEl.textContent.trim().replace(/\\s+/g,' ') : '';
    return { href, name, price, src };
}).filter(p => p.name && p.href)
"""

_JS_EXTRACTORS: dict[str, str] = {
    "trendyol":    _JS_TRENDYOL,
    "hepsiburada": _JS_HEPSIBURADA,
    "amazon_tr":   _JS_AMAZON,
    "n11":         _JS_N11,
}

# URL validity checks per platform
_URL_CONTAINS: dict[str, str] = {
    "trendyol":    "trendyol.com",
    "hepsiburada": "hepsiburada.com",
    "amazon_tr":   "amazon.com.tr",
    "n11":         "n11.com",
}


# ---------------------------------------------------------------------------
# Core scraping
# ---------------------------------------------------------------------------

async def _scrape_query(page, query: str, platform: str, existing_urls: set[str]) -> list[dict]:
    url = _search_url(platform, query)
    print(f"[alt] {platform} query={query!r}")

    try:
        await page.goto(url, wait_until="domcontentloaded", timeout=35000)
    except Exception as e:
        print(f"[alt] goto error: {e}")
        return []

    await page.wait_for_timeout(3500)

    js = _JS_EXTRACTORS.get(platform, _JS_TRENDYOL)
    try:
        items = await page.evaluate(js)
    except Exception as e:
        print(f"[alt] JS eval error: {e}")
        items = []

    if not items and platform == "hepsiburada":
        print(f"[alt] hepsiburada: JS returned 0 items — saving debug HTML")
        try:
            html_dbg = await page.content()
            import tempfile, os
            dbg_path = os.path.join(tempfile.gettempdir(), "hb_search_debug.html")
            with open(dbg_path, "w", encoding="utf-8") as f:
                f.write(html_dbg[:80000])
            print(f"[alt] hepsiburada: HTML saved to {dbg_path}")
        except Exception as e:
            print(f"[alt] hepsiburada: debug save error: {e}")

    domain_check = _URL_CONTAINS.get(platform, "")
    raw: list[dict] = []
    for item in (items or []):
        href = (item.get("href") or "").strip()
        name = (item.get("name") or "").strip()
        if not href or not name:
            continue
        if domain_check and domain_check not in href:
            continue
        # Ensure it's actually a product page (not a category/listing page)
        if platform == "hepsiburada":
            if not (_re.search(r"/[a-z0-9-]+-p[m]?-", href)):
                continue
        if platform == "trendyol" and "-p-" not in href:
            continue
        if href in existing_urls:
            continue
        raw.append({
            "name": name[:120],
            "price": _parse_price(item.get("price", "")),
            "image": item.get("src", "") if _is_valid_image(item.get("src")) else None,
            "url": href,
        })

    print(f"[alt] raw results: {len(raw)}")
    return raw


# ---------------------------------------------------------------------------
# Public API
# ---------------------------------------------------------------------------

async def get_alternatives(
    category: str,
    product_name: str,
    base_price: float,
    brand: str = "",
    platform: str = "trendyol",
) -> list[dict]:
    """
    Find alternatives on the SAME platform the user submitted.
    Never mixes platforms.
    """
    # Normalise platform — unknown platforms → trendyol
    if platform not in _JS_EXTRACTORS:
        platform = "trendyol"
    display_name = _DISPLAY.get(platform, "Web")

    ptype = extract_product_type(product_name, category, brand=brand)
    type_name = ptype["name"]
    queries   = ptype["queries"]
    required  = ptype["required"]
    forbidden = ptype["forbidden"]

    if not ptype.get("isSpecific"):
        print(f"[alt] non-specific type, attempting with relaxed filtering: {product_name!r}")
        required = []  # don't require specific keywords for unknown product types
        if not queries:
            print(f"[alt] no queries available, returning empty for: {product_name!r}")
            return []

    if brand:
        queries = queries + [f"{brand} {type_name}"]
    queries = list(dict.fromkeys(q for q in queries if q.strip()))

    print(f"[alt] platform={platform!r} type={type_name!r}")
    print(f"[alt] queries={queries}")
    print(f"[alt] required={required}  forbidden={forbidden}")

    target = 5
    accepted: list[dict] = []
    existing_urls: set[str] = set()
    base_norm = _norm(product_name)

    try:
        async with async_playwright() as p:
            browser = await p.chromium.launch(headless=True, args=_LAUNCH_ARGS)
            ctx = await browser.new_context(
                user_agent=(
                    "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) "
                    "AppleWebKit/537.36 (KHTML, like Gecko) "
                    "Chrome/124.0.0.0 Safari/537.36"
                ),
                locale="tr-TR",
                viewport={"width": 1280, "height": 900},
                extra_http_headers={"Accept-Language": "tr-TR,tr;q=0.9,en;q=0.8"},
            )
            await ctx.add_init_script(_STEALTH)
            page = await ctx.new_page()

            for query in queries:
                if len(accepted) >= target:
                    break

                raw_batch = await _scrape_query(page, query, platform, existing_urls)

                for item in raw_batch:
                    if len(accepted) >= target:
                        break
                    url  = item.get("url", "")
                    name = item.get("name", "")
                    if not url or not name or url in existing_urls:
                        continue
                    if _norm(name) == base_norm or base_norm in _norm(name):
                        continue

                    has_image = _is_valid_image(item.get("image"))
                    score = _relevance_score(
                        name, product_name, category, required, forbidden, type_name,
                        base_price, item.get("price", ""), has_image,
                    )
                    if score < 70:
                        continue

                    accepted.append({
                        "name": name,
                        "price": item.get("price", ""),
                        "image": item.get("image"),
                        "url": url,
                        "reason": f"Aynı ürün tipinde ({type_name}) {display_name} alternatifi.",
                        "platform": display_name,
                        "isDirectProductUrl": True,
                    })
                    existing_urls.add(url)
                    print(f"[alt] ACCEPTED score={score}: {name[:55]!r}")

                print(f"[alt] after '{query}': {len(accepted)} accepted")

            await browser.close()

    except Exception as e:
        print(f"[alt] Playwright error: {e}")
        traceback.print_exc()

    print(f"[alt] returning {len(accepted)} alts (platform={platform!r} type={type_name!r})")
    return accepted[:target]
