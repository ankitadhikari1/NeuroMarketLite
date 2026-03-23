from fastapi import APIRouter, Depends, HTTPException, status, WebSocket, WebSocketDisconnect
from sqlalchemy.orm import Session
from models import database, schemas
from services import auth, stock_service
from risk_engine import risk_control_engine
from typing import List, Dict, Any
import asyncio
import json
import random

router = APIRouter(prefix="/trading", tags=["trading"])
risk_engine = risk_control_engine.RiskControlEngine()

@router.get("/stocks/popular", response_model=List[schemas.StockInfo])
def get_popular_stocks():
    return stock_service.StockService.get_popular_stocks()

@router.get("/stocks/{symbol}", response_model=schemas.StockInfo)
def get_stock_info(symbol: str):
    info = stock_service.StockService.get_stock_price(symbol)
    if not info:
        raise HTTPException(status_code=404, detail=f"Stock {symbol} not found")
    return info

@router.get("/stocks/{symbol}/history")
def get_stock_history(symbol: str, period: str = "1mo"):
    return stock_service.StockService.get_historical_data(symbol, period)

@router.get("/stocks/{symbol}/candles")
def get_stock_candles(symbol: str, interval: str = "1m", period: str = "1d"):
    return stock_service.StockService.get_candles(symbol, interval=interval, period=period)

@router.websocket("/ws/price")
async def price_websocket(websocket: WebSocket, token: str, symbols: str = "AAPL", simulate: bool = True):
    await websocket.accept()
    try:
        from jose import jwt
        import os
        SECRET_KEY = os.getenv("SECRET_KEY", "your-secret-key-for-development-only")
        ALGORITHM = "HS256"
        payload = jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])
        username = payload.get("sub")
        if not username:
            await websocket.close(code=1008)
            return
    except Exception:
        await websocket.close(code=1008)
        return

    requested = [s.strip().upper() for s in symbols.split(",") if s.strip()]
    last_prices: Dict[str, float] = {}
    try:
        while True:
            data = []
            for sym in requested:
                info = stock_service.StockService.get_stock_price(sym, max_age_s=1.5)
                if info:
                    payload = info.model_dump() if hasattr(info, "model_dump") else info.dict()
                    if simulate:
                        current = float(payload.get("price", 0.0) or 0.0)
                        prev = last_prices.get(sym)
                        if prev is not None and abs(current - prev) < 1e-9:
                            drift = (random.random() - 0.5) * max(0.01, prev * 0.0005)
                            current = max(0.01, prev + drift)
                            payload["price"] = current
                        last_prices[sym] = float(payload.get("price", 0.0) or 0.0)
                    data.append(payload)
            await websocket.send_text(json.dumps({"type": "prices", "data": data}))
            await asyncio.sleep(1.0)
    except WebSocketDisconnect:
        return

@router.post("/trade", response_model=schemas.Trade)
def create_trade(
    trade_in: schemas.TradeCreate,
    current_user: database.User = Depends(auth.get_current_user),
    db: Session = Depends(auth.get_db)
):
    # Check emotional state for risk management if provided
    if trade_in.emotional_state:
        # Split "state (confidence)" format
        parts = trade_in.emotional_state.split(" (")
        emotion = parts[0].lower().strip()
        if emotion == "anxiet":
            emotion = "anxiety"
        if emotion == "greeed":
            emotion = "greed"
        confidence = 0.8
        if len(parts) > 1:
            try:
                confidence = float(parts[1].replace("%)", "")) / 100
            except:
                pass

        # Get recent trades for behavior rules
        recent_trades = db.query(database.Trade).filter(
            database.Trade.user_id == current_user.id
        ).order_by(database.Trade.timestamp.desc()).limit(20).all()

        trade_amount = float(trade_in.quantity) * float(trade_in.price)
        
        permission = risk_engine.check_trade_permission(
            current_user.id, 
            emotion, 
            confidence, 
            trade_amount=trade_amount,
            recent_trades=recent_trades,
            confirmed=bool(trade_in.confirmed)
        )
        
        if not permission["allowed"]:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail={
                    "message": permission["message"],
                    "action": permission["action"],
                    "cooldown_remaining": permission.get("cooldown_remaining", 0),
                    "max_trade_amount": permission.get("max_trade_amount")
                }
            )

    # Handle Portfolio update
    portfolio_item = db.query(database.Portfolio).filter(
        database.Portfolio.user_id == current_user.id,
        database.Portfolio.stock_symbol == trade_in.stock_symbol
    ).first()

    if trade_in.trade_type == "BUY":
        total_cost = float(trade_in.quantity) * float(trade_in.price)
        if (current_user.cash_balance or 0.0) < total_cost:
            raise HTTPException(status_code=400, detail="Insufficient cash balance")
        current_user.cash_balance = float(current_user.cash_balance or 0.0) - total_cost
        if portfolio_item:
            # Update existing holding
            total_cost = (portfolio_item.quantity * portfolio_item.avg_price) + (trade_in.quantity * trade_in.price)
            new_quantity = portfolio_item.quantity + trade_in.quantity
            portfolio_item.avg_price = total_cost / new_quantity
            portfolio_item.quantity = new_quantity
        else:
            # Create new holding
            new_item = database.Portfolio(
                user_id=current_user.id,
                stock_symbol=trade_in.stock_symbol,
                quantity=trade_in.quantity,
                avg_price=trade_in.price
            )
            db.add(new_item)
    elif trade_in.trade_type == "SELL":
        if not portfolio_item or portfolio_item.quantity < trade_in.quantity:
            raise HTTPException(status_code=400, detail="Insufficient quantity to sell")
        
        proceeds = float(trade_in.quantity) * float(trade_in.price)
        current_user.cash_balance = float(current_user.cash_balance or 0.0) + proceeds
        portfolio_item.quantity -= trade_in.quantity
        if portfolio_item.quantity == 0:
            db.delete(portfolio_item)
    
    # Record trade
    new_trade = database.Trade(
        user_id=current_user.id,
        stock_symbol=trade_in.stock_symbol,
        trade_type=trade_in.trade_type,
        quantity=trade_in.quantity,
        price=trade_in.price,
        emotional_state=trade_in.emotional_state
    )
    db.add(new_trade)
    db.commit()
    db.refresh(new_trade)
    return new_trade

@router.get("/portfolio", response_model=List[schemas.Portfolio])
def get_portfolio(
    current_user: database.User = Depends(auth.get_current_user),
    db: Session = Depends(auth.get_db)
):
    return db.query(database.Portfolio).filter(database.Portfolio.user_id == current_user.id).all()

@router.get("/watchlist", response_model=List[str])
def get_watchlist(
    current_user: database.User = Depends(auth.get_current_user),
    db: Session = Depends(auth.get_db)
):
    items = db.query(database.Watchlist).filter(database.Watchlist.user_id == current_user.id).all()
    return [item.stock_symbol for item in items]

@router.post("/watchlist", response_model=Dict[str, str])
def add_to_watchlist(
    payload: Dict[str, str],
    current_user: database.User = Depends(auth.get_current_user),
    db: Session = Depends(auth.get_db)
):
    
    symbol = payload.get("symbol", "").upper()
    if not symbol:
        raise HTTPException(status_code=400, detail="Symbol is required")
    
    existing = db.query(database.Watchlist).filter(
        database.Watchlist.user_id == current_user.id,
        database.Watchlist.stock_symbol == symbol
    ).first()
    
    if existing:
        return {"message": "Already in watchlist"}
        
    new_item = database.Watchlist(user_id=current_user.id, stock_symbol=symbol)
    db.add(new_item)
    db.commit()
    return {"message": f"Added {symbol} to watchlist"}

@router.delete("/watchlist/{symbol}", response_model=Dict[str, str])
def remove_from_watchlist(
    symbol: str,
    current_user: database.User = Depends(auth.get_current_user),
    db: Session = Depends(auth.get_db)
):
    symbol = symbol.upper()
    item = db.query(database.Watchlist).filter(
        database.Watchlist.user_id == current_user.id,
        database.Watchlist.stock_symbol == symbol
    ).first()
    
    if not item:
        raise HTTPException(status_code=404, detail="Not in watchlist")
        
    db.delete(item)
    db.commit()
    return {"message": f"Removed {symbol} from watchlist"}

@router.get("/history", response_model=List[schemas.Trade])
def get_trade_history(
    current_user: database.User = Depends(auth.get_current_user),
    db: Session = Depends(auth.get_db)
):
    return db.query(database.Trade).filter(database.Trade.user_id == current_user.id).order_by(database.Trade.timestamp.desc()).all()
