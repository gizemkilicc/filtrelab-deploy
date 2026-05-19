import traceback
from typing import Optional

from fastapi import APIRouter
from fastapi.responses import JSONResponse
from pydantic import BaseModel

from services.cross_platform_matcher import find_cross_platform_matches

router = APIRouter()

_VALID_PLATFORMS = {"trendyol", "hepsiburada", "amazon_tr"}


def _normalize_platform(name: str) -> str:
    """Map display names and variations to internal platform IDs."""
    n = (name or "").lower().strip()
    if "trendyol" in n:
        return "trendyol"
    if "hepsiburada" in n:
        return "hepsiburada"
    if "amazon" in n:
        return "amazon_tr"
    return n


class CrossPlatformRequest(BaseModel):
    source_platform: str
    product_name: str
    brand: Optional[str] = ""
    price: Optional[float] = 0.0


@router.post("/cross-platform-compare")
async def cross_platform_compare(request: CrossPlatformRequest):
    platform = _normalize_platform(request.source_platform)
    print(f"[cross-platform] received source_platform={request.source_platform!r} → normalized={platform!r}")
    print(f"[cross-platform] product_name={request.product_name!r} brand={request.brand!r} price={request.price}")

    if platform not in _VALID_PLATFORMS:
        return JSONResponse(
            status_code=422,
            content={"error": f"Desteklenmeyen platform: {request.source_platform!r}"},
        )
    try:
        result = await find_cross_platform_matches(
            source_platform=platform,
            product_name=request.product_name,
            brand=request.brand or "",
            price=request.price or 0.0,
        )
        return result
    except Exception:
        traceback.print_exc()
        return JSONResponse(
            status_code=500,
            content={"error": "Platform karşılaştırması yapılamadı."},
        )
