from urllib.parse import urlparse
import re
import requests
from bs4 import BeautifulSoup
import json

TR_MAP = {
    "canlandirici": "Canlandırıcı", "gozenek": "Gözenek", "sikilastirici": "Sıkılaştırıcı",
    "urun": "Ürün", "gunes": "Güneş", "yuz": "Yüz", "sac": "Saç", "bakim": "Bakım",
    "kadin": "Kadın", "erkek": "Erkek", "ayakkabi": "Ayakkabı", "canta": "Çanta",
    "telefon": "Telefon", "kulaklik": "Kulaklık", "bilgisayar": "Bilgisayar",
    "oyuncu": "Oyuncu", "makinesi": "Makinesi"
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

def extract_product_info(url: str):
    parsed_url = urlparse(url)
    domain = parsed_url.netloc.lower()
    path_segments = [seg for seg in parsed_url.path.strip("/").split("/") if seg]

    product_name = None
    brand = None
    platform = "Genel"
    slug_keywords = []
    extracted_image = None
    extracted_price = None
    productId = None
    rating = 0.0
    review_count = 0
    
    data_source = "fallback"
    confidence = 0.5
    extracted_fields = {"title": False, "image": False, "price": False, "brand": False}

    if "trendyol.com" in domain:
        platform = "Trendyol"
        if len(path_segments) >= 2:
            brand_slug = path_segments[0]
            slug_part = path_segments[1]
            if "-p-" in slug_part:
                parts = slug_part.split("-p-")
                slug_part = parts[0]
                productId = parts[1]
            slug_keywords = slug_part.split("-")
    elif "hepsiburada.com" in domain:
        platform = "Hepsiburada"
        if len(path_segments) >= 1:
            slug_keywords = path_segments[-1].split("-p-")[0].split("-c-")[0].split("-")
    elif "amazon.com" in domain:
        platform = "Amazon"
        if len(path_segments) >= 3 and path_segments[1] == "dp":
            slug_keywords = path_segments[0].split("-")

    headers = {
        "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36",
        "Accept-Language": "tr-TR,tr;q=0.9,en-US;q=0.8,en;q=0.7",
    }

    try:
        response = requests.get(url, headers=headers, timeout=5)
        if response.status_code == 200:
            soup = BeautifulSoup(response.content, "lxml")
            
            # 1. Try JSON-LD
            scripts = soup.find_all("script", type="application/ld+json")
            for script in scripts:
                if not script.string: continue
                try:
                    data = json.loads(script.string)
                    if isinstance(data, list):
                        for item in data:
                            if item.get("@type") == "Product":
                                data = item
                                break
                    if data.get("@type") == "Product":
                        if data.get("name"):
                            product_name = data.get("name")
                            extracted_fields["title"] = True
                        if data.get("image"):
                            extracted_image = data["image"][0] if isinstance(data.get("image"), list) else data["image"]
                            extracted_fields["image"] = True
                        if data.get("brand"):
                            brand = data["brand"].get("name") if isinstance(data["brand"], dict) else str(data["brand"])
                            extracted_fields["brand"] = True
                        if data.get("offers"):
                            offers = data["offers"]
                            if isinstance(offers, dict) and offers.get("price"):
                                extracted_price = float(offers.get("price"))
                                extracted_fields["price"] = True
                        if data.get("aggregateRating"):
                            agg = data["aggregateRating"]
                            if agg.get("ratingValue"):
                                rating = float(agg.get("ratingValue"))
                            if agg.get("reviewCount"):
                                review_count = int(agg.get("reviewCount"))

                        data_source = "json_ld"
                        confidence = 0.95
                        break
                except Exception:
                    continue

            # 2. If no json-ld or missing fields, try Meta Tags
            if not extracted_fields["title"]:
                og_title = soup.find("meta", property="og:title")
                if og_title and og_title.get("content"):
                    product_name = og_title["content"].split(" - ")[0].split(" | ")[0]
                    extracted_fields["title"] = True
                    if data_source == "fallback":
                        data_source = "scraped_meta"
                        confidence = 0.85

            if not extracted_fields["image"]:
                og_image = soup.find("meta", property="og:image")
                if og_image and og_image.get("content"):
                    extracted_image = og_image["content"]
                    extracted_fields["image"] = True

            if not extracted_fields["price"]:
                price_meta = soup.find("meta", property="product:price:amount")
                if price_meta and price_meta.get("content"):
                    try:
                        extracted_price = float(price_meta["content"])
                        extracted_fields["price"] = True
                    except:
                        pass
    except Exception as e:
        print(f"Scraping error: {e}")

    if not product_name or not extracted_price:
        # Strict failure: If we can't get basic info, we fail. No mock data.
        raise ValueError("Bu ürün bilgileri alınamadı. Lütfen geçerli bir ürün linki deneyin.")

    if not brand and "trendyol.com" in domain and len(path_segments) >= 2:
        brand = beautify_turkish(path_segments[0])
        extracted_fields["brand"] = True

    if not brand:
        brand = "Bilinmeyen Marka"

    # Default rating logic if none scraped
    if rating == 0.0:
        rating = 4.0
    if review_count == 0:
        review_count = 10

    return {
        "extractedFromUrl": True if confidence > 0.1 else False,
        "sourceUrl": url,
        "sourcePlatform": platform,
        "dataSource": data_source,
        "confidence": confidence,
        "extractedFields": extracted_fields,
        "productName": product_name,
        "brand": brand,
        "productId": productId,
        "slugKeywords": slug_keywords,
        "scrapedImage": extracted_image,
        "scrapedPrice": extracted_price,
        "rating": rating,
        "reviewCount": review_count
    }
