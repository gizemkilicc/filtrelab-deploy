from collections import Counter
from typing import Any

from fastapi import APIRouter, Depends, Header, HTTPException
from pydantic import BaseModel
from sqlalchemy.orm import Session

from services.auth_service import decode_access_token, get_user_by_id
from services.database import (
    AnalysisHistory,
    Favorite,
    PriceTracking,
    User,
    get_db,
)

router = APIRouter(tags=["user-features"])


class PriceTrackingCreate(BaseModel):
    productName: str
    productUrl: str
    currentPrice: str
    targetPrice: str | None = None
    image: str | None = None
    platform: str | None = None


class AnalysisHistoryCreate(BaseModel):
    productName: str
    productUrl: str
    image: str | None = None
    price: str | None = None
    platform: str | None = None
    finalDecision: str | None = None
    trustScore: float | None = None
    fakeReviewRisk: float | None = None
    sentimentScore: float | None = None
    pricePerformance: float | None = None


class FavoriteCreate(BaseModel):
    productName: str
    productUrl: str
    image: str | None = None
    price: str | None = None
    platform: str | None = None


def _parse_bearer(authorization: str | None) -> str | None:
    if authorization and authorization.startswith("Bearer "):
        return authorization[7:]
    return None


def current_user(
    authorization: str | None = Header(default=None),
    db: Session = Depends(get_db),
) -> User:
    token = _parse_bearer(authorization)
    if not token:
        raise HTTPException(status_code=401, detail="Bu özellik için giriş yapmalısınız.")

    payload = decode_access_token(token)
    if not payload or not payload.get("sub"):
        raise HTTPException(status_code=401, detail="Bu özellik için giriş yapmalısınız.")

    user = get_user_by_id(db, int(payload["sub"]))
    if not user:
        raise HTTPException(status_code=401, detail="Bu özellik için giriş yapmalısınız.")
    return user


def _iso(value: Any) -> str | None:
    return value.isoformat() if value else None


def _tracking_item(item: PriceTracking) -> dict[str, Any]:
    return {
        "id": item.id,
        "productName": item.product_name,
        "productUrl": item.product_url,
        "currentPrice": item.current_price,
        "targetPrice": item.target_price,
        "image": item.image,
        "platform": item.platform,
        "createdAt": _iso(item.created_at),
    }


def _history_item(item: AnalysisHistory) -> dict[str, Any]:
    return {
        "id": item.id,
        "productName": item.product_name,
        "productUrl": item.product_url,
        "image": item.image,
        "price": item.price,
        "platform": item.platform,
        "finalDecision": item.final_decision,
        "trustScore": item.trust_score,
        "fakeReviewRisk": item.fake_review_risk,
        "sentimentScore": item.sentiment_score,
        "pricePerformance": item.price_performance,
        "createdAt": _iso(item.created_at),
    }


def _favorite_item(item: Favorite) -> dict[str, Any]:
    return {
        "id": item.id,
        "productName": item.product_name,
        "productUrl": item.product_url,
        "image": item.image,
        "price": item.price,
        "platform": item.platform,
        "createdAt": _iso(item.created_at),
    }


@router.post("/price-tracking")
def add_price_tracking(
    body: PriceTrackingCreate,
    user: User = Depends(current_user),
    db: Session = Depends(get_db),
):
    item = PriceTracking(
        user_id=user.id,
        product_name=body.productName.strip(),
        product_url=body.productUrl.strip(),
        current_price=body.currentPrice.strip(),
        target_price=body.targetPrice.strip() if body.targetPrice else None,
        image=body.image,
        platform=body.platform,
    )
    db.add(item)
    db.commit()
    db.refresh(item)
    return {"success": True, "item": _tracking_item(item)}


@router.get("/price-tracking")
def list_price_tracking(user: User = Depends(current_user), db: Session = Depends(get_db)):
    items = (
        db.query(PriceTracking)
        .filter(PriceTracking.user_id == user.id)
        .order_by(PriceTracking.created_at.desc())
        .all()
    )
    return {"success": True, "items": [_tracking_item(item) for item in items]}


@router.delete("/price-tracking/{item_id}")
def delete_price_tracking(item_id: int, user: User = Depends(current_user), db: Session = Depends(get_db)):
    item = db.query(PriceTracking).filter(PriceTracking.id == item_id, PriceTracking.user_id == user.id).first()
    if not item:
        raise HTTPException(status_code=404, detail="Kayıt bulunamadı.")
    db.delete(item)
    db.commit()
    return {"success": True}


@router.post("/analysis-history")
def add_analysis_history(
    body: AnalysisHistoryCreate,
    user: User = Depends(current_user),
    db: Session = Depends(get_db),
):
    item = AnalysisHistory(
        user_id=user.id,
        product_name=body.productName.strip(),
        product_url=body.productUrl.strip(),
        image=body.image,
        price=body.price,
        platform=body.platform,
        final_decision=body.finalDecision,
        trust_score=body.trustScore,
        fake_review_risk=body.fakeReviewRisk,
        sentiment_score=body.sentimentScore,
        price_performance=body.pricePerformance,
    )
    db.add(item)
    db.commit()
    db.refresh(item)
    return {"success": True, "item": _history_item(item)}


@router.get("/analysis-history")
def list_analysis_history(user: User = Depends(current_user), db: Session = Depends(get_db)):
    items = (
        db.query(AnalysisHistory)
        .filter(AnalysisHistory.user_id == user.id)
        .order_by(AnalysisHistory.created_at.desc())
        .all()
    )
    return {"success": True, "items": [_history_item(item) for item in items]}


@router.delete("/analysis-history/{item_id}")
def delete_analysis_history(item_id: int, user: User = Depends(current_user), db: Session = Depends(get_db)):
    item = db.query(AnalysisHistory).filter(AnalysisHistory.id == item_id, AnalysisHistory.user_id == user.id).first()
    if not item:
        raise HTTPException(status_code=404, detail="Kayıt bulunamadı.")
    db.delete(item)
    db.commit()
    return {"success": True}


@router.post("/favorites")
def add_favorite(body: FavoriteCreate, user: User = Depends(current_user), db: Session = Depends(get_db)):
    item = Favorite(
        user_id=user.id,
        product_name=body.productName.strip(),
        product_url=body.productUrl.strip(),
        image=body.image,
        price=body.price,
        platform=body.platform,
    )
    db.add(item)
    db.commit()
    db.refresh(item)
    return {"success": True, "item": _favorite_item(item)}


@router.get("/favorites")
def list_favorites(user: User = Depends(current_user), db: Session = Depends(get_db)):
    items = (
        db.query(Favorite)
        .filter(Favorite.user_id == user.id)
        .order_by(Favorite.created_at.desc())
        .all()
    )
    return {"success": True, "items": [_favorite_item(item) for item in items]}


@router.delete("/favorites/{item_id}")
def delete_favorite(item_id: int, user: User = Depends(current_user), db: Session = Depends(get_db)):
    item = db.query(Favorite).filter(Favorite.id == item_id, Favorite.user_id == user.id).first()
    if not item:
        raise HTTPException(status_code=404, detail="Kayıt bulunamadı.")
    db.delete(item)
    db.commit()
    return {"success": True}


@router.get("/recommendations")
def recommendations(user: User = Depends(current_user), db: Session = Depends(get_db)):
    favorites = db.query(Favorite).filter(Favorite.user_id == user.id).all()
    history = db.query(AnalysisHistory).filter(AnalysisHistory.user_id == user.id).all()
    trackings = db.query(PriceTracking).filter(PriceTracking.user_id == user.id).all()

    if not favorites and not history and not trackings:
        return {
            "success": True,
            "message": "Henüz öneri oluşturmak için yeterli veri yok.",
            "recommendations": [],
        }

    names = [item.product_name for item in favorites + history + trackings if item.product_name]
    platforms = [item.platform for item in favorites + trackings if item.platform]
    common_words = Counter(
        word.lower()
        for name in names
        for word in name.split()
        if len(word) > 3 and not word.isdigit()
    )
    top_terms = [word for word, _ in common_words.most_common(3)]

    recommendations_list = []
    if favorites:
        recommendations_list.append({
            "title": "Favorilerine yakın ürünleri karşılaştır",
            "description": "Favoriye aldığın ürünleri fiyat, yorum güveni ve iade riskiyle tekrar karşılaştırman mantıklı olur.",
            "source": _favorite_item(favorites[-1]),
        })
    if trackings:
        recommendations_list.append({
            "title": "Fiyat alarmındaki ürünleri takip et",
            "description": "Fiyat takibindeki ürünlerde hedef fiyata yaklaşanları önce değerlendir.",
            "source": _tracking_item(trackings[-1]),
        })
    if history:
        phrase = ", ".join(top_terms) if top_terms else "benzer ürünler"
        recommendations_list.append({
            "title": "Son analizlerine göre seçim alanın netleşiyor",
            "description": f"Analiz geçmişinde {phrase} öne çıkıyor. Yeni ürün eklerken aynı kullanım amacına gerçekten uyup uymadığını kontrol et.",
            "source": _history_item(history[-1]),
        })

    if platforms:
        platform, _ = Counter(platforms).most_common(1)[0]
        recommendations_list.append({
            "title": f"{platform} ürünlerinde çapraz kontrol yap",
            "description": "Aynı ürünü farklı satıcılarda fiyat ve iade koşulları açısından karşılaştır.",
            "source": None,
        })

    return {
        "success": True,
        "message": None,
        "recommendations": recommendations_list[:4],
    }
