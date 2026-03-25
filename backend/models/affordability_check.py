"""Affordability check history model."""

from sqlalchemy import Column, Integer, String, Float, DateTime, Text, JSON, ForeignKey
from sqlalchemy.sql import func
from database import Base


class AffordabilityCheck(Base):
    __tablename__ = "affordability_checks"

    id = Column(Integer, primary_key=True, autoincrement=True)
    user_id = Column(Integer, ForeignKey("users.id"), nullable=False, index=True)
    expense_name = Column(String(255), nullable=False)
    expense_amount = Column(Float, nullable=False)
    expense_category = Column(String(100), nullable=False)
    expense_date = Column(DateTime, nullable=False)
    decision = Column(String(20), nullable=False)  # APPROVE, DEFER, CRITICAL
    priority_tier = Column(String(10), nullable=False)
    reason_code = Column(String(100), nullable=True)
    deferral_days = Column(Integer, nullable=True)
    claude_explanation = Column(Text, nullable=True)
    forecast_data = Column(JSON, nullable=True)
    alternative_paths = Column(JSON, nullable=True)
    created_at = Column(DateTime, server_default=func.now())

    def to_dict(self):
        return {
            "id": self.id,
            "expense_name": self.expense_name,
            "expense_amount": self.expense_amount,
            "expense_category": self.expense_category,
            "expense_date": self.expense_date.isoformat() if self.expense_date else None,
            "decision": self.decision,
            "priority_tier": self.priority_tier,
            "reason_code": self.reason_code,
            "deferral_days": self.deferral_days,
            "claude_explanation": self.claude_explanation,
            "forecast_data": self.forecast_data,
            "alternative_paths": self.alternative_paths,
            "created_at": self.created_at.isoformat() if self.created_at else None,
        }
