from pydantic import BaseModel
from typing import Optional
from schemas.affordability import AlternativePath, AffordabilityResponse

class AIActionEmailRequest(BaseModel):
    result: AffordabilityResponse
    path: AlternativePath
    recipient_type: str # 'landlord', 'vendor', 'lender'

class SendEmailRequest(BaseModel):
    recipient: str
    action_type: str
    email_content: str
