import json
import os
import re
from difflib import SequenceMatcher
from typing import Any

import requests

SYSTEM_PROMPT = (
    "Sen FiltreLAB Asistan'sın. Kullanıcının son mesajına cevap ver. "
    "Cevaplarını mevcut ürün analiz verilerine ve konuşma geçmişine dayandır. "
    "Aynı genel analiz cevabını tekrar etme. Kullanıcının sorusu neyse sadece "
    "onu cevapla. Ürün datasında olmayan bilgiyi kesinmiş gibi söyleme. Eksik "
    "veri varsa belirt. Doğal Türkçe konuş. Gerektiğinde kısa, gerektiğinde "
    "açıklayıcı cevap ver."
)

RULE_BASED_INTENTS = {
    "buy_advice",
    "color_question",
    "daily_use",
    "price_question",
    "expensive_or_worth",
    "cheap_quality_concern",
    "alternative_request",
    "review_trust",
    "fake_review_question",
    "return_risk",
    "product_feature",
    "compare_request",
    "usage_scenario",
    "gift_advice",
    "skin_sensitivity",
    "size_fit",
    "durability",
    "brand_trust",
    "seller_trust",
    "explain_decision",
    "why_not_recommended",
    "why_recommended",
}


def _safe_str(value: Any, default: str = "") -> str:
    if value is None:
        return default
    text = str(value).strip()
    return text if text else default


def _safe_number(value: Any) -> float | None:
    if value in (None, ""):
        return None
    try:
        return float(str(value).replace(",", "."))
    except Exception:
        return None


def _text_of(item: Any) -> str:
    if isinstance(item, dict):
        return _safe_str(item.get("content") or item.get("text"))
    return _safe_str(getattr(item, "content", "") or getattr(item, "text", ""))


def _role_of(item: Any) -> str:
    if isinstance(item, dict):
        return _safe_str(item.get("role"))
    return _safe_str(getattr(item, "role", ""))


def _last_messages(history: list[Any], limit: int = 12) -> list[dict[str, str]]:
    cleaned = []
    for item in history[-limit:]:
        role = _role_of(item)
        content = _text_of(item)
        if role in {"user", "assistant"} and content:
            cleaned.append({"role": role, "content": content[:900]})
    return cleaned


def _last_assistant(history: list[Any]) -> str:
    for item in reversed(history):
        if _role_of(item) == "assistant":
            return _text_of(item)
    return ""


def _recent_user_text(history: list[Any]) -> str:
    return " ".join(
        _text_of(item) for item in history[-12:] if _role_of(item) == "user"
    ).lower()


def _tokens(text: str) -> set[str]:
    return set(re.findall(r"[a-zA-ZçğıöşüÇĞİÖŞÜ0-9]+", text.lower()))


def _contains_any(text: str, phrases: list[str]) -> bool:
    return any(phrase in text for phrase in phrases)


def _contains_word(text: str, words: list[str]) -> bool:
    token_set = _tokens(text)
    return any(word in token_set for word in words)


def _alternatives(analysis: dict[str, Any] | None) -> list[dict[str, Any]]:
    if not analysis:
        return []
    alts = analysis.get("alternativeProducts") or analysis.get("betterAlternatives") or []
    return [alt for alt in alts if isinstance(alt, dict)]


def _summary(analysis: dict[str, Any]) -> dict[str, Any]:
    return {
        "product": _safe_str(analysis.get("productName"), "Bu ürün"),
        "brand": _safe_str(analysis.get("brand")),
        "category": _safe_str(analysis.get("category"), "Genel"),
        "price": _safe_str(analysis.get("price")),
        "rating": _safe_number(analysis.get("rating")),
        "reviews": _safe_number(analysis.get("reviewCount")),
        "questions": _safe_number(analysis.get("questionCount")),
        "seller": _safe_number(analysis.get("sellerScore")),
        "fake": _safe_number(analysis.get("fakeReviewRisk")),
        "return": _safe_str(analysis.get("returnRisk")),
        "trust": _safe_number(analysis.get("trustScore")),
        "sentiment": _safe_number(analysis.get("sentimentScore")),
        "value": _safe_number(analysis.get("pricePerformance")),
        "decision": _safe_str(analysis.get("finalDecision"), "BEKLE"),
        "analysis": _safe_str(analysis.get("analysis")),
        "shopping": _safe_str(analysis.get("shoppingBehavior")),
    }


def _fmt(value: Any, suffix: str = "") -> str:
    if value is None:
        return "veri yok"
    if isinstance(value, float):
        return f"{int(value)}{suffix}" if value.is_integer() else f"{value:g}{suffix}"
    return f"{value}{suffix}"


def _category_type(analysis: dict[str, Any] | None) -> str:
    if not analysis:
        return "genel"
    text = f"{analysis.get('category', '')} {analysis.get('productName', '')}".lower()
    if _contains_any(text, ["maskara", "mascara", "kirpik"]):
        return "maskara"
    if _contains_any(text, ["kozmetik", "cilt", "makyaj", "bakım", "parfüm"]):
        return "kozmetik"
    if _contains_any(text, ["giyim", "ayakkabı", "elbise", "pantolon", "kaban", "çanta"]):
        return "giyim"
    if _contains_any(text, ["elektronik", "telefon", "kulaklık", "laptop", "saat"]):
        return "elektronik"
    if _contains_any(text, ["aydınlatma", "bahçe", "lamba", "avize"]):
        return "aydınlatma"
    return "genel"


def extract_product_features(analysis: dict[str, Any] | None) -> dict[str, Any]:
    if not analysis:
        return {
            "category": "genel",
            "color": None,
            "colorPhrase": None,
            "effects": [],
            "intensity": None,
            "isMascara": False,
        }

    product_name = _safe_str(analysis.get("productName"))
    haystack = " ".join([
        product_name,
        _safe_str(analysis.get("category")),
        _safe_str(analysis.get("analysis")),
        _safe_str(analysis.get("shoppingBehavior")),
    ]).lower()

    color_map = [
        ("ultra siyah", "siyah"),
        ("kahverengi", "kahverengi"),
        ("lacivert", "lacivert"),
        ("şeffaf", "şeffaf"),
        ("seffaf", "şeffaf"),
        ("kırmızı", "kırmızı"),
        ("kirmizi", "kırmızı"),
        ("pembe", "pembe"),
        ("beyaz", "beyaz"),
        ("siyah", "siyah"),
        ("mavi", "mavi"),
        ("nude", "nude"),
        ("gri", "gri"),
    ]
    color = None
    color_phrase = None
    lower_name = product_name.lower()
    for phrase, normalized in color_map:
        index = lower_name.find(phrase)
        if index >= 0:
            original = product_name[index:index + len(phrase)]
            color_phrase = " ".join(part.capitalize() for part in original.split())
            color = normalized
            break

    effects = []
    if _contains_any(haystack, ["hacim", "volume", "dolgun", "dolgunlaştır"]):
        effects.append("hacim")
    if _contains_any(haystack, ["uzunluk", "uzatma", "uzatır", "length"]):
        effects.append("uzunluk")
    if _contains_any(haystack, ["kalıcı", "kalicilik", "waterproof", "suya dayanıklı"]):
        effects.append("kalıcılık")

    intensity = None
    if _contains_any(haystack, ["ultra siyah", "yoğun", "yogun", "intense", "dolgunlaştır", "hacim"]):
        intensity = "yoğun"
    elif _contains_any(haystack, ["doğal", "dogal", "hafif", "soft", "nude"]):
        intensity = "doğal"

    return {
        "category": _category_type(analysis),
        "color": color,
        "colorPhrase": color_phrase,
        "effects": effects,
        "intensity": intensity,
        "isMascara": _category_type(analysis) == "maskara",
    }


def extract_user_preferences(message: str, history: list[Any]) -> dict[str, bool]:
    text = f"{_recent_user_text(history)} {message.lower()}"
    does_not_want_intense = (
        _contains_any(text, [
            "çok yoğun istemiyorum", "cok yogun istemiyorum", "yoğun istemiyorum",
            "yogun istemiyorum", "çok yoğun siyah istemiyorum", "cok yogun siyah istemiyorum",
            "abartı istemiyorum", "abarti istemiyorum",
        ])
        or (("yoğun" in text or "yogun" in text or "siyah" in text) and _contains_any(text, ["istemiyorum", "olmasın", "olmasin"]))
    )
    cheap_quality = _contains_any(text, [
        "ucuz olan kalitesiz", "ucuzsa kalitesiz", "kalitesiz olabilir",
        "ucuz ama kaliteli", "en ucuz", "kalite önemli", "kalite onemli",
    ])
    return {
        "wantsNaturalLook": does_not_want_intense or _contains_any(text, ["doğal", "dogal", "hafif", "soft", "sade"]),
        "wantsDailyUse": _contains_any(text, ["her gün", "her gun", "günlük", "gunluk", "düzenli kullanım", "duzenli kullanim", "düzenli kullan", "duzenli kullan"]),
        "wantsLongLasting": _contains_any(text, ["kalıcı", "kalici", "akmasın", "akmasin", "dayansın", "dayansin", "uzun süre", "uzun sure"]),
        "wantsCheap": _contains_any(text, ["ucuz", "uygun fiyat", "bütçe", "butce"]),
        "qualityConcern": cheap_quality,
        "cheapQualityConcern": cheap_quality,
        "sensitiveSkinOrEyes": _contains_any(text, ["hassas", "alerji", "yakma", "gözüm", "gozum", "cildim", "cildime"]),
        "giftPurpose": _contains_any(text, ["anneme", "annem", "hediye", "sevgilime", "arkadaşıma", "arkadasima"]),
        "budgetConcern": _contains_any(text, ["bütçe", "butce", "pahalı", "pahali", "fiyat"]),
        "doesNotWantIntense": does_not_want_intense,
        "needsDurability": _contains_any(text, ["dayanıklı", "dayanikli", "uzun ömür", "uzun omur", "sağlam", "saglam"]),
    }


def detect_intent(message: str, history: list[Any], analysis: dict[str, Any] | None) -> str:
    text = message.lower().strip()
    recent = _recent_user_text(history)
    current_preferences = extract_user_preferences(message, [])

    if _contains_any(text, ["hangi renk", "rengi", "renk", "siyah mı", "siyah mi", "kahverengi mi"]):
        return "color_question"
    if _contains_any(text, ["alternatif", "başka ürün", "baska urun", "daha iyisi", "yerine ne", "ne alınır", "ne alinir"]):
        return "alternative_request"
    if _contains_any(text, ["karşılaştır", "karsilastir", "kıyas", "kiyas", "hangisi", "mi yoksa"]):
        return "compare_request"
    if _contains_any(text, ["fiyatı ne", "fiyati ne", "kaç tl", "kac tl", "fiyat ne"]):
        return "price_question"
    if current_preferences["cheapQualityConcern"]:
        return "cheap_quality_concern"
    if _contains_any(text, ["pahalı mı", "pahali mi", "değer mi", "deger mi", "parasına değer", "parasina deger"]):
        return "expensive_or_worth"
    if current_preferences["giftPurpose"]:
        return "gift_advice"
    if current_preferences["wantsDailyUse"]:
        return "daily_use"
    if current_preferences["sensitiveSkinOrEyes"]:
        return "skin_sensitivity"
    if current_preferences["doesNotWantIntense"] or current_preferences["wantsNaturalLook"]:
        return "usage_scenario"
    if _contains_word(text, ["sahte"]):
        return "fake_review_question"
    if _contains_word(text, ["yorum", "yorumlar", "yorumları", "yorumlari", "değerlendirme", "degerlendirme"]):
        return "review_trust"
    if _contains_any(text, ["iade", "geri gönder", "geri gonder"]):
        return "return_risk"
    if _contains_any(text, ["beden", "kalıp", "kalip", "üstüme", "ustume"]):
        return "size_fit"
    if _contains_any(text, ["dayanıklı", "dayanikli", "uzun ömür", "uzun omur", "sağlam", "saglam"]):
        return "durability"
    if _contains_any(text, ["marka", "brand"]):
        return "brand_trust"
    if _contains_any(text, ["satıcı", "satici", "mağaza", "magaza", "seller"]):
        return "seller_trust"
    if _contains_any(text, ["neden önerilmiyor", "neden onerilmiyor", "niye önerilmiyor", "niye onerilmiyor", "önerilmedi", "onerilmedi"]):
        return "why_not_recommended"
    if _contains_any(text, ["neden öneriliyor", "neden oneriliyor", "niye iyi", "neden iyi"]):
        return "why_recommended"
    if _contains_any(text, ["neden", "niye", "açıkla", "acikla"]):
        return "explain_decision"
    if _contains_any(text, ["hacim", "dolgun", "dolgunlaştır", "dolgunlastir", "uzatır", "uzatir", "uzunluk", "topak", "topaklan", "kalıcı mı", "kalici mi", "özelliği", "ozelligi"]):
        return "product_feature"
    if _contains_any(text, ["alınır mı", "alinir mi", "almalı mıyım", "almali miyim", "mantıklı mı", "mantikli mi", "önerir misin", "onerir misin"]):
        return "buy_advice"
    if len(text.split()) <= 4 and any(word in recent for word in ["fiyat", "yorum", "alternatif", "alınır", "alinir"]):
        return "follow_up"
    return "unknown"


def build_chat_context(message: str, history: list[Any], analysis: dict[str, Any] | None) -> dict[str, Any]:
    intent = detect_intent(message, history, analysis)
    preferences = extract_user_preferences(message, history)
    features = extract_product_features(analysis)
    return {
        "message": message,
        "history": _last_messages(history, 12),
        "analysis": analysis or {},
        "intent": intent,
        "preferences": preferences,
        "features": features,
    }


def _price_values(alts: list[dict[str, Any]]) -> list[float]:
    values = []
    for alt in alts:
        raw = _safe_str(alt.get("price"))
        cleaned = raw.replace("TL", "").replace("₺", "").replace(".", "").replace(",", ".").strip()
        try:
            if cleaned:
                values.append(float(cleaned))
        except Exception:
            continue
    return values


def _price_text(value: float) -> str:
    return f"{value:.0f}" if value.is_integer() else f"{value:.2f}"


def _color_reply(features: dict[str, Any]) -> str:
    if features.get("color"):
        phrase = features.get("colorPhrase") or features["color"]
        return f"Ürün adında '{phrase}' geçtiği için rengi {features['color']} görünüyor. Net renk tonunu görmek için ürün görsellerini de kontrol etmeni öneririm."
    return "Ürün adından net renk bilgisi çıkaramadım. Ürün açıklaması veya satıcı bilgisi kontrol edilmeli."


def _daily_use_reply(features: dict[str, Any], analysis: dict[str, Any]) -> str:
    if features.get("isMascara"):
        if features.get("intensity") == "yoğun" or "hacim" in features.get("effects", []):
            return "Her gün kullanım için uygun olabilir ama bu ürün 'dolgunlaştırıcı' ve 'ultra siyah' olduğu için doğal görünüm isteyenlere biraz yoğun gelebilir. Günlük kullanımda kolay temizlenme ve topaklanma yorumlarına özellikle bakmanı öneririm."
        return "Her gün kullanım için değerlendirilebilir. Yine de kolay temizlenme, topaklanma ve hassas göz yorumlarını kontrol etmek iyi olur."
    category = features.get("category")
    if category == "kozmetik":
        return "Düzenli kullanımda cilt/göz hassasiyeti ve içerik uyumu önemli. İlk kullanımda küçük miktarla denemek daha güvenli olur."
    if category == "elektronik":
        return "Her gün kullanacaksan batarya, bağlantı kararlılığı, garanti ve uzun kullanım şikayetleri daha önemli hale gelir."
    if category == "giyim":
        return "Her gün kullanım için rahatlık, kumaş dayanıklılığı ve kalıp yorumları belirleyici olur."
    return "Düzenli kullanım için ürünün dayanıklılık, iade riski ve kullanıcı yorumları birlikte değerlendirilmeli."


def _usage_reply(features: dict[str, Any], preferences: dict[str, bool]) -> str:
    if features.get("isMascara") and preferences.get("doesNotWantIntense"):
        return "O zaman bu ürün tam aradığın tarz olmayabilir. 'Ultra siyah' ve hacim etkili olduğu için daha belirgin bir görünüm hedefliyor. Daha doğal bitişli bir maskara daha uygun olabilir."
    if features.get("isMascara") and preferences.get("wantsNaturalLook"):
        return "Doğal görünüm istiyorsan bu ürünü biraz temkinli değerlendirirdim. Ürün adı hacim/yoğun etkiyi öne çıkarıyorsa günlük soft makyaj için daha hafif bir maskara daha iyi olabilir."
    return "Kullanım amacına göre karar vermek daha doğru. Ürünün vaatleri beklentine uyuyorsa değerlendirilebilir; uymuyorsa alternatiflere bakmak daha mantıklı."


def _price_reply(analysis: dict[str, Any], worth: bool = False) -> str:
    info = _summary(analysis)
    alts = _alternatives(analysis)
    prices = _price_values(alts)
    base = f"Ürünün fiyatı {info['price']} görünüyor." if info["price"] else "Ürünün fiyat bilgisi net görünmüyor."
    if prices:
        avg = sum(prices) / len(prices)
        base += f" Alternatiflerde ortalama fiyat yaklaşık {_price_text(avg)} TL civarında."
    if worth:
        value = info["value"]
        if value is not None and value >= 7:
            base += " Fiyat/performans sinyali iyi olduğu için fiyatı bütçene uyuyorsa mantıklı olabilir."
        elif value is not None:
            base += " Fiyat/performans çok güçlü görünmediği için benzer ürünlerle karşılaştırmak iyi olur."
    elif info["value"] is not None:
        base += " Fiyat/performans skorunu da benzer ürünlerle birlikte düşünmek iyi olur."
    return base


def _cheap_quality_reply(analysis: dict[str, Any]) -> str:
    alts = _alternatives(analysis)[:3]
    if alts:
        return "Haklısın, sadece en ucuz ürüne yönelmek doğru olmayabilir. Burada yorum güveni, puan ve kullanıcı şikayetleri de önemli. Orta fiyatlı ama yorumları güçlü bir alternatif daha mantıklı olabilir."
    return "Haklısın, ucuz ürün bazen kalite veya beklenti tarafında zayıf kalabiliyor. Bu yüzden sadece fiyata değil, yorumların tutarlılığına ve iade riskine de bakmak daha doğru."


def _alternative_reply(analysis: dict[str, Any]) -> str:
    alts = _alternatives(analysis)[:3]
    if not alts:
        return "Bu ürünle gerçekten alakalı doğrulanmış alternatif bulamadım. Alakasız ürün önermek yerine mevcut ürünün güçlü ve zayıf taraflarını değerlendirebilirim."
    lines = ["Şunlara bakabilirsin:"]
    for idx, alt in enumerate(alts, 1):
        lines.append(f"{idx}. {_safe_str(alt.get('name'), 'Ürün')} – {_safe_str(alt.get('price'), 'fiyat yok')}")
    return "\n".join(lines)


def _feature_reply(message: str, features: dict[str, Any]) -> str:
    text = message.lower()
    if _contains_any(text, ["hacim", "dolgun", "dolgunlaştır", "dolgunlastir"]):
        if "hacim" in features.get("effects", []):
            return "Ürün adında 'dolgunlaştırıcı' ve hacim etkisi geçtiği için hacim vermeyi hedefliyor gibi görünüyor."
        return "Ürün adından hacim etkisini net çıkaramadım. Hacim beklentin varsa açıklama ve kullanıcı yorumlarına bakmalısın."
    if _contains_any(text, ["uzatır", "uzatir", "uzunluk"]):
        if "uzunluk" in features.get("effects", []):
            return "Ürün adında 'uzunluk etkili' geçtiği için kirpikleri daha uzun göstermeyi hedefliyor gibi görünüyor."
        return "Ürün adından uzatma etkisi net anlaşılmıyor. Bu konuda kullanıcı yorumları daha belirleyici."
    if _contains_any(text, ["topak", "topaklan"]):
        return "Topaklanma ürün adından net anlaşılmaz. Düşük puanlı yorumlarda topaklanma şikayetinin tekrar edip etmediğine bakmak gerekir."
    return "Bu özelliği ürün adından net çıkaramadım. Ürün açıklaması veya kullanıcı yorumları kontrol edilmeli."


def _review_reply(analysis: dict[str, Any], fake_only: bool = False) -> str:
    info = _summary(analysis)
    if fake_only:
        if info["fake"] is None:
            return "Sahte yorum riski için elimde net veri yok. Yorumların tarihleri, benzer cümleler ve düşük puanlı şikayetler kontrol edilmeli."
        if info["fake"] < 30:
            return "Sahte yorum riski düşük görünüyor; bu olumlu. Yine de çok benzer yazılmış yorumlar veya aşırı kısa övgüler varsa ayrıca kontrol etmek iyi olur."
        return "Sahte yorum riski biraz dikkat gerektiriyor. Yorum sayısı yüksek olsa bile düşük puanlı yorumları ve tekrar eden şikayetleri okumak iyi olur."
    if info["fake"] is not None and info["fake"] < 30:
        return "Yorumların güvenilir görünmesi olumlu bir işaret. Çok yüksek sahte yorum riski görünmüyor; yine de düşük puanlı yorumlarda tekrar eden şikayet var mı bakmanı öneririm."
    return "Yorumları tek başına yeterli görmezdim. Sahte yorum riski, düşük puanlı yorumlar ve tekrar eden şikayetler birlikte değerlendirilmeli."


def _return_reply(analysis: dict[str, Any], features: dict[str, Any]) -> str:
    info = _summary(analysis)
    if features.get("category") == "maskara":
        return f"İade riski {info['return'] or 'belirsiz'} görünüyor. Maskarada beklenti farkı, topaklanma, kolay temizlenmeme veya hassas göz şikayetleri iade sebebi olabilir."
    return f"İade riski {info['return'] or 'belirsiz'} görünüyor. Satın almadan önce düşük puanlı yorumlarda tekrar eden şikayet var mı kontrol et."


def _decision_reason_reply(analysis: dict[str, Any], negative: bool = False, positive: bool = False) -> str:
    info = _summary(analysis)
    decision = info["decision"]
    weak_reasons = []
    strong_reasons = []
    if info["return"] in {"Orta", "Yüksek"}:
        weak_reasons.append(f"iade riski {info['return'].lower()}")
    if info["fake"] is not None and info["fake"] >= 45:
        weak_reasons.append("yorum güveni zayıf")
    if info["value"] is not None and info["value"] < 6:
        weak_reasons.append("fiyat/performans zayıf")
    elif info["value"] is not None and info["value"] < 7:
        weak_reasons.append("fiyat/performans orta seviyede")
    if info["trust"] is not None and info["trust"] >= 75:
        strong_reasons.append("güven sinyali güçlü")
    if info["rating"] is not None and info["rating"] >= 4:
        strong_reasons.append("puanı iyi")

    if negative:
        if decision != "ÖNERİLMEZ":
            reason_text = ", ".join(weak_reasons) if weak_reasons else "bazı sinyallerin net güçlü olmaması"
            return f"Bu ürün aslında doğrudan 'önerilmez' değil; karar {decision}. Temkin sebebi {reason_text}. Bu yüzden alternatiflerle karşılaştırmak iyi olur."
        return "Önerilmeme nedeni " + (", ".join(weak_reasons) if weak_reasons else "analizdeki risk sinyallerinin güçlü olması") + "."
    if decision == "ÖNERİLMEZ":
        return "Önerilmeme nedeni " + (", ".join(weak_reasons) if weak_reasons else "analizdeki risk sinyallerinin güçlü olması") + "."
    if positive or decision == "ALINABİLİR":
        return "Önerilmesinin nedeni " + (", ".join(strong_reasons) if strong_reasons else "genel analiz sinyallerinin olumlu olması") + "."
    mixed = weak_reasons + strong_reasons
    return "Karar çok net değil; " + (", ".join(mixed) if mixed else "fiyat, yorum ve risk sinyalleri birlikte değerlendirilmeli") + "."


def _gift_reply(analysis: dict[str, Any], features: dict[str, Any]) -> str:
    if features.get("category") == "maskara":
        return "Annene hediye olarak alınabilir ama maskara kişisel tercih ürünü: yoğun siyah ve hacim etkisi herkesin günlük zevkine uymayabilir. Hassas göz, kolay temizlenme ve değişim/iade koşullarını kontrol etmeni öneririm."
    return "Hediye için kişisel tercih ve iade kolaylığı önemli. Ürün kategori olarak riskliyse daha genel kullanıma uygun bir alternatif seçmek daha güvenli olabilir."


def _skin_reply(features: dict[str, Any]) -> str:
    if features.get("category") == "maskara":
        return "Hassas göz için kesin uygun diyemem. Yanma, sulanma, kolay temizlenme ve hipoalerjenik içerik yorumlarına özellikle bakmalısın."
    return "Hassas cilt/göz durumunda içerik uyumu önemli. İlk kullanımda küçük miktarla denemek ve alerjen içerikleri kontrol etmek daha güvenli olur."


def _general_without_analysis(message: str) -> str:
    text = message.lower()
    if _contains_any(text, ["ucuz", "kalite", "pahalı", "pahali"]):
        return "Genel olarak sadece en ucuz ürüne yönelmek doğru olmayabilir; yorum kalitesi, iade kolaylığı ve ürünün kullanım amacına uyumu da önemli."
    if _contains_any(text, ["hediye", "anneme", "sevgilime"]):
        return "Hediye alırken kişisel tercih riski düşük, iadesi kolay ve yorumları tutarlı ürünlere yönelmek daha güvenli olur."
    return "Önce bir ürün linki analiz etmelisin. Sonra o ürün hakkında detaylı yorum yapabilirim."


def generate_rule_based_reply(
    intent: str,
    preferences: dict[str, bool],
    analysis: dict[str, Any] | None,
    history: list[Any],
    message: str = "",
) -> str:
    if not analysis:
        return _general_without_analysis(message)

    info = _summary(analysis)
    features = extract_product_features(analysis)

    if intent == "color_question":
        return _color_reply(features)
    if intent == "daily_use":
        return _daily_use_reply(features, analysis)
    if intent == "usage_scenario":
        return _usage_reply(features, preferences)
    if intent == "price_question":
        return _price_reply(analysis)
    if intent == "expensive_or_worth":
        return _price_reply(analysis, worth=True)
    if intent == "cheap_quality_concern":
        return _cheap_quality_reply(analysis)
    if intent == "alternative_request":
        return _alternative_reply(analysis)
    if intent == "compare_request":
        return _alternative_reply(analysis)
    if intent == "review_trust":
        return _review_reply(analysis)
    if intent == "fake_review_question":
        return _review_reply(analysis, fake_only=True)
    if intent == "return_risk":
        return _return_reply(analysis, features)
    if intent == "product_feature":
        return _feature_reply(message, features)
    if intent == "gift_advice":
        return _gift_reply(analysis, features)
    if intent == "skin_sensitivity":
        return _skin_reply(features)
    if intent == "size_fit":
        return "Beden/kalıp için ürün yorumları daha belirleyici olur. Kendi ölçülerine yakın kullanıcı yorumlarını ve iade koşullarını kontrol etmelisin."
    if intent == "durability":
        return "Dayanıklılık için ürün adından kesin sonuç çıkaramam. Uzun kullanım yorumları, malzeme kalitesi ve garanti/iade koşulları daha belirleyici."
    if intent == "brand_trust":
        return f"{info['brand'] or 'Bu marka'} için genel marka itibarı verim yok; bu ürün özelinde yorum güveni, puan ve iade riskiyle değerlendirmek daha doğru."
    if intent == "seller_trust":
        return f"Satıcı için elimdeki sinyal { _fmt(info['seller'], '/10') }. Satıcı puanı, teslimat yorumları ve iade süreci birlikte kontrol edilmeli."
    if intent == "why_not_recommended":
        return _decision_reason_reply(analysis, negative=True)
    if intent == "why_recommended":
        return _decision_reason_reply(analysis, positive=True)
    if intent == "explain_decision":
        return _decision_reason_reply(analysis)
    if intent == "buy_advice":
        if info["decision"] == "ALINABİLİR":
            return "Alınabilir görünüyor; ama kullanım amacına uyduğundan emin ol. Özellikle ürünün vaat ettiği etki senin beklentinle örtüşüyorsa tercih edilebilir."
        if info["decision"] == "ÖNERİLMEZ":
            return "Ben bu üründe temkinli olurdum. Risk sinyalleri veya fiyat/performans tarafı yeterince güçlü görünmüyor; alternatiflere bakmak daha iyi."
        return "Karar net değil; fiyat, yorum güveni ve kullanım beklentin üzerinden alternatiflerle karşılaştırmanı öneririm."
    if intent == "follow_up":
        return "Önceki konu üzerinden düşünürsek, karar verirken tek bir ölçüte takılma; fiyat, yorum güveni ve kullanım amacına uyum birlikte önemli."

    return "Bu konuda net cevap verebilmem için sorunu biraz daha ürün özelliği, fiyat, yorum veya kullanım amacı üzerinden sorabilir misin?"


def _compact_analysis(analysis: dict[str, Any]) -> dict[str, Any]:
    keys = [
        "productName", "brand", "category", "price", "rating", "reviewCount",
        "questionCount", "sellerScore", "fakeReviewRisk", "returnRisk",
        "trustScore", "sentimentScore", "pricePerformance", "finalDecision",
        "analysis", "shoppingBehavior", "alternativeProducts", "betterAlternatives",
    ]
    return {key: analysis.get(key) for key in keys if key in analysis}


def generate_llm_reply(
    message: str,
    history: list[Any],
    analysis: dict[str, Any],
    intent: str,
    preferences: dict[str, bool],
) -> str | None:
    api_key = os.getenv("OPENROUTER_API_KEY", "").strip()
    model = os.getenv("OPENROUTER_MODEL")
    if not api_key:
        return None
    if not model:
        return None

    features = extract_product_features(analysis)
    messages = [{"role": "system", "content": SYSTEM_PROMPT}]
    messages.extend(_last_messages(history, 12))
    messages.append({
        "role": "user",
        "content": (
            f"latest user message: {message}\n"
            f"product analysis: {json.dumps(_compact_analysis(analysis), ensure_ascii=False)}\n"
            f"extracted intent: {intent}\n"
            f"extracted preferences: {json.dumps(preferences, ensure_ascii=False)}\n"
            f"extracted product features: {json.dumps(features, ensure_ascii=False)}\n"
            "Do not repeat raw product statistics unless directly relevant. "
            "Answer only the user's actual question."
        ),
    })

    try:
        response = requests.post(
            "https://openrouter.ai/api/v1/chat/completions",
            headers={"Authorization": f"Bearer {api_key}", "Content-Type": "application/json"},
            json={
                "model": model,
                "messages": messages,
                "temperature": 0.35,
                "max_tokens": 420,
            },
            timeout=20,
        )
        response.raise_for_status()
        return response.json()["choices"][0]["message"]["content"].strip()
    except Exception as exc:
        print(f"[chatbot] OpenRouter fallback to rules: {exc}")
        return None


def prevent_repeated_reply(reply: str, history: list[Any]) -> str:
    last = _last_assistant(history)
    if not last:
        return reply
    similarity = SequenceMatcher(None, reply.lower(), last.lower()).ratio()
    if similarity <= 0.70:
        return reply
    return "Önceki cevabı biraz açayım: Aynı noktayı tekrar etmek yerine, kararını kullanım amacına göre netleştirelim. Fiyat, yorum güveni, ürün özelliği veya alternatiflerden hangisi kafanı karıştırıyorsa ona göre değerlendirebilirim."


def chat_reply(message: str, history: list[Any], analysis: dict[str, Any] | None) -> dict[str, Any]:
    context = build_chat_context(message, history, analysis)
    intent = context["intent"]
    preferences = context["preferences"]

    if analysis and intent not in RULE_BASED_INTENTS:
        llm_reply = generate_llm_reply(message, history, analysis, intent, preferences)
        if llm_reply:
            return {
                "reply": prevent_repeated_reply(llm_reply, history),
                "intent": intent,
                "preferences": preferences,
            }

    reply = generate_rule_based_reply(intent, preferences, analysis, history, message)
    return {
        "reply": prevent_repeated_reply(reply, history),
        "intent": intent,
        "preferences": preferences,
    }
