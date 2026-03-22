from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from models import database, schemas
from services import auth
from typing import List, Optional, Dict, Any

router = APIRouter(prefix="/admin", tags=["admin"])

def require_admin(current_user: database.User = Depends(auth.get_current_user)) -> database.User:
    if not getattr(current_user, "is_admin", False):
        raise HTTPException(status_code=403, detail="Admin access required")
    return current_user

@router.get("/users", response_model=List[schemas.AdminUser])
def list_users(
    q: Optional[str] = None,
    _: database.User = Depends(require_admin),
    db: Session = Depends(auth.get_db),
):
    query = db.query(database.User)
    if q:
        query = query.filter(database.User.username.contains(q))
    return query.order_by(database.User.created_at.desc()).limit(200).all()

@router.post("/balance/set", response_model=schemas.AdminUser)
def set_balance(
    payload: schemas.AdminBalanceUpdate,
    _: database.User = Depends(require_admin),
    db: Session = Depends(auth.get_db),
):
    user = db.query(database.User).filter(database.User.username == payload.username).first()
    if not user:
        raise HTTPException(status_code=404, detail="User not found")
    user.cash_balance = float(payload.amount)
    db.commit()
    db.refresh(user)
    return user

@router.post("/balance/topup", response_model=schemas.AdminUser)
def top_up(
    payload: schemas.AdminTopUp,
    _: database.User = Depends(require_admin),
    db: Session = Depends(auth.get_db),
):
    user = db.query(database.User).filter(database.User.username == payload.username).first()
    if not user:
        raise HTTPException(status_code=404, detail="User not found")
    user.cash_balance = float(user.cash_balance or 0.0) + float(payload.amount)
    db.commit()
    db.refresh(user)
    return user

def _get_user_or_404(db: Session, username: str) -> database.User:
    user = db.query(database.User).filter(database.User.username == username).first()
    if not user:
        raise HTTPException(status_code=404, detail="User not found")
    return user

@router.get("/user/{username}/portfolio", response_model=List[schemas.Portfolio])
def admin_user_portfolio(
    username: str,
    _: database.User = Depends(require_admin),
    db: Session = Depends(auth.get_db),
):
    user = _get_user_or_404(db, username)
    return db.query(database.Portfolio).filter(database.Portfolio.user_id == user.id).all()

@router.get("/user/{username}/trades", response_model=List[schemas.Trade])
def admin_user_trades(
    username: str,
    _: database.User = Depends(require_admin),
    db: Session = Depends(auth.get_db),
):
    user = _get_user_or_404(db, username)
    return (
        db.query(database.Trade)
        .filter(database.Trade.user_id == user.id)
        .order_by(database.Trade.timestamp.desc())
        .limit(300)
        .all()
    )

@router.get("/user/{username}/options", response_model=List[schemas.OptionTrade])
def admin_user_options(
    username: str,
    _: database.User = Depends(require_admin),
    db: Session = Depends(auth.get_db),
):
    user = _get_user_or_404(db, username)
    return (
        db.query(database.OptionTrade)
        .filter(database.OptionTrade.user_id == user.id)
        .order_by(database.OptionTrade.opened_at.desc())
        .limit(300)
        .all()
    )

@router.get("/user/{username}/emotions", response_model=List[schemas.EmotionLog])
def admin_user_emotion_logs(
    username: str,
    _: database.User = Depends(require_admin),
    db: Session = Depends(auth.get_db),
):
    user = _get_user_or_404(db, username)
    return (
        db.query(database.EmotionLog)
        .filter(database.EmotionLog.user_id == user.id)
        .order_by(database.EmotionLog.timestamp.desc())
        .limit(200)
        .all()
    )
