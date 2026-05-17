import re

from fastapi import APIRouter, Depends, Header, HTTPException
from pydantic import BaseModel
from sqlalchemy.orm import Session

from services.auth_service import (
    create_access_token,
    create_password_reset_token,
    create_user,
    decode_access_token,
    get_user_by_email,
    get_user_by_id,
    reset_password_with_token,
    verify_password,
)
from services.database import AnalysisHistory, get_db
from services.email_service import send_password_reset_email

router = APIRouter(prefix="/auth", tags=["auth"])

_EMAIL_RE = re.compile(r"^[a-zA-Z0-9._%+\-]+@[a-zA-Z0-9.\-]+\.[a-zA-Z]{2,}$")


# ── Request models ────────────────────────────────────────────────────────────

class RegisterRequest(BaseModel):
    email: str
    password: str
    firstName: str | None = None
    lastName: str | None = None
    name: str | None = None


class LoginRequest(BaseModel):
    email: str
    password: str


class ForgotPasswordRequest(BaseModel):
    email: str


class ResetPasswordRequest(BaseModel):
    token: str
    newPassword: str


class SendVerificationRequest(BaseModel):
    email: str


def _user_payload(user, db: Session | None = None) -> dict:
    first_name = (user.first_name or "").strip()
    last_name = (user.last_name or "").strip()
    if not first_name and not last_name and user.name:
        parts = user.name.strip().split(" ", 1)
        first_name = parts[0] if parts else ""
        last_name = parts[1] if len(parts) > 1 else ""
    payload = {
        "id": user.id,
        "firstName": first_name,
        "lastName": last_name,
        "name": user.name or f"{first_name} {last_name}".strip(),
        "email": user.email,
        "createdAt": user.created_at.isoformat() if user.created_at else None,
    }
    if db:
        payload["analysisCount"] = db.query(AnalysisHistory).filter(AnalysisHistory.user_id == user.id).count()
    return payload


# ── Helper ────────────────────────────────────────────────────────────────────

def _parse_bearer(authorization: str | None) -> str | None:
    if authorization and authorization.startswith("Bearer "):
        return authorization[7:]
    return None


# ── Endpoints ─────────────────────────────────────────────────────────────────

@router.post("/register")
def register(body: RegisterRequest, db: Session = Depends(get_db)):
    email = body.email.strip().lower()
    first_name = (body.firstName or "").strip()
    last_name = (body.lastName or "").strip()
    if (not first_name or not last_name) and body.name:
        parts = body.name.strip().split(" ", 1)
        first_name = first_name or (parts[0] if parts else "")
        last_name = last_name or (parts[1] if len(parts) > 1 else "")
    password = body.password

    if not _EMAIL_RE.match(email):
        raise HTTPException(status_code=400, detail="Geçersiz e-posta formatı.")
    if len(password) < 6:
        raise HTTPException(status_code=400, detail="Şifre en az 6 karakter olmalıdır.")
    if not first_name:
        raise HTTPException(status_code=400, detail="Ad boş olamaz.")
    if not last_name:
        raise HTTPException(status_code=400, detail="Soyad boş olamaz.")
    if get_user_by_email(db, email):
        raise HTTPException(status_code=409, detail="Bu e-posta adresi zaten kayıtlı.")

    user = create_user(db, first_name=first_name, last_name=last_name, email=email, password=password)

    return {
        "success": True,
        "message": "Kayıt başarılı. Giriş yapabilirsiniz.",
        "userId": user.id,
    }


@router.post("/login")
def login(body: LoginRequest, db: Session = Depends(get_db)):
    email = body.email.strip().lower()
    user = get_user_by_email(db, email)

    if not user or not verify_password(body.password, user.password_hash):
        raise HTTPException(status_code=401, detail="E-posta veya şifre hatalı.")

    access_token = create_access_token(user.id, user.email)

    return {
        "success": True,
        "accessToken": access_token,
        "user": _user_payload(user),
    }


@router.post("/forgot-password")
def forgot_password(body: ForgotPasswordRequest, db: Session = Depends(get_db)):
    email = body.email.strip().lower()
    user = get_user_by_email(db, email)

    # Always return success to prevent email enumeration
    if user:
        token = create_password_reset_token(db, user.id)
        send_password_reset_email(email, token)

    return {
        "success": True,
        "message": "Şifre sıfırlama bağlantısı e-posta adresinize gönderildi.",
    }


@router.post("/reset-password")
def reset_password(body: ResetPasswordRequest, db: Session = Depends(get_db)):
    if len(body.newPassword) < 6:
        raise HTTPException(status_code=400, detail="Şifre en az 6 karakter olmalıdır.")

    ok = reset_password_with_token(db, body.token, body.newPassword)
    if not ok:
        raise HTTPException(
            status_code=400,
            detail="Geçersiz veya süresi dolmuş sıfırlama bağlantısı.",
        )
    return {"success": True, "message": "Şifreniz başarıyla güncellendi."}


@router.post("/send-verification-email")
def resend_verification(body: SendVerificationRequest, db: Session = Depends(get_db)):
    return {"success": True, "message": "E-posta doğrulama bu sürümde gerekli değildir."}


@router.get("/verify-email")
def verify_email(token: str, db: Session = Depends(get_db)):
    return {"success": True, "message": "E-posta doğrulama bu sürümde gerekli değildir. Giriş yapabilirsiniz."}


@router.get("/me")
def get_me(
    authorization: str | None = Header(default=None),
    db: Session = Depends(get_db),
):
    token = _parse_bearer(authorization)
    if not token:
        raise HTTPException(status_code=401, detail="Oturum açmanız gerekiyor.")

    payload = decode_access_token(token)
    if not payload:
        raise HTTPException(status_code=401, detail="Geçersiz veya süresi dolmuş oturum.")

    user = get_user_by_id(db, int(payload["sub"]))
    if not user:
        raise HTTPException(status_code=404, detail="Kullanıcı bulunamadı.")

    return _user_payload(user, db)
