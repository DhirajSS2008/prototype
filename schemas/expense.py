"""Pydantic schemas for expense input."""

from pydantic import BaseModel, Field
from datetime import datetime


CATEGORIES = [
    "Health & Medical",
    "Legal & Compliance",
    "Critical Operations",
    "Tax & Government",
    "Equipment & Tools",
    "Travel & Transport",
    "Vendor Advances",
    "Marketing",
    "Rent & Lease",
    "Loan EMI",
    "Supplier Payments",
    "Office Supplies",
    "Subscriptions",
    "Upgrades",
    "Discretionary",
    "Entertainment",
    "Other",
]


class ExpenseInput(BaseModel):
    name: str = Field(..., min_length=1, max_length=255)
    amount: float = Field(..., gt=0, description="Expense amount (positive)")
    date: datetime
    category: str = Field(..., description="Expense category")

    class Config:
        json_schema_extra = {
            "example": {
                "name": "New laptop for design team",
                "amount": 1500.00,
                "date": "2026-04-01T00:00:00",
                "category": "Equipment & Tools",
            }
        }
