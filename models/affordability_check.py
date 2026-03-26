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
<<<<<<< HEAD
    recommended_date = Column(String(50), nullable=True)
    current_balance = Column(Float, nullable=True)
    projected_balance_at_date = Column(Float, nullable=True)
    monthly_burn_rate = Column(Float, nullable=True)
    ai_explanation = Column(Text, nullable=True)
=======
    claude_explanation = Column(Text, nullable=True)
>>>>>>> 8a260015108003b30586cdffc9a5d14ec1407d73
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
<<<<<<< HEAD
            "recommended_date": self.recommended_date,
            "current_balance": self.current_balance,
            "projected_balance_at_date": self.projected_balance_at_date,
            "monthly_burn_rate": self.monthly_burn_rate,
            "ai_explanation": self.ai_explanation,
=======
            "claude_explanation": self.claude_explanation,
>>>>>>> 8a260015108003b30586cdffc9a5d14ec1407d73
            "forecast_data": self.forecast_data,
            "alternative_paths": self.alternative_paths,
            "created_at": self.created_at.isoformat() if self.created_at else None,
        }
