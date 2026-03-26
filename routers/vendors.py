"""Vendor contacts management API endpoints."""

import logging
from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

from database import get_db
from models.user import User
from models.vendor_contact import VendorContact
from schemas.vendor import VendorContactCreate, VendorContactUpdate
from services.auth_service import get_current_user
from services.email_service import send_email
from services.gemini_service import generate_reminder_email

logger = logging.getLogger(__name__)
router = APIRouter(prefix="/api/vendors", tags=["vendors"])


@router.get("")
def list_vendors(
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    """List all vendor contacts for current user."""
    vendors = (
        db.query(VendorContact)
        .filter(VendorContact.user_id == current_user.id)
        .order_by(VendorContact.vendor_name)
        .all()
    )
    return {"vendors": [v.to_dict() for v in vendors]}


@router.get("/{vendor_id}")
def get_vendor(
    vendor_id: int,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    """Get a single vendor contact."""
    vendor = (
        db.query(VendorContact)
        .filter(VendorContact.id == vendor_id, VendorContact.user_id == current_user.id)
        .first()
    )
    if not vendor:
        raise HTTPException(404, "Vendor not found")
    return vendor.to_dict()


@router.post("")
def create_vendor(
    data: VendorContactCreate,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    """Create a new vendor contact."""
    vendor = VendorContact(
        user_id=current_user.id,
        vendor_name=data.vendor_name,
        email=data.email,
        relationship_type=data.relationship_type,
        contact_person=data.contact_person,
        outstanding_amount=data.outstanding_amount,
        notes=data.notes,
    )
    db.add(vendor)
    db.commit()
    db.refresh(vendor)
    return vendor.to_dict()


@router.put("/{vendor_id}")
def update_vendor(
    vendor_id: int,
    data: VendorContactUpdate,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    """Update an existing vendor contact."""
    vendor = (
        db.query(VendorContact)
        .filter(VendorContact.id == vendor_id, VendorContact.user_id == current_user.id)
        .first()
    )
    if not vendor:
        raise HTTPException(404, "Vendor not found")

    update_data = data.model_dump(exclude_unset=True)
    for key, value in update_data.items():
        setattr(vendor, key, value)

    db.commit()
    db.refresh(vendor)
    return vendor.to_dict()


@router.delete("/{vendor_id}")
def delete_vendor(
    vendor_id: int,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    """Delete a vendor contact."""
    vendor = (
        db.query(VendorContact)
        .filter(VendorContact.id == vendor_id, VendorContact.user_id == current_user.id)
        .first()
    )
    if not vendor:
        raise HTTPException(404, "Vendor not found")

    db.delete(vendor)
    db.commit()
    return {"status": "deleted"}


@router.post("/{vendor_id}/send-reminder")
async def send_vendor_reminder(
    vendor_id: int,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    """Send a reminder email to a vendor about outstanding balance."""
    vendor = (
        db.query(VendorContact)
        .filter(VendorContact.id == vendor_id, VendorContact.user_id == current_user.id)
        .first()
    )
    if not vendor:
        raise HTTPException(404, "Vendor not found")

    if not vendor.email:
        raise HTTPException(400, "Vendor has no email address configured")

    # Generate automated subject and body using Gemini
    email_data = await generate_reminder_email(
        vendor_name=vendor.vendor_name,
        outstanding_amount=vendor.outstanding_amount,
        contact_person=vendor.contact_person,
        business_name="LiquiSense"
    )

    success = await send_email(
        to_email=vendor.email, 
        subject=email_data["subject"], 
        body=email_data["body"]
    )

    if success:
        return {"status": "success", "message": f"Reminder sent to {vendor.email} with automated subject"}
    else:
        raise HTTPException(500, "Failed to send email via Resend/SMTP")
