"""Duygu analizi: Türkçe yorumlar → OpenRouter/DeepSeek ile İngilizce çeviri →
AWS Comprehend BatchDetectSentiment.

Tasarım ilkesi: bu modül ASLA exception fırlatmaz. Her dış çağrı (OpenRouter,
AWS) try/except + timeout ile korunur. Herhangi bir adım başarısız olursa bir
fallback sözlüğü döndürülür ve çağıran kod (mock_ai) mevcut algoritmayı
kullanmaya devam eder. Böylece backend 500 dönmez, frontend boş yanıt almaz,
site çökmez.
"""

import json
import os
import re
from typing import List, Optional

import boto3
import requests
from botocore.config import Config as BotoConfig

OPENROUTER_URL = "https://openrouter.ai/api/v1/chat/completions"
OPENROUTER_MODEL = "deepseek/deepseek-chat"

_MAX_REVIEWS = 25            # AWS Comprehend BatchDetectSentiment limiti
_MAX_CHARS = 4900            # Comprehend metin başına ~5000 byte sınırı
_OPENROUTER_TIMEOUT = 20     # saniye
_AWS_TIMEOUT = 10            # saniye

# Comprehend duygu etiketi → ağırlıklı skor
_SENTIMENT_WEIGHTS = {"POSITIVE": 100, "NEGATIVE": 0, "NEUTRAL": 50, "MIXED": 50}


def _fallback(source: str, error: Optional[str] = None) -> dict:
    """Standart fallback sözlüğü — frontend hiçbir zaman boş yanıt almaz."""
    result = {
        "sentiment_score": 50,
        "positive": 0,
        "negative": 0,
        "neutral": 0,
        "total_analyzed": 0,
        "source": source,
    }
    if error:
        result["error"] = error
    return result


def _normalize_texts(reviews: List) -> List[str]:
    """reviews listesini temiz string listesine çevirir.
    Öğe dict ise 'text' alanını alır, string ise doğrudan kullanır."""
    texts: List[str] = []
    for item in reviews or []:
        if isinstance(item, dict):
            value = item.get("text") or ""
        else:
            value = item or ""
        value = str(value).strip()
        if value:
            texts.append(value[:_MAX_CHARS])
    return texts


def _parse_json_array(content: str) -> Optional[list]:
    """LLM yanıtından JSON dizisini çıkarır (```json blokları dahil)."""
    if not content:
        return None
    try:
        parsed = json.loads(content)
        return parsed if isinstance(parsed, list) else None
    except Exception:
        pass
    match = re.search(r"\[.*\]", content, re.DOTALL)
    if match:
        try:
            parsed = json.loads(match.group(0))
            return parsed if isinstance(parsed, list) else None
        except Exception:
            return None
    return None


def _translate_to_english(texts: List[str]) -> Optional[List[str]]:
    """Türkçe yorumları OpenRouter/DeepSeek ile İngilizce'ye çevirir.
    Başarısız olursa None döndürür (çağıran kod fallback'e düşer)."""
    api_key = os.getenv("OPENROUTER_API_KEY")
    if not api_key:
        print("[Comprehend] OPENROUTER_API_KEY bulunamadı")
        return None
    try:
        reviews_json = json.dumps(texts, ensure_ascii=False)
        prompt = (
            "Translate these Turkish reviews to English. Return only a JSON "
            "array of translated strings, same order:\n" + reviews_json
        )
        response = requests.post(
            OPENROUTER_URL,
            headers={
                "Authorization": f"Bearer {api_key}",
                "Content-Type": "application/json",
            },
            json={
                "model": OPENROUTER_MODEL,
                "messages": [{"role": "user", "content": prompt}],
            },
            timeout=_OPENROUTER_TIMEOUT,
        )
        response.raise_for_status()
        content = response.json()["choices"][0]["message"]["content"]
        translated = _parse_json_array(content)
        if not translated:
            print("[Comprehend] Çeviri yanıtı JSON dizisi olarak ayrıştırılamadı")
            return None
        cleaned = [str(t).strip()[:_MAX_CHARS] for t in translated if str(t).strip()]
        return cleaned or None
    except Exception as e:
        print(f"[Comprehend] Çeviri hatası: {e}")
        return None


def analyze_sentiment_batch(reviews: List, language_code: str = "tr") -> dict:
    """
    Türkçe yorumları İngilizce'ye çevirip AWS Comprehend ile duygu analizi yapar.

    Akış:
      1. reviews listesinden ilk 25 yorumun metnini al
      2. OpenRouter/DeepSeek ile Türkçe → İngilizce çevir
      3. AWS Comprehend BatchDetectSentiment (LanguageCode="en")
      4. POSITIVE=100, NEGATIVE=0, NEUTRAL=50, MIXED=50 ağırlıklı ortalama

    Asla exception fırlatmaz. Dönen 'source' alanı:
      - "aws_comprehend"        → başarılı
      - "fallback_no_reviews"   → yorum yok
      - "fallback_error"        → çeviri veya Comprehend başarısız
    """
    try:
        texts = _normalize_texts(reviews)
        if not texts:
            return _fallback("fallback_no_reviews")

        # 1) İlk 25 yorum (mevcut yorum sayısı 25'ten azsa hepsi)
        texts = texts[:_MAX_REVIEWS]

        # 2) Türkçe → İngilizce çeviri
        translated = _translate_to_english(texts)
        if not translated:
            return _fallback("fallback_error", "translation_failed")

        # 3) AWS Comprehend BatchDetectSentiment
        client = boto3.client(
            "comprehend",
            region_name=os.getenv("AWS_REGION", "eu-north-1"),
            aws_access_key_id=os.getenv("AWS_ACCESS_KEY_ID"),
            aws_secret_access_key=os.getenv("AWS_SECRET_ACCESS_KEY"),
            config=BotoConfig(
                connect_timeout=_AWS_TIMEOUT,
                read_timeout=_AWS_TIMEOUT,
                retries={"max_attempts": 1},
            ),
        )
        response = client.batch_detect_sentiment(
            TextList=translated[:_MAX_REVIEWS],
            LanguageCode="en",
        )
        results = response.get("ResultList", [])
        if not results:
            return _fallback("fallback_error", "no_comprehend_results")

        # 4) Sayımlar ve ağırlıklı ortalama skor
        positive = sum(1 for r in results if r.get("Sentiment") == "POSITIVE")
        negative = sum(1 for r in results if r.get("Sentiment") == "NEGATIVE")
        neutral = sum(1 for r in results if r.get("Sentiment") == "NEUTRAL")
        total = len(results)

        weighted = sum(_SENTIMENT_WEIGHTS.get(r.get("Sentiment"), 50) for r in results)
        sentiment_score = round(weighted / total) if total else 50

        return {
            "sentiment_score": sentiment_score,
            "positive": positive,
            "negative": negative,
            "neutral": neutral,
            "total_analyzed": total,
            "source": "aws_comprehend",
        }
    except Exception as e:
        print(f"[Comprehend] Hata: {e}")
        return _fallback("fallback_error", str(e))
