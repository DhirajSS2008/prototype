"""Vendor/Bank contact ORM model."""

from sqlalchemy import Column, Integer, String, Float, DateTime, Text, ForeignKey
from sqlalchemy.sql import func
from database import Base


class VendorContact(Base):
    __tablename__ = "vendor_contacts"

    id = Column(Integer, primary_key=True, autoincrement=True)
    user_id = Column(Integer, ForeignKey("users.id"), nullable=False, index=True)
    vendor_name = Column(String(255), nullable=False)
    email = Column(String(255), nullable=True)
    relationship_type = Column(String(50), nullable=False)  # local_vendor, bank, supplier, landlord, tax_authority
    contact_person = Column(String(255), nullable=True)
    outstanding_amount = Column(Float, default=0.0)
    notes = Column(Text, nullable=True)
    created_at = Column(DateTime, server_default=func.now())
    updated_at = Column(DateTime, server_default=func.now(), onupdate=func.now())

    def to_dict(self):
        return {
            "id": self.id,
            "user_id": self.user_id,
            "vendor_name": self.vendor_name,
            "email": self.email,
            "relationship_type": self.relationship_type,
            "contact_person": self.contact_person,
            "outstanding_amount": self.outstanding_amount,
            "notes": self.notes,
            "created_at": self.created_at.isoformat() if self.created_at else None,
            "updated_at": self.updated_at.isoformat() if self.updated_at else None,
        }
