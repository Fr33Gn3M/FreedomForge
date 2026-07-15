# models.py
from pydantic import BaseModel


class LoginRequest(BaseModel):
    username: str
    password: str


class UserCreate(BaseModel):
    username: str
    password: str
    email: str


class UserInfo(BaseModel):
    username: str
    email: str
    roles: list[str] = []
    nickname: str = ""
    avatar: str = ""


class Token(BaseModel):
    access_token: str
    token_type: str


class AccessCodesResponse(BaseModel):
    codes: list[str]
