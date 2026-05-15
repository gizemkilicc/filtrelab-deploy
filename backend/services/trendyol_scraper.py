import re
import json
from urllib.parse import urlparse
from playwright.async_api import async_playwright

TR_MAP = {
    "canlandirici": "Canlandırıcı", "gozenek": "Gözenek", "sikilastirici": "Sıkılaştırıcı",
    "urun": "Ürün", "gunes": "Güneş", "yuz": "Yüz", "sac": "Saç", "bakim": "Bakım",
    "kadin": "Kadın", "erkek": "Erkek", "ayakkabi": "Ayakkabı", "canta": "Çanta",
    "telefon": "Telefon", "kulaklik": "Kulaklık", "bilgisayar": "Bilgisayar",
    "oyuncu": "Oyuncu", "makinesi": "Makinesi", "asit": "Asit", "tonik": "Tonik"
}

def beautify_turkish(text: str) -> str:
    words = text.split("-")
    beautified_words = []
    for word in words:
        lower_word = word.lower()
        if lower_word in TR_MAP:
            beautified_words.append(TR_MAP[lower_word])
        else:
            beautified_words.append(word.capitalize())
    return " ".join(beautified_words)

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
    description = ""
    slug_keywords = []
    
    data_source = {
        "productName": "fallback",
        "price": "fallback",
        "image": "fallback",
        "rating": "fallback",
        "reviewCount": "fallback",
        "questionCount": "fallback",
        "sellerScore": "fallback"
    }

    # Extract initial info from URL
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
                user_agent="Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36",
                locale="tr-TR"
            )
            page = await context.new_page()
            
            try:
                await page.goto(url, wait_until="domcontentloaded", timeout=15000)
                await page.wait_for_timeout(2000) # Give it 2s for react hydrate
            except Exception as e:
                print(f"Page load timeout or error: {e}")

            # 1. Title / Name
            title_el = await page.query_selector('h1.pr-new-br, [data-testid*="product-title"], h1')
            if title_el:
                try:
                    product_name = await title_el.inner_text()
                    product_name = product_name.replace('\n', ' ').strip()
                    data_source["productName"] = "dom"
                    
                    # Try to extract brand from title if there is a span
                    brand_span = await title_el.query_selector('a, span')
                    if brand_span:
                        b_text = await brand_span.inner_text()
                        if b_text:
                            brand = b_text.strip()
                            data_source["brand"] = "dom"
                except: pass

            # 2. Price
            price_el = await page.query_selector('.prc-dsc, .prc-slg, .product-price-container, [data-testid*="price"]')
            if price_el:
                try:
                    p_text = await price_el.inner_text()
                    # e.g. "277,90 TL"
                    price = p_text.strip()
                    if "TL" not in price: price += " TL"
                    data_source["price"] = "dom"
                except: pass

            # 3. Image
            img_el = await page.query_selector('.product-image-container img, .gallery-container img, .base-product-image img')
            if img_el:
                image = await img_el.get_attribute('src')
                data_source["image"] = "dom"
            
            # Try meta image if DOM fails
            if not image:
                meta_img = await page.query_selector('meta[property="og:image"]')
                if meta_img:
                    image = await meta_img.get_attribute('content')
                    data_source["image"] = "meta"

            # 4. Rating
            rating_el = await page.query_selector('.rating-score, .ratings')
            if rating_el:
                try:
                    r_text = await rating_el.inner_text()
                    r_match = re.search(r'\b([1-5][.,][0-9])\b', r_text)
                    if r_match:
                        rating = float(r_match.group(1).replace(',', '.'))
                        data_source["rating"] = "dom"
                except: pass

            # 5. Review Count
            try:
                # Often in text "54406 Değerlendirme"
                review_el = await page.query_selector('a:has-text("Değerlendirme"), span:has-text("Değerlendirme")')
                if review_el:
                    rev_text = await review_el.inner_text()
                    rev_match = re.search(r'(\d+[.\d]*)\s*Değerlendirme', rev_text)
                    if rev_match:
                        review_count = int(rev_match.group(1).replace('.', ''))
                        data_source["reviewCount"] = "dom"
            except: pass

            # 6. Question Count
            try:
                q_el = await page.query_selector('a:has-text("Soru"), span:has-text("Soru-Cevap")')
                if q_el:
                    q_text = await q_el.inner_text()
                    q_match = re.search(r'(\d+[.\d]*)\s*Soru', q_text)
                    if q_match:
                        question_count = int(q_match.group(1).replace('.', ''))
                        data_source["questionCount"] = "dom"
            except: pass

            # 7. Seller Score
            try:
                s_el = await page.query_selector('.seller-store-score, [data-testid="seller-score"]')
                if s_el:
                    s_text = await s_el.inner_text()
                    s_match = re.search(r'(\d+[.,]\d+)', s_text)
                    if s_match:
                        seller_score = float(s_match.group(1).replace(',', '.'))
                        data_source["sellerScore"] = "dom"
            except: pass

            # 8. Category Breadcrumb
            try:
                crumbs = await page.query_selector_all('.breadcrumb-item')
                if crumbs:
                    texts = [await c.inner_text() for c in crumbs]
                    category = " / ".join([t.strip() for t in texts if t.strip()])
            except: pass

            # 9. Fallback Regex over page body
            if not price or not rating or not review_count:
                try:
                    body_text = await page.inner_text('body')
                    if not price:
                        p_match = re.search(r'(\d{1,3}(?:\.\d{3})*,\d{2})\s*TL', body_text)
                        if p_match:
                            price = p_match.group(1) + " TL"
                            data_source["price"] = "regex"
                    
                    if not rating:
                        r_match = re.search(r'\b([1-5][.,][0-9])\b', body_text)
                        if r_match:
                            rating = float(r_match.group(1).replace(',', '.'))
                            data_source["rating"] = "regex"

                    if not review_count:
                        rev_match = re.search(r'(\d+[.\d]*)\s*Değerlendirme', body_text)
                        if rev_match:
                            review_count = int(rev_match.group(1).replace('.', ''))
                            data_source["reviewCount"] = "regex"
                except: pass

            await browser.close()
    except Exception as e:
        print(f"Playwright execution error: {e}")

    # Final fallbacks to avoid crashing, but must respect "Don't fake data if it doesn't exist"
    # Actually, we shouldn't fake data. We just pass what we have.
    # The analyze.py / mock_ai.py will handle missing critical fields.

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
        "dataSource": data_source
    }
