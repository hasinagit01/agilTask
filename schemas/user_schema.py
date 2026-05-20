from datetime import datetime
from typing import Optional

from pydantic import BaseModel, ConfigDict, EmailStr, Field


class RegisterRequest(BaseModel):
    email: EmailStr
    password: str = Field(min_length=8)
    firstname: Optional[str] = None
    name: Optional[str] = None


class LoginRequest(BaseModel):
    email: EmailStr
    password: str


class TokenResponse(BaseModel):
    data: "TokenData"


class TokenData(BaseModel):
    access_token: str
    token_type: str = "bearer"
    expires_in_minutes: int


TokenResponse.model_rebuild()


class UserResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    email: str
    firstname: Optional[str] = None
    name: Optional[str] = None
    created_at: datetime


class SingleUserResponse(BaseModel):
    data: UserResponse


class UpdateEmailRequest(BaseModel):
    email: EmailStr


class UpdateProfileRequest(BaseModel):
    firstname: Optional[str] = None
    name: Optional[str] = None


class UpdatePasswordRequest(BaseModel):
    current_password: str
    new_password: str = Field(min_length=8)


class DeleteAccountRequest(BaseModel):
    password: str
