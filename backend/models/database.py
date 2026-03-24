from sqlalchemy import create_engine, Column, Integer, String, Float, DateTime, ForeignKey, Boolean
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker, relationship
from datetime import datetime
import os

SQLALCHEMY_DATABASE_URL = "sqlite:///./neuro_market.db"

engine = create_engine(
    SQLALCHEMY_DATABASE_URL, connect_args={"check_same_thread": False}
)
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

Base = declarative_base()

class User(Base):
    __tablename__ = "users"

    id = Column(Integer, primary_key=True, index=True)
    username = Column(String, unique=True, index=True)
    email = Column(String, unique=True, index=True)
    hashed_password = Column(String)
    is_admin = Column(Boolean, default=False)
    cash_balance = Column(Float, default=10000.0)
    created_at = Column(DateTime, default=datetime.utcnow)

    trades = relationship("Trade", back_populates="user")
    portfolio = relationship("Portfolio", back_populates="user")
    watchlist = relationship("Watchlist", back_populates="user")
    emotion_logs = relationship("EmotionLog", back_populates="user")
    eeg_signals = relationship("EEGSignal", back_populates="user")

class Watchlist(Base):
    __tablename__ = "watchlist"

    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id"), index=True)
    stock_symbol = Column(String, index=True)
    created_at = Column(DateTime, default=datetime.utcnow)

    user = relationship("User", back_populates="watchlist")

class Trade(Base):
    __tablename__ = "trades"

    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id"))
    stock_symbol = Column(String)
    trade_type = Column(String) # BUY or SELL
    quantity = Column(Float)
    price = Column(Float)
    timestamp = Column(DateTime, default=datetime.utcnow)
    emotional_state = Column(String)

    user = relationship("User", back_populates="trades")

class OptionTrade(Base):
    __tablename__ = "option_trades"

    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id"), index=True)
    underlying_symbol = Column(String, index=True)
    option_type = Column(String)  # CALL or PUT
    strike = Column(Float)
    expiry = Column(String)  # YYYY-MM-DD
    contracts = Column(Integer)
    side = Column(String, default="LONG")  # LONG only for now
    entry_price = Column(Float)
    exit_price = Column(Float, nullable=True)
    status = Column(String, default="OPEN")  # OPEN or CLOSED
    stop_loss = Column(Float, nullable=True)
    take_profit = Column(Float, nullable=True)
    opened_at = Column(DateTime, default=datetime.utcnow)
    closed_at = Column(DateTime, nullable=True)
    emotional_state = Column(String, nullable=True)

    user = relationship("User")

class Portfolio(Base):
    __tablename__ = "portfolio"

    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id"))
    stock_symbol = Column(String)
    quantity = Column(Float)
    avg_price = Column(Float)

    user = relationship("User", back_populates="portfolio")

class EmotionLog(Base):
    __tablename__ = "emotion_logs"

    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id"))
    emotion = Column(String)
    confidence = Column(Float)
    timestamp = Column(DateTime, default=datetime.utcnow)

    user = relationship("User", back_populates="emotion_logs")

class EEGSignal(Base):
    __tablename__ = "eeg_signals"

    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id"))
    alpha = Column(Float)
    beta = Column(Float)
    gamma = Column(Float)
    theta = Column(Float)
    delta = Column(Float)
    timestamp = Column(DateTime, default=datetime.utcnow)

    user = relationship("User", back_populates="eeg_signals")

def init_db():
    Base.metadata.create_all(bind=engine)

    with engine.connect() as conn:
        cols = [row[1] for row in conn.exec_driver_sql("PRAGMA table_info(users)").fetchall()]
        if "is_admin" not in cols:
            conn.exec_driver_sql("ALTER TABLE users ADD COLUMN is_admin BOOLEAN DEFAULT 0")
            conn.exec_driver_sql("UPDATE users SET is_admin = 0 WHERE is_admin IS NULL")
        if "cash_balance" not in cols:
            conn.exec_driver_sql("ALTER TABLE users ADD COLUMN cash_balance FLOAT DEFAULT 10000.0")
            conn.exec_driver_sql("UPDATE users SET cash_balance = 10000.0 WHERE cash_balance IS NULL")
        conn.commit()

    admin_username = os.getenv("ADMIN_USERNAME")
    admin_email = os.getenv("ADMIN_EMAIL")
    admin_password = os.getenv("ADMIN_PASSWORD")
    admin_balance = float(os.getenv("ADMIN_BALANCE", "1000000"))

    if admin_username and admin_email and admin_password:
        from passlib.context import CryptContext
        pwd_context = CryptContext(schemes=["pbkdf2_sha256"], deprecated="auto")
        db = SessionLocal()
        try:
            existing = db.query(User).filter(User.username == admin_username).first()
            if not existing:
                admin_user = User(
                    username=admin_username,
                    email=admin_email,
                    hashed_password=pwd_context.hash(admin_password),
                    is_admin=True,
                    cash_balance=admin_balance,
                )
                db.add(admin_user)
                db.commit()
        finally:
            db.close()
