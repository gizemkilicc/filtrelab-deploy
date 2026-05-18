import os
from datetime import datetime

from sqlalchemy import JSON, Boolean, Column, DateTime, Float, ForeignKey, Integer, String, Text, create_engine
from sqlalchemy.dialects.postgresql import JSONB
from sqlalchemy.orm import declarative_base, sessionmaker

DATABASE_URL = os.getenv("DATABASE_URL")

if not DATABASE_URL:
    raise RuntimeError(
        "DATABASE_URL env değişkeni eksik. "
        "backend/.env dosyasına DATABASE_URL=postgresql://user:pass@localhost:5432/filterlab ekleyin."
    )

# SQLite needs check_same_thread=False to work with FastAPI's threaded requests
_connect_args = {"check_same_thread": False} if DATABASE_URL.startswith("sqlite") else {}
engine = create_engine(DATABASE_URL, pool_pre_ping=True, connect_args=_connect_args)
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)
Base = declarative_base()


class User(Base):
    __tablename__ = "users"

    id = Column(Integer, primary_key=True, index=True)
    name = Column(String, nullable=False)
    first_name = Column(String, nullable=True)
    last_name = Column(String, nullable=True)
    email = Column(String, unique=True, index=True, nullable=False)
    password_hash = Column(String, nullable=False)
    is_verified = Column(Boolean, default=False)
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)


class PasswordResetToken(Base):
    __tablename__ = "password_reset_tokens"

    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id", ondelete="CASCADE"), nullable=False)
    token = Column(String, unique=True, index=True, nullable=False)
    expires_at = Column(DateTime, nullable=False)
    used = Column(Boolean, default=False)
    created_at = Column(DateTime, default=datetime.utcnow)


class EmailVerificationToken(Base):
    __tablename__ = "email_verification_tokens"

    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id", ondelete="CASCADE"), nullable=False)
    token = Column(String, unique=True, index=True, nullable=False)
    expires_at = Column(DateTime, nullable=False)
    used = Column(Boolean, default=False)
    created_at = Column(DateTime, default=datetime.utcnow)


class PriceTracking(Base):
    __tablename__ = "price_trackings"

    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id", ondelete="CASCADE"), nullable=False, index=True)
    product_name = Column(String, nullable=False)
    product_url = Column(Text, nullable=False)
    current_price = Column(String, nullable=False)
    target_price = Column(String, nullable=True)
    image = Column(Text, nullable=True)
    platform = Column(String, nullable=True)
    created_at = Column(DateTime, default=datetime.utcnow)


class AnalysisHistory(Base):
    __tablename__ = "analysis_history"

    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id", ondelete="CASCADE"), nullable=False, index=True)
    product_name = Column(String, nullable=False)
    product_url = Column(Text, nullable=False)
    image = Column(Text, nullable=True)
    price = Column(String, nullable=True)
    platform = Column(String, nullable=True)
    final_decision = Column(String, nullable=True)
    trust_score = Column(Float, nullable=True)
    fake_review_risk = Column(Float, nullable=True)
    sentiment_score = Column(Float, nullable=True)
    price_performance = Column(Float, nullable=True)
    # JSONB on PostgreSQL, generic JSON on SQLite/others — no production regression
    raw_result = Column(JSON().with_variant(JSONB(), "postgresql"), nullable=True)
    created_at = Column(DateTime, default=datetime.utcnow)


class Favorite(Base):
    __tablename__ = "favorites"

    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id", ondelete="CASCADE"), nullable=False, index=True)
    product_name = Column(String, nullable=False)
    product_url = Column(Text, nullable=False)
    image = Column(Text, nullable=True)
    price = Column(String, nullable=True)
    platform = Column(String, nullable=True)
    created_at = Column(DateTime, default=datetime.utcnow)


def init_db():
    Base.metadata.create_all(bind=engine)


def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()
