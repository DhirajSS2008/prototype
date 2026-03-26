"""Transaction ORM model."""

from sqlalchemy import Column, Integer, String, Float, Boolean, DateTime, Text, ForeignKey
from sqlalchemy.sql import func
from database import Base


class Transaction(Base):
    __tablename__ = "transactions"

    id = Column(Integer, primary_key=True, autoincrement=True)
    user_id = Column(Integer, ForeignKey("users.id"), nullable=False, index=True)
    date = Column(DateTime, nullable=False)
    amount = Column(Float, nullable=False)
    balance = Column(Float, nullable=True)  # Running balance from bank statement
    category = Column(String(100), nullable=False, index=True)
    counterparty = Column(String(255), nullable=True)
    is_recurring = Column(Boolean, default=False)
    source = Column(String(50), nullable=False)  # 'pdf', 'ocr', 'manual'
    confidence = Column(Float, default=1.0)  # 0.0 to 1.0
    needs_review = Column(Boolean, default=False)
    raw_text = Column(Text, nullable=True)
    created_at = Column(DateTime, server_default=func.now())
    updated_at = Column(DateTime, server_default=func.now(), onupdate=func.now())

    def to_dict(self):
        return {
            "id": self.id,
            "date": self.date.isoformat() if self.date else None,
            "amount": self.amount,
            "balance": self.balance,
            "category": self.category,
            "counterparty": self.counterparty,
            "is_recurring": self.is_recurring,
            "source": self.source,
            "confidence": self.confidence,
            "needs_review": self.needs_review,
            "created_at": self.created_at.isoformat() if self.created_at else None,
        }
