<<<<<<< HEAD
"""Affordability engine API endpoint — powered by Gemini AI."""

import logging
from datetime import datetime
from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel
=======
"""Affordability engine API endpoint."""

import logging
from fastapi import APIRouter, Depends, HTTPException
>>>>>>> 8a260015108003b30586cdffc9a5d14ec1407d73
from sqlalchemy.orm import Session

from database import get_db
from models.user import User
<<<<<<< HEAD
from models.transaction import Transaction
from models.email_draft import EmailDraft
from schemas.expense import ExpenseInput
from schemas.affordability import AffordabilityResponse
from schemas.email_draft import EmailSendRequest
from services.affordability_service import run_affordability_check
from services.gemini_service import generate_explanation, generate_negotiation_email, generate_borrowing_email
from services.auth_service import get_current_user
from services.email_service import send_email
from services.forecast_service import forecast_liquidity, invalidate_forecast_cache
from models.affordability_check import AffordabilityCheck
from models.ai_action_log import AIActionLog
from schemas.ai_action import AIActionEmailRequest, SendEmailRequest
from redis_client import cache_delete
=======
from schemas.expense import ExpenseInput
from schemas.affordability import AffordabilityResponse
from services.affordability_service import run_affordability_check
from services.claude_service import generate_explanation, generate_negotiation_email
from services.auth_service import get_current_user
from models.affordability_check import AffordabilityCheck
>>>>>>> 8a260015108003b30586cdffc9a5d14ec1407d73

logger = logging.getLogger(__name__)
router = APIRouter(prefix="/api/affordability", tags=["affordability"])


<<<<<<< HEAD
class ConfirmPurchaseRequest(BaseModel):
    expense_name: str
    expense_amount: float
    expense_category: str
    expense_date: str  # ISO format date


=======
>>>>>>> 8a260015108003b30586cdffc9a5d14ec1407d73
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

<<<<<<< HEAD
        # Generate AI explanation via Gemini
        explanation = await generate_explanation(result)
        result.ai_explanation = explanation
=======
        # Generate Claude explanation
        explanation = await generate_explanation(result)
        result.claude_explanation = explanation
>>>>>>> 8a260015108003b30586cdffc9a5d14ec1407d73

        # Generate negotiation email for CRITICAL decisions
        if result.decision == "CRITICAL" and result.alternative_paths:
            defer_path = next(
                (p for p in result.alternative_paths if p.path_type == "defer_obligation"),
                None,
            )
            if defer_path and defer_path.obligation_name:
<<<<<<< HEAD
                email_data = await generate_negotiation_email(
                    result,
                    defer_path.obligation_name,
                    "local_vendor",
                    defer_path.deferral_days or 15,
                )
                result.negotiation_email = email_data
=======
                email = await generate_negotiation_email(
                    result,
                    defer_path.obligation_name,
                    defer_path.deferral_days or 15,
                )
                result.negotiation_email = email
>>>>>>> 8a260015108003b30586cdffc9a5d14ec1407d73

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
<<<<<<< HEAD
            recommended_date=result.recommended_date,
            current_balance=result.current_balance,
            projected_balance_at_date=result.projected_balance_at_date,
            monthly_burn_rate=result.monthly_burn_rate,
            ai_explanation=result.ai_explanation,
=======
            claude_explanation=result.claude_explanation,
>>>>>>> 8a260015108003b30586cdffc9a5d14ec1407d73
            forecast_data=[fp.model_dump() for fp in result.forecast_data[:30]],
            alternative_paths=[ap.model_dump() for ap in result.alternative_paths],
        )
        db.add(check)
        db.commit()

        return result

    except Exception as e:
        logger.error(f"Affordability check error: {e}")
        raise HTTPException(500, f"Error running affordability check: {str(e)}")


<<<<<<< HEAD
@router.post("/confirm-purchase")
def confirm_purchase(
    request: ConfirmPurchaseRequest,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    """Confirm an affordable purchase: record as transaction and return updated forecast."""
    try:
        # Parse the expense date
        try:
            expense_date = datetime.fromisoformat(request.expense_date)
        except ValueError:
            expense_date = datetime.now()

        # Record the expense as a debit transaction
        transaction = Transaction(
            user_id=current_user.id,
            date=expense_date,
            amount=-abs(request.expense_amount),  # Negative = debit
            category=request.expense_category,
            counterparty=request.expense_name,
            source="affordability_confirm",
            is_recurring=False,
            confidence=1.0,
            needs_review=False,
            raw_text=f"Confirmed purchase: {request.expense_name}",
        )
        db.add(transaction)
        db.commit()

        # Invalidate caches so forecast is recalculated
        try:
            cache_delete(f"expense_profile:{current_user.id}")
        except Exception:
            pass
        invalidate_forecast_cache(current_user.id)

        # Get fresh forecast
        forecast_points, current_balance = forecast_liquidity(db, current_user.id, forecast_days=30)

        return {
            "status": "confirmed",
            "message": f"Purchase '{request.expense_name}' confirmed and recorded",
            "transaction_id": transaction.id,
            "updated_forecast": [fp.model_dump() for fp in forecast_points],
            "current_balance": round(current_balance, 2),
        }

    except Exception as e:
        db.rollback()
        logger.error(f"Confirm purchase error: {e}")
        raise HTTPException(500, f"Error confirming purchase: {str(e)}")


=======
>>>>>>> 8a260015108003b30586cdffc9a5d14ec1407d73
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


<<<<<<< HEAD
@router.post("/generate-action-email")
async def generate_action_email(
    request: AIActionEmailRequest,
    current_user: User = Depends(get_current_user),
):
    """Generate inline action email using Gemini AI — tone-aware based on path type."""
    if request.path.path_type == "defer_obligation":
        counterparty = request.path.obligation_name or "Shop Rent Landlord"
        relationship = getattr(request, 'recipient_type', 'local_vendor') or 'local_vendor'
        email_data = await generate_negotiation_email(
            request.result,
            counterparty,
            relationship,
            request.path.deferral_days or 15,
        )
    elif request.path.path_type == "short_term_borrowing":
        email_data = await generate_borrowing_email(
            request.result,
            request.path.borrowing_amount or 17500.0,
            request.path.borrowing_cost or 262.50,
            f"covering high-priority {request.result.expense_name}",
        )
    else:
        raise HTTPException(400, "Unsupported action type")
    
    return {"email": email_data}


@router.post("/send-action-email")
async def send_action_email(
    request: SendEmailRequest,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    """Log the action and dispatch the email."""
    # Log in AI actions table
    log = AIActionLog(
        user_id=current_user.id,
        recipient=request.recipient,
        action_type=request.action_type,
        email_content=request.email_content,
    )
    db.add(log)

    # Also store as EmailDraft for tracking
    draft = EmailDraft(
        user_id=current_user.id,
        recipient_email=request.recipient,
        recipient_name=request.recipient,
        subject=f"{request.action_type.replace('_', ' ').capitalize()} Request",
        body=request.email_content,
        status="sent",
        sent_at=datetime.now(),
    )
    db.add(draft)
    db.commit()
    
    # Try sending via Mailgun / SMTP
    success = await send_email(
        to_email=request.recipient,
        subject=f"{request.action_type.replace('_', ' ').capitalize()} Request - LiquiSense",
        body=request.email_content,
    )
    
    if not success:
        draft.status = "failed"
        db.commit()
        logger.warning(f"Email logged but dispatch failed for {request.recipient}")
    
    return {"status": "success", "message": "Email sent successfully", "draft_id": draft.id}


@router.post("/send-composed-email")
async def send_composed_email(
    request: EmailSendRequest,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    """Send a fully composed email (from the modal) with subject and body."""
    # Store draft
    draft = EmailDraft(
        user_id=current_user.id,
        recipient_email=request.recipient_email,
        recipient_name=request.recipient_name,
        relationship_type=request.relationship_type,
        subject=request.subject,
        body=request.body,
        affordability_check_id=request.affordability_check_id,
        status="sent",
        sent_at=datetime.now(),
    )
    db.add(draft)
    
    # Log in AI actions
    log = AIActionLog(
        user_id=current_user.id,
        recipient=request.recipient_email,
        action_type=request.action_type or "composed_email",
        email_content=f"Subject: {request.subject}\n\n{request.body}",
    )
    db.add(log)
    db.commit()

    # Send
    success = await send_email(
        to_email=request.recipient_email,
        subject=request.subject,
        body=request.body,
    )

    if not success:
        draft.status = "failed"
        db.commit()

    return {
        "status": "success" if success else "failed",
        "message": "Email sent successfully" if success else "Email dispatch failed",
        "draft_id": draft.id,
    }
=======
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
>>>>>>> 8a260015108003b30586cdffc9a5d14ec1407d73
