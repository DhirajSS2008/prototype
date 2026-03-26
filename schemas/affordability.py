"""Pydantic schemas for affordability engine response."""

from pydantic import BaseModel
from typing import Optional
from datetime import datetime


class AlternativePath(BaseModel):
    path_type: str  # 'defer_obligation' or 'short_term_borrowing'
    description: str
    obligation_name: Optional[str] = None
    deferral_days: Optional[int] = None
    penalty_cost: Optional[float] = None
    borrowing_amount: Optional[float] = None
    borrowing_source: Optional[str] = None
    borrowing_cost: Optional[float] = None
    cost_of_missing: Optional[float] = None


class ForecastPoint(BaseModel):
    date: str
    projected_balance: float
<<<<<<< HEAD
    confidence_upper: Optional[float] = None
    confidence_lower: Optional[float] = None
=======
>>>>>>> 8a260015108003b30586cdffc9a5d14ec1407d73
    has_obligation: bool = False
    obligation_name: Optional[str] = None
    obligation_amount: Optional[float] = None


class AffordabilityResponse(BaseModel):
    decision: str  # APPROVE, DEFER, CRITICAL
    priority_tier: str  # HIGH, MID, LOW
    reason_code: str
    expense_name: str
    expense_amount: float
    expense_category: str
    current_balance: float
    projected_balance_at_date: float
    monthly_burn_rate: float
    deferral_days: Optional[int] = None
    recommended_date: Optional[str] = None
    forecast_data: list[ForecastPoint] = []
    alternative_paths: list[AlternativePath] = []
<<<<<<< HEAD
    ai_explanation: Optional[str] = None
    negotiation_email: Optional[dict] = None  # {subject, body}
=======
    claude_explanation: Optional[str] = None
    negotiation_email: Optional[str] = None
>>>>>>> 8a260015108003b30586cdffc9a5d14ec1407d73
    created_at: Optional[datetime] = None

    class Config:
        json_schema_extra = {
            "example": {
                "decision": "DEFER",
                "priority_tier": "MID",
                "reason_code": "LIQUIDITY_TIGHT",
                "expense_name": "New laptop",
                "expense_amount": 1500.0,
                "expense_category": "Equipment & Tools",
                "current_balance": 5000.0,
                "projected_balance_at_date": 2300.0,
                "monthly_burn_rate": 8500.0,
                "deferral_days": 12,
                "recommended_date": "2026-04-12",
            }
        }
