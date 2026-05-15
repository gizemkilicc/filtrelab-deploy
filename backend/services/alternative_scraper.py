from playwright.async_api import async_playwright

async def get_alternatives(category: str, product_name: str, base_price: float):
    alternatives = []
    
    query = product_name.split()[0] if product_name else category.split("/")[0].strip()
    search_url = f"https://www.trendyol.com/sr?q={query}"
    
    try:
        async with async_playwright() as p:
            browser = await p.chromium.launch(headless=True)
            context = await browser.new_context(
                user_agent="Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36",
                locale="tr-TR"
            )
            page = await context.new_page()
            
            try:
                await page.goto(search_url, wait_until="domcontentloaded", timeout=15000)
                await page.wait_for_timeout(2000)
            except Exception:
                pass
            
            cards = await page.query_selector_all('.p-card-wrppr')
            
            for card in cards[:4]:
                try:
                    a_tag = await card.query_selector('a')
                    if not a_tag: continue
                    
                    href = await a_tag.get_attribute('href')
                    url = "https://www.trendyol.com" + href if href else ""
                    
                    name_span = await card.query_selector('.prdct-desc-cntnr-name')
                    brand_span = await card.query_selector('.prdct-desc-cntnr-ttl')
                    price_div = await card.query_selector('.prc-box-dscntd')
                    img_tag = await card.query_selector('.p-card-img')
                    
                    name_text = await name_span.inner_text() if name_span else ""
                    brand_text = await brand_span.inner_text() if brand_span else ""
                    price_text = await price_div.inner_text() if price_div else ""
                    img_src = await img_tag.get_attribute('src') if img_tag else ""
                    
                    full_name = f"{brand_text} {name_text}".strip()
                    
                    if full_name and price_text and url:
                        alternatives.append({
                            "name": full_name,
                            "price": price_text.strip(),
                            "image": img_src,
                            "url": url,
                            "reason": "Gerçek arama sonucundan çekilmiş alternatif ürün.",
                            "isDirectProductUrl": True
                        })
                except Exception:
                    continue
                    
            await browser.close()
    except Exception as e:
        print(f"Alternative scraping failed: {e}")

    return alternatives
