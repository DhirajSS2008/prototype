"""SARIMAX forecast service for cash flow projection."""

import logging
from datetime import datetime, timedelta
from typing import Optional
import numpy as np
import pandas as pd
from sqlalchemy.orm import Session

from models.transaction import Transaction
from models.cash_balance import CashBalanceSnapshot
from schemas.affordability import ForecastPoint

logger = logging.getLogger(__name__)


def get_daily_cash_flow(db: Session, user_id: int, days_back: int = 180) -> pd.DataFrame:
    """Get daily net cash flow from transactions."""
    cutoff = datetime.now() - timedelta(days=days_back)

    transactions = (
        db.query(Transaction)
        .filter(Transaction.user_id == user_id, Transaction.date >= cutoff)
        .all()
    )

    if not transactions:
        return pd.DataFrame()

    data = [{"date": t.date, "amount": t.amount} for t in transactions]
    df = pd.DataFrame(data)
    df["date"] = pd.to_datetime(df["date"]).dt.date

    # Aggregate to daily net flow
    daily = df.groupby("date")["amount"].sum().reset_index()
    daily.columns = ["date", "net_flow"]
    daily["date"] = pd.to_datetime(daily["date"])
    daily = daily.sort_values("date").set_index("date")

    # Fill missing dates with 0
    full_range = pd.date_range(start=daily.index.min(), end=daily.index.max(), freq="D")
    daily = daily.reindex(full_range, fill_value=0)
    daily.index.name = "date"

    return daily


def get_current_balance(db: Session, user_id: int) -> float:
    """Get the latest cash balance for a user.
    
    Priority: last uploaded transaction's balance column > CashBalanceSnapshot > sum of transactions.
    """
    # 1. Try the balance column from the most recent transaction (last row of uploaded data)
    last_tx_with_balance = (
        db.query(Transaction)
        .filter(Transaction.user_id == user_id, Transaction.balance.isnot(None))
        .order_by(Transaction.date.desc(), Transaction.id.desc())
        .first()
    )
    if last_tx_with_balance and last_tx_with_balance.balance is not None:
        return last_tx_with_balance.balance

    # 2. Fallback: CashBalanceSnapshot
    snapshot = (
        db.query(CashBalanceSnapshot)
        .filter(CashBalanceSnapshot.user_id == user_id)
        .order_by(CashBalanceSnapshot.date.desc())
        .first()
    )
    if snapshot:
        return snapshot.balance

    # 3. Fallback: sum all transactions for this user
    from sqlalchemy import func
    total = (
        db.query(func.sum(Transaction.amount))
        .filter(Transaction.user_id == user_id)
        .scalar()
    )
    return total or 0.0


def get_recurring_obligations(db: Session, user_id: int) -> list[dict]:
    """Get all known recurring obligations for overlay."""
    recurring = (
        db.query(Transaction)
        .filter(
            Transaction.user_id == user_id,
            Transaction.is_recurring == True,
            Transaction.amount < 0,
        )
        .all()
    )

    # Group by counterparty/category and get average
    obligations = {}
    for t in recurring:
        key = t.counterparty or t.category
        if key not in obligations:
            obligations[key] = {
                "name": key,
                "category": t.category,
                "amounts": [],
                "dates": [],
            }
        obligations[key]["amounts"].append(abs(t.amount))
        obligations[key]["dates"].append(t.date.day if t.date else 1)

    result = []
    for key, data in obligations.items():
        avg_amount = np.mean(data["amounts"])
        # Most common day of month
        from collections import Counter
        day_counter = Counter(data["dates"])
        typical_day = day_counter.most_common(1)[0][0]

        result.append({
            "name": data["name"],
            "category": data["category"],
            "amount": round(avg_amount, 2),
            "typical_day": typical_day,
        })

    return result


def forecast_liquidity(
    db: Session,
    user_id: int,
    forecast_days: int = 60,
) -> tuple[list[ForecastPoint], float]:
    """Generate a day-by-day projected liquidity curve using SARIMAX.

    Returns: (list of ForecastPoints, current_balance)
    """
    daily_flow = get_daily_cash_flow(db, user_id)
    current_balance = get_current_balance(db, user_id)
    obligations = get_recurring_obligations(db, user_id)

    forecast_points = []
    today = datetime.now().date()

    if daily_flow.empty or len(daily_flow) < 30:
        # Not enough data for SARIMAX — use simple averaging
        logger.warning("Not enough data for SARIMAX, using simple average forecast")
        avg_daily = daily_flow["net_flow"].mean() if not daily_flow.empty else 0

        running_balance = current_balance
        for i in range(forecast_days):
            forecast_date = today + timedelta(days=i + 1)

            # Check for obligations on this day
            day_obligation = None
            for obl in obligations:
                if forecast_date.day == obl["typical_day"]:
                    day_obligation = obl
                    break

            daily_change = avg_daily
            if day_obligation:
                daily_change -= day_obligation["amount"]

            running_balance += daily_change

            forecast_points.append(ForecastPoint(
                date=forecast_date.isoformat(),
                projected_balance=round(running_balance, 2),
                has_obligation=day_obligation is not None,
                obligation_name=day_obligation["name"] if day_obligation else None,
                obligation_amount=day_obligation["amount"] if day_obligation else None,
            ))

        return forecast_points, current_balance

    # SARIMAX forecast
    try:
        from statsmodels.tsa.statespace.sarimax import SARIMAX

        # Fit model
        model = SARIMAX(
            daily_flow["net_flow"],
            order=(1, 1, 1),
            seasonal_order=(1, 1, 1, 7),  # Weekly seasonality
            enforce_stationarity=False,
            enforce_invertibility=False,
        )
        fitted = model.fit(disp=False, maxiter=100)

        # Forecast
        forecast = fitted.forecast(steps=forecast_days)

        running_balance = current_balance
        for i, (date_idx, predicted_flow) in enumerate(forecast.items()):
            forecast_date = today + timedelta(days=i + 1)

            # Find obligations
            day_obligation = None
            for obl in obligations:
                if forecast_date.day == obl["typical_day"]:
                    day_obligation = obl
                    break

            daily_change = predicted_flow
            if day_obligation:
                daily_change -= day_obligation["amount"]

            running_balance += daily_change

            forecast_points.append(ForecastPoint(
                date=forecast_date.isoformat(),
                projected_balance=round(running_balance, 2),
                has_obligation=day_obligation is not None,
                obligation_name=day_obligation["name"] if day_obligation else None,
                obligation_amount=day_obligation["amount"] if day_obligation else None,
            ))

    except Exception as e:
        logger.error(f"SARIMAX forecast failed, falling back to simple: {e}")
        # Fallback to simple average
        avg_daily = daily_flow["net_flow"].mean()
        running_balance = current_balance

        for i in range(forecast_days):
            forecast_date = today + timedelta(days=i + 1)
            day_obligation = None
            for obl in obligations:
                if forecast_date.day == obl["typical_day"]:
                    day_obligation = obl
                    break

            daily_change = avg_daily
            if day_obligation:
                daily_change -= day_obligation["amount"]

            running_balance += daily_change

            forecast_points.append(ForecastPoint(
                date=forecast_date.isoformat(),
                projected_balance=round(running_balance, 2),
                has_obligation=day_obligation is not None,
                obligation_name=day_obligation["name"] if day_obligation else None,
                obligation_amount=day_obligation["amount"] if day_obligation else None,
            ))

    return forecast_points, current_balance
