from pydantic import BaseModel, EmailStr
from typing import List, Optional, Dict
from datetime import datetime

class UserBase(BaseModel):
    username: str
    email: EmailStr

class UserCreate(UserBase):
    password: str
    password_confirmation: str

class UserLogin(BaseModel):
    username: str
    password: str

class User(UserBase):
    id: int
    is_admin: bool = False
    cash_balance: float = 0.0
    created_at: datetime

    class Config:
        from_attributes = True

class Token(BaseModel):
    access_token: str
    token_type: str

class TokenData(BaseModel):
    username: Optional[str] = None

class TradeBase(BaseModel):
    stock_symbol: str
    trade_type: str
    quantity: float
    price: float
    emotional_state: Optional[str] = None

class TradeCreate(TradeBase):
    confirmed: Optional[bool] = False

class Trade(TradeBase):
    id: int
    user_id: int
    timestamp: datetime

    class Config:
        from_attributes = True

class PortfolioBase(BaseModel):
    stock_symbol: str
    quantity: float
    avg_price: float

class Portfolio(PortfolioBase):
    id: int
    user_id: int

    class Config:
        from_attributes = True

class EmotionLogBase(BaseModel):
    emotion: str
    confidence: float

class EmotionLog(EmotionLogBase):
    id: int
    user_id: int
    timestamp: datetime

    class Config:
        from_attributes = True

class EEGSignalBase(BaseModel):
    alpha: float
    beta: float
    gamma: float
    theta: float
    delta: float

class EEGSignal(EEGSignalBase):
    id: int
    user_id: int
    timestamp: datetime

    class Config:
        from_attributes = True

class StockInfo(BaseModel):
    symbol: str
    price: float
    change: float
    change_percent: float
    company_name: str

class AdminBalanceUpdate(BaseModel):
    username: str
    amount: float

class AdminTopUp(BaseModel):
    username: str
    amount: float

class AdminUser(BaseModel):
    id: int
    username: str
    email: EmailStr
    is_admin: bool
    cash_balance: float
    created_at: datetime

    class Config:
        from_attributes = True

class OptionTradeCreate(BaseModel):
    underlying_symbol: str
    option_type: str
    strike: float
    expiry: str
    contracts: int
    stop_loss: Optional[float] = None
    take_profit: Optional[float] = None
    emotional_state: Optional[str] = None

class OptionTrade(BaseModel):
    id: int
    user_id: int
    underlying_symbol: str
    option_type: str
    strike: float
    expiry: str
    contracts: int
    side: str
    entry_price: float
    exit_price: Optional[float] = None
    status: str
    stop_loss: Optional[float] = None
    take_profit: Optional[float] = None
    opened_at: datetime
    closed_at: Optional[datetime] = None
    emotional_state: Optional[str] = None

    class Config:
        from_attributes = True

class OptionPositionSnapshot(BaseModel):
    id: int
    underlying_symbol: str
    option_type: str
    strike: float
    expiry: str
    contracts: int
    entry_price: float
    mark_price: float
    pnl: float
    pnl_percent: float
    stop_loss: Optional[float] = None
    take_profit: Optional[float] = None

class PracticeRecommendation(BaseModel):
    symbol: str
    action: str
    confidence: float
    rationale: List[str]
    indicators: Dict[str, float]
    user_stats: Dict[str, float]

class PracticeEmotion(BaseModel):
    state: str
    confidence: float = 0.0

class PracticeRecommendationRequest(BaseModel):
    symbol: str
    current_price: Optional[float] = None
    practice_stats: Optional[Dict[str, float]] = None
    emotion: Optional[PracticeEmotion] = None
