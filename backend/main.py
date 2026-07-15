# main.py
from fastapi import FastAPI, Depends, HTTPException, status, Query
from fastapi.middleware.cors import CORSMiddleware
from fastapi.security import OAuth2PasswordBearer
from jose import JWTError, jwt
from passlib.context import CryptContext
from datetime import datetime, timedelta
from typing import Optional

from common.response import ResponseModel
from common.models import (
    LoginRequest, UserCreate, Token, UserInfo, AccessCodesResponse,
    UserUpdateRequest, RoleCreate, RoleUpdate, RoleMenuAssign,
    MenuCreate, MenuUpdate,
)
from database import (
    init_db,
    get_user_by_username, create_user, get_users, update_user, delete_user,
    get_roles, get_all_roles, get_role, create_role, update_role, delete_role,
    get_role_menu_ids, set_role_menus,
    get_menus, get_menu, create_menu, update_menu, delete_menu,
    get_access_codes, get_user_menus,
)

# 初始化数据库
init_db()

# 安全配置
SECRET_KEY = "your-secret-key-change-in-production"
ALGORITHM = "HS256"
ACCESS_TOKEN_EXPIRE_MINUTES = 30

pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")

app = FastAPI(title="FreedomForge API")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

oauth2_scheme = OAuth2PasswordBearer(tokenUrl="/api/token")


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


def get_current_user(token: str = Depends(oauth2_scheme)):
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


# ========== 认证路由 ==========

@app.post("/api/register", summary="用户注册")
def register(user: UserCreate):
    hashed_pw = get_password_hash(user.password)
    created = create_user(username=user.username, hashed_password=hashed_pw, email=user.email)
    if not created:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="用户名已存在")
    return ResponseModel(code=200, message="用户注册成功", data={"username": user.username})


@app.post("/api/token", response_model=ResponseModel, summary="用户登录")
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
        code=200, message="登录成功",
        data={"access_token": access_token, "token_type": "bearer"},
    )


@app.get("/api/users/me", summary="获取当前用户信息")
def read_users_me(current_user: dict = Depends(get_current_user)):
    return ResponseModel(
        code=200, message="获取用户信息成功",
        data=UserInfo(
            username=current_user["username"],
            email=current_user["email"],
            roles=[current_user.get("role", "user")],
            nickname=current_user.get("nickname", current_user["username"]),
            avatar=current_user.get("avatar", ""),
        ),
    )


@app.get("/api/auth/codes", summary="获取当前用户权限码")
def get_user_codes(current_user: dict = Depends(get_current_user)):
    codes = get_access_codes(current_user["username"])
    return ResponseModel(code=200, message="获取权限码成功", data={"codes": codes})


@app.post("/api/auth/logout", summary="用户登出")
def logout(current_user: dict = Depends(get_current_user)):
    return ResponseModel(code=200, message="登出成功", data="SUCCESS")


# ========== 菜单路由（鉴权后的动态菜单）==========

@app.get("/api/menu/all", summary="获取当前用户可访问的菜单树")
def get_my_menus(current_user: dict = Depends(get_current_user)):
    menus = get_user_menus(current_user["username"])
    return ResponseModel(code=200, message="获取菜单成功", data=menus)


# ========== 用户管理 ==========

@app.get("/api/system/user/list", summary="用户列表")
def user_list(
    page: int = Query(1, ge=1),
    page_size: int = Query(10, ge=1, le=100),
    keyword: str = Query(""),
    current_user: dict = Depends(get_current_user),
):
    return ResponseModel(code=200, message="成功", data=get_users(page, page_size, keyword))


@app.put("/api/system/user/{user_id}", summary="编辑用户")
def user_update(user_id: int, req: UserUpdateRequest, current_user: dict = Depends(get_current_user)):
    kwargs = {k: v for k, v in req.model_dump().items() if v is not None}
    if not kwargs:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="无更新数据")
    update_user(user_id, **kwargs)
    return ResponseModel(code=200, message="更新成功", data=None)


@app.delete("/api/system/user/{user_id}", summary="删除用户")
def user_delete(user_id: int, current_user: dict = Depends(get_current_user)):
    delete_user(user_id)
    return ResponseModel(code=200, message="删除成功", data=None)


# ========== 角色管理 ==========

@app.get("/api/system/role/list", summary="角色列表")
def role_list(current_user: dict = Depends(get_current_user)):
    return ResponseModel(code=200, message="成功", data=get_roles())


@app.get("/api/system/role/all", summary="所有角色（下拉用）")
def role_all(current_user: dict = Depends(get_current_user)):
    return ResponseModel(code=200, message="成功", data=get_all_roles())


@app.post("/api/system/role", summary="新增角色")
def role_create(req: RoleCreate, current_user: dict = Depends(get_current_user)):
    ok = create_role(req.name, req.code, req.description)
    if not ok:
        raise HTTPException(status_code=400, detail="角色编码已存在")
    return ResponseModel(code=200, message="创建成功", data=None)


@app.get("/api/system/role/{role_id}", summary="角色详情")
def role_detail(role_id: int, current_user: dict = Depends(get_current_user)):
    r = get_role(role_id)
    if not r:
        raise HTTPException(status_code=404, detail="角色不存在")
    return ResponseModel(code=200, message="成功", data=r)


@app.put("/api/system/role/{role_id}", summary="编辑角色")
def role_update(role_id: int, req: RoleUpdate, current_user: dict = Depends(get_current_user)):
    kwargs = {k: v for k, v in req.model_dump().items() if v is not None}
    update_role(role_id, **kwargs)
    return ResponseModel(code=200, message="更新成功", data=None)


@app.delete("/api/system/role/{role_id}", summary="删除角色")
def role_delete(role_id: int, current_user: dict = Depends(get_current_user)):
    delete_role(role_id)
    return ResponseModel(code=200, message="删除成功", data=None)


@app.get("/api/system/role/{role_id}/menus", summary="获取角色菜单权限")
def role_menus_get(role_id: int, current_user: dict = Depends(get_current_user)):
    return ResponseModel(code=200, message="成功", data=get_role_menu_ids(role_id))


@app.put("/api/system/role/{role_id}/menus", summary="设置角色菜单权限")
def role_menus_set(role_id: int, req: RoleMenuAssign, current_user: dict = Depends(get_current_user)):
    set_role_menus(role_id, req.menu_ids)
    return ResponseModel(code=200, message="权限分配成功", data=None)


# ========== 菜单管理 ==========

@app.get("/api/system/menu/list", summary="菜单列表")
def menu_list(current_user: dict = Depends(get_current_user)):
    return ResponseModel(code=200, message="成功", data=get_menus())


@app.post("/api/system/menu", summary="新增菜单")
def menu_create(req: MenuCreate, current_user: dict = Depends(get_current_user)):
    create_menu(**req.model_dump())
    return ResponseModel(code=200, message="创建成功", data=None)


@app.get("/api/system/menu/{menu_id}", summary="菜单详情")
def menu_detail(menu_id: int, current_user: dict = Depends(get_current_user)):
    m = get_menu(menu_id)
    if not m:
        raise HTTPException(status_code=404, detail="菜单不存在")
    return ResponseModel(code=200, message="成功", data=m)


@app.put("/api/system/menu/{menu_id}", summary="编辑菜单")
def menu_update(menu_id: int, req: MenuUpdate, current_user: dict = Depends(get_current_user)):
    kwargs = {k: v for k, v in req.model_dump().items() if v is not None}
    update_menu(menu_id, **kwargs)
    return ResponseModel(code=200, message="更新成功", data=None)


@app.delete("/api/system/menu/{menu_id}", summary="删除菜单")
def menu_delete(menu_id: int, current_user: dict = Depends(get_current_user)):
    delete_menu(menu_id)
    return ResponseModel(code=200, message="删除成功", data=None)
