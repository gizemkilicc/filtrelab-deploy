import traceback

from fastapi import APIRouter
from fastapi.responses import JSONResponse

from models.response_model import AnalyzeRequest
from services.mock_ai import generate_analysis

router = APIRouter()


@router.post("/analyze")
async def analyze_url(request: AnalyzeRequest):
    try:
        analysis_data = await generate_analysis(request.url)
        return analysis_data

    except ValueError as e:
        # Scraper returned empty data or unsupported platform
        return JSONResponse(
            status_code=422,
            content={"success": False, "error": str(e)},
        )
    except Exception as e:
        print("[analyze] Unhandled exception:")
        traceback.print_exc()
        return JSONResponse(
            status_code=500,
            content={"success": False, "error": "Ürün bilgileri alınamadı. Lütfen geçerli bir ürün bağlantısı deneyin."},
        )
