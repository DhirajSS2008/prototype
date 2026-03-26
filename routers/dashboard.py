"""Dashboard data API endpoint."""

import logging
<<<<<<< HEAD
from datetime import datetime, timedelta
=======
from datetime import datetime
>>>>>>> 8a260015108003b30586cdffc9a5d14ec1407d73
from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session

from database import get_db
from models.user import User
from models.transaction import Transaction
from models.cash_balance import CashBalanceSnapshot
from models.affordability_check import AffordabilityCheck
from services.profiler_service import run_full_profile
from services.forecast_service import forecast_liquidity, get_current_balance
from services.auth_service import get_current_user
from schemas.expense import CATEGORIES
from redis_client import cache_get, cache_set

logger = logging.getLogger(__name__)
router = APIRouter(prefix="/api/dashboard", tags=["dashboard"])


@router.get("")
def get_dashboard_data(
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    """Get all data needed for the main dashboard."""
    uid = current_user.id

    # Current balance
    current_balance = get_current_balance(db, uid)

    # Expense profile (cached per user)
    cache_key = f"expense_profile:{uid}"
    profile = cache_get(cache_key)
    if not profile:
        profile = run_full_profile(db, uid)
        cache_set(cache_key, profile, ttl=600)

    # Latest affordability check
    latest_check = (
        db.query(AffordabilityCheck)
        .filter(AffordabilityCheck.user_id == uid)
        .order_by(AffordabilityCheck.created_at.desc())
        .first()
    )

    # Recent checks count
    total_checks = db.query(AffordabilityCheck).filter(AffordabilityCheck.user_id == uid).count()

    # Transaction stats
    total_transactions = db.query(Transaction).filter(Transaction.user_id == uid).count()
    needs_review_count = (
        db.query(Transaction)
        .filter(Transaction.user_id == uid, Transaction.needs_review == True)
        .count()
    )

    return {
        "current_balance": round(current_balance, 2),
        "monthly_burn_rate": profile.get("monthly_burn_rate", 0),
        "category_breakdown": profile.get("category_averages", {}),
        "recurring_info": profile.get("recurring_classification", {}),
        "total_transactions": total_transactions,
        "needs_review_count": needs_review_count,
        "latest_check": latest_check.to_dict() if latest_check else None,
        "total_checks": total_checks,
        "date_range": profile.get("date_range"),
    }


@router.get("/forecast")
def get_forecast(
    days: int = 30,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    """Get cash flow forecast data for charts."""
    forecast_points, current_balance = forecast_liquidity(db, current_user.id, forecast_days=days)

    return {
        "current_balance": round(current_balance, 2),
        "forecast": [fp.model_dump() for fp in forecast_points],
    }


@router.get("/categories")
def get_categories():
    """Get available expense categories."""
    return {"categories": CATEGORIES}


@router.post("/balance")
def set_balance(
    balance: float,
    date: str = None,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    """Set or update the current cash balance."""
    snapshot = CashBalanceSnapshot(
        user_id=current_user.id,
        date=datetime.fromisoformat(date) if date else datetime.now(),
        balance=balance,
    )
    db.add(snapshot)
    db.commit()

    return {"message": "Balance updated", "balance": balance}
<<<<<<< HEAD


@router.get("/credit-debit-history")
def get_credit_debit_history(
    days: int = 30,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    """Get daily credit and debit totals for the past N days."""
    from sqlalchemy import func, cast, Date

    cutoff = datetime.now() - timedelta(days=days)
    uid = current_user.id

    # Query transactions grouped by date
    rows = (
        db.query(
            cast(Transaction.date, Date).label("day"),
            func.sum(
                func.IF(Transaction.amount > 0, Transaction.amount, 0)
            ).label("credit"),
            func.sum(
                func.IF(Transaction.amount < 0, func.abs(Transaction.amount), 0)
            ).label("debit"),
        )
        .filter(Transaction.user_id == uid, Transaction.date >= cutoff)
        .group_by("day")
        .order_by("day")
        .all()
    )

    data = []
    for row in rows:
        credit_val = round(float(row.credit or 0), 2)
        debit_val = round(float(row.debit or 0), 2)
        # Skip days with no activity so graph never shows zero-flat lines
        if credit_val == 0 and debit_val == 0:
            continue
        data.append({
            "date": row.day.isoformat() if row.day else None,
            "credit": credit_val,
            "debit": debit_val,
        })

    return {"history": data, "days": days}
=======
>>>>>>> 8a260015108003b30586cdffc9a5d14ec1407d73
