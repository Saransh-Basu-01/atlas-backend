from pydantic import BaseModel,ConfigDict,Field,EmailStr
from datetime import datetime

class UserBase(BaseModel):
    username:str=Field(min_length=1,max_length=50)
    email:EmailStr=Field(max_length=120)

class UserCreate(UserBase):
    password:str=Field(min_length=8)

class UserLogin(BaseModel):
    email: EmailStr
    password: str

class UserResponse(UserBase):
    model_config = ConfigDict(from_attributes=True)

    id: int


class UserUpdate(BaseModel):
    username:str|None=Field(default=None,min_length=1,max_length=50)
    email:EmailStr|None=Field(default=None,max_length=120)

class TokenResponse(BaseModel):
    access_token: str
    refresh_token: str
    token_type: str = "bearer"

class TokenPayload(BaseModel):
    sub: str
    exp: int

class RefreshTokenRequest(BaseModel):
    refresh_token: str