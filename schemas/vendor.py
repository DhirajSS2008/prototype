"""Pydantic schemas for vendor contacts."""

from pydantic import BaseModel, Field
from typing import Optional


RELATIONSHIP_TYPES = [
    "local_vendor", "bank", "supplier", "landlord", "tax_authority",
]


class VendorContactCreate(BaseModel):
    vendor_name: str = Field(..., min_length=1, max_length=255)
    email: Optional[str] = None
    relationship_type: str = Field(..., description="Relationship type with this contact")
    contact_person: Optional[str] = None
    outstanding_amount: float = Field(default=0.0, ge=0)
    notes: Optional[str] = None


class VendorContactUpdate(BaseModel):
    vendor_name: Optional[str] = None
    email: Optional[str] = None
    relationship_type: Optional[str] = None
    contact_person: Optional[str] = None
    outstanding_amount: Optional[float] = None
    notes: Optional[str] = None


class VendorContactResponse(BaseModel):
    id: int
    vendor_name: str
    email: Optional[str]
    relationship_type: str
    contact_person: Optional[str]
    outstanding_amount: float
    notes: Optional[str]
    created_at: Optional[str]
    updated_at: Optional[str]

    class Config:
        from_attributes = True
