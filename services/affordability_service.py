"""Affordability decision engine."""

import logging
from datetime import datetime, timedelta
from typing import Optional
from sqlalchemy.orm import Session

from models.priority_mapping import PriorityMapping
from schemas.expense import ExpenseInput
from schemas.affordability import AffordabilityResponse, AlternativePath, ForecastPoint
from services.forecast_service import forecast_liquidity, get_recurring_obligations, get_current_balance
from services.profiler_service import run_full_profile
from redis_client import cache_get, cache_set

logger = logging.getLogger(__name__)

# Rupee sign as unicode escape — avoids CP1252 UnicodeEncodeError on Windows
_SYM = "\u20b9"

# Thresholds
COMFORTABLE_MARGIN = 0.20  # 20% margin above zero
TIGHT_THRESHOLD = 0.05     # 5% margin — risky


def get_priority_tier(category: str, db: Session) -> tuple[str, float, float]:
<<<<<<< HEAD
    """Get priority tier, flexibility, and penalty for a category."""
=======
    """Get priority tier, flexibility, and penalty for a category.

    Returns (priority_tier, flexibility_score, penalty_rate)
    """
>>>>>>> 8a260015108003b30586cdffc9a5d14ec1407d73
    mapping = db.query(PriorityMapping).filter(
        PriorityMapping.category == category
    ).first()

    if mapping:
        return mapping.priority_tier, mapping.flexibility_score, mapping.penalty_rate

    return "LOW", 0.8, 0.0


def find_most_deferrable_obligation(
    obligations: list[dict],
    db: Session,
) -> Optional[dict]:
    """Find the most deferrable upcoming obligation based on flexibility and penalty."""
    if not obligations:
        return None

    scored = []
    for obl in obligations:
        _, flexibility, penalty = get_priority_tier(obl["category"], db)
<<<<<<< HEAD
=======
        # Higher flexibility + lower penalty = more deferrable
>>>>>>> 8a260015108003b30586cdffc9a5d14ec1407d73
        score = flexibility - (penalty * 2)
        scored.append({**obl, "flexibility": flexibility, "penalty": penalty, "defer_score": score})

    scored.sort(key=lambda x: x["defer_score"], reverse=True)
    return scored[0] if scored else None


def compute_borrowing_estimate(
    shortfall: float,
    expense_amount: float,
) -> AlternativePath:
    """Compute minimum borrowing needed to cover a high-priority expense."""
<<<<<<< HEAD
    buffer = shortfall * 1.1
    borrowing_amount = max(buffer, expense_amount * 0.5)

    overdraft_rate = 0.015
    credit_line_rate = 0.012
=======
    buffer = shortfall * 1.1  # 10% safety buffer
    borrowing_amount = max(buffer, expense_amount * 0.5)

    # Estimate costs for different sources
    overdraft_rate = 0.015  # 1.5% per month
    credit_line_rate = 0.012  # 1.2% per month
>>>>>>> 8a260015108003b30586cdffc9a5d14ec1407d73

    return AlternativePath(
        path_type="short_term_borrowing",
        description=f"Short-term borrowing of {_SYM}{borrowing_amount:,.2f} to cover the expense without missing critical obligations",
        borrowing_amount=round(borrowing_amount, 2),
        borrowing_source="Overdraft or Credit Line",
        borrowing_cost=round(borrowing_amount * overdraft_rate, 2),
<<<<<<< HEAD
        cost_of_missing=round(expense_amount * 0.25, 2),
=======
        cost_of_missing=round(expense_amount * 0.25, 2),  # Estimated cost of missing the expense
>>>>>>> 8a260015108003b30586cdffc9a5d14ec1407d73
    )


def run_affordability_check(
    expense: ExpenseInput,
    db: Session,
    user_id: int,
) -> AffordabilityResponse:
    """Run the full affordability decision engine.

    Process:
    1. Forecast liquidity for 30-60 days
    2. Overlay fixed obligations
    3. Classify expense priority
    4. Run decision logic
    5. Generate alternative paths if needed
    """
<<<<<<< HEAD
    expense_amount = expense.amount

=======
>>>>>>> 8a260015108003b30586cdffc9a5d14ec1407d73
    # Get cached profile or compute fresh
    cache_key = f"expense_profile:{user_id}"
    profile = cache_get(cache_key)
    if not profile:
        profile = run_full_profile(db, user_id)
        cache_set(cache_key, profile, ttl=600)

    monthly_burn = profile.get("monthly_burn_rate", 0)

    # Forecast liquidity
    forecast_points, current_balance = forecast_liquidity(db, user_id, forecast_days=60)

    # Get priority tier
    priority_tier, flexibility, penalty_rate = get_priority_tier(expense.category, db)

    # Find projected balance at expense date
    expense_date_str = expense.date.date().isoformat()
    projected_at_date = current_balance
    for fp in forecast_points:
        if fp.date == expense_date_str:
            projected_at_date = fp.projected_balance
            break

<<<<<<< HEAD
    min_projected = min(fp.projected_balance for fp in forecast_points) if forecast_points else current_balance
    balance_after_expense = projected_at_date - expense_amount
=======
    # Check if projected balance after obligations stays above zero
    min_projected = min(fp.projected_balance for fp in forecast_points) if forecast_points else current_balance
    balance_after_expense = projected_at_date - expense.amount
>>>>>>> 8a260015108003b30586cdffc9a5d14ec1407d73

    # Decision logic
    decision = "APPROVE"
    reason_code = "AFFORDABLE"
    deferral_days = None
    recommended_date = None
    alternative_paths = []

    if balance_after_expense > current_balance * COMFORTABLE_MARGIN:
<<<<<<< HEAD
=======
        # Comfortable — approve regardless of priority
>>>>>>> 8a260015108003b30586cdffc9a5d14ec1407d73
        decision = "APPROVE"
        reason_code = "COMFORTABLE_LIQUIDITY"

    elif balance_after_expense > current_balance * TIGHT_THRESHOLD:
<<<<<<< HEAD
=======
        # Tight liquidity
>>>>>>> 8a260015108003b30586cdffc9a5d14ec1407d73
        if priority_tier == "HIGH":
            decision = "APPROVE"
            reason_code = "TIGHT_BUT_HIGH_PRIORITY"
        else:
            decision = "DEFER"
            reason_code = "LIQUIDITY_TIGHT"

<<<<<<< HEAD
            for i, fp in enumerate(forecast_points):
                if fp.projected_balance > projected_at_date + expense_amount * 0.5:
=======
            # Find next receivable / balance recovery point
            for i, fp in enumerate(forecast_points):
                if fp.projected_balance > projected_at_date + expense.amount * 0.5:
>>>>>>> 8a260015108003b30586cdffc9a5d14ec1407d73
                    deferral_days = i + 1
                    recommended_date = fp.date
                    break

            if not deferral_days:
<<<<<<< HEAD
                deferral_days = 14
                recommended_date = (datetime.now() + timedelta(days=14)).date().isoformat()

    elif balance_after_expense <= 0 or min_projected - expense_amount < 0:
=======
                deferral_days = 14  # Default 2-week deferral
                recommended_date = (datetime.now() + timedelta(days=14)).date().isoformat()

    elif balance_after_expense <= 0 or min_projected - expense.amount < 0:
        # Critical — balance would go negative
>>>>>>> 8a260015108003b30586cdffc9a5d14ec1407d73
        if priority_tier == "HIGH":
            decision = "CRITICAL"
            reason_code = "CRITICAL_HIGH_PRIORITY"

<<<<<<< HEAD
=======
            # Path 1: Find most deferrable obligation
>>>>>>> 8a260015108003b30586cdffc9a5d14ec1407d73
            obligations = get_recurring_obligations(db, user_id)
            deferrable = find_most_deferrable_obligation(obligations, db)

            if deferrable:
                alternative_paths.append(AlternativePath(
                    path_type="defer_obligation",
                    description=f"Defer payment to {deferrable['name']} ({deferrable['category']}) to free up {_SYM}{deferrable['amount']:,.2f}",
                    obligation_name=deferrable["name"],
                    deferral_days=15,
                    penalty_cost=round(deferrable["amount"] * deferrable.get("penalty", 0.05), 2),
                ))

<<<<<<< HEAD
            shortfall = abs(balance_after_expense)
            alternative_paths.append(compute_borrowing_estimate(shortfall, expense_amount))
=======
            # Path 2: Borrowing estimate
            shortfall = abs(balance_after_expense)
            alternative_paths.append(compute_borrowing_estimate(shortfall, expense.amount))
>>>>>>> 8a260015108003b30586cdffc9a5d14ec1407d73

        elif priority_tier == "MID":
            decision = "DEFER"
            reason_code = "INSUFFICIENT_LIQUIDITY"
            deferral_days = 21
            recommended_date = (datetime.now() + timedelta(days=21)).date().isoformat()

        else:
            decision = "DEFER"
            reason_code = "NOT_AFFORDABLE"
            deferral_days = 30
            recommended_date = (datetime.now() + timedelta(days=30)).date().isoformat()

    else:
<<<<<<< HEAD
=======
        # Edge case
>>>>>>> 8a260015108003b30586cdffc9a5d14ec1407d73
        decision = "DEFER"
        reason_code = "MARGINAL_LIQUIDITY"
        deferral_days = 7
        recommended_date = (datetime.now() + timedelta(days=7)).date().isoformat()

    return AffordabilityResponse(
        decision=decision,
        priority_tier=priority_tier,
        reason_code=reason_code,
        expense_name=expense.name,
        expense_amount=expense.amount,
        expense_category=expense.category,
        current_balance=round(current_balance, 2),
        projected_balance_at_date=round(projected_at_date, 2),
        monthly_burn_rate=round(monthly_burn, 2),
        deferral_days=deferral_days,
        recommended_date=recommended_date,
        forecast_data=forecast_points,
        alternative_paths=alternative_paths,
    )
