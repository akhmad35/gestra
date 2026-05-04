from pydantic import BaseModel, EmailStr, Field
from typing import Optional

class UserBase(BaseModel):
    nama: str = Field(min_length=2, max_length=100)
    email: EmailStr

class UserCreate(UserBase):
    password: str = Field(min_length=6, max_length=128)

class UserLogin(BaseModel):
    email: EmailStr
    password: str = Field(min_length=6, max_length=128)

class UserUpdateRole(BaseModel):
    role: str = Field(pattern="^(murid|guru)$")

class UserResponse(UserBase):
    id: int
    role: str

    class Config:
        from_attributes = True
