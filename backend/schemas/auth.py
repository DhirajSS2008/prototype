"""Pydantic schemas for authentication."""

from pydantic import BaseModel, Field, EmailStr
from datetime import datetime
from typing import Optional


class SignUpRequest(BaseModel):
    email: str = Field(..., min_length=5, max_length=255)
    password: str = Field(..., min_length=6, max_length=128)
    confirm_password: str = Field(..., min_length=6, max_length=128)


class SignInRequest(BaseModel):
    email: str = Field(..., min_length=5, max_length=255)
    password: str = Field(..., min_length=6, max_length=128)


class TokenResponse(BaseModel):
    access_token: str
    token_type: str = "bearer"
    user: "UserResponse"


class UserResponse(BaseModel):
    id: int
    email: str
    created_at: Optional[datetime] = None

    class Config:
        from_attributes = True
