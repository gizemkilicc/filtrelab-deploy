"""SYSTEM 1 endpoint'i — Pseudo Comprehend yorum analizi.

POST /pseudo-comprehend
Gövde: {"reviews": [ "metin", {"text": "metin", "rating": 5}, ... ]}
Yanıt: pseudo_comprehend_analysis çıktısı.

Endpoint hiçbir koşulda 500 dönmez; beklenmedik hatada bile 200 + güvenli
fallback sözlüğü döndürür (frontend asla boş yanıt almaz).
"""

import traceback
from typing import List

from fastapi import APIRouter
from fastapi.responses import JSONResponse
from pydantic import BaseModel

from services.pseudo_comprehend import pseudo_comprehend_analysis

router = APIRouter()


class PseudoComprehendRequest(BaseModel):
    # Öğeler string ya da {text, rating} sözlüğü olabilir; motor normalize eder.
    reviews: List = []


_SAFE_FALLBACK = {
    "sentiment_score": 50,
    "positive": 0,
    "negative": 0,
    "neutral": 0,
    "mixed": 0,
    "suspicious_review_count": 0,
    "review_risk_score": 0,
    "detected_key_phrases": [],
    "source": "deepseek_fallback",
}


@router.post("/pseudo-comprehend")
async def pseudo_comprehend(request: PseudoComprehendRequest):
    """Yorum listesi için duygu + sahte yorum + anahtar kelime analizi döndürür."""
    try:
        return await pseudo_comprehend_analysis(request.reviews)
    except Exception:
        traceback.print_exc()
        # Endpoint asla çökmez / 500 dönmez.
        return JSONResponse(status_code=200, content=dict(_SAFE_FALLBACK))
