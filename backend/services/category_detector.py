import re

CATEGORY_KEYWORDS = {
    "kozmetik": ["serum", "tonik", "toner", "skincare", "beauty", "makeup", "kozmetik", "cilt", "bakim", "bakım", "glikolik", "asit", "nemlendirici", "krem", "gunes", "güneş", "spf", "makyaj", "purest", "hyaluronic", "niacinamide"],
    "elektronik": ["headphone", "earbud", "kulaklik", "kulaklık", "airpods", "bluetooth", "headset"],
    "laptop": ["laptop", "notebook", "macbook", "thinkpad", "gaming-laptop"],
    "telefon": ["iphone", "samsung", "telefon", "phone", "xiaomi"],
    "ayakkabi": ["sneaker", "shoes", "ayakkabi", "ayakkabı", "nike", "adidas", "puma"],
    "canta": ["bag", "canta", "çanta", "backpack"],
    "saat": ["watch", "saat", "smartwatch"],
    "kahve": ["coffee", "kahve", "espresso", "latte", "machine"]
}

def normalize_text(text: str) -> str:
    text = text.lower()
    text = text.replace("ı", "i").replace("ö", "o").replace("ü", "u").replace("ş", "s").replace("ğ", "g").replace("ç", "c")
    text = re.sub(r'[^a-z0-9-]', '-', text)
    return text

def detect_category(url: str, slug_keywords: list = None) -> tuple[str, float]:
    normalized_url = normalize_text(url)
    if slug_keywords:
        normalized_url += " " + " ".join([normalize_text(kw) for kw in slug_keywords])
    
    for category, keywords in CATEGORY_KEYWORDS.items():
        if any(kw in normalized_url for kw in keywords):
            return category, 0.92
            
    return "genel", 0.50
