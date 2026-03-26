"""Pydantic schemas for email drafts."""

from pydantic import BaseModel, Field
from typing import Optional


class EmailDraftCreate(BaseModel):
    recipient_email: str = Field(..., min_length=1)
    recipient_name: Optional[str] = None
    relationship_type: Optional[str] = None
    subject: str = Field(..., min_length=1)
    body: str = Field(..., min_length=1)
    affordability_check_id: Optional[int] = None


class EmailDraftResponse(BaseModel):
    id: int
    recipient_email: str
    recipient_name: Optional[str]
    relationship_type: Optional[str]
    subject: str
    body: str
    status: str
    affordability_check_id: Optional[int]
    sent_at: Optional[str]
    created_at: Optional[str]

    class Config:
        from_attributes = True


class EmailSendRequest(BaseModel):
    """Request to send a composed email via the backend."""
    recipient_email: str
    recipient_name: Optional[str] = None
    relationship_type: Optional[str] = None
    subject: str
    body: str
    action_type: Optional[str] = None  # defer_obligation, short_term_borrowing
    affordability_check_id: Optional[int] = None
