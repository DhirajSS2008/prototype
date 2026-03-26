"""Transaction CRUD endpoints."""

import os
import glob
import logging
from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.orm import Session
from typing import Optional

from database import get_db
from models.user import User
from models.transaction import Transaction
from schemas.transaction import TransactionCreate, TransactionResponse
from models.affordability_check import AffordabilityCheck
from models.cash_balance import CashBalanceSnapshot
from services.auth_service import get_current_user

router = APIRouter(prefix="/api/transactions", tags=["transactions"])


@router.get("")
def list_transactions(
    skip: int = 0,
    limit: int = 50,
    category: Optional[str] = None,
    needs_review: Optional[bool] = None,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    """List transactions with optional filtering."""
    query = db.query(Transaction).filter(Transaction.user_id == current_user.id)

    if category:
        query = query.filter(Transaction.category == category)
    if needs_review is not None:
        query = query.filter(Transaction.needs_review == needs_review)

    total = query.count()
    transactions = (
        query.order_by(Transaction.date.desc())
        .offset(skip)
        .limit(limit)
        .all()
    )

    return {
        "total": total,
        "transactions": [t.to_dict() for t in transactions],
    }


@router.post("")
def create_transaction(
    tx: TransactionCreate,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    """Manually create a transaction."""
    transaction = Transaction(
        user_id=current_user.id,
        date=tx.date,
        amount=tx.amount,
        category=tx.category,
        counterparty=tx.counterparty,
        source=tx.source,
        is_recurring=tx.is_recurring,
        confidence=tx.confidence,
        needs_review=tx.needs_review,
        raw_text=tx.raw_text,
    )
    db.add(transaction)
    db.commit()
    db.refresh(transaction)
    return transaction.to_dict()


@router.put("/{transaction_id}")
def update_transaction(
    transaction_id: int,
    tx: TransactionCreate,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    """Update a transaction (e.g., after manual review)."""
    transaction = (
        db.query(Transaction)
        .filter(Transaction.id == transaction_id, Transaction.user_id == current_user.id)
        .first()
    )
    if not transaction:
        raise HTTPException(404, "Transaction not found")

    transaction.date = tx.date
    transaction.amount = tx.amount
    transaction.category = tx.category
    transaction.counterparty = tx.counterparty
    transaction.source = tx.source
    transaction.is_recurring = tx.is_recurring
    transaction.confidence = tx.confidence
    transaction.needs_review = tx.needs_review

    db.commit()
    return transaction.to_dict()


@router.delete("/{transaction_id}")
def delete_transaction(
    transaction_id: int,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    """Delete a transaction."""
    transaction = (
        db.query(Transaction)
        .filter(Transaction.id == transaction_id, Transaction.user_id == current_user.id)
        .first()
    )
    if not transaction:
        raise HTTPException(404, "Transaction not found")

    db.delete(transaction)
    db.commit()
    return {"message": "Transaction deleted"}


@router.delete("")
def clear_all_data(
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    """Delete all transactions, checks, snapshots, and uploaded files for current user (Full Reset)."""
    logger = logging.getLogger(__name__)
    try:
        tx_count = db.query(Transaction).filter(Transaction.user_id == current_user.id).delete()
        check_count = db.query(AffordabilityCheck).filter(AffordabilityCheck.user_id == current_user.id).delete()
        snap_count = db.query(CashBalanceSnapshot).filter(CashBalanceSnapshot.user_id == current_user.id).delete()
        db.commit()

        # Clean up uploaded files
        from config import get_settings
        settings = get_settings()
        upload_dir = settings.UPLOAD_DIR
        files_removed = 0
        if os.path.isdir(upload_dir):
            for f in glob.glob(os.path.join(upload_dir, "*")):
                try:
                    os.remove(f)
                    files_removed += 1
                except OSError:
                    pass

        # Invalidate Redis cache
        try:
            from redis_client import cache_delete
            cache_delete(f"expense_profile:{current_user.id}")
        except Exception:
            pass  # Redis may not be available

<<<<<<< HEAD
        # Invalidate forecast model cache
        try:
            from services.forecast_service import invalidate_forecast_cache
            invalidate_forecast_cache(current_user.id)
        except Exception:
            pass

=======
>>>>>>> 8a260015108003b30586cdffc9a5d14ec1407d73
        logger.info(
            f"Reset for user {current_user.id}: "
            f"{tx_count} transactions, {check_count} checks, "
            f"{snap_count} snapshots, {files_removed} files removed"
        )

        return {
            "message": "All history and data cleared successfully",
            "deleted": {
                "transactions": tx_count,
                "affordability_checks": check_count,
                "balance_snapshots": snap_count,
                "uploaded_files": files_removed,
            },
        }
    except Exception as e:
        db.rollback()
        raise HTTPException(500, f"Error clearing data: {str(e)}")
