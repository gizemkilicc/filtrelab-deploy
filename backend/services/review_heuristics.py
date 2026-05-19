"""Yorum sezgisel analiz yardımcıları (SYSTEM 1 — Pseudo Comprehend).

Bu modüldeki her şey saf Python'dur: ağ/IO yapmaz, deterministiktir, hızlıdır
ve exception sızdırmaz. pseudo_comprehend motoru bu fonksiyonları sahte yorum
tespiti, anahtar kelime çıkarımı ve risk skorlaması için kullanır.
"""

import re
from collections import Counter
from typing import List, Optional

# ── Sabitler ────────────────────────────────────────────────────────────────

# Anahtar kelime çıkarımında elenecek Türkçe + genel stopword'ler
_STOPWORDS = {
    "ve", "ile", "bir", "bu", "şu", "için", "çok", "daha", "ama", "de", "da",
    "ki", "mi", "mı", "mu", "ne", "her", "gibi", "kadar", "ben", "sen", "biz",
    "siz", "onlar", "olarak", "olan", "var", "yok", "çünkü", "fakat", "ya",
    "hem", "ürün", "ürünü", "aldım", "geldi", "the", "a", "an", "is", "it",
    "to", "of", "and", "in",
}

# Tek başına anlamsız kabul edilen kısa/jenerik yorum kalıpları
_GENERIC_PHRASES = {
    "güzel", "harika", "iyi", "süper", "mükemmel", "tavsiye ederim", "beğendim",
    "çok güzel", "çok iyi", "memnunum", "teşekkürler", "kötü", "berbat",
    "idare eder", "fena değil", "ürün güzel", "bayıldım", "👍",
}

# Basit Türkçe duygu sözlüğü — rating/metin uyumsuzluğu tespitinde kullanılır
_POSITIVE_WORDS = {
    "güzel", "harika", "mükemmel", "süper", "kaliteli", "memnun", "beğendim",
    "tavsiye", "hızlı", "sağlam", "şahane", "bayıldım", "muhteşem", "iyi",
    "kullanışlı", "uygun", "başarılı",
}
_NEGATIVE_WORDS = {
    "kötü", "berbat", "rezalet", "kalitesiz", "bozuk", "pişman", "kırık",
    "yavaş", "iğrenç", "beğenmedim", "kandırıldım", "çöp", "saçma", "vasat",
    "hayal", "sorunlu", "eksik",
}

# Emoji aralıkları (sembol + piktografik bloklar)
_EMOJI_RE = re.compile(
    "[\U0001F000-\U0001FAFF\U00002600-\U000027BF"
    "\U0001F1E6-\U0001F1FF⬀-⯿←-⇿]"
)
_WORD_RE = re.compile(r"\w+", re.UNICODE)


# ── Yardımcı fonksiyonlar ───────────────────────────────────────────────────

def normalize_review(item) -> dict:
    """str veya dict olabilen ham yorum öğesini {text, rating} sözlüğüne çevirir.

    Hatalı/eksik veriye karşı tamamen toleranslıdır; asla exception fırlatmaz.
    """
    if isinstance(item, dict):
        text = str(item.get("text") or "").strip()
        rating = item.get("rating")
    else:
        text = str(item or "").strip()
        rating = None
    try:
        rating = float(rating) if rating is not None else None
    except (TypeError, ValueError):
        rating = None
    return {"text": text, "rating": rating}


def _tokens(text: str) -> List[str]:
    """Metni küçük harfli kelime listesine ayırır."""
    return [w.lower() for w in _WORD_RE.findall(text or "")]


def is_short_or_generic(text: str) -> bool:
    """Çok kısa veya tek başına anlamsız jenerik yorumları işaretler."""
    t = (text or "").strip().lower()
    if len(t) < 12:
        return True
    if t.strip(" .!👍") in _GENERIC_PHRASES:
        return True
    return len(_tokens(t)) <= 2


def emoji_stats(text: str) -> tuple:
    """(emoji_sayısı, emoji_oranı) döndürür."""
    if not text:
        return 0, 0.0
    emojis = _EMOJI_RE.findall(text)
    return len(emojis), len(emojis) / max(len(text), 1)


def is_emoji_spam(text: str) -> bool:
    """Aşırı emoji içeren / emojiyle doldurulmuş yorumları yakalar."""
    count, ratio = emoji_stats(text)
    words = len(_tokens(text))
    return count >= 5 or (count >= 3 and words <= 3) or ratio > 0.3


def lexicon_sentiment(text: str) -> str:
    """Sözlük tabanlı kaba duygu sınıfı: POSITIVE / NEGATIVE / NEUTRAL.

    AWS ve DeepSeek erişilemezse son katman fallback olarak da kullanılır.
    """
    words = set(_tokens(text))
    pos = len(words & _POSITIVE_WORDS)
    neg = len(words & _NEGATIVE_WORDS)
    if pos > neg:
        return "POSITIVE"
    if neg > pos:
        return "NEGATIVE"
    return "NEUTRAL"


def rating_text_mismatch(text: str, rating: Optional[float]) -> bool:
    """Yıldız puanı ile metnin duygusu çelişiyor mu? (manipülasyon sinyali)"""
    if rating is None:
        return False
    sentiment = lexicon_sentiment(text)
    if rating >= 4 and sentiment == "NEGATIVE":
        return True
    if rating <= 2 and sentiment == "POSITIVE":
        return True
    return False


def detect_duplicate_indices(texts: List[str]) -> set:
    """Aynı metnin tekrar ettiği yorumların indekslerini döndürür."""
    seen: dict = {}
    dups: set = set()
    for i, t in enumerate(texts):
        key = re.sub(r"\s+", " ", (t or "").strip().lower())
        if not key:
            continue
        if key in seen:
            dups.add(i)
            dups.add(seen[key])
        else:
            seen[key] = i
    return dups


def extract_key_phrases(texts: List[str], top_n: int = 10) -> List[str]:
    """Yorumlardan en sık geçen anlamlı kelimeleri (anahtar ifadeler) çıkarır."""
    counter: Counter = Counter()
    for t in texts:
        for w in _tokens(t):
            if len(w) < 3 or w in _STOPWORDS or w.isdigit():
                continue
            counter[w] += 1
    return [w for w, _ in counter.most_common(top_n)]


def analyze_review_heuristics(reviews: List[dict]) -> dict:
    """Tüm sezgisel kontrolleri çalıştırır ve sahte yorum metriklerini döndürür.

    reviews: normalize_review çıktısı sözlüklerinden oluşan liste.
    Dönüş: {suspicious_review_count, review_risk_score, detected_key_phrases,
            per_review_flags}
    """
    texts = [r["text"] for r in reviews]
    dup_idx = detect_duplicate_indices(texts)

    suspicious = 0
    per_review_flags: List[List[str]] = []
    for i, r in enumerate(reviews):
        flags: List[str] = []
        if i in dup_idx:
            flags.append("duplicate")
        if is_short_or_generic(r["text"]):
            flags.append("short_generic")
        if is_emoji_spam(r["text"]):
            flags.append("emoji_spam")
        if rating_text_mismatch(r["text"], r["rating"]):
            flags.append("rating_mismatch")
        if flags:
            suspicious += 1
        per_review_flags.append(flags)

    total = len(reviews) or 1
    # Risk skoru: şüpheli yorum oranı (%70 ağırlık) + bayrak yoğunluğu (%30)
    flag_weight = sum(len(f) for f in per_review_flags)
    risk = round(min(100.0, (suspicious / total) * 70 + (flag_weight / total) * 30))

    return {
        "suspicious_review_count": suspicious,
        "review_risk_score": risk,
        "detected_key_phrases": extract_key_phrases(texts),
        "per_review_flags": per_review_flags,
    }
