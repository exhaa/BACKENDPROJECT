from pydantic import BaseModel, EmailStr, Field


class UserIdSchema(BaseModel):
    id: int

class RegisterSchema(BaseModel):
    name: str = Field(..., min_length=2)
    email: EmailStr
    password: str = Field(..., min_length=8)