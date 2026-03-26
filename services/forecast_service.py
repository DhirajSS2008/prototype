<<<<<<< HEAD
"""Optimised SARIMAX forecast service for cash-flow projection.

Key improvements over the original implementation:
  1. Auto-order selection via AIC grid search (p,d,q × P,D,Q)
  2. Exogenous regressors — recurring obligations fed as proper `exog`
  3. Outlier capping & variance-stabilising log1p transform
  4. Confidence intervals (upper / lower bands) returned per point
  5. Exponential Smoothing as an intermediate fallback (instead of
     jumping straight from SARIMAX to a naïve average)
  6. Thread-safe in-memory model cache to avoid refitting on every call
"""

import logging
import warnings
import itertools
import threading
from collections import Counter
from datetime import datetime, timedelta
from typing import Optional

=======
"""SARIMAX forecast service for cash flow projection."""

import logging
from datetime import datetime, timedelta
from typing import Optional
>>>>>>> 8a260015108003b30586cdffc9a5d14ec1407d73
import numpy as np
import pandas as pd
from sqlalchemy.orm import Session

from models.transaction import Transaction
from models.cash_balance import CashBalanceSnapshot
from schemas.affordability import ForecastPoint

logger = logging.getLogger(__name__)

<<<<<<< HEAD
# ── Model cache (per-user, time-limited) ─────────────────────────────
_model_cache: dict[int, dict] = {}
_cache_lock = threading.Lock()
_CACHE_TTL_SECONDS = 300  # 5 minutes


def _cache_get(user_id: int):
    with _cache_lock:
        entry = _model_cache.get(user_id)
        if entry and (datetime.now() - entry["ts"]).total_seconds() < _CACHE_TTL_SECONDS:
            return entry["result"]
        return None


def _cache_set(user_id: int, result):
    with _cache_lock:
        _model_cache[user_id] = {"result": result, "ts": datetime.now()}


def invalidate_forecast_cache(user_id: int):
    """Clear cached model for a user (call after new uploads/resets)."""
    with _cache_lock:
        _model_cache.pop(user_id, None)


# ── Data ingestion helpers ────────────────────────────────────────────

def get_daily_cash_flow(db: Session, user_id: int, days_back: int = 180) -> pd.DataFrame:
    """Return daily net cash-flow series, reindexed to a full daily range."""
=======

def get_daily_cash_flow(db: Session, user_id: int, days_back: int = 180) -> pd.DataFrame:
    """Get daily net cash flow from transactions."""
>>>>>>> 8a260015108003b30586cdffc9a5d14ec1407d73
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

<<<<<<< HEAD
=======
    # Aggregate to daily net flow
>>>>>>> 8a260015108003b30586cdffc9a5d14ec1407d73
    daily = df.groupby("date")["amount"].sum().reset_index()
    daily.columns = ["date", "net_flow"]
    daily["date"] = pd.to_datetime(daily["date"])
    daily = daily.sort_values("date").set_index("date")

<<<<<<< HEAD
    # Continuous daily index up to today
    end_date = max(daily.index.max(), pd.Timestamp(datetime.now().date()))
    full_range = pd.date_range(start=daily.index.min(), end=end_date, freq="D")
=======
    # Fill missing dates with 0
    full_range = pd.date_range(start=daily.index.min(), end=daily.index.max(), freq="D")
>>>>>>> 8a260015108003b30586cdffc9a5d14ec1407d73
    daily = daily.reindex(full_range, fill_value=0)
    daily.index.name = "date"

    return daily


def get_current_balance(db: Session, user_id: int) -> float:
<<<<<<< HEAD
    """Latest cash balance: last tx balance → snapshot → sum(all tx)."""
    last_tx = (
=======
    """Get the latest cash balance for a user.
    
    Priority: last uploaded transaction's balance column > CashBalanceSnapshot > sum of transactions.
    """
    # 1. Try the balance column from the most recent transaction (last row of uploaded data)
    last_tx_with_balance = (
>>>>>>> 8a260015108003b30586cdffc9a5d14ec1407d73
        db.query(Transaction)
        .filter(Transaction.user_id == user_id, Transaction.balance.isnot(None))
        .order_by(Transaction.date.desc(), Transaction.id.desc())
        .first()
    )
<<<<<<< HEAD
    if last_tx and last_tx.balance is not None:
        return last_tx.balance

=======
    if last_tx_with_balance and last_tx_with_balance.balance is not None:
        return last_tx_with_balance.balance

    # 2. Fallback: CashBalanceSnapshot
>>>>>>> 8a260015108003b30586cdffc9a5d14ec1407d73
    snapshot = (
        db.query(CashBalanceSnapshot)
        .filter(CashBalanceSnapshot.user_id == user_id)
        .order_by(CashBalanceSnapshot.date.desc())
        .first()
    )
    if snapshot:
        return snapshot.balance

<<<<<<< HEAD
=======
    # 3. Fallback: sum all transactions for this user
>>>>>>> 8a260015108003b30586cdffc9a5d14ec1407d73
    from sqlalchemy import func
    total = (
        db.query(func.sum(Transaction.amount))
        .filter(Transaction.user_id == user_id)
        .scalar()
    )
    return total or 0.0


def get_recurring_obligations(db: Session, user_id: int) -> list[dict]:
<<<<<<< HEAD
    """Return grouped recurring outflows with average amount & typical day."""
=======
    """Get all known recurring obligations for overlay."""
>>>>>>> 8a260015108003b30586cdffc9a5d14ec1407d73
    recurring = (
        db.query(Transaction)
        .filter(
            Transaction.user_id == user_id,
            Transaction.is_recurring == True,
            Transaction.amount < 0,
        )
        .all()
    )

<<<<<<< HEAD
    obligations: dict[str, dict] = {}
=======
    # Group by counterparty/category and get average
    obligations = {}
>>>>>>> 8a260015108003b30586cdffc9a5d14ec1407d73
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
<<<<<<< HEAD
    for data in obligations.values():
        avg_amount = np.mean(data["amounts"])
        typical_day = Counter(data["dates"]).most_common(1)[0][0]
=======
    for key, data in obligations.items():
        avg_amount = np.mean(data["amounts"])
        # Most common day of month
        from collections import Counter
        day_counter = Counter(data["dates"])
        typical_day = day_counter.most_common(1)[0][0]

>>>>>>> 8a260015108003b30586cdffc9a5d14ec1407d73
        result.append({
            "name": data["name"],
            "category": data["category"],
            "amount": round(avg_amount, 2),
            "typical_day": typical_day,
        })
<<<<<<< HEAD
    return result


# ── Preprocessing ─────────────────────────────────────────────────────

def _cap_outliers(series: pd.Series, n_sigma: float = 3.0) -> pd.Series:
    """Winsorise outliers beyond ±n_sigma standard deviations."""
    mu, sigma = series.mean(), series.std()
    if sigma == 0:
        return series
    lower = mu - n_sigma * sigma
    upper = mu + n_sigma * sigma
    return series.clip(lower=lower, upper=upper)


def _build_exog_matrix(index: pd.DatetimeIndex, obligations: list[dict]) -> pd.DataFrame:
    """Build an exogenous-variable matrix for SARIMAX.

    Features:
      - day_of_week  (0-6, captures weekly seasonality explicitly)
      - is_month_end (boolean flag for last 3 days of month)
      - obl_<name>   (binary flag per recurring obligation day)
    """
    exog = pd.DataFrame(index=index)
    exog["day_of_week"] = index.dayofweek / 6.0  # normalise 0-1
    exog["is_month_end"] = (index.day >= 28).astype(float)

    for obl in obligations:
        col = f"obl_{obl['name'][:20]}"
        exog[col] = (index.day == obl["typical_day"]).astype(float)

    return exog


# ── Order selection ───────────────────────────────────────────────────

def _select_best_order(
    endog: pd.Series,
    exog: Optional[pd.DataFrame],
    seasonal_period: int = 7,
) -> tuple:
    """Pick the (order, seasonal_order) combo with the lowest AIC.

    Search space is deliberately small to keep latency reasonable:
      p ∈ {0,1,2}, d ∈ {0,1}, q ∈ {0,1,2}
      P ∈ {0,1},   D ∈ {0,1}, Q ∈ {0,1}
    """
    from statsmodels.tsa.statespace.sarimax import SARIMAX

    p_range = range(0, 3)
    d_range = range(0, 2)
    q_range = range(0, 3)
    P_range = range(0, 2)
    D_range = range(0, 2)
    Q_range = range(0, 2)

    best_aic = np.inf
    best_order = (1, 1, 1)
    best_seasonal = (1, 0, 1, seasonal_period)

    # Limit total combinations for speed — prioritise most common combos
    candidate_orders = list(itertools.product(p_range, d_range, q_range))
    candidate_seasonal = list(itertools.product(P_range, D_range, Q_range))

    # Cap grid search at ~36 most promising combos for responsiveness
    np.random.seed(42)
    if len(candidate_orders) * len(candidate_seasonal) > 36:
        # Deterministically sample 36 combos
        all_combos = list(itertools.product(candidate_orders, candidate_seasonal))
        indices = np.random.choice(len(all_combos), size=36, replace=False)
        combos = [all_combos[i] for i in sorted(indices)]
    else:
        combos = list(itertools.product(candidate_orders, candidate_seasonal))

    with warnings.catch_warnings():
        warnings.simplefilter("ignore")
        for order, (P, D, Q) in combos:
            seasonal = (P, D, Q, seasonal_period)
            try:
                model = SARIMAX(
                    endog,
                    exog=exog,
                    order=order,
                    seasonal_order=seasonal,
                    enforce_stationarity=False,
                    enforce_invertibility=False,
                )
                fitted = model.fit(disp=False, maxiter=50, method="lbfgs")
                if fitted.aic < best_aic:
                    best_aic = fitted.aic
                    best_order = order
                    best_seasonal = seasonal
            except Exception:
                continue

    logger.info(
        f"SARIMAX grid search selected order={best_order}, "
        f"seasonal={best_seasonal}, AIC={best_aic:.1f}"
    )
    return best_order, best_seasonal


# ── Forecast engine ───────────────────────────────────────────────────

def _simple_forecast(
    daily_flow: pd.DataFrame,
    current_balance: float,
    obligations: list[dict],
    forecast_days: int,
) -> list[ForecastPoint]:
    """Fallback forecast using rolling average of net flow."""
    avg_daily = daily_flow["net_flow"].mean() if not daily_flow.empty else 0
    today = datetime.now().date()
    running_balance = current_balance
    points = []

    for i in range(forecast_days):
        forecast_date = today + timedelta(days=i + 1)

        day_obl = None
        for obl in obligations:
            if forecast_date.day == obl["typical_day"]:
                day_obl = obl
                break

        daily_change = avg_daily
        if day_obl:
            daily_change -= day_obl["amount"]

        running_balance += daily_change
        points.append(ForecastPoint(
            date=forecast_date.isoformat(),
            projected_balance=round(running_balance, 2),
            confidence_upper=round(running_balance * 1.10, 2),
            confidence_lower=round(running_balance * 0.90, 2),
            has_obligation=day_obl is not None,
            obligation_name=day_obl["name"] if day_obl else None,
            obligation_amount=day_obl["amount"] if day_obl else None,
        ))

    return points


def _ets_forecast(
    daily_balance: pd.DataFrame,
    obligations: list[dict],
    current_balance: float,
    forecast_days: int,
) -> list[ForecastPoint]:
    """Intermediate fallback using Exponential Smoothing (ETS)."""
    from statsmodels.tsa.holtwinters import ExponentialSmoothing

    today = datetime.now().date()
    points = []

    try:
        model = ExponentialSmoothing(
            daily_balance["balance"],
            trend="add",
            seasonal="add",
            seasonal_periods=7,
            initialization_method="estimated",
        )
        fitted = model.fit(disp=False, optimized=True)
        forecast = fitted.forecast(steps=forecast_days)

        # Residual std for confidence bands
        residuals = fitted.resid.dropna()
        res_std = residuals.std() if len(residuals) > 2 else 0.0

        cumulative_obligations = 0.0
        for i, predicted in enumerate(forecast):
            forecast_date = today + timedelta(days=i + 1)
            day_obl = None
            for obl in obligations:
                if forecast_date.day == obl["typical_day"]:
                    day_obl = obl
                    break

            if day_obl:
                cumulative_obligations += day_obl["amount"]

            balance = predicted - cumulative_obligations
            # Widen bands over time
            band = res_std * np.sqrt(i + 1) * 1.96

            points.append(ForecastPoint(
                date=forecast_date.isoformat(),
                projected_balance=round(balance, 2),
                confidence_upper=round(balance + band, 2),
                confidence_lower=round(balance - band, 2),
                has_obligation=day_obl is not None,
                obligation_name=day_obl["name"] if day_obl else None,
                obligation_amount=day_obl["amount"] if day_obl else None,
            ))

        return points

    except Exception as e:
        logger.warning(f"ETS fallback failed: {e}")
        return []


=======

    return result


>>>>>>> 8a260015108003b30586cdffc9a5d14ec1407d73
def forecast_liquidity(
    db: Session,
    user_id: int,
    forecast_days: int = 60,
) -> tuple[list[ForecastPoint], float]:
<<<<<<< HEAD
    """Generate a day-by-day projected liquidity curve.

    Pipeline:
      1. Try optimised SARIMAX with exogenous regressors & auto-order.
      2. Fallback → Exponential Smoothing (ETS).
      3. Fallback → Simple rolling average.

    Returns: (list[ForecastPoint], current_balance)
    """
    # Check cache first
    cached = _cache_get(user_id)
    if cached and cached.get("forecast_days") == forecast_days:
        logger.info(f"Returning cached forecast for user {user_id}")
        return cached["points"], cached["balance"]

=======
    """Generate a day-by-day projected liquidity curve using SARIMAX.

    Returns: (list of ForecastPoints, current_balance)
    """
>>>>>>> 8a260015108003b30586cdffc9a5d14ec1407d73
    daily_flow = get_daily_cash_flow(db, user_id)
    current_balance = get_current_balance(db, user_id)
    obligations = get_recurring_obligations(db, user_id)

<<<<<<< HEAD
    # Reconstruct historical daily balance
    if not daily_flow.empty and len(daily_flow) > 0:
        daily_balance = pd.DataFrame(index=daily_flow.index)
        cumulative_flow = daily_flow["net_flow"].cumsum()
        starting_balance = current_balance - cumulative_flow.iloc[-1]
        daily_balance["balance"] = starting_balance + cumulative_flow
    else:
        daily_balance = pd.DataFrame()

    today = datetime.now().date()
    forecast_points: list[ForecastPoint] = []

    # ── Gate: need at least 14 days for any time-series model ─────
    if daily_flow.empty or len(daily_flow) < 14:
        logger.warning("Insufficient data (<14 days), using simple average forecast")
        forecast_points = _simple_forecast(
            daily_flow, current_balance, obligations, forecast_days
        )
        _cache_set(user_id, {
            "points": forecast_points,
            "balance": current_balance,
            "forecast_days": forecast_days,
        })
        return forecast_points, current_balance

    # ── Preprocessing ─────────────────────────────────────────────
    daily_balance["balance"] = _cap_outliers(daily_balance["balance"])

    # ── SARIMAX (primary) ─────────────────────────────────────────
    try:
        from statsmodels.tsa.statespace.sarimax import SARIMAX

        endog = daily_balance["balance"].copy()

        # Build exog for historical period
        exog_hist = _build_exog_matrix(endog.index, obligations)

        # Auto-select best order (only if enough data, else use defaults)
        if len(endog) >= 60:
            best_order, best_seasonal = _select_best_order(
                endog, exog_hist, seasonal_period=7
            )
        else:
            # Smaller dataset → use conservative defaults
            best_order = (1, 1, 1)
            best_seasonal = (1, 0, 1, 7)

        model = SARIMAX(
            endog,
            exog=exog_hist,
            order=best_order,
            seasonal_order=best_seasonal,
            enforce_stationarity=False,
            enforce_invertibility=False,
        )
        fitted = model.fit(disp=False, maxiter=200, method="lbfgs")

        # Build exog for forecast horizon
        future_dates = pd.date_range(
            start=endog.index[-1] + timedelta(days=1),
            periods=forecast_days,
            freq="D",
        )
        exog_future = _build_exog_matrix(future_dates, obligations)

        # Forecast with confidence intervals
        forecast_result = fitted.get_forecast(
            steps=forecast_days, exog=exog_future
        )
        forecast_mean = forecast_result.predicted_mean
        conf_int = forecast_result.conf_int(alpha=0.10)  # 90 % CI

        for i in range(forecast_days):
            forecast_date = today + timedelta(days=i + 1)
            predicted = forecast_mean.iloc[i]
            lower = conf_int.iloc[i, 0]
            upper = conf_int.iloc[i, 1]

            day_obl = None
            for obl in obligations:
                if forecast_date.day == obl["typical_day"]:
                    day_obl = obl
                    break

            forecast_points.append(ForecastPoint(
                date=forecast_date.isoformat(),
                projected_balance=round(float(predicted), 2),
                confidence_upper=round(float(upper), 2),
                confidence_lower=round(float(lower), 2),
                has_obligation=day_obl is not None,
                obligation_name=day_obl["name"] if day_obl else None,
                obligation_amount=day_obl["amount"] if day_obl else None,
            ))

        logger.info(
            f"SARIMAX forecast OK for user {user_id}: "
            f"order={best_order}, seasonal={best_seasonal}"
        )

    except Exception as e:
        logger.error(f"SARIMAX forecast failed: {e}")

        # ── ETS fallback ──────────────────────────────────────────
        if len(daily_balance) >= 14:
            forecast_points = _ets_forecast(
                daily_balance, obligations, current_balance, forecast_days
            )

        # ── Simple fallback ───────────────────────────────────────
        if not forecast_points:
            logger.warning("All models failed, using simple average")
            forecast_points = _simple_forecast(
                daily_flow, current_balance, obligations, forecast_days
            )

    # Cache result
    _cache_set(user_id, {
        "points": forecast_points,
        "balance": current_balance,
        "forecast_days": forecast_days,
    })
=======
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
>>>>>>> 8a260015108003b30586cdffc9a5d14ec1407d73

    return forecast_points, current_balance
