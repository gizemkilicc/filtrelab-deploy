"""Pseudo AWS Comprehend motoru (SYSTEM 1).

Yorumlar için duygu analizi + sahte yorum tespiti + anahtar kelime çıkarımı
üretir. Duygu analizinde 3 katmanlı fallback uygulanır:

    1. Gerçek AWS Comprehend          → source = "aws_comprehend"
    2. DeepSeek (OpenRouter) sınıflama → source = "deepseek_fallback"
    3. Sözlük tabanlı sezgisel motor   → source = "deepseek_fallback"

Sahte yorum sezgileri (review_heuristics) her durumda çalışır — saf Python.

Tasarım ilkesi: pseudo_comprehend_analysis ASLA exception fırlatmaz. Her dış
çağrı try/except + timeout korumalıdır; başarısızlıkta bir alt katmana düşülür.
Hiçbir koşulda backend çökmez, frontend boş yanıt almaz.

Çıktı sözlüğü:
    {
      sentiment_score, positive, negative, neutral, mixed,
      suspicious_review_count, review_risk_score,
      detected_key_phrases, source
    }
"""

import asyncio
import hashlib
import json
import os
import re
import time
from typing import List, Optional

import requests

from .comprehend_service import analyze_sentiment_batch
from .review_heuristics import (
    analyze_review_heuristics,
    lexicon_sentiment,
    normalize_review,
)

OPENROUTER_URL = "https://openrouter.ai/api/v1/chat/completions"
OPENROUTER_MODEL = "deepseek/deepseek-chat"

_MAX_REVIEWS = 25            # AWS Comprehend batch limiti ile uyumlu
_OPENROUTER_TIMEOUT = 20     # saniye — DeepSeek isteği
_DEEPSEEK_RETRIES = 2        # 1 deneme + 1 retry
_CACHE_TTL = 600             # saniye — sonuç önbelleği ömrü
_CACHE_MAX = 200             # önbellekte tutulacak azami kayıt

_SENTIMENT_WEIGHTS = {"POSITIVE": 100, "NEGATIVE": 0, "NEUTRAL": 50, "MIXED": 50}

# Sonuç önbelleği: { reviews_hash: (timestamp, result) }
_cache: dict = {}

# AWS kalıcı bir hatayla (abonelik/izin/endpoint) düşerse tekrar denenmez —
# gereksiz çeviri + timeout maliyetini önler. Süreç yeniden başlayınca sıfırlanır
# (yani AWS hesabı aktive olduğunda otomatik yeniden devreye girer).
_aws_permanently_down = False
_AWS_PERMANENT_MARKERS = (
    "subscriptionrequired", "accessdenied", "could not connect",
    "endpointconnectionerror", "unrecognizedclient", "invalidsignature",
)


# ── Yardımcı fonksiyonlar ───────────────────────────────────────────────────

def _empty_result(source: str = "deepseek_fallback") -> dict:
    """Yorum yokken / beklenmedik hatada dönen güvenli sonuç."""
    return {
        "sentiment_score": 50,
        "positive": 0,
        "negative": 0,
        "neutral": 0,
        "mixed": 0,
        "suspicious_review_count": 0,
        "review_risk_score": 0,
        "detected_key_phrases": [],
        "source": source,
    }


def _cache_key(reviews: List[dict]) -> str:
    raw = json.dumps([(r["text"], r["rating"]) for r in reviews], ensure_ascii=False)
    return hashlib.sha256(raw.encode("utf-8")).hexdigest()


def _cache_get(key: str) -> Optional[dict]:
    entry = _cache.get(key)
    if entry and (time.time() - entry[0]) < _CACHE_TTL:
        return entry[1]
    return None


def _cache_set(key: str, result: dict) -> None:
    _cache[key] = (time.time(), result)
    if len(_cache) > _CACHE_MAX:  # en eski kayıtları temizle
        for k, _ in sorted(_cache.items(), key=lambda kv: kv[1][0])[: _CACHE_MAX // 4]:
            _cache.pop(k, None)


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


def _counts_from_labels(labels: List[str]) -> dict:
    """Duygu etiketi listesinden sayımlar + ağırlıklı skor üretir."""
    pos = labels.count("POSITIVE")
    neg = labels.count("NEGATIVE")
    neu = labels.count("NEUTRAL")
    mix = labels.count("MIXED")
    total = len(labels) or 1
    weighted = sum(_SENTIMENT_WEIGHTS.get(lbl, 50) for lbl in labels)
    return {
        "sentiment_score": round(weighted / total),
        "positive": pos, "negative": neg, "neutral": neu, "mixed": mix,
    }


# ── Katman 1: AWS Comprehend ────────────────────────────────────────────────

def _aws_sentiment(reviews: List[dict]) -> Optional[dict]:
    """AWS Comprehend dener. Başarılıysa duygu sözlüğü, değilse None döndürür.

    Senkron çalışır; çağıran asyncio.to_thread ile sarmalar.
    """
    global _aws_permanently_down
    if _aws_permanently_down:
        return None
    try:
        result = analyze_sentiment_batch(reviews)
    except Exception as e:  # comprehend_service zaten yutuyor; yine de güvence
        print(f"[pseudo_comprehend] AWS çağrısı beklenmedik hata: {e}")
        return None

    if result.get("source") == "aws_comprehend":
        total = result.get("total_analyzed", 0) or len(reviews)
        pos = result.get("positive", 0)
        neg = result.get("negative", 0)
        neu = result.get("neutral", 0)
        return {
            "sentiment_score": result.get("sentiment_score", 50),
            "positive": pos, "negative": neg, "neutral": neu,
            "mixed": max(0, total - pos - neg - neu),
        }

    # Kalıcı bir hata mı? Öyleyse sonraki çağrılarda AWS atlanır.
    err = str(result.get("error", "")).lower()
    if any(marker in err for marker in _AWS_PERMANENT_MARKERS):
        _aws_permanently_down = True
        print(f"[pseudo_comprehend] AWS kalıcı devre dışı (yeniden başlatınca "
              f"sıfırlanır): {result.get('error')}")
    return None


# ── Katman 2: DeepSeek (OpenRouter) ─────────────────────────────────────────

def _deepseek_classify(texts: List[str]) -> Optional[List[str]]:
    """DeepSeek ile her yorumu POSITIVE/NEGATIVE/NEUTRAL/MIXED sınıflar.

    Türkçe metinle doğrudan çalışır (çeviri gerekmez). timeout + retry korumalı.
    Başarısız olursa None döndürür. Senkron — çağıran to_thread ile sarmalar.
    """
    api_key = os.getenv("OPENROUTER_API_KEY")
    if not api_key:
        print("[pseudo_comprehend] OPENROUTER_API_KEY yok — DeepSeek atlanıyor")
        return None

    prompt = (
        "Classify the sentiment of each Turkish product review below. Return "
        "ONLY a JSON array of strings, same order, each exactly one of: "
        "POSITIVE, NEGATIVE, NEUTRAL, MIXED.\n"
        + json.dumps(texts, ensure_ascii=False)
    )
    for attempt in range(1, _DEEPSEEK_RETRIES + 1):
        try:
            resp = requests.post(
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
            resp.raise_for_status()
            content = resp.json()["choices"][0]["message"]["content"]
            labels = _parse_json_array(content)
            if labels:
                # Geçersiz etiketleri NEUTRAL'a normalize et
                return [
                    (str(lbl).strip().upper()
                     if str(lbl).strip().upper() in _SENTIMENT_WEIGHTS
                     else "NEUTRAL")
                    for lbl in labels
                ]
            print(f"[pseudo_comprehend] DeepSeek yanıtı ayrıştırılamadı "
                  f"(deneme {attempt})")
        except Exception as e:
            print(f"[pseudo_comprehend] DeepSeek deneme {attempt} hata: {e}")
        if attempt < _DEEPSEEK_RETRIES:
            time.sleep(0.5)
    return None


# ── Ana giriş noktası ───────────────────────────────────────────────────────

async def pseudo_comprehend_analysis(reviews: List) -> dict:
    """SYSTEM 1 ana fonksiyonu — yorum listesini analiz eder.

    reviews: str veya {text, rating} sözlüklerinden oluşan liste.
    Asla exception fırlatmaz; her zaman geçerli bir sonuç sözlüğü döndürür.
    """
    try:
        normalized = [normalize_review(r) for r in (reviews or [])]
        normalized = [r for r in normalized if r["text"]][:_MAX_REVIEWS]
        if not normalized:
            return _empty_result(source="deepseek_fallback")

        # Önbellek kontrolü (hızlı yanıt)
        key = _cache_key(normalized)
        cached = _cache_get(key)
        if cached is not None:
            return cached

        texts = [r["text"] for r in normalized]

        # ── Duygu: Katman 1 (AWS) → Katman 2 (DeepSeek) → Katman 3 (sözlük) ──
        sentiment = await asyncio.to_thread(_aws_sentiment, normalized)
        if sentiment is not None:
            source = "aws_comprehend"
        else:
            labels = await asyncio.to_thread(_deepseek_classify, texts)
            if not labels:  # son katman: sözlük tabanlı
                labels = [lexicon_sentiment(t) for t in texts]
            sentiment = _counts_from_labels(labels)
            source = "deepseek_fallback"

        # ── Sahte yorum sezgileri (her zaman çalışır, saf Python) ──
        heur = analyze_review_heuristics(normalized)

        result = {
            "sentiment_score": sentiment["sentiment_score"],
            "positive": sentiment["positive"],
            "negative": sentiment["negative"],
            "neutral": sentiment["neutral"],
            "mixed": sentiment["mixed"],
            "suspicious_review_count": heur["suspicious_review_count"],
            "review_risk_score": heur["review_risk_score"],
            "detected_key_phrases": heur["detected_key_phrases"],
            "source": source,
        }
        _cache_set(key, result)
        return result
    except Exception as e:
        # Hiçbir koşulda yukarı exception sızmaz — backend çökmez.
        print(f"[pseudo_comprehend] Beklenmeyen hata, fallback döndürülüyor: {e}")
        return _empty_result(source="deepseek_fallback")
