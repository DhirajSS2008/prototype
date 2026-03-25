"""Pydantic schemas for transactions."""

from pydantic import BaseModel, Field
from datetime import datetime
from typing import Optional


class TransactionBase(BaseModel):
    date: datetime
    amount: float = Field(..., description="Transaction amount (positive=income, negative=expense)")
    category: str = Field(..., max_length=100)
    counterparty: Optional[str] = None
    source: str = Field(..., description="Source: pdf, ocr, manual")


class TransactionCreate(TransactionBase):
    balance: Optional[float] = None
    is_recurring: bool = False
    confidence: float = Field(default=1.0, ge=0.0, le=1.0)
    needs_review: bool = False
    raw_text: Optional[str] = None


class TransactionResponse(TransactionBase):
    id: int
    balance: Optional[float] = None
    is_recurring: bool
    confidence: float
    needs_review: bool
    created_at: datetime

    class Config:
        from_attributes = True


class TransactionBulkCreate(BaseModel):
    transactions: list[TransactionCreate]


class ExtractedTransaction(BaseModel):
    """A transaction extracted from a document before DB insertion."""
    date: Optional[datetime] = None
    amount: Optional[float] = None
    category: str = "Other"
    counterparty: Optional[str] = None
    confidence: float = 0.0
    raw_text: Optional[str] = None
