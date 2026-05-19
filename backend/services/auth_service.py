import os
import secrets
from datetime import datetime, timedelta

import bcrypt
from jose import JWTError, jwt
from sqlalchemy.orm import Session

from .database import EmailVerificationToken, PasswordResetToken, User

JWT_SECRET = os.getenv("JWT_SECRET", "filtre-lab-dev-secret-change-in-production")
JWT_ALGORITHM = "HS256"
ACCESS_TOKEN_EXPIRE_MINUTES = 60 * 24 * 7  # 7 days


# ── Password helpers ─────────────────────────────────────────────────────────

def hash_password(plain: str) -> str:
    return bcrypt.hashpw(plain.encode(), bcrypt.gensalt()).decode()


def verify_password(plain: str, hashed: str) -> bool:
    try:
        return bcrypt.checkpw(plain.encode(), hashed.encode())
    except Exception:
        return False


# ── JWT helpers ──────────────────────────────────────────────────────────────

def _token_version(user: User) -> int:
    return user.token_version if user.token_version is not None else 1


def create_access_token(user_id: int, email: str, token_version: int = 1) -> str:
    payload = {
        "sub": str(user_id),
        "email": email,
        "tvs": token_version,
        "exp": datetime.utcnow() + timedelta(minutes=ACCESS_TOKEN_EXPIRE_MINUTES),
    }
    return jwt.encode(payload, JWT_SECRET, algorithm=JWT_ALGORITHM)


def decode_access_token(token: str) -> dict | None:
    try:
        return jwt.decode(token, JWT_SECRET, algorithms=[JWT_ALGORITHM])
    except JWTError:
        return None


def validate_token_version(user: User, payload: dict) -> bool:
    """False means the token was issued before a password reset — reject it."""
    return _token_version(user) == (payload.get("tvs") or 1)


# ── User operations ──────────────────────────────────────────────────────────

def get_user_by_email(db: Session, email: str) -> User | None:
    return db.query(User).filter(User.email == email.lower().strip()).first()


def get_user_by_id(db: Session, user_id: int) -> User | None:
    return db.query(User).filter(User.id == user_id).first()


def create_user(
    db: Session,
    email: str,
    password: str,
    first_name: str = "",
    last_name: str = "",
    name: str | None = None,
) -> User:
    display_name = (name or f"{first_name.strip()} {last_name.strip()}").strip()
    user = User(
        name=display_name,
        first_name=first_name.strip() or None,
        last_name=last_name.strip() or None,
        email=email.lower().strip(),
        password_hash=hash_password(password),
        is_verified=False,
        token_version=1,
    )
    db.add(user)
    db.commit()
    db.refresh(user)
    return user


# ── Email verification ───────────────────────────────────────────────────────

def create_email_verification_token(db: Session, user_id: int) -> str:
    # Invalidate old tokens
    db.query(EmailVerificationToken).filter(
        EmailVerificationToken.user_id == user_id,
        EmailVerificationToken.used == False,  # noqa: E712
    ).delete()
    db.commit()

    token = secrets.token_urlsafe(32)
    record = EmailVerificationToken(
        user_id=user_id,
        token=token,
        expires_at=datetime.utcnow() + timedelta(hours=24),
    )
    db.add(record)
    db.commit()
    return token


def verify_email_token(db: Session, token: str) -> User | None:
    record = db.query(EmailVerificationToken).filter(
        EmailVerificationToken.token == token,
        EmailVerificationToken.used == False,  # noqa: E712
    ).first()
    if not record:
        return None
    if datetime.utcnow() > record.expires_at:
        return None
    user = get_user_by_id(db, record.user_id)
    if not user:
        return None
    user.is_verified = True
    record.used = True
    db.commit()
    return user


# ── Password reset ───────────────────────────────────────────────────────────

def create_password_reset_token(db: Session, user_id: int) -> str:
    # Invalidate old tokens
    db.query(PasswordResetToken).filter(
        PasswordResetToken.user_id == user_id,
        PasswordResetToken.used == False,  # noqa: E712
    ).delete()
    db.commit()

    token = secrets.token_urlsafe(32)
    record = PasswordResetToken(
        user_id=user_id,
        token=token,
        expires_at=datetime.utcnow() + timedelta(minutes=30),
    )
    db.add(record)
    db.commit()
    return token


def reset_password_with_token(db: Session, token: str, new_password: str) -> bool:
    record = db.query(PasswordResetToken).filter(
        PasswordResetToken.token == token,
        PasswordResetToken.used == False,  # noqa: E712
    ).first()
    if not record:
        return False
    if datetime.utcnow() > record.expires_at:
        return False
    user = get_user_by_id(db, record.user_id)
    if not user:
        return False
    user.password_hash = hash_password(new_password)
    # Invalidate all existing JWT tokens by bumping token_version
    user.token_version = _token_version(user) + 1
    record.used = True
    db.commit()
    return True
