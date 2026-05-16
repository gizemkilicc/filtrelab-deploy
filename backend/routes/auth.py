import re

from fastapi import APIRouter, Depends, Header, HTTPException
from pydantic import BaseModel
from sqlalchemy.orm import Session

from services.auth_service import (
    create_access_token,
    create_email_verification_token,
    create_password_reset_token,
    create_user,
    decode_access_token,
    get_user_by_email,
    get_user_by_id,
    reset_password_with_token,
    verify_email_token,
    verify_password,
)
from services.database import get_db
from services.email_service import send_password_reset_email, send_verification_email

router = APIRouter(prefix="/auth", tags=["auth"])

_EMAIL_RE = re.compile(r"^[a-zA-Z0-9._%+\-]+@[a-zA-Z0-9.\-]+\.[a-zA-Z]{2,}$")


# ── Request models ────────────────────────────────────────────────────────────

class RegisterRequest(BaseModel):
    email: str
    password: str
    name: str


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


# ── Helper ────────────────────────────────────────────────────────────────────

def _parse_bearer(authorization: str | None) -> str | None:
    if authorization and authorization.startswith("Bearer "):
        return authorization[7:]
    return None


# ── Endpoints ─────────────────────────────────────────────────────────────────

@router.post("/register")
def register(body: RegisterRequest, db: Session = Depends(get_db)):
    email = body.email.strip().lower()
    name = body.name.strip()
    password = body.password

    if not _EMAIL_RE.match(email):
        raise HTTPException(status_code=400, detail="Geçersiz e-posta formatı.")
    if len(password) < 6:
        raise HTTPException(status_code=400, detail="Şifre en az 6 karakter olmalıdır.")
    if not name:
        raise HTTPException(status_code=400, detail="Ad Soyad boş olamaz.")
    if get_user_by_email(db, email):
        raise HTTPException(status_code=409, detail="Bu e-posta adresi zaten kayıtlı.")

    user = create_user(db, name=name, email=email, password=password)
    token = create_email_verification_token(db, user.id)
    send_verification_email(email, token)

    return {
        "success": True,
        "message": "Kayıt başarılı. Lütfen e-posta adresinizi doğrulayın.",
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
        "user": {
            "id": user.id,
            "name": user.name,
            "email": user.email,
            "isVerified": user.is_verified,
        },
        "emailVerified": user.is_verified,
        "message": None if user.is_verified else "E-posta adresinizi henüz doğrulamadınız.",
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
    email = body.email.strip().lower()
    user = get_user_by_email(db, email)
    if user and not user.is_verified:
        token = create_email_verification_token(db, user.id)
        send_verification_email(email, token)
    return {"success": True, "message": "Doğrulama e-postası gönderildi."}


@router.get("/verify-email")
def verify_email(token: str, db: Session = Depends(get_db)):
    user = verify_email_token(db, token)
    if not user:
        raise HTTPException(
            status_code=400,
            detail="Geçersiz veya süresi dolmuş doğrulama bağlantısı.",
        )
    return {"success": True, "message": "E-posta adresiniz doğrulandı. Giriş yapabilirsiniz."}


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

    return {
        "id": user.id,
        "name": user.name,
        "email": user.email,
        "isVerified": user.is_verified,
        "createdAt": user.created_at.isoformat(),
    }
