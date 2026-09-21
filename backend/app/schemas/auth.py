from pydantic import BaseModel, EmailStr, Field

class LoginRequest(BaseModel):
    email: EmailStr
    password: str = Field(min_length=12)

class TokenResponse(BaseModel):
    access_token: str
    token_type: str = "bearer"
    expires_in: int

class UserCreate(BaseModel):
    nombres: str
    apellidos: str
    email: EmailStr
    password: str = Field(min_length=12)
    role_code: str

class UserRead(BaseModel):
    id: int
    nombres: str
    apellidos: str
    email: EmailStr
    rol: str
    activo: bool
