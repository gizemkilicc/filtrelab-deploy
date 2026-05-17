from pydantic import BaseModel
from typing import List, Optional


class AlternativeProduct(BaseModel):
    name: str
    price: str
    image: Optional[str] = None
    reason: str
    url: str
    isDirectProductUrl: bool


class AnalyzeRequest(BaseModel):
    url: str
    includeReviews: bool = False


class ReviewRequest(BaseModel):
    url: str
    maxReviews: Optional[int] = None


class ReviewsExportRequest(BaseModel):
    url: str
    maxReviews: Optional[int] = None
    format: str = "json"


class AnalyzeResponse(BaseModel):
    extractedFromUrl: bool
    sourceUrl: str
    sourcePlatform: str
    dataSource: str
    confidence: float
    extractedFields: dict
    productName: str
    brand: str
    category: str
    categoryConfidence: float
    price: str
    image: Optional[str] = None
    rating: float
    reviewCount: int
    fakeReviewRisk: int
    trustScore: int
    returnProbability: str
    sentimentScore: float
    pricePerformanceScore: float
    psychologyWarning: str
    finalDecision: str
    decisionReason: str
    fakeReviewExplanation: str
    returnReasonExplanation: str
    betterAlternatives: List[AlternativeProduct]
