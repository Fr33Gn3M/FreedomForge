# models.py
from pydantic import BaseModel, Field
from typing import Optional


# ========== 认证 ==========

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


# ========== 用户管理 ==========

class UserUpdateRequest(BaseModel):
    email: Optional[str] = None
    nickname: Optional[str] = None
    role_id: Optional[int] = None


# ========== 角色管理 ==========

class RoleCreate(BaseModel):
    name: str
    code: str
    description: str = ""


class RoleUpdate(BaseModel):
    name: Optional[str] = None
    code: Optional[str] = None
    description: Optional[str] = None
    status: Optional[int] = None


class RoleMenuAssign(BaseModel):
    menu_ids: list[int] = []


# ========== 菜单管理 ==========

class MenuCreate(BaseModel):
    parent_id: int = 0
    name: str
    path: str = ""
    component: str = ""
    icon: str = ""
    type: str = "menu"          # dir / menu / button
    permission_code: str = ""
    sort: int = 0
    status: int = 1


class MenuUpdate(BaseModel):
    parent_id: Optional[int] = None
    name: Optional[str] = None
    path: Optional[str] = None
    component: Optional[str] = None
    icon: Optional[str] = None
    type: Optional[str] = None
    permission_code: Optional[str] = None
    sort: Optional[int] = None
    status: Optional[int] = None
