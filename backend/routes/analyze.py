from fastapi import APIRouter
from models.response_model import AnalyzeRequest, AnalyzeResponse
from services.mock_ai import generate_analysis
import asyncio

router = APIRouter()

from fastapi.responses import JSONResponse

@router.post("/analyze")
async def analyze_url(request: AnalyzeRequest):
    try:
        # Generate dynamic analysis via Playwright
        analysis_data = await generate_analysis(request.url)
        return analysis_data
        
    except ValueError as e:
        return JSONResponse(status_code=400, content={"success": False, "error": str(e)})
    except Exception as e:
        print(f"Analyze error: {e}")
        return JSONResponse(status_code=500, content={"success": False, "error": "Ürün bilgileri alınamadı. Trendyol sayfası engellemiş olabilir."})
