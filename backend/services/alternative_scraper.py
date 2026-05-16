import re
from urllib.parse import quote_plus
from playwright.async_api import async_playwright

STOP_WORDS = {
    "ve", "ile", "için", "bir", "bu", "ml", "gr", "kg", "adet",
    "li", "lü", "lı", "lu", "de", "da", "den", "dan", "ten", "tan",
    "the", "and", "with",
}

_GOOD_EXTS = (".jpg", ".jpeg", ".png", ".webp")
_BAD_PATTERNS = ("logo", "icon", "placeholder", "blank", "svg")


def _is_valid_image(url: str | None) -> bool:
    if not url or not isinstance(url, str):
        return False
    u = url.strip().lower()
    if not u.startswith("http"):
        return False
    if any(bad in u for bad in _BAD_PATTERNS):
        return False
    return True


def extract_search_query(product_name: str, category: str) -> str:
    """Extract 2-3 product-type keywords from the end of product name (brand names appear at start)."""
    if not product_name:
        return category.split("/")[0].strip() if category else ""

    words = product_name.lower().split()

    # Strip trailing units
    while words and re.match(r"^\d+$|^(ml|gr|kg|adet|li|lü|lı|lu|x|cm|mm)$", words[-1]):
        words.pop()

    # Collect meaningful words from the end
    meaningful = []
    for word in reversed(words):
        clean = re.sub(r"[^a-züöşçğı]", "", word)
        if len(clean) > 3 and clean not in STOP_WORDS and not clean.isdigit():
            meaningful.insert(0, clean)
        if len(meaningful) >= 3:
            break

    if meaningful:
        return " ".join(meaningful)

    return category.split("/")[0].strip() if category else product_name.split()[0]


async def _get_img_from_element(img_el) -> str | None:
    if not img_el:
        return None
    for attr in ("src", "data-src", "data-original", "data-lazy-src"):
        try:
            val = await img_el.get_attribute(attr)
            if val and val.strip() and val.strip().startswith("http"):
                if _is_valid_image(val.strip()):
                    return val.strip()
        except Exception:
            continue
    # srcset fallback
    try:
        ss = await img_el.get_attribute("srcset")
        if ss:
            first = ss.split(",")[0].strip().split(" ")[0]
            if first.startswith("http") and _is_valid_image(first):
                return first
    except Exception:
        pass
    return None


async def _parse_card(card) -> dict | None:
    """Parse one product card. Returns dict or None if invalid."""
    try:
        # URL — must be specific product page
        a_tag = await card.query_selector("a")
        if not a_tag:
            return None
        href = await a_tag.get_attribute("href") or ""
        if "-p-" not in href:
            return None
        url = ("https://www.trendyol.com" + href) if href.startswith("/") else href

        # Name
        name_el = await card.query_selector(".prdct-desc-cntnr-name, [class*='prdct-desc'] span, [class*='product-name']")
        brand_el = await card.query_selector(".prdct-desc-cntnr-ttl, [class*='brand'], [class*='prdct-ttl']")

        name_text = (await name_el.inner_text()).strip() if name_el else ""
        brand_text = (await brand_el.inner_text()).strip() if brand_el else ""
        full_name = f"{brand_text} {name_text}".strip() if brand_text else name_text

        if not full_name:
            # fallback: try alt text from image
            img_el = await card.query_selector("img")
            if img_el:
                alt = await img_el.get_attribute("alt") or ""
                full_name = alt.strip()

        if not full_name:
            return None

        # Price
        price_el = await card.query_selector(".prc-box-dscntd, .prc-box-sllng, [class*='price']")
        price_text = (await price_el.inner_text()).strip() if price_el else ""
        if price_text and "TL" not in price_text:
            price_text += " TL"

        # Image
        img_el = await card.query_selector("img.p-card-img, img[class*='product'], img[class*='card'], img")
        img_src = await _get_img_from_element(img_el)

        return {
            "name": full_name,
            "price": price_text,
            "image": img_src,
            "url": url,
            "reason": "Aynı kategoriden gerçek Trendyol ürünü.",
            "isDirectProductUrl": True,
        }
    except Exception as e:
        print(f"[alternatives] card parse error: {e}")
        return None


async def _scrape_search_page(page, target: int) -> list[dict]:
    """Scrape product cards from already-loaded search results page."""
    results = []

    # Wait for product cards
    try:
        await page.wait_for_selector(".p-card-wrppr, [class*='p-card'], article", timeout=10000)
    except Exception:
        pass

    # Try multiple card selectors
    card_selectors = [
        ".p-card-wrppr",
        "[class*='p-card-wrppr']",
        "article.p-card",
        "[data-testid*='product-card']",
    ]
    cards = []
    for sel in card_selectors:
        try:
            found = await page.query_selector_all(sel)
            if found:
                cards = found
                print(f"[alternatives] found {len(found)} cards with selector '{sel}'")
                break
        except Exception:
            continue

    if not cards:
        # Last resort: use JavaScript to find all product links
        try:
            links = await page.evaluate("""
                () => {
                    return Array.from(document.querySelectorAll('a[href*="-p-"]'))
                        .slice(0, 20)
                        .map(a => {
                            const href = a.href;
                            const img = a.querySelector('img');
                            const src = img ? (img.src || img.getAttribute('data-src') || '') : '';
                            const nameEl = a.querySelector('[class*="name"], [class*="title"], span');
                            const name = nameEl ? nameEl.textContent.trim() : '';
                            const priceEl = a.querySelector('[class*="price"], [class*="prc"]');
                            const price = priceEl ? priceEl.textContent.trim() : '';
                            return { href, src, name, price };
                        })
                        .filter(p => p.name && p.href.includes('-p-'));
                }
            """)
            for link_data in (links or [])[:target]:
                if len(results) >= target:
                    break
                href = link_data.get("href", "")
                name = link_data.get("name", "")
                price = link_data.get("price", "")
                src = link_data.get("src", "")
                if not name or not href:
                    continue
                if not href.startswith("http"):
                    href = "https://www.trendyol.com" + href
                if price and "TL" not in price:
                    price += " TL"
                results.append({
                    "name": name[:120],
                    "price": price,
                    "image": src if _is_valid_image(src) else None,
                    "url": href,
                    "reason": "Aynı kategoriden gerçek Trendyol ürünü.",
                    "isDirectProductUrl": True,
                })
        except Exception as e:
            print(f"[alternatives] JS link extraction error: {e}")
        return results

    for card in cards:
        if len(results) >= target:
            break
        parsed = await _parse_card(card)
        if parsed:
            results.append(parsed)

    return results


async def get_alternatives(category: str, product_name: str, base_price: float) -> list[dict]:
    query = extract_search_query(product_name, category)
    encoded_query = quote_plus(query)
    search_url = f"https://www.trendyol.com/sr?q={encoded_query}"

    print(f"[alternatives] query={query!r}  url={search_url}")

    results = []
    target = 5

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
                await page.goto(search_url, wait_until="networkidle", timeout=45000)
            except Exception:
                try:
                    await page.goto(search_url, wait_until="domcontentloaded", timeout=30000)
                except Exception as e:
                    print(f"[alternatives] page load error: {e}")

            await page.wait_for_timeout(3000)

            results = await _scrape_search_page(page, target)

            # If not enough results, try a shorter query
            if len(results) < 3 and " " in query:
                shorter_query = query.split()[0]
                fallback_url = f"https://www.trendyol.com/sr?q={quote_plus(shorter_query)}"
                print(f"[alternatives] retrying with shorter query={shorter_query!r}")
                try:
                    await page.goto(fallback_url, wait_until="domcontentloaded", timeout=30000)
                    await page.wait_for_timeout(2000)
                    more = await _scrape_search_page(page, target - len(results))
                    # Avoid duplicates by URL
                    existing_urls = {r["url"] for r in results}
                    for r in more:
                        if r["url"] not in existing_urls:
                            results.append(r)
                            existing_urls.add(r["url"])
                except Exception as e:
                    print(f"[alternatives] fallback search error: {e}")

            await browser.close()

    except Exception as e:
        print(f"[alternatives] Playwright error: {e}")

    print(f"[alternatives] returning {len(results)} alternatives")
    if not results:
        print("[alternatives] WARNING: No alternatives found — Trendyol may have blocked the request or the query returned no products.")

    return results[:target]
