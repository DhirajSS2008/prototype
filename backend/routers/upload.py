"""File upload API endpoint."""

import os
import uuid
import logging
from datetime import datetime
from fastapi import APIRouter, UploadFile, File, Depends, HTTPException
from sqlalchemy.orm import Session

from database import get_db
from models.user import User
from models.transaction import Transaction
from services.pdf_service import extract_transactions_from_pdf
from services.ocr_service import extract_transactions_from_image
from services.auth_service import get_current_user
from tasks.analysis_tasks import run_profiler_analysis
from config import get_settings

logger = logging.getLogger(__name__)
router = APIRouter(prefix="/api/upload", tags=["upload"])

ALLOWED_EXTENSIONS = {".pdf", ".png", ".jpg", ".jpeg", ".tiff", ".bmp", ".webp"}


def get_file_extension(filename: str) -> str:
    return os.path.splitext(filename)[1].lower()


@router.post("")
async def upload_file(
    file: UploadFile = File(...),
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    """Upload a bank PDF, invoice, or receipt image for parsing."""
    settings = get_settings()

    ext = get_file_extension(file.filename or "")
    if ext not in ALLOWED_EXTENSIONS:
        raise HTTPException(400, f"Unsupported file type: {ext}. Allowed: {ALLOWED_EXTENSIONS}")

    # Save file temporarily
    os.makedirs(settings.UPLOAD_DIR, exist_ok=True)
    file_id = str(uuid.uuid4())
    file_path = os.path.join(settings.UPLOAD_DIR, f"{file_id}{ext}")

    try:
        content = await file.read()
        if len(content) > settings.MAX_UPLOAD_SIZE:
            raise HTTPException(413, "File too large")

        with open(file_path, "wb") as f:
            f.write(content)

        # Route to appropriate parser
        if ext == ".pdf":
            extracted = extract_transactions_from_pdf(file_path)
        else:
            extracted = extract_transactions_from_image(file_path)

        # Store in database
        stored = []
        for entry in extracted:
            tx = Transaction(
                user_id=current_user.id,
                date=entry.get("date") or datetime.now(),
                amount=entry.get("amount", 0),
                balance=entry.get("balance"),
                category=entry.get("category", "Other"),
                counterparty=entry.get("counterparty"),
                source=entry.get("source", "unknown"),
                confidence=entry.get("confidence", 0),
                needs_review=entry.get("confidence", 0) < 0.7,
                raw_text=entry.get("raw_text"),
            )
            db.add(tx)
            stored.append(tx)

        db.commit()

        # Auto-create a CashBalanceSnapshot from the last row's balance
        if stored:
            last_with_balance = None
            for tx in reversed(stored):
                if tx.balance is not None:
                    last_with_balance = tx
                    break
            if last_with_balance:
                from models.cash_balance import CashBalanceSnapshot
                snapshot = CashBalanceSnapshot(
                    user_id=current_user.id,
                    date=last_with_balance.date or datetime.now(),
                    balance=last_with_balance.balance,
                )
                db.add(snapshot)
                db.commit()

        # Trigger background analysis
        try:
            from tasks.analysis_tasks import celery_run_profiler_analysis
            celery_run_profiler_analysis.delay(current_user.id)
        except Exception:
            # Celery not available — run synchronously
            run_profiler_analysis(current_user.id)

        return {
            "file_id": file_id,
            "filename": file.filename,
            "transactions_extracted": len(stored),
            "transactions": [
                {
                    "id": tx.id,
                    "date": tx.date.isoformat() if tx.date else None,
                    "amount": tx.amount,
                    "category": tx.category,
                    "counterparty": tx.counterparty,
                    "confidence": tx.confidence,
                    "needs_review": tx.needs_review,
                }
                for tx in stored
            ],
        }

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Upload processing error: {e}")
        raise HTTPException(500, f"Error processing file: {str(e)}")
    finally:
        # Clean up
        if os.path.exists(file_path):
            os.remove(file_path)
