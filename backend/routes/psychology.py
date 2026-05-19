"""SYSTEM 2 endpoint'i — Shopping Psychology Engine.

POST /shopping-psychology
Gövde: {"history": [ {category, brand, price, productName, productUrl,
                      trustScore, viewCount}, ... ]}
Yanıt: analyze_shopping_behavior çıktısı.

Endpoint hiçbir koşulda 500 dönmez; beklenmedik hatada bile 200 + güvenli
varsayılan döndürür.
"""

import traceback
from typing import List

from fastapi import APIRouter
from fastapi.responses import JSONResponse
from pydantic import BaseModel

from services.psychology_service import analyze_shopping_behavior

router = APIRouter()


class ShoppingPsychologyRequest(BaseModel):
    # Her öğe görüntülenen/analiz edilen bir ürünü temsil eden sözlüktür.
    history: List = []


_SAFE_FALLBACK = {
    "shopping_personality": "Analytical Researcher",
    "trust_sensitivity": 50,
    "impulsive_vs_analytical": 50,
    "budget_behavior": "Belirsiz",
    "recommendation_strategy": "Henüz yeterli gezinme verisi yok.",
    "confidence_score": 0,
}


@router.post("/shopping-psychology")
async def shopping_psychology(request: ShoppingPsychologyRequest):
    """Gezinme geçmişinden alışveriş kişiliği profili döndürür."""
    try:
        return analyze_shopping_behavior(request.history)
    except Exception:
        traceback.print_exc()
        return JSONResponse(status_code=200, content=dict(_SAFE_FALLBACK))
