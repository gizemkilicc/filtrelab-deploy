import os
import re
import json
import asyncio
from urllib.parse import parse_qsl, urlencode, urlparse, urlunparse
from playwright.async_api import async_playwright

from .review_analytics import compute_star_quota, compute_review_analytics

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

_EMBEDDED_KEYWORDS = (
    "productdetail", "productdata", "review", "comment", "rating", "campaign",
    "price", "offer", "sellingprice", "discountedprice", "saleprice",
)
_PRICE_KEYS = {
    "price", "saleprice", "sellingprice", "discountedprice", "campaignprice",
    "originalprice", "pricevalue", "basketprice", "productprice",
}
_COUNT_KEYS = {
    "reviewcount", "commentcount", "ratingcount", "totalreviewcount",
    "totalcommentcount", "totalelements", "totalcount",
}
_QUESTION_KEYS = {
    "questioncount", "totalquestioncount", "questiontotalcount",
    "answeredquestioncount", "totalquestions", "qnacount",
}

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


def _price_to_float(value: str | None) -> float | None:
    if not value:
        return None
    text = str(value).replace("TL", "").replace("₺", "").strip()
    text = re.sub(r"[^\d,.]", "", text)
    if not text:
        return None
    try:
        if "," in text:
            return float(text.replace(".", "").replace(",", "."))
        if "." in text and len(text.rsplit(".", 1)[-1]) in (1, 2):
            return float(text)
        return float(text.replace(".", ""))
    except ValueError:
        return None


def _format_price_candidate(value: str | None) -> str | None:
    parsed = _price_to_float(value)
    if parsed is None or parsed <= 0:
        return None
    return format_price_turkish(parsed)


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


async def extract_price_candidates(page, jsonld_price: str | None = None, meta_price: str | None = None) -> list[dict]:
    candidates: list[dict] = []
    if jsonld_price:
        formatted = _format_price_candidate(jsonld_price)
        if formatted:
            candidates.append({
                "text": formatted,
                "source": "jsonld_offers",
                "parentText": "JSON-LD offers.price",
                "confidence": 80,
            })
    if meta_price:
        formatted = _format_price_candidate(meta_price)
        if formatted:
            candidates.append({
                "text": formatted,
                "source": "meta_product_price",
                "parentText": "meta product:price:amount",
                "confidence": 40,
            })

    try:
        dom_candidates = await page.evaluate("""
            () => {
                const selectors = [
                    '.prc-dsc',
                    '.prc-slg',
                    '.prc-box-dscntd',
                    '.product-price-container',
                    '[data-testid*="price"]',
                    '[class*="product-price"]',
                    '[class*="price-container"]'
                ];
                const badContext = [
                    'diğer satıcı', 'diger satici', 'benzer ürün', 'benzer urun',
                    'taksit', 'kargo', 'önerilen', 'onerilen', 'sepete ekle',
                    'birlikte al', 'kampanya'
                ];
                const out = [];
                const seen = new Set();
                const pushCandidate = (el, selector) => {
                    if (!el) return;
                    const text = (el.textContent || '').replace(/\\s+/g, ' ').trim();
                    const match = text.match(/(?:₺\\s*)?([\\d]{1,3}(?:\\.\\d{3})*(?:,\\d{1,2})?|\\d+(?:,\\d{1,2})?)\\s*(?:TL|₺)?/i);
                    if (!match) return;
                    const priceText = match[0].includes('TL') || match[0].includes('₺') ? match[0] : match[1] + ' TL';
                    if (seen.has(priceText + selector)) return;
                    seen.add(priceText + selector);
                    const parent = el.closest('.product-detail-container, .product-container, .pr-in-w, .pdp, main, body');
                    const parentText = ((parent && parent.textContent) || '').replace(/\\s+/g, ' ').trim().slice(0, 260);
                    let confidence = 0;
                    if (/prc-dsc|prc-slg|prc-box-dscntd|product-price-container/.test(selector)) confidence += 72;
                    if (parent && parent !== document.body) confidence += 20;
                    const ctx = parentText.toLocaleLowerCase('tr-TR');
                    for (const bad of badContext) {
                        if (ctx.includes(bad)) confidence -= 50;
                    }
                    out.push({ text: priceText, source: selector, parentText, confidence });
                };
                for (const selector of selectors) {
                    document.querySelectorAll(selector).forEach(el => pushCandidate(el, selector));
                }
                return out;
            }
        """)
        for item in dom_candidates or []:
            formatted = _format_price_candidate(item.get("text"))
            if not formatted:
                continue
            candidates.append({
                "text": formatted,
                "source": item.get("source", "dom"),
                "parentText": item.get("parentText", "")[:160],
                "confidence": int(item.get("confidence") or 0),
            })
    except Exception as e:
        print(f"[PRICE CANDIDATES] extraction_error={e}")

    candidates = [c for c in candidates if _price_to_float(c.get("text")) is not None]
    candidates.sort(key=lambda c: c.get("confidence", 0), reverse=True)
    print(f"[PRICE DOM CANDIDATES] {json.dumps([c for c in candidates if not str(c.get('source')).startswith(('jsonld', 'meta'))][:8], ensure_ascii=False)}")
    return candidates


def _select_price_candidate(candidates: list[dict]) -> tuple[str | None, str | None]:
    if not candidates:
        print("[PRICE SELECTED] None")
        print("[PRICE SOURCE] missing")
        print("[PRICE WHY] no candidates found")
        return None, None

    # Separate DOM main-container candidates from API/JSON sources
    dom_main = [
        c for c in candidates
        if any(sel in str(c.get("source", ""))
               for sel in ("prc-dsc", "prc-slg", "prc-box-dscntd", "product-price-container"))
    ]
    api_candidates = [
        c for c in candidates
        if str(c.get("source", "")).startswith(("embedded_json", "jsonld", "meta"))
    ]

    selected = candidates[0]
    why = f"highest confidence={selected.get('confidence')} among {len(candidates)} candidates"

    # If DOM main-container and API sources exist, compare them
    if dom_main and api_candidates:
        dom_price = _price_to_float(dom_main[0].get("text"))
        api_price = _price_to_float(api_candidates[0].get("text"))
        if dom_price and api_price:
            diff_pct = abs(dom_price - api_price) / max(dom_price, api_price)
            if diff_pct > 0.05:
                # Sources disagree by >5% → prefer main product DOM container
                print(
                    f"[PRICE WHY] source mismatch: dom_main={dom_price} ({dom_main[0].get('source')}) "
                    f"vs api={api_price} ({api_candidates[0].get('source')}) diff={diff_pct:.1%} "
                    f"— preferring DOM main container"
                )
                selected = dom_main[0]
                why = f"mismatch resolved: dom_main preferred (diff={diff_pct:.1%})"
            else:
                why += f"; sources agree within {diff_pct:.1%}"

    print(f"[PRICE SELECTED] {selected.get('text')}")
    print(f"[PRICE SOURCE] {selected.get('source')} confidence={selected.get('confidence')}")
    print(f"[PRICE WHY] {why}")
    return selected.get("text"), selected.get("source")


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


def _iter_jsonld_products(data):
    if isinstance(data, list):
        for item in data:
            yield from _iter_jsonld_products(item)
    elif isinstance(data, dict):
        node_type = data.get("@type")
        if node_type == "Product" or (isinstance(node_type, list) and "Product" in node_type):
            yield data
        for key in ("@graph", "graph", "itemListElement"):
            child = data.get(key)
            if child:
                yield from _iter_jsonld_products(child)
        item = data.get("item")
        if item:
            yield from _iter_jsonld_products(item)


def _extract_balanced_json(text: str, start: int) -> str | None:
    while start < len(text) and text[start] not in "{[":
        start += 1
    if start >= len(text):
        return None
    opener = text[start]
    closer = "}" if opener == "{" else "]"
    stack = [closer]
    in_string = False
    escape = False
    quote = ""
    for i in range(start + 1, len(text)):
        ch = text[i]
        if in_string:
            if escape:
                escape = False
            elif ch == "\\":
                escape = True
            elif ch == quote:
                in_string = False
            continue
        if ch in ("'", '"'):
            in_string = True
            quote = ch
            continue
        if ch in "{[":
            stack.append("}" if ch == "{" else "]")
        elif stack and ch == stack[-1]:
            stack.pop()
            if not stack:
                return text[start:i + 1]
    return None


def _loads_jsonish(raw: str):
    raw = (raw or "").strip()
    if not raw:
        return None
    try:
        return json.loads(raw)
    except Exception:
        return None


def _extract_embedded_json_objects(html: str) -> list[tuple[str, object]]:
    objects: list[tuple[str, object]] = []
    if not html:
        return objects

    for idx, match in enumerate(re.finditer(
        r"<script\b([^>]*)>(.*?)</script>",
        html,
        flags=re.IGNORECASE | re.DOTALL,
    )):
        attrs = match.group(1) or ""
        script = match.group(2) or ""
        attrs_l = attrs.lower()
        script_l = script.lower()
        source = f"script_{idx}"

        if "application/ld+json" in attrs_l:
            data = _loads_jsonish(script)
            if data is not None:
                objects.append(("jsonld", data))
            continue

        if "__next_data__" in attrs_l or "__next_data__" in script_l:
            data = _loads_jsonish(script)
            if data is not None:
                objects.append(("__NEXT_DATA__", data))
                continue

        if not any(k in script_l for k in _EMBEDDED_KEYWORDS):
            continue

        # Try direct JSON first, then assignments such as window.__INITIAL_STATE__ = {...}
        data = _loads_jsonish(script)
        if data is not None:
            objects.append((source, data))
            continue

        for key in (
            "__INITIAL_STATE__", "__PRODUCT_DETAIL_APP_INITIAL_STATE__", "__PRODUCT_DETAIL_STATE__",
            "productDetail", "productData", "window.__INITIAL_STATE__",
        ):
            pos = script.find(key)
            if pos == -1:
                continue
            raw_json = _extract_balanced_json(script, pos)
            data = _loads_jsonish(raw_json or "")
            if data is not None:
                objects.append((key, data))
                break

    print(f"[SOURCE JSON] parsed={len(objects)}")
    return objects


def _path_has(path: list[str], *needles: str) -> bool:
    joined = ".".join(path).lower()
    return any(n in joined for n in needles)


def _normalise_candidate_price(value) -> str | None:
    if isinstance(value, dict):
        for key in ("value", "text", "price", "amount", "sellingPrice", "discountedPrice"):
            if key in value:
                formatted = _normalise_candidate_price(value.get(key))
                if formatted:
                    return formatted
        return None
    return _format_price_candidate(str(value))


def _extract_json_price_candidates(objects: list[tuple[str, object]], product_id: str | None) -> list[dict]:
    candidates: list[dict] = []

    def walk(value, source: str, path: list[str], product_context: bool):
        current_context = product_context
        if isinstance(value, dict):
            lower = {str(k).lower(): v for k, v in value.items()}
            dict_text = json.dumps(value, ensure_ascii=False)[:2500].lower()
            if product_id and product_id in dict_text:
                current_context = True
            if any(k in lower for k in ("productid", "contentid", "id")) and any(
                token in ".".join(path).lower() for token in ("product", "detail", "content")
            ):
                current_context = True

            for key, raw in value.items():
                key_l = str(key).lower()
                next_path = path + [key_l]
                if key_l in _PRICE_KEYS:
                    formatted = _normalise_candidate_price(raw)
                    if formatted:
                        confidence = 75
                        if key_l in {"sellingprice", "discountedprice", "saleprice", "productprice"}:
                            confidence += 5
                        if current_context or _path_has(next_path, "productdetail", "product", "pdp", "content"):
                            confidence += 10
                        if _path_has(next_path, "coupon", "kupon", "shipping", "cargo", "kargo", "installment", "taksit", "othermerchant", "merchant"):
                            confidence -= 80
                        candidates.append({
                            "text": formatted,
                            "source": f"embedded_json:{source}:{'.'.join(next_path[-4:])}",
                            "parentText": ".".join(next_path[-6:]),
                            "confidence": confidence,
                        })
                walk(raw, source, next_path, current_context)
        elif isinstance(value, list):
            for idx, child in enumerate(value[:300]):
                walk(child, source, path + [str(idx)], current_context)

    for source, data in objects:
        walk(data, source, [], False)

    unique: dict[tuple[str, str], dict] = {}
    for c in candidates:
        key = (c["text"], c["source"])
        if key not in unique or c["confidence"] > unique[key]["confidence"]:
            unique[key] = c
    out = sorted(unique.values(), key=lambda c: c.get("confidence", 0), reverse=True)
    print(f"[PRICE JSON CANDIDATES] {json.dumps(out[:10], ensure_ascii=False)}")
    return out


def _extract_json_review_count(objects: list[tuple[str, object]], product_id: str | None) -> tuple[int | None, str | None]:
    candidates: list[tuple[int, str, int]] = []

    def walk(value, source: str, path: list[str], product_context: bool):
        current_context = product_context
        if isinstance(value, dict):
            text_preview = json.dumps(value, ensure_ascii=False)[:2500].lower()
            if product_id and product_id in text_preview:
                current_context = True
            for key, raw in value.items():
                key_l = str(key).lower()
                next_path = path + [key_l]
                if key_l in _COUNT_KEYS:
                    n = _extract_first_number(raw)
                    if n is not None and n > 0:
                        score = 50
                        if key_l in {"reviewcount", "commentcount", "ratingcount", "totalreviewcount", "totalcommentcount"}:
                            score += 30
                        if current_context or _path_has(next_path, "product", "detail", "rating", "review", "comment"):
                            score += 20
                        if _path_has(next_path, "search", "listing", "merchant", "seller", "coupon", "campaign"):
                            score -= 50
                        if score >= 60:
                            candidates.append((score, f"embedded_json:{source}:{'.'.join(next_path[-5:])}", n))
                walk(raw, source, next_path, current_context)
        elif isinstance(value, list):
            for idx, child in enumerate(value[:300]):
                walk(child, source, path + [str(idx)], product_context)

    for source, data in objects:
        walk(data, source, [], False)

    candidates.sort(reverse=True)
    if candidates:
        score, source, count = candidates[0]
        print(f"[COUNT SOURCE] embedded reviewCount={count} source={source} score={score}")
        return count, source
    return None, None


def _extract_json_question_count(objects: list[tuple[str, object]], product_id: str | None) -> tuple[int | None, str | None]:
    candidates: list[tuple[int, str, int]] = []

    def walk(value, source: str, path: list[str], product_context: bool):
        current_context = product_context
        if isinstance(value, dict):
            text_preview = json.dumps(value, ensure_ascii=False)[:2500].lower()
            if product_id and product_id in text_preview:
                current_context = True
            for key, raw in value.items():
                key_l = str(key).lower()
                next_path = path + [key_l]
                if key_l in _QUESTION_KEYS:
                    n = _extract_first_number(raw)
                    if n is not None and n >= 0:
                        score = 50
                        if current_context or _path_has(next_path, "product", "detail", "question"):
                            score += 20
                        if _path_has(next_path, "search", "listing", "merchant", "seller"):
                            score -= 50
                        if score >= 50:
                            candidates.append((score, f"embedded_json:{source}:{'.'.join(next_path[-5:])}", n))
                walk(raw, source, next_path, current_context)
        elif isinstance(value, list):
            for idx, child in enumerate(value[:300]):
                walk(child, source, path + [str(idx)], product_context)

    for source, data in objects:
        walk(data, source, [], False)

    candidates.sort(reverse=True)
    if candidates:
        score, source, count = candidates[0]
        print(f"[COUNT SOURCE] embedded questionCount={count} source={source} score={score}")
        return count, source
    return None, None


def _extract_embedded_reviews(objects: list[tuple[str, object]], product_name: str | None) -> tuple[list[dict], dict | None, str]:
    best_reviews: list[dict] = []
    best_dist: dict | None = None
    best_source = "embedded_json"
    for source, data in objects:
        reviews, dist, _ = _parse_review_body(data, product_name)
        if len(reviews) > len(best_reviews):
            best_reviews = reviews
            best_dist = dist
            best_source = f"embedded_json:{source}"
    print(f"[REVIEWS] embedded_json={len(best_reviews)}")
    return best_reviews, best_dist, best_source


def _debug_json_parse_failure(body: dict, product_name: str | None = None) -> None:
    try:
        keys = list(body.keys())[:30] if isinstance(body, dict) else []
        print(f"[REVIEWS DEBUG] raw top-level keys={keys}")

        if isinstance(body, dict):
            for top_k, top_v in list(body.items())[:6]:
                if isinstance(top_v, dict):
                    nested_keys = list(top_v.keys())[:20]
                    print(f"[REVIEWS DEBUG] nested keys under '{top_k}'={nested_keys}")
                    for sub_k, sub_v in list(top_v.items())[:3]:
                        if isinstance(sub_v, list) and sub_v:
                            first = sub_v[0]
                            if isinstance(first, dict):
                                print(f"[REVIEWS DEBUG] list '{top_k}.{sub_k}' item keys={list(first.keys())[:15]}")
                                print(f"[REVIEWS DEBUG] first item preview={json.dumps(first, ensure_ascii=False)[:300]}")
                elif isinstance(top_v, list) and top_v:
                    first = top_v[0]
                    if isinstance(first, dict):
                        print(f"[REVIEWS DEBUG] list '{top_k}' item keys={list(first.keys())[:15]}")
                        print(f"[REVIEWS DEBUG] first 2 items={json.dumps(top_v[:2], ensure_ascii=False)[:400]}")

        preview = json.dumps(body, ensure_ascii=False)[:1200]
        print(f"[REVIEWS DEBUG] raw preview={preview}")
        retry_reviews = _dedupe_reviews(_collect_reviews_recursive(body, product_name), product_name)
        print(f"[REVIEWS DEBUG] recursive_retry={len(retry_reviews)}")
    except Exception as e:
        print(f"[REVIEWS DEBUG] failed to inspect raw response: {e}")


def _try_known_trendyol_structures(body: dict, product_name: str | None = None) -> list[dict]:
    """Try known Trendyol API container paths before falling back to recursive search."""
    container_paths = [
        ["result", "productReviews"],
        ["result", "commentList"],
        ["result", "reviews"],
        ["result", "content"],
        ["result", "elements"],
        ["result", "items"],
        ["result", "reviewList"],
        ["result", "commentItems"],
        ["result", "reviewsContent"],
        ["data", "content"],
        ["data", "reviews"],
        ["data", "commentList"],
        ["data", "items"],
        ["productReviews"],
        ["commentList"],
        ["reviews"],
        ["comments"],
        ["content"],
        ["elements"],
        ["items"],
        ["reviewList"],
        ["commentItems"],
        ["reviewsContent"],
    ]
    text_keys_ordered = [
        "comment", "commenttext", "reviewtext", "text",
        "message", "description", "commentcontent", "reviewcomment",
        "userreviewcomment", "body", "feedback", "opinion", "content",
    ]
    rating_keys_ordered = [
        "commentrate", "rating", "rate", "star", "starrating",
        "userreviewrate", "ratingvalue", "commentrating", "reviewrate", "score",
    ]
    user_keys_ordered = [
        "userdisplayname", "username", "user", "nickname",
        "customername", "userfullname", "displayname",
    ]
    date_keys_ordered = [
        "commentdate", "date", "createddate", "reviewdate", "userreviewdate", "lastmodifieddate",
    ]

    def _get_path(node, parts: list[str]):
        for part in parts:
            if not isinstance(node, dict):
                return None
            found = node.get(part)
            if found is None:
                found = next((v for k, v in node.items() if k.lower() == part.lower()), None)
            node = found
        return node

    for path in container_paths:
        review_list = _get_path(body, path)
        if not isinstance(review_list, list) or not review_list:
            continue
        if not isinstance(review_list[0], dict):
            continue
        print(f"[REVIEWS DEBUG] known structure path={'.'.join(path)!r} count={len(review_list)}")

        reviews = []
        for item in review_list:
            if not isinstance(item, dict):
                continue
            lower_item = {str(k).lower(): v for k, v in item.items()}
            text = None
            for key in text_keys_ordered:
                raw = lower_item.get(key)
                if isinstance(raw, str) and len(raw.strip()) >= 10:
                    if not _looks_like_ui_review_text(raw, product_name):
                        text = _normalise_review_text(raw)
                        break
            if not text:
                continue
            rating = None
            for key in rating_keys_ordered:
                n = _extract_first_number(lower_item.get(key))
                if n is not None and 1 <= n <= 5:
                    rating = n
                    break
            user = None
            for key in user_keys_ordered:
                raw = lower_item.get(key)
                if isinstance(raw, str) and raw.strip():
                    user = _normalise_review_text(raw)
                    break
            date = None
            for key in date_keys_ordered:
                raw = lower_item.get(key)
                if raw is not None and str(raw).strip():
                    date = str(raw).strip()
                    break
            raw_id = (
                lower_item.get("id") or lower_item.get("reviewid")
                or lower_item.get("commentid") or ""
            )
            reviews.append({
                "id": str(raw_id) if raw_id else "",
                "text": text,
                "rating": rating,
                "date": date,
                "user": user,
                "source": "trendyol_reviews_api",
            })

        if reviews:
            return reviews

    return []


def _normalise_review_text(value: str) -> str:
    return re.sub(r"\s+", " ", value or "").strip()


def _looks_like_ui_review_text(text: str, product_name: str | None = None) -> bool:
    clean = _normalise_review_text(text)
    low = clean.lower()
    if len(clean) < 10:
        return True
    if product_name and clean[:100].lower() == product_name[:100].lower():
        return True
    ui_phrases = (
        "değerlendirmeler", "yorumları göster", "daha fazla", "satıcıya sor",
        "ürünü değerlendir", "yorum yaz", "sepete ekle", "tüm yorumlar",
        "fotoğraflı yorum", "yardımcı oldu", "filtrele", "sırala",
    )
    if any(p in low for p in ui_phrases):
        return True
    pname = (product_name or "").lower()
    cosmetic_product = any(k in pname for k in ("krem", "cream", "nemlendirici", "atoderm", "maskara", "serum", "tonik"))
    if cosmetic_product and re.search(r"\b(xs|s beden|m beden|l beden|xl|boyum|kilom|beden|elbise|pantolon)\b", low):
        return True
    return False


def _extract_first_number(value) -> int | None:
    if value is None:
        return None
    if isinstance(value, bool):
        return None
    if isinstance(value, (int, float)):
        return int(value)
    text = str(value)
    match = re.search(r"\d+", text.replace(".", "").replace(",", ""))
    return int(match.group(0)) if match else None


def _collect_reviews_recursive(node, product_name: str | None = None) -> list[dict]:
    text_keys = {
        "text", "comment", "reviewtext", "content", "message", "commenttext", "review", "description",
        "commentcontent", "reviewcomment", "userreviewcomment", "reviewbody", "body", "feedback",
        "opinion", "commentbody",
    }
    rating_keys = {
        "rating", "rate", "star", "score", "starcount", "ratingscore",
        "commentrate", "starrating", "reviewrating", "commentrating", "userreviewrate",
        "ratingvalue", "starvalue", "reviewrate",
    }
    user_keys = {"user", "username", "nickname", "customername", "userfullname", "displayname", "userdisplayname"}
    date_keys = {"date", "createddate", "commentdate", "reviewdate", "userreviewdate", "lastmodifieddate"}
    id_keys = {"id", "reviewid", "commentid"}
    reviews: list[dict] = []

    def walk(value):
        if isinstance(value, dict):
            lower = {str(k).lower(): v for k, v in value.items()}
            text = None
            for key in text_keys:
                raw = lower.get(key)
                if isinstance(raw, str) and not _looks_like_ui_review_text(raw, product_name):
                    text = _normalise_review_text(raw)
                    break
            if text:
                rating = None
                for key in rating_keys:
                    n = _extract_first_number(lower.get(key))
                    if n is not None and 1 <= n <= 5:
                        rating = n
                        break
                user = None
                for key in user_keys:
                    raw = lower.get(key)
                    if isinstance(raw, str) and raw.strip():
                        user = _normalise_review_text(raw)
                        break
                date = None
                for key in date_keys:
                    raw = lower.get(key)
                    if raw is not None and str(raw).strip():
                        date = str(raw).strip()
                        break
                raw_id = None
                for key in id_keys:
                    raw = lower.get(key)
                    if raw is not None and str(raw).strip():
                        raw_id = str(raw).strip()
                        break
                reviews.append({
                    "id": raw_id or "",
                    "text": text,
                    "rating": rating,
                    "date": date,
                    "user": user,
                    "source": "trendyol_reviews_api",
                })
            for child in value.values():
                walk(child)
        elif isinstance(value, list):
            for child in value:
                walk(child)

    walk(node)
    return reviews


def _find_rating_distribution(node) -> dict | None:
    found: dict[str, int] | None = None

    def as_distribution(value) -> dict | None:
        if not isinstance(value, dict):
            return None
        dist: dict[str, int] = {}
        for key, raw in value.items():
            key_text = str(key).lower()
            star = _extract_first_number(key_text)
            count = _extract_first_number(raw)
            if star is not None and count is not None and 1 <= star <= 5:
                dist[str(star)] = count
        return dist if len(dist) >= 2 else None

    def walk(value):
        nonlocal found
        if found is not None:
            return
        if isinstance(value, dict):
            for key, child in value.items():
                key_l = str(key).lower()
                if any(token in key_l for token in ("distribution", "ratingcount", "starcount", "ratingsummary")):
                    dist = as_distribution(child)
                    if dist:
                        found = dist
                        return
                walk(child)
        elif isinstance(value, list):
            for child in value:
                walk(child)

    walk(node)
    return found


def _find_pagination_meta(node) -> dict:
    meta: dict = {}

    def maybe_set_from_dict(value: dict):
        lower = {str(k).lower(): v for k, v in value.items()}
        for key in ("totalcount", "total", "totalelements", "totalresults", "commentcount", "reviewcount"):
            if key in lower and "totalCount" not in meta:
                n = _extract_first_number(lower.get(key))
                if n is not None:
                    meta["totalCount"] = n
        for key in ("totalpages", "totalpage", "pagecount"):
            if key in lower and "totalPages" not in meta:
                n = _extract_first_number(lower.get(key))
                if n is not None:
                    meta["totalPages"] = n
        for key in ("currentpage", "page", "pagenumber", "number"):
            if key in lower and "currentPage" not in meta:
                n = _extract_first_number(lower.get(key))
                if n is not None:
                    meta["currentPage"] = n
        for key in ("hasnextpage", "hasnext"):
            if key in lower and "hasNextPage" not in meta:
                meta["hasNextPage"] = bool(lower.get(key))
        if "last" in lower and "hasNextPage" not in meta:
            meta["hasNextPage"] = not bool(lower.get("last"))

    def walk(value):
        if isinstance(value, dict):
            maybe_set_from_dict(value)
            for child in value.values():
                walk(child)
        elif isinstance(value, list):
            for child in value:
                walk(child)

    walk(node)
    return meta


def _dedupe_reviews(reviews: list[dict], product_name: str | None = None) -> list[dict]:
    deduped: list[dict] = []
    seen: set[str] = set()
    for review in reviews:
        text = _normalise_review_text(str(review.get("text") or ""))
        if _looks_like_ui_review_text(text, product_name):
            continue
        key = str(review.get("id") or "") or text[:120].lower()
        if key in seen:
            continue
        seen.add(key)
        review["text"] = text
        deduped.append(review)
    return deduped


def _parse_review_body(body: dict, product_name: str | None = None) -> tuple[list[dict], dict | None, dict]:
    """
    Parse one page of API response.
    Returns (review_objects, rating_distribution, pagination_meta).

    pagination_meta keys (present only when found in response):
      totalCount   – total reviews on the platform for this product
      totalPages   – total number of pages
      currentPage  – page index returned by the API
      hasNextPage  – bool hint from the API
    """
    # Try known Trendyol structures first (faster + more precise key matching)
    known = _try_known_trendyol_structures(body, product_name)
    if known:
        reviews = _dedupe_reviews(known, product_name)
    else:
        reviews = _dedupe_reviews(_collect_reviews_recursive(body, product_name), product_name)
    rating_dist = _find_rating_distribution(body)
    pagination = _find_pagination_meta(body)

    return reviews, rating_dist, pagination


def _setup_request_capture(page) -> list[str]:
    captured: list[str] = []

    def _capture(url: str, source: str) -> None:
        low = url.lower()
        parsed = urlparse(url)
        host = parsed.netloc.lower()
        path = parsed.path.lower()
        if not (
            host == "apigw.trendyol.com"
            or "discovery-storefront" in low
            or "review-read" in path
            or "product-reviews" in path
            or "comments" in path
        ):
            return
        if not any(key in low for key in ("review-read", "product-reviews", "comments", "comment")):
            return
        if url not in captured:
            captured.append(url)
            print(f"[REVIEWS] intercepted {source} url={url}")

    def _on_request(request) -> None:
        _capture(request.url, "request")

    def _on_response(response) -> None:
        _capture(response.url, "response")

    page.on("request", _on_request)
    page.on("response", _on_response)
    return captured


def _is_review_endpoint(url: str) -> bool:
    low = url.lower()
    parsed = urlparse(url)
    host = parsed.netloc.lower()
    path = parsed.path.lower()
    allowed_host = host == "apigw.trendyol.com" or "trendyol.com" in host
    allowed_path = any(key in path for key in ("product-reviews", "review-read", "comments", "comment"))
    return allowed_host and allowed_path


def _normalise_review_endpoint(url: str, size: int = _PAGE_SIZE) -> str:
    parsed = urlparse(url)
    params = [(k, v) for k, v in parse_qsl(parsed.query, keep_blank_values=True)
              if k.lower() not in {"page", "size", "pagesize"}]
    params.append(("page", "0"))
    if "product-reviews" in parsed.path.lower() or "review-read" in parsed.path.lower():
        params.append(("pageSize", str(size)))
    else:
        params.append(("size", str(size)))
    query = urlencode(params, doseq=True)
    return urlunparse(parsed._replace(query=query))


def _build_page_url(base_url: str, page_num: int, size: int) -> str:
    parsed = urlparse(base_url)
    params = [(k, v) for k, v in parse_qsl(parsed.query, keep_blank_values=True)
              if k.lower() not in {"page", "size", "pagesize"}]
    params.append(("page", str(page_num)))
    if "product-reviews" in parsed.path.lower() or "review-read" in parsed.path.lower():
        params.append(("pageSize", str(size)))
    else:
        params.append(("size", str(size)))
    return urlunparse(parsed._replace(query=urlencode(params, doseq=True)))


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
    product_name: str | None = None,
    page_size: int | None = None,
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

    actual_page_size = page_size or _PAGE_SIZE

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

        page_reviews, page_dist, page_meta = _parse_review_body(body, product_name)
        loaded_this_page = len(page_reviews)
        if loaded_this_page == 0:
            _debug_json_parse_failure(body, product_name)

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
                if len(all_reviews) >= target:
                    break

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
        base_url = _normalise_review_endpoint(template.format(pid=product_id), _PAGE_SIZE)
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


_STAR_FILTER_PARAMS = ("star", "starFilter", "ratingFilter", "filterStar")


async def _try_fetch_by_star_filter(
    page,
    base_url: str,
    star: int,
    quota: int,
    seen: set[str],
) -> list[dict]:
    """Fetch reviews for a specific star rating using platform filter params."""
    for param_name in _STAR_FILTER_PARAMS:
        sep = "&" if "?" in base_url else "?"
        filtered_url = f"{base_url}{sep}{param_name}={star}"
        probe_url = _build_page_url(filtered_url, 0, _PAGE_SIZE)
        body, status = await _refetch_with_status(page, probe_url)
        if status != 200 or not body:
            continue
        probe_reviews, _, _ = _parse_review_body(body)
        if not probe_reviews:
            continue
        # Verify filter works: sampled reviews must mostly match the target star
        rated = [r for r in probe_reviews if r.get("rating") is not None]
        if rated:
            wrong = sum(1 for r in rated if int(r["rating"]) != star)
            if wrong > len(rated) * 0.3:
                print(f"[REVIEWS] star={star} param={param_name!r} filter ineffective ({wrong}/{len(rated)} wrong)")
                continue
        print(f"[REVIEWS] star={star} param={param_name!r} filter confirmed")
        collected: list[dict] = []
        page_num = 0
        while len(collected) < quota:
            url = _build_page_url(filtered_url, page_num, _PAGE_SIZE)
            body, status = await _refetch_with_status(page, url)
            if status in (403, 429) or not body:
                break
            page_reviews, _, _ = _parse_review_body(body)
            if not page_reviews:
                break
            added = 0
            for r in page_reviews:
                dedup_key = r["id"] if r["id"] else r["text"][:80]
                if dedup_key not in seen:
                    seen.add(dedup_key)
                    collected.append(r)
                    added += 1
            if added == 0:
                break
            page_num += 1
            await asyncio.sleep(0.1)
        print(f"[REVIEWS] star={star} supplemental loaded={len(collected)}")
        return collected
    return []


async def _supplement_negative_reviews(
    page,
    base_url: str,
    reviews: list[dict],
    rating_dist: dict | None,
    max_reviews: int,
) -> list[dict]:
    """Top up 1-star and 2-star reviews to their computed quota via star filter."""
    if not rating_dist or not base_url:
        return reviews
    seen: set[str] = {r["id"] if r["id"] else r["text"][:80] for r in reviews}
    star_quota = compute_star_quota(rating_dist, max_reviews)
    extra: list[dict] = []
    for neg_star in (1, 2):
        available = rating_dist.get(str(neg_star), 0)
        if not available:
            continue
        loaded = sum(1 for r in reviews if r.get("rating") == neg_star)
        target = star_quota.get(str(neg_star), 0)
        if loaded >= target:
            continue
        need = target - loaded
        print(f"[REVIEWS] star={neg_star} loaded={loaded} target={target} need={need}")
        extra.extend(await _try_fetch_by_star_filter(page, base_url, neg_star, need, seen))
    return reviews + extra


async def _extract_reviews_trendyol(
    page,
    captured_urls: list[str],
    product_id: str | None,
    review_count: int | None,
    max_reviews: int,
    product_name: str | None = None,
    embedded_objects: list[tuple[str, object]] | None = None,
) -> tuple[list[dict], dict | None, str, bool, str, int | None]:
    """
    Master review extractor with full pagination.
    Returns (reviews, rating_distribution, source, completed, reason, api_total_count).
    """
    print(f"[REVIEWS] productId={product_id!r} knownReviewCount={review_count}")
    print(f"[REVIEWS] intercepted {len(captured_urls)} candidate URLs")

    # ── Strategy 1: intercepted URLs → strip page params → paginate ─────────
    review_urls = [u for u in captured_urls if _is_review_endpoint(u)]
    review_urls = sorted(
        dict.fromkeys(review_urls),
        key=lambda u: (
            0 if "review-read" in u.lower() or "product-reviews" in u.lower() else 1,
            1 if "pagesize=5" in u.lower() or "size=5" in u.lower() else 0,
            len(u),
        ),
    )

    for captured in review_urls[:8]:
        # Use pageSize=20 for "detailed" endpoints; they may not support higher values
        is_detailed = "detailed" in captured.lower()
        ep_page_size = 20 if is_detailed else _PAGE_SIZE
        base_url = _normalise_review_endpoint(captured, ep_page_size)
        probe_url = _build_page_url(base_url, 0, ep_page_size)
        body, status = await _refetch_with_status(page, probe_url)
        if status == 200 and body:
            probe_reviews, _, _ = _parse_review_body(body, product_name)
            if not probe_reviews:
                _debug_json_parse_failure(body, product_name)
            if probe_reviews:
                print(f"[REVIEWS] using intercepted base_url={base_url[:80]}")
                reviews, dist, completed, reason, api_total = await _fetch_all_pages(
                    page, base_url, review_count, max_reviews, product_name, ep_page_size
                )
                if reviews:
                    reviews = await _supplement_negative_reviews(page, base_url, reviews, dist, max_reviews)
                    source = "intercepted_rate_limited" if reason == "rate_limited" else "intercepted"
                    return reviews, dist, source, completed, reason, api_total

    # ── Strategy 2: known endpoint templates → paginate ──────────────────────
    if product_id:
        base_url = await _find_working_endpoint(page, product_id)
        if base_url:
            reviews, dist, completed, reason, api_total = await _fetch_all_pages(
                page, base_url, review_count, max_reviews, product_name
            )
            if reviews:
                reviews = await _supplement_negative_reviews(page, base_url, reviews, dist, max_reviews)
                source = "api_rate_limited" if reason == "rate_limited" else "trendyol_reviews_api"
                return reviews, dist, source, completed, reason, api_total

    # ── Strategy 3: embedded/source JSON fallback ───────────────────────────
    if embedded_objects:
        embedded_reviews, embedded_dist, embedded_source = _extract_embedded_reviews(embedded_objects, product_name)
        if embedded_reviews:
            return embedded_reviews[:max_reviews], embedded_dist, embedded_source, False, "embedded_json_fallback", None

    # ── Strategy 4: DOM fallback (single page, no pagination) ────────────────
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
    product_id = _extract_product_id(url)
    debug: dict = {
        "productIdMissing": product_id is None,
        "priceCandidates": [],
        "reviewEndpointCandidates": [],
    }

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
    jsonld_price = None
    meta_price = None

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
    reviews_api_total = None

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
                await page.goto(url, wait_until="domcontentloaded", timeout=45000)
            except Exception:
                try:
                    await page.goto(url, wait_until="domcontentloaded", timeout=30000)
                except Exception as e:
                    print(f"[scraper] Page load error: {e}")

            await page.wait_for_timeout(2500)
            html = await page.content()
            embedded_objects = _extract_embedded_json_objects(html)
            debug["embeddedJsonSources"] = [source for source, _ in embedded_objects[:20]]

            # ── 1. JSON-LD ─────────────────────────────────────────────────
            try:
                for el in await page.query_selector_all('script[type="application/ld+json"]'):
                    try:
                        raw = await el.inner_text()
                        data = json.loads(raw)
                        for item in _iter_jsonld_products(data):
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
                                jsonld_price = str(offers["price"])
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

                if not image or data_source["image"] in {"jsonld", "fallback"}:
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

                if not price or data_source["price"] in {"fallback"}:
                    el = await page.query_selector('meta[property="product:price:amount"]')
                    if el:
                        c = await el.get_attribute("content")
                        if c:
                            meta_price = c.strip()
                            price = format_price_turkish(c.strip())
                            data_source["price"] = "meta"

                if not rating:
                    for sel in [
                        'meta[itemprop="ratingValue"]',
                        'meta[property="product:rating"]',
                        'meta[name="rating"]',
                    ]:
                        el = await page.query_selector(sel)
                        if el:
                            c = await el.get_attribute("content")
                            if c:
                                try:
                                    rating = float(str(c).replace(",", "."))
                                    data_source["rating"] = "meta"
                                    break
                                except ValueError:
                                    pass
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

            embedded_price_candidates = _extract_json_price_candidates(embedded_objects, product_id)
            price_candidates = embedded_price_candidates + await extract_price_candidates(page, jsonld_price, meta_price)
            price_candidates.sort(key=lambda c: c.get("confidence", 0), reverse=True)
            debug["priceCandidates"] = price_candidates[:8]
            print(f"[PRICE CANDIDATES FULL] {json.dumps(price_candidates[:12], ensure_ascii=False)}")
            selected_price, selected_price_source = _select_price_candidate(price_candidates)
            if selected_price:
                price = selected_price
                if selected_price_source in {"jsonld_offers", "meta_product_price"}:
                    data_source["price"] = "jsonld" if selected_price_source == "jsonld_offers" else "meta"
                elif str(selected_price_source).startswith("embedded_json"):
                    data_source["price"] = "embedded"
                else:
                    data_source["price"] = "dom"
                debug["priceSourceDetail"] = selected_price_source

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
            print(f"[IMAGE] selected={image}")
            print(f"[IMAGE] source={data_source.get('image')}")

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
                embedded_review_count, embedded_count_source = _extract_json_review_count(embedded_objects, product_id)
                if embedded_review_count is not None:
                    review_count = embedded_review_count
                    data_source["reviewCount"] = embedded_count_source or "embedded"

            if not review_count or data_source["reviewCount"] == "fallback":
                for sel in [
                    ".reviews-summary-reviews-detail",
                    ".reviews-summary-reviews-summary .reviews-summary-reviews-detail",
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
                embedded_q_count, embedded_q_source = _extract_json_question_count(embedded_objects, product_id)
                if embedded_q_count is not None:
                    question_count = embedded_q_count
                    data_source["questionCount"] = embedded_q_source or "embedded"

            if not question_count or data_source["questionCount"] == "fallback":
                for sel in [
                    ".questions-summary-questions-summary",
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

            try:
                crumbs = await page.query_selector_all(".breadcrumb-item")
                if crumbs:
                    texts = [await c.inner_text() for c in crumbs]
                    category = " / ".join([t.strip() for t in texts if t.strip()])
            except Exception:
                pass

            product_name_l = (product_name or "").lower()
            if "maskara" in product_name_l or "mascara" in product_name_l:
                category = "Kozmetik / Makyaj / Göz Makyajı"
            elif any(k in product_name_l for k in ("nemlendirici", "atoderm", "cream", "krem")):
                category = "Kozmetik / Cilt Bakımı / Nemlendirici Krem"

            # ── 4. Reviews ─────────────────────────────────────────────────
            if effective_max_reviews > 0:
                debug["reviewEndpointCandidates"] = captured_urls[:12]
                (
                    reviews, rating_distribution, reviews_source,
                    reviews_completed, reviews_reason, reviews_api_total,
                ) = await _extract_reviews_trendyol(
                    page, captured_urls, product_id, review_count, effective_max_reviews, product_name, embedded_objects
                )
                data_source["reviews"] = reviews_source
                if review_count is None and reviews_api_total is not None:
                    review_count = reviews_api_total
                    data_source["reviewCount"] = "review_api_total"
            else:
                reviews_reason = "not_requested"
                data_source["reviews"] = "none"

            # ── 5. Full body regex (last resort for product data) ───────────
            needs_body = not rating
            if needs_body:
                try:
                    body_text = await page.inner_text("body")

                    if not rating or data_source["rating"] == "fallback":
                        m = re.search(r"\b([1-5][.,][0-9])\b", body_text)
                        if m:
                            rating = float(m.group(1).replace(",", "."))
                            data_source["rating"] = "regex"

                except Exception:
                    pass

            _UNRELIABLE_COUNT_SOURCES = {"regex", "body_regex", "fallback", "dom", "js"}
            if data_source.get("reviewCount") in _UNRELIABLE_COUNT_SOURCES:
                if review_count is not None:
                    print(f"[COUNT SOURCE] rejected reviewCount={review_count} source={data_source.get('reviewCount')}")
                review_count = None
                data_source["reviewCount"] = "fallback"
            if data_source.get("questionCount") in _UNRELIABLE_COUNT_SOURCES:
                if question_count is not None:
                    print(f"[COUNT SOURCE] rejected questionCount={question_count} source={data_source.get('questionCount')}")
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

    # Data validation: if reviewCount is from an unreliable source and reviews couldn't be loaded,
    # null it to avoid showing wrong numbers
    _reliable_count_sources = {"review_api_total", "jsonld", "embedded"}
    if (review_count is not None and review_count > 0 and reviews_loaded == 0
            and data_source.get("reviewCount") not in _reliable_count_sources):
        print(
            f"[REVIEWS WARNING] reviewCount={review_count} source={data_source.get('reviewCount')} "
            f"but reviewsLoaded=0 — nulling unreliable count"
        )
        review_count = None
        data_source["reviewCount"] = "fallback"

    # Confidence assessment
    if reviews_loaded > 0:
        review_confidence = "OK"
    elif review_count and review_count > 0:
        review_confidence = "REVIEW_TEXT_MISSING"
    else:
        review_confidence = "NO_REVIEWS"

    # Transparent warning for platform-capped pagination
    if reviews_reason in ("platform_limit_reached", "pagination_incomplete"):
        print(
            f"[REVIEWS WARNING] platform limit reached: "
            f"apiTotalCount={reviews_api_total} reviewCount={review_count} "
            f"loaded={reviews_loaded} reason={reviews_reason}"
        )

    review_analytics = compute_review_analytics(reviews, rating_distribution, effective_max_reviews)

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
    if reviews_api_total is not None:
        review_stats["apiTotalCount"] = reviews_api_total
    if reviews_reason in ("platform_limit_reached", "pagination_incomplete"):
        review_stats["platformLimitReached"] = True
    if reviews_loaded == 0 and reviews_reason not in ("no_reviews_found", "not_started"):
        review_stats["error"] = "reviews_could_not_be_loaded"

    return {
        "sourceUrl": url,
        "sourcePlatform": "Trendyol" if "trendyol" in domain else "Web",
        "productId": product_id,
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
        "debug": debug,
    }
