"""Email draft ORM model for audit and tracking."""

from sqlalchemy import Column, Integer, String, Text, DateTime, ForeignKey
from sqlalchemy.sql import func
from database import Base


class EmailDraft(Base):
    __tablename__ = "email_drafts"

    id = Column(Integer, primary_key=True, autoincrement=True)
    user_id = Column(Integer, ForeignKey("users.id"), nullable=False, index=True)
    recipient_email = Column(String(255), nullable=False)
    recipient_name = Column(String(255), nullable=True)
    relationship_type = Column(String(50), nullable=True)  # local_vendor, bank, supplier, landlord, tax_authority
    subject = Column(String(500), nullable=False)
    body = Column(Text, nullable=False)
    status = Column(String(20), nullable=False, default="draft")  # draft, sent, failed
    affordability_check_id = Column(Integer, ForeignKey("affordability_checks.id"), nullable=True)
    sent_at = Column(DateTime, nullable=True)
    created_at = Column(DateTime, server_default=func.now())

    def to_dict(self):
        return {
            "id": self.id,
            "user_id": self.user_id,
            "recipient_email": self.recipient_email,
            "recipient_name": self.recipient_name,
            "relationship_type": self.relationship_type,
            "subject": self.subject,
            "body": self.body,
            "status": self.status,
            "affordability_check_id": self.affordability_check_id,
            "sent_at": self.sent_at.isoformat() if self.sent_at else None,
            "created_at": self.created_at.isoformat() if self.created_at else None,
        }
