"""Affordability engine API endpoint."""

import logging
from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

from database import get_db
from models.user import User
from schemas.expense import ExpenseInput
from schemas.affordability import AffordabilityResponse
from services.affordability_service import run_affordability_check
from services.claude_service import generate_explanation, generate_negotiation_email
from services.auth_service import get_current_user
from models.affordability_check import AffordabilityCheck

logger = logging.getLogger(__name__)
router = APIRouter(prefix="/api/affordability", tags=["affordability"])


@router.post("", response_model=AffordabilityResponse)
async def check_affordability(
    expense: ExpenseInput,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    """Run affordability check for a proposed expense."""
    try:
        # Run the engine
        result = run_affordability_check(expense, db, current_user.id)

        # Generate Claude explanation
        explanation = await generate_explanation(result)
        result.claude_explanation = explanation

        # Generate negotiation email for CRITICAL decisions
        if result.decision == "CRITICAL" and result.alternative_paths:
            defer_path = next(
                (p for p in result.alternative_paths if p.path_type == "defer_obligation"),
                None,
            )
            if defer_path and defer_path.obligation_name:
                email = await generate_negotiation_email(
                    result,
                    defer_path.obligation_name,
                    defer_path.deferral_days or 15,
                )
                result.negotiation_email = email

        # Store in history
        check = AffordabilityCheck(
            user_id=current_user.id,
            expense_name=result.expense_name,
            expense_amount=result.expense_amount,
            expense_category=result.expense_category,
            expense_date=expense.date,
            decision=result.decision,
            priority_tier=result.priority_tier,
            reason_code=result.reason_code,
            deferral_days=result.deferral_days,
            claude_explanation=result.claude_explanation,
            forecast_data=[fp.model_dump() for fp in result.forecast_data[:30]],
            alternative_paths=[ap.model_dump() for ap in result.alternative_paths],
        )
        db.add(check)
        db.commit()

        return result

    except Exception as e:
        logger.error(f"Affordability check error: {e}")
        raise HTTPException(500, f"Error running affordability check: {str(e)}")


@router.get("/history")
def get_affordability_history(
    skip: int = 0,
    limit: int = 20,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    """Get history of affordability checks."""
    total = db.query(AffordabilityCheck).filter(AffordabilityCheck.user_id == current_user.id).count()
    checks = (
        db.query(AffordabilityCheck)
        .filter(AffordabilityCheck.user_id == current_user.id)
        .order_by(AffordabilityCheck.created_at.desc())
        .offset(skip)
        .limit(limit)
        .all()
    )

    return {
        "total": total,
        "checks": [c.to_dict() for c in checks],
    }


@router.post("/generate-email")
async def generate_email(
    counterparty: str,
    deferral_days: int = 15,
    expense: ExpenseInput = None,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    """Generate a negotiation email for obligation deferral."""
    result = run_affordability_check(expense, db, current_user.id) if expense else None

    if not result:
        from schemas.affordability import AffordabilityResponse
        result = AffordabilityResponse(
            decision="CRITICAL",
            priority_tier="HIGH",
            reason_code="MANUAL_REQUEST",
            expense_name="Manual request",
            expense_amount=0,
            expense_category="Other",
            current_balance=0,
            projected_balance_at_date=0,
            monthly_burn_rate=0,
        )

    email = await generate_negotiation_email(result, counterparty, deferral_days)
    return {"email": email}
