"""
Cross-platform price comparison.

Searches the same product on the other two platforms and returns ranked matches.
One Playwright browser, two pages in parallel — keeps total search time under ~12 s.
In-memory cache with 1-hour TTL avoids redundant scraping.

Matching pipeline (no AI — pure string analysis):
  1. _extract_universal_signature() — pulls out numerical specs, size, model
     numbers, variants, and key words from ANY product name.
  2. _prefilter_candidate() — splits candidates into:
       • hard-reject : different generation, different variant (Pro Max vs Pro)
       • soft-pass   : different capacity/size/color (same product, different variant)
       • exact-pass  : no detected conflicts
  3. Exact candidates are scored first; soft candidates are used only as fallback.
  4. Soft fallback is shown with a variant_warning and confidence capped at "low".
  5. Accept threshold: 0.80 for exact, 0.75 for soft fallback.
"""

import asyncio
import re
import time
from difflib import SequenceMatcher
from urllib.parse import quote_plus

from playwright.async_api import async_playwright

from .alternative_scraper import (
    _JS_HEPSIBURADA,
    _JS_AMAZON,
    _LAUNCH_ARGS,
    _STEALTH,
    _norm,
    _is_valid_image,
    _parse_price,
)
from .price_utils import parse_tr_price

# ─── Constants ───────────────────────────────────────────────────────────────

_UA = (
    "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) "
    "AppleWebKit/537.36 (KHTML, like Gecko) "
    "Chrome/124.0.0.0 Safari/537.36"
)

_ALL_PLATFORMS = ["trendyol", "hepsiburada", "amazon_tr"]

_PLATFORM_SEARCH_URL = {
    "trendyol":    "https://www.trendyol.com/sr?q={}",
    "hepsiburada": "https://www.hepsiburada.com/ara?q={}",
    "amazon_tr":   "https://www.amazon.com.tr/s?k={}",
}

# Color words excluded from search queries to widen results
_COLOR_WORDS = frozenset({
    # Turkish
    'siyah', 'beyaz', 'mavi', 'kırmızı', 'gri', 'yeşil', 'sarı', 'pembe',
    'mor', 'lacivert', 'kahverengi', 'turuncu', 'bej', 'altın', 'gümüş',
    'titanyum', 'kozmik', 'doğal', 'çöl', 'gece', 'yıldız',
    # English (appear in Turkish product names for Apple/Samsung products)
    'black', 'white', 'blue', 'red', 'gray', 'grey', 'green', 'yellow',
    'pink', 'purple', 'brown', 'orange', 'beige', 'gold', 'silver',
    'titanium', 'cosmic', 'natural', 'desert', 'midnight', 'starlight',
    'graphite', 'sierra', 'pacific',
})

# Trendyol JS extractor — content-based price search handles class-name changes
_JS_TRENDYOL_CROSS = """
() => {
    // Turkish price pattern: digits with optional thousands-dot and decimal-comma
    const TR_PRICE_RE = /\\d{1,3}(?:\\.\\d{3})*(?:,\\d{1,2})?\\s*(?:TL|₺)/i;

    function extractPrice(a) {
        // 1) Named selectors (most precise — try first)
        const namedSels = [
            '[class*="prc-box-dscntd"]',
            '[class*="prc-box-sllng"]',
            '[class*="prc-slg"]',
            '[class*="prc-dsc"]',
            '[class*="price-item"]',
            'span[class*="prc-box"]',
            'div[class*="product-price"] span',
            'span.price-value',
            '[class="price-value"]',
            '[class*="price-value"]',
            '[class*="selling-price"]',
        ];
        for (const sel of namedSels) {
            const el = a.querySelector(sel);
            if (!el) continue;
            const t = el.textContent.trim().replace(/\\s+/g, ' ');
            if (t && /\\d/.test(t)) return t;
        }

        // 2) Content-based: any element (not too deep) whose text matches TR price
        const allEls = Array.from(a.querySelectorAll('*'));
        for (const el of allEls) {
            if (el.children.length > 4) continue; // skip large containers
            const t = el.textContent.trim().replace(/\\s+/g, ' ');
            if (TR_PRICE_RE.test(t)) {
                const m = t.match(TR_PRICE_RE);
                if (m) return m[0];
            }
        }

        // 3) Last-resort leaf scan — pick first element with TL/₺
        const leaves = allEls.filter(el => el.children.length === 0);
        for (const el of leaves) {
            const t = el.textContent.trim();
            if (/[\\d][.,]\\d.*(?:TL|₺)|(?:TL|₺).*\\d/.test(t)) return t;
        }
        return '';
    }

    const cards = Array.from(document.querySelectorAll(
        'a[data-testid="product-card"], a.product-card, a[href*="-p-"]'
    )).slice(0, 40);

    const results = [];
    for (const a of cards) {
        if (!a.href || !a.href.includes('trendyol.com') || !a.href.includes('-p-')) continue;

        const img = a.querySelector('img');
        const src = img ? (img.src || img.getAttribute('data-src') || '') : '';
        const alt = img ? (img.alt || '') : '';

        const nameEl = a.querySelector(
            'span.product-name, [class="product-name"], [class*="product-name"]'
        );
        let name = nameEl ? nameEl.textContent.trim() : alt;
        if (!name) continue;
        name = name.substring(0, 120);

        const price = extractPrice(a);

        results.push({ href: a.href, name, price, src });
        if (results.length >= 20) break;
    }
    return results;
}
"""

_JS_EXTRACTORS = {
    "trendyol":    _JS_TRENDYOL_CROSS,
    "hepsiburada": _JS_HEPSIBURADA,
    "amazon_tr":   _JS_AMAZON,
}

# ─── In-memory cache ─────────────────────────────────────────────────────────

_CACHE: dict[str, tuple[float, dict]] = {}
_CACHE_TTL = 3600


def _cache_key(source_platform: str, brand: str, name: str) -> str:
    words = _norm(f"{brand} {name}").split()[:5]
    return f"{source_platform}:{'_'.join(words)}"


def _get_cached(key: str) -> dict | None:
    entry = _CACHE.get(key)
    if entry and time.time() - entry[0] < _CACHE_TTL:
        return entry[1]
    _CACHE.pop(key, None)
    return None


def _set_cached(key: str, data: dict) -> None:
    # Don't cache all-empty results — transient scraper failure may have caused them
    matches = data.get("matches", [])
    if matches and all(not m.get("found") for m in matches):
        print(f"[cross] skipping cache (all not-found) key={key!r}")
        return
    _CACHE[key] = (time.time(), data)
    if len(_CACHE) > 500:
        cutoff = time.time() - _CACHE_TTL
        for k in [k for k, (ts, _) in list(_CACHE.items()) if ts < cutoff]:
            _CACHE.pop(k, None)


# ─── Signature extraction (used by _match_score for numerical penalties) ──────

_NOT_MODEL_WORDS = frozenset({
    've', 'ile', 'bir', 'yıl', 'son', 'en', 'bu', 'şu', 'da', 'de',
    'set', 'adet', 'paket', 'kutu', 'top', 'tane', 'parça',
    'renk', 'boya', 'kat', 'kap',
})


def _extract_universal_signature(name: str) -> dict:
    """Used internally by _match_score for numerical-spec penalty scoring."""
    nl = name.lower()
    _NUMERIC_PATTERNS: list[tuple[str, str]] = [
        (r'(\d+)\s*gb\b',                         'storage_gb'),
        (r'(\d+)\s*tb\b',                         'storage_tb'),
        (r'(\d+)\s*mb\b',                         'storage_mb'),
        (r'(\d+)\s*ml\b',                         'volume_ml'),
        (r'(\d+)\s*l\b(?!cd|ed)',                 'volume_l'),
        (r'(\d+)\s*mg\b',                         'weight_mg'),
        (r'(\d+)\s*(?:gr|g)\b(?!b)',              'weight_g'),
        (r'(\d+)\s*kg\b',                         'weight_kg'),
        (r'(\d+)\s*cm\b',                         'size_cm'),
        (r'(\d+)\s*mm\b',                         'size_mm'),
        (r'(\d+)\s*(?:inch|inç|")\b',             'size_inch'),
        (r'(\d+)\s*(?:numara|no\.?|beden)\b',     'shoe_size'),
        (r'(?:numara|no\.?|beden)\s*(\d+)\b',     'shoe_size'),
    ]
    numerical_specs: list[tuple[str, str]] = []
    seen: set[str] = set()
    for pattern, key in _NUMERIC_PATTERNS:
        m = re.search(pattern, nl)
        if m and key not in seen:
            numerical_specs.append((key, m.group(1)))
            seen.add(key)
    return {'numerical_specs': numerical_specs}


# ─── New pre-filter helpers ───────────────────────────────────────────────────

_TR_CHAR_MAP = str.maketrans('ıığğüüşşöö çç', 'iiggüüssöö cc')

_TR_TO_ASCII = str.maketrans(
    'ıİğĞüÜşŞöÖçÇâîû',
    'iigguussooccaiu',
)

_KNOWN_BRANDS = frozenset({
    'puma', 'nike', 'adidas', 'reebok', 'new balance', 'converse', 'vans',
    'apple', 'samsung', 'xiaomi', 'huawei', 'oppo', 'oneplus', 'sony',
    'lg', 'philips', 'arzum', 'tefal', 'fakir', 'bosch', 'braun', 'rowenta',
    'loreal', "l'oreal", 'maybelline', 'nyx', 'mac', 'urban decay', 'sephora',
    'mavi', 'koton', 'lcw', 'defacto', 'colins', 'pierre cardin', 'levi',
    'lacoste', 'tommy', 'polo', 'calvin klein',
})

_STOP_WORDS = frozenset({
    've', 'ile', 'icin', 'a', 'an', 'the', 'of', 'in', 'on', 'at', 'by',
    'erkek', 'kadin', 'cocuk', 'unisex', 'yetiskin',
    'spor', 'urun', 'yeni', 'orijinal', 'orjinal', 'garanti',
    'ayakkabi', 'sneaker', 'bot', 'sandalet',  # generic category words
    'telefon', 'akilli', 'cep',
})


def _normalize_text(text: str) -> str:
    """Lowercase + strip Turkish diacritics + collapse whitespace/punctuation."""
    if not text:
        return ""
    t = text.lower().translate(_TR_TO_ASCII)
    t = re.sub(r'[^\w\s]', ' ', t)
    return re.sub(r'\s+', ' ', t).strip()


def _extract_strong_signals(name: str) -> dict:
    """
    Extract only high-confidence discriminating signals.
    Used by the new prefilter and fast-track logic.
    """
    n = _normalize_text(name)
    tokens = set(n.split()) - _STOP_WORDS

    # Product codes: 5-10 char strings with at least one digit (e.g. 396353, HBCV00005)
    raw_codes = re.findall(r'\b([A-Za-z0-9]{5,10})\b', name)
    product_codes = frozenset(
        c.upper() for c in raw_codes if any(d.isdigit() for d in c)
    )

    # Detect brand
    detected_brand: str | None = None
    for brand in _KNOWN_BRANDS:
        if brand in n:
            detected_brand = brand
            break

    # Storage: "128 gb", "256gb", "512gb"
    storage_m = re.search(r'(\d{2,4})\s*(gb|tb)\b', n)
    storage = storage_m.group(0).replace(' ', '') if storage_m else None

    # Shoe size: 35-50
    shoe_size_m = re.search(r'\b(3[5-9]|4[0-9]|50)\b', n)
    shoe_size = shoe_size_m.group(1) if shoe_size_m else None

    # Explicit size in cm
    size_cm_m = re.search(r'(\d{2,3})\s*cm\b', n)
    size_cm = size_cm_m.group(1) if size_cm_m else None

    return {
        'normalized':    n,
        'tokens':        tokens,
        'product_codes': product_codes,
        'brand':         detected_brand,
        'storage':       storage,
        'shoe_size':     shoe_size,
        'size_cm':       size_cm,
    }


# ─── Pre-filter (new, relaxed) ────────────────────────────────────────────────

def _prefilter_candidate(
    source_name: str,
    cand_name: str,
    source_price: float = 0,
    cand_price: float = 0,
) -> tuple[bool, str]:
    """
    Philosophy: trust the scorer. Only hard-reject when we are CERTAIN
    the candidate is a different product — never reject due to language/
    capitalisation/color-translation differences.

    Returns (passes, reason).
    """
    if not cand_name or not cand_name.strip():
        return False, "empty name"

    # Marka kontrolü: kaynak ürünün ilk kelimesi adayda yoksa REDDET
    source_words = source_name.lower().split()
    candidate_name_lower = cand_name.lower()
    if source_words and len(source_words[0]) > 3:
        first_word = source_words[0]
        if first_word not in candidate_name_lower:
            return False, f"brand_first_word_missing: {first_word}"

    src = _extract_strong_signals(source_name)
    cnd = _extract_strong_signals(cand_name)

    # ── FAST-PASS: matching product code → definitely the same product ────────
    if src['product_codes'] and cnd['product_codes']:
        common = src['product_codes'] & cnd['product_codes']
        if common:
            return True, f"product_code_match:{common}"

    # ── HARD REJECT 1: clearly different brand ────────────────────────────────
    if src['brand'] and cnd['brand'] and src['brand'] != cnd['brand']:
        return False, f"brand_mismatch: {src['brand']} vs {cnd['brand']}"

    # ── HARD REJECT 2: storage mismatch (e.g. 128gb vs 256gb) ────────────────
    if src['storage'] and cnd['storage'] and src['storage'] != cnd['storage']:
        # Only reject if similarity is also low — same model exists in multiple
        # capacities but names are quite different
        sim = SequenceMatcher(None, src['normalized'], cnd['normalized']).ratio()
        if sim < 0.45:
            return False, f"storage_mismatch: {src['storage']} vs {cnd['storage']}"

    # ── HARD REJECT 3: explicit shoe size mismatch ────────────────────────────
    if src['shoe_size'] and cnd['shoe_size'] and src['shoe_size'] != cnd['shoe_size']:
        return False, f"shoe_size: {src['shoe_size']} vs {cnd['shoe_size']}"

    # ── HARD REJECT 4: explicit pan/pot cm size mismatch ─────────────────────
    if src['size_cm'] and cnd['size_cm'] and src['size_cm'] != cnd['size_cm']:
        return False, f"size_cm: {src['size_cm']} vs {cnd['size_cm']}"

    # ── SOFT CHECK: very low token overlap + very low similarity ──────────────
    src_tok = src['tokens']
    cnd_tok = cnd['tokens']
    if src_tok and cnd_tok:
        overlap = len(src_tok & cnd_tok) / min(len(src_tok), len(cnd_tok))
        if overlap < 0.15:
            sim = SequenceMatcher(None, src['normalized'], cnd['normalized']).ratio()
            if sim < 0.28:
                return False, f"low_overlap:{overlap:.2f} sim:{sim:.2f}"

    return True, "ok"


# ─── Scoring helpers ──────────────────────────────────────────────────────────

def _build_query(brand: str, name: str) -> str:
    """
    Build a targeted search query: brand + product model, excluding color words.
    Stripping colors widens results to all variants of the same model.
    """
    full = f"{brand} {name}".strip() if brand else name
    words = [w for w in full.split() if w.lower() not in _COLOR_WORDS]
    return " ".join(words[:7])


def _str_to_price(price_str: str) -> float | None:
    """Parse raw price text to float, handling Turkish format correctly."""
    return parse_tr_price(price_str)


def _match_score(
    source_name: str,
    source_brand: str,
    cand_name: str,
    cand_brand: str = "",
    source_price: float | None = None,
    cand_price: float | None = None,
) -> float:
    """
    0..1 score.
    - SequenceMatcher on combined name+brand strings
    - +0.15 brand exact-match bonus
    - −0.25 for each numerical spec type that both sides have but differ
    - −0.20 if prices differ by more than 5×
    """
    source_combined = _norm(f"{source_name} {source_brand}").strip()
    cand_combined   = _norm(f"{cand_name} {cand_brand}").strip()

    score: float = SequenceMatcher(None, source_combined, cand_combined).ratio()

    sb = _norm(source_brand).strip()
    if sb and sb in cand_combined:
        score += 0.15

    src_sig  = _extract_universal_signature(source_name)
    cand_sig = _extract_universal_signature(cand_name)
    src_nums  = dict(src_sig['numerical_specs'])
    cand_nums = dict(cand_sig['numerical_specs'])
    for key in src_nums:
        if key in cand_nums and src_nums[key] != cand_nums[key]:
            score -= 0.25

    try:
        sp = float(source_price or 0)
        cp = float(cand_price or 0)
        if sp > 0 and cp > 0 and max(sp, cp) / min(sp, cp) > 5:
            score -= 0.20
    except Exception:
        pass

    # KRİTİK KURAL: kaynak ürün adındaki marka (ilk kelime) adayda yoksa MAX 0.3
    source_first_words = source_name.lower().split()
    if source_first_words and len(source_first_words[0]) > 3:
        first_word = source_first_words[0]
        if first_word not in cand_name.lower():
            score = min(score, 0.30)

    return min(max(score, 0.0), 1.0)


def _platform_display_name(platform: str) -> str:
    return {
        "trendyol":    "Trendyol",
        "hepsiburada": "Hepsiburada",
        "amazon_tr":   "Amazon TR",
    }.get(platform, platform)


def _score_to_confidence(score: float) -> str:
    if score >= 0.85:
        return "high"
    if score >= 0.65:
        return "medium"
    return "low"    # 0.65–0.85


# ─── Playwright search ────────────────────────────────────────────────────────

async def _search_one_page(page, platform: str, query: str) -> list[dict]:
    url_tpl = _PLATFORM_SEARCH_URL.get(platform)
    if not url_tpl:
        return []

    search_url = url_tpl.format(quote_plus(query))
    print(f"[cross] {platform} → {search_url[:80]}")

    try:
        await page.goto(search_url, wait_until="domcontentloaded", timeout=25000)
    except Exception as e:
        print(f"[cross] {platform} goto error: {e}")
        return []

    await page.wait_for_timeout(1000)

    js = _JS_EXTRACTORS.get(platform, _JS_TRENDYOL_CROSS)
    try:
        items = await page.evaluate(js)
    except Exception as e:
        print(f"[cross] {platform} js error: {e}")
        return []

    candidates = []
    for item in (items or [])[:15]:          # increased from 10 → 15
        href = (item.get("href") or "").strip()
        name = (item.get("name") or "").strip()
        if not href or not name:
            continue
        price_raw  = item.get("price") or ""
        price_float = _str_to_price(price_raw)
        # Re-format to canonical Turkish string for display
        price_str = _parse_price(price_raw) if not price_float else (
            f"{int(price_float):,}".replace(",", ".") + " TL"
            if price_float == int(price_float)
            else f"{price_float:,.2f}".replace(",", "X").replace(".", ",").replace("X", ".") + " TL"
        )
        warn = " ⚠️ SUSPICIOUS" if (price_float is not None and price_float < 30) else ""
        print(f"[{platform}-search] raw={price_raw!r:35s} → parsed={price_float}{warn}")
        candidates.append({
            "name":        name[:120],
            "price_str":   price_str,
            "price":       price_float,
            "image_url":   item.get("src") if _is_valid_image(item.get("src")) else None,
            "product_url": href,
        })

    print(f"[cross] {platform} candidates={len(candidates)}")
    return candidates


async def _run_parallel_searches(
    query: str,
    target_platforms: list[str],
) -> dict[str, list[dict]]:
    results: dict[str, list[dict]] = {p: [] for p in target_platforms}

    async with async_playwright() as pw:
        browser = await pw.chromium.launch(headless=True, args=_LAUNCH_ARGS)
        ctx = await browser.new_context(
            user_agent=_UA,
            locale="tr-TR",
            viewport={"width": 1280, "height": 900},
            extra_http_headers={"Accept-Language": "tr-TR,tr;q=0.9,en;q=0.8"},
        )
        await ctx.add_init_script(_STEALTH)

        pages = [await ctx.new_page() for _ in target_platforms]
        raw_results = await asyncio.gather(
            *[_search_one_page(pg, plat, query) for pg, plat in zip(pages, target_platforms)],
            return_exceptions=True,
        )
        await browser.close()

    for plat, res in zip(target_platforms, raw_results):
        if isinstance(res, Exception):
            print(f"[cross] {plat} exception: {res}")
        else:
            results[plat] = res

    return results


# ─── Public API ──────────────────────────────────────────────────────────────

_ACCEPT_THRESHOLD = 0.65


async def find_cross_platform_matches(
    source_platform: str,
    product_name: str,
    brand: str,
    price: float,
) -> dict:
    """Find the same product on the other two platforms."""
    key = _cache_key(source_platform, brand, product_name)
    cached = _get_cached(key)
    if cached:
        print(f"[cross] cache hit key={key!r}")
        return cached

    target_platforms = [p for p in _ALL_PLATFORMS if p != source_platform]
    query = _build_query(brand, product_name)
    print(f"[cross] source={source_platform!r} query={query!r} targets={target_platforms}")

    try:
        search_results = await _run_parallel_searches(query, target_platforms)
    except Exception as e:
        print(f"[cross] search failed: {e}")
        search_results = {p: [] for p in target_platforms}

    src_signals = _extract_strong_signals(product_name)

    matches: list[dict] = []
    all_prices: list[tuple[str, float]] = []
    if price and price > 0:
        all_prices.append((source_platform, price))

    for platform in target_platforms:
        raw_candidates = search_results.get(platform, [])

        # ── Debug log ─────────────────────────────────────────────────────
        print(f"[cross] {platform} ===== FILTER START ({len(raw_candidates)} raw) =====")
        for c in raw_candidates[:5]:
            print(f"   raw: {c['name'][:80]!r}")

        # ── Pre-filter: hard rejects only ────────────────────────────────
        passed_cands: list[dict] = []
        hard_count = 0

        for cand in raw_candidates:
            passes, reason = _prefilter_candidate(
                product_name, cand["name"], price, cand.get("price") or 0
            )
            if not passes:
                print(f"[cross] hard-reject {platform}: {cand['name'][:55]!r} | {reason}")
                hard_count += 1
            else:
                passed_cands.append(cand)

        print(f"[cross] {platform}: passed={len(passed_cands)} hard_reject={hard_count}")

        # ── Product code fast-track ────────────────────────────────────────
        best_cand:  dict | None = None
        best_score: float = 0.0

        if src_signals['product_codes']:
            for cand in passed_cands:
                cnd_signals = _extract_strong_signals(cand["name"])
                common = src_signals['product_codes'] & cnd_signals['product_codes']
                if common:
                    print(f"[cross] {platform}: product_code fast-track {common} → {cand['name'][:60]!r}")
                    best_cand = cand
                    best_score = 1.0
                    break

        # ── Score if no fast-track hit ────────────────────────────────────
        if best_cand is None:
            for cand in passed_cands:
                score = _match_score(
                    product_name, brand,
                    cand["name"], cand_brand="",
                    source_price=price, cand_price=cand.get("price"),
                )
                if score > best_score:
                    best_score = score
                    best_cand  = cand

        print(f"[cross] {platform}: best_score={best_score:.3f} threshold={_ACCEPT_THRESHOLD}")

        if best_cand and best_score >= _ACCEPT_THRESHOLD:
            matches.append({
                "platform":         platform,
                "found":            True,
                "product_name":     best_cand["name"],
                "product_url":      best_cand["product_url"],
                "image_url":        best_cand["image_url"],
                "price":            best_cand["price"],
                "price_str":        best_cand["price_str"],
                "confidence":       _score_to_confidence(best_score),
                "match_score":      round(best_score, 3),
                "not_found_reason": None,
                "variant_warning":  None,
            })
            if best_cand["price"] and best_cand["price"] > 0:
                all_prices.append((platform, best_cand["price"]))
        else:
            not_found_reason = (
                "Bu platformda benzer ürün bulunamadı"
                if not raw_candidates
                else "Bu platformda aynı ürün bulunamadı"
            )
            matches.append({
                "platform":         platform,
                "found":            False,
                "product_name":     None,
                "product_url":      None,
                "image_url":        None,
                "price":            None,
                "price_str":        None,
                "confidence":       "not_found",
                "match_score":      round(best_score, 3) if best_score > 0 else None,
                "not_found_reason": not_found_reason,
                "variant_warning":  None,
            })

        print(f"[cross] {platform} ===== FILTER END =====")

    # Price comparison summary
    cheapest_platform: str | None = None
    cheapest_price_val: float | None = None
    most_expensive_platform: str | None = None
    most_expensive_price_val: float | None = None
    source_rank: int | None = None
    is_source_cheapest = False
    is_source_most_expensive = False
    savings_amount: float | None = None
    savings_pct: float | None = None
    comparison_message: str | None = None
    price_diff: float | None = None

    valid = sorted([(p, v) for p, v in all_prices if v and v > 0], key=lambda x: x[1])
    total_platforms_with_price = len(valid)

    if len(valid) >= 2:
        cheapest_platform         = valid[0][0]
        cheapest_price_val        = valid[0][1]
        most_expensive_platform   = valid[-1][0]
        most_expensive_price_val  = valid[-1][1]
        price_diff = round(most_expensive_price_val - cheapest_price_val, 2)

        for idx, (plat, _) in enumerate(valid):
            if plat == source_platform:
                source_rank = idx + 1
                break

        is_source_cheapest       = (source_platform == cheapest_platform)
        is_source_most_expensive = (source_platform == most_expensive_platform)

        if price and price > 0 and cheapest_price_val and cheapest_price_val > 0:
            if is_source_cheapest:
                if len(valid) > 1:
                    second_price = valid[1][1]
                    advantage = second_price - price
                    advantage_pct = (advantage / second_price * 100) if second_price > 0 else 0
                    savings_amount = round(advantage, 2)
                    savings_pct    = round(advantage_pct, 1)
                    comparison_message = (
                        f"Bu platform en ucuzu. Diğer platformlardan "
                        f"{advantage:.0f} TL (%{advantage_pct:.1f}) daha ucuz."
                    )
            else:
                loss = price - cheapest_price_val
                loss_pct = (loss / price * 100) if price > 0 else 0
                savings_amount     = round(-loss, 2)    # negative = kullanıcı fazla ödüyor
                savings_pct        = round(-loss_pct, 1)
                cheapest_name      = _platform_display_name(cheapest_platform)
                comparison_message = (
                    f"{cheapest_name} platformunda "
                    f"{loss:.0f} TL (%{loss_pct:.1f}) daha ucuz!"
                )

    result = {
        "source_platform":            source_platform,
        "source_product_name":        product_name,
        "source_price":               price,
        "matches":                    matches,
        # legacy (kept for backward compat)
        "cheapest_platform":          cheapest_platform,
        "price_difference_max":       price_diff,
        # new fields
        "cheapest_price":             cheapest_price_val,
        "most_expensive_platform":    most_expensive_platform,
        "most_expensive_price":       most_expensive_price_val,
        "source_rank":                source_rank,
        "total_platforms_with_price": total_platforms_with_price,
        "is_source_cheapest":         is_source_cheapest,
        "is_source_most_expensive":   is_source_most_expensive,
        "savings_amount":             savings_amount,
        "savings_percentage":         savings_pct,
        "comparison_message":         comparison_message,
    }

    _set_cached(key, result)
    print(f"[cross] done cheapest={cheapest_platform!r} diff={price_diff} source_rank={source_rank}")
    return result
