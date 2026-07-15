# database.py
import sqlite3
from pathlib import Path

DB_PATH = Path("data/users.db")


def init_db():
    """初始化数据库，创建 users 表（兼容旧表迁移）"""
    DB_PATH.parent.mkdir(exist_ok=True)
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()

    # 先创建基础表
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS users (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            username TEXT UNIQUE NOT NULL,
            hashed_password TEXT NOT NULL,
            email TEXT NOT NULL
        )
    """)

    # 兼容已有表：尝试新增列
    for col, col_def in [
        ("role", "TEXT NOT NULL DEFAULT 'user'"),
        ("nickname", "TEXT"),
        ("avatar", "TEXT"),
    ]:
        try:
            cursor.execute(f"ALTER TABLE users ADD COLUMN {col} {col_def}")
        except sqlite3.OperationalError:
            pass  # 列已存在，跳过

    conn.commit()
    conn.close()


def get_user_by_username(username: str):
    """根据用户名查询用户"""
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    cursor.execute(
        "SELECT id, username, hashed_password, email, role, nickname, avatar "
        "FROM users WHERE username = ?",
        (username,),
    )
    row = cursor.fetchone()
    conn.close()
    if row:
        return {
            "id": row[0],
            "username": row[1],
            "hashed_password": row[2],
            "email": row[3],
            "role": row[4] or "user",
            "nickname": row[5] or "",
            "avatar": row[6] or "",
        }
    return None


def create_user(username: str, hashed_password: str, email: str, role: str = "user"):
    """创建新用户"""
    try:
        conn = sqlite3.connect(DB_PATH)
        cursor = conn.cursor()
        cursor.execute(
            "INSERT INTO users (username, hashed_password, email, role, nickname) "
            "VALUES (?, ?, ?, ?, ?)",
            (username, hashed_password, email, role, username),
        )
        conn.commit()
        conn.close()
        return True
    except sqlite3.IntegrityError:
        return False  # 用户名已存在


def update_user_role(username: str, role: str):
    """更新用户角色"""
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    cursor.execute("UPDATE users SET role = ? WHERE username = ?", (role, username))
    conn.commit()
    conn.close()


# 角色 → 权限码映射
ROLE_ACCESS_CODES = {
    "super": ["*"],  # 全部权限
    "admin": [
        "dashboard:view",
        "system:view",
        "system:user:view",
        "system:user:edit",
        "system:role:view",
    ],
    "user": ["dashboard:view"],
}


def get_access_codes(username: str):
    """根据用户名获取权限码列表"""
    user = get_user_by_username(username)
    if not user:
        return []
    role = user.get("role", "user")
    return ROLE_ACCESS_CODES.get(role, ROLE_ACCESS_CODES["user"])
