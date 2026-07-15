# main.py
from fastapi import FastAPI, Depends, HTTPException, status
from fastapi.middleware.cors import CORSMiddleware
from fastapi.security import OAuth2PasswordBearer
from jose import JWTError, jwt
from passlib.context import CryptContext
from datetime import datetime, timedelta
from typing import Optional

from common.response import ResponseModel
from database import (
    init_db,
    get_user_by_username,
    create_user,
    update_user_role,
    get_access_codes,
)
from common.models import (
    LoginRequest,
    UserCreate,
    Token,
    UserInfo,
    AccessCodesResponse,
)

# 初始化数据库
init_db()

# 安全配置
SECRET_KEY = "your-secret-key-change-in-production"  # 生产环境务必更换！
ALGORITHM = "HS256"
ACCESS_TOKEN_EXPIRE_MINUTES = 30

pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")

app = FastAPI(title="FreedomForge API")

# 允许前端跨域（开发用）
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


# ========== 工具函数 ==========

def verify_password(plain_password, hashed_password):
    return pwd_context.verify(plain_password, hashed_password)


def get_password_hash(password: str) -> str:
    return pwd_context.hash(password)


def create_access_token(data: dict, expires_delta: Optional[timedelta] = None):
    to_encode = data.copy()
    expire = datetime.utcnow() + (expires_delta or timedelta(minutes=15))
    to_encode.update({"exp": expire})
    return jwt.encode(to_encode, SECRET_KEY, algorithm=ALGORITHM)


def authenticate_user(username: str, password: str):
    user = get_user_by_username(username)
    if not user or not verify_password(password, user["hashed_password"]):
        return False
    return user


# ========== OAuth2 方案 ==========

oauth2_scheme = OAuth2PasswordBearer(tokenUrl="/api/token")


def get_current_user(token: str = Depends(oauth2_scheme)):
    """从 Bearer Token 中解析并验证用户"""
    credentials_exception = HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail="无法验证凭据",
        headers={"WWW-Authenticate": "Bearer"},
    )
    try:
        payload = jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])
        username: str = payload.get("sub")
        if username is None:
            raise credentials_exception
    except JWTError:
        raise credentials_exception

    user = get_user_by_username(username)
    if user is None:
        raise credentials_exception
    return user


# ========== 路由 ==========

@app.post("/api/register", summary="用户注册")
def register(user: UserCreate):
    hashed_pw = get_password_hash(user.password)
    created = create_user(
        username=user.username,
        hashed_password=hashed_pw,
        email=user.email,
        role="user",  # 新注册用户默认为普通用户
    )
    if not created:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="用户名已存在",
        )
    return ResponseModel(
        code=200,
        message="用户注册成功",
        data={"username": user.username},
    )


@app.post("/api/token", response_model=ResponseModel, summary="用户登录（获取 token）")
def login(login_data: LoginRequest):
    user = authenticate_user(login_data.username, login_data.password)
    if not user:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="用户名或密码错误",
            headers={"WWW-Authenticate": "Bearer"},
        )
    access_token_expires = timedelta(minutes=ACCESS_TOKEN_EXPIRE_MINUTES)
    access_token = create_access_token(
        data={"sub": user["username"]},
        expires_delta=access_token_expires,
    )
    return ResponseModel(
        code=200,
        message="登录成功",
        data=Token(
            access_token=access_token,
            token_type="bearer",
        ),
    )


@app.get("/api/users/me", summary="获取当前用户信息（需登录）")
def read_users_me(current_user: dict = Depends(get_current_user)):
    return ResponseModel(
        code=200,
        message="获取用户信息成功",
        data=UserInfo(
            username=current_user["username"],
            email=current_user["email"],
            roles=[current_user.get("role", "user")],
            nickname=current_user.get("nickname", current_user["username"]),
            avatar=current_user.get("avatar", ""),
        ),
    )


@app.get("/api/auth/codes", summary="获取当前用户权限码（需登录）")
def get_user_codes(current_user: dict = Depends(get_current_user)):
    codes = get_access_codes(current_user["username"])
    return ResponseModel(
        code=200,
        message="获取权限码成功",
        data=AccessCodesResponse(codes=codes),
    )


@app.post("/api/auth/logout", summary="用户登出")
def logout(current_user: dict = Depends(get_current_user)):
    # JWT 无状态，客户端删除 token 即登出
    # 后续可加入 token 黑名单机制
    return ResponseModel(
        code=200,
        message="登出成功",
        data="SUCCESS",
    )
