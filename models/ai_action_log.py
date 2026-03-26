from sqlalchemy import Column, Integer, String, Text, DateTime, ForeignKey
from sqlalchemy.sql import func
from database import Base

class AIActionLog(Base):
    __tablename__ = "ai_action_logs"

    id = Column(Integer, primary_key=True, autoincrement=True)
    user_id = Column(Integer, ForeignKey("users.id"), nullable=False, index=True)
    recipient = Column(String(255), nullable=False)
    action_type = Column(String(50), nullable=False) # 'defer_obligation' or 'short_term_borrowing'
    email_content = Column(Text, nullable=False)
    timestamp = Column(DateTime, server_default=func.now())

    def to_dict(self):
        return {
            "id": self.id,
            "user_id": self.user_id,
            "recipient": self.recipient,
            "action_type": self.action_type,
            "email_content": self.email_content,
            "timestamp": self.timestamp.isoformat() if self.timestamp else None,
        }
