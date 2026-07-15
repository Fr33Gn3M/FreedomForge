# database.py
import sqlite3
from pathlib import Path

DB_PATH = Path("data/users.db")


def get_conn():
    DB_PATH.parent.mkdir(exist_ok=True)
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    conn.execute("PRAGMA foreign_keys = ON")
    return conn


# ==================== 初始化 ====================

def init_db():
    """初始化所有表 + 种子数据"""
    conn = get_conn()
    cursor = conn.cursor()

    # 用户表
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS users (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            username TEXT UNIQUE NOT NULL,
            hashed_password TEXT NOT NULL,
            email TEXT NOT NULL
        )
    """)
    for col, col_def in [
        ("nickname", "TEXT"),
        ("avatar", "TEXT"),
        ("role_id", "INTEGER DEFAULT NULL"),
    ]:
        try:
            cursor.execute(f"ALTER TABLE users ADD COLUMN {col} {col_def}")
        except sqlite3.OperationalError:
            pass

    # 角色表
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS roles (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            name TEXT NOT NULL,
            code TEXT UNIQUE NOT NULL,
            description TEXT DEFAULT '',
            status INTEGER DEFAULT 1,
            created_at TEXT DEFAULT (datetime('now','localtime'))
        )
    """)

    # 菜单表
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS menus (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            parent_id INTEGER DEFAULT 0,
            name TEXT NOT NULL,
            path TEXT DEFAULT '',
            component TEXT DEFAULT '',
            icon TEXT DEFAULT '',
            type TEXT NOT NULL DEFAULT 'menu',
            permission_code TEXT DEFAULT '',
            sort INTEGER DEFAULT 0,
            status INTEGER DEFAULT 1,
            created_at TEXT DEFAULT (datetime('now','localtime'))
        )
    """)

    # 角色-菜单关联表
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS role_menus (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            role_id INTEGER NOT NULL,
            menu_id INTEGER NOT NULL,
            FOREIGN KEY (role_id) REFERENCES roles(id) ON DELETE CASCADE,
            FOREIGN KEY (menu_id) REFERENCES menus(id) ON DELETE CASCADE
        )
    """)

    # 用户表迁移：添加 role_id
    try:
        cursor.execute("ALTER TABLE users ADD COLUMN role_id INTEGER DEFAULT NULL")
    except sqlite3.OperationalError:
        pass

    # 尝试迁移旧 role 字段到 role_id
    try:
        cursor.execute("SELECT role FROM users LIMIT 1")
        rows = cursor.execute("SELECT id, role FROM users WHERE role IS NOT NULL").fetchall()
        for row in rows:
            role_row = cursor.execute("SELECT id FROM roles WHERE code = ?", (row["role"],)).fetchone()
            if role_row:
                cursor.execute("UPDATE users SET role_id = ? WHERE id = ?", (role_row["id"], row["id"]))
    except sqlite3.OperationalError:
        pass

    conn.commit()

    # 种子数据
    _seed_roles(cursor)
    _seed_menus(cursor)
    _seed_role_menus(cursor)
    _seed_admin_user(cursor)

    conn.commit()
    conn.close()


# ==================== 种子数据 ====================

def _seed_roles(cursor):
    existing = cursor.execute("SELECT COUNT(*) as cnt FROM roles").fetchone()
    if existing["cnt"] == 0:
        roles = [
            ("超级管理员", "super", "拥有所有权限"),
            ("管理员", "admin", "系统管理权限"),
            ("普通用户", "user", "基础访问权限"),
        ]
        cursor.executemany(
            "INSERT INTO roles (name, code, description) VALUES (?, ?, ?)", roles
        )


def _seed_menus(cursor):
    existing = cursor.execute("SELECT COUNT(*) as cnt FROM menus").fetchone()
    if existing["cnt"] > 0:
        return

    menus = [
        # 仪表盘
        (0, "仪表盘", "/dashboard", "", "lucide:layout-dashboard", "dir", "", 1),
        (1, "工作台", "/dashboard/workspace", "/dashboard/workspace/index", "", "menu", "", 1),
        (1, "分析页", "/dashboard/analytics", "/dashboard/analytics/index", "", "menu", "", 2),
        # 系统管理
        (0, "系统管理", "/system", "", "lucide:settings", "dir", "", 2),
        (4, "用户管理", "/system/user", "/system/user/index", "", "menu", "system:user:view", 1),
        (4, "角色管理", "/system/role", "/system/role/index", "", "menu", "system:role:view", 2),
        (4, "菜单管理", "/system/menu", "/system/menu/index", "", "menu", "system:menu:view", 3),
        # 按钮权限
        (5, "新增用户", "", "", "", "button", "system:user:add", 1),
        (5, "编辑用户", "", "", "", "button", "system:user:edit", 2),
        (5, "删除用户", "", "", "", "button", "system:user:delete", 3),
        (6, "新增角色", "", "", "", "button", "system:role:add", 1),
        (6, "编辑角色", "", "", "", "button", "system:role:edit", 2),
        (6, "删除角色", "", "", "", "button", "system:role:delete", 3),
        (6, "分配权限", "", "", "", "button", "system:role:assign", 4),
        (7, "新增菜单", "", "", "", "button", "system:menu:add", 1),
        (7, "编辑菜单", "", "", "", "button", "system:menu:edit", 2),
        (7, "删除菜单", "", "", "", "button", "system:menu:delete", 3),
        # 关于
        (0, "关于", "/about", "/_core/about/index", "", "menu", "", 99),
    ]
    cursor.executemany(
        "INSERT INTO menus (parent_id, name, path, component, icon, type, permission_code, sort) "
        "VALUES (?, ?, ?, ?, ?, ?, ?, ?)",
        menus,
    )


def _seed_role_menus(cursor):
    existing = cursor.execute("SELECT COUNT(*) as cnt FROM role_menus").fetchone()
    if existing["cnt"] > 0:
        return

    super_id = cursor.execute("SELECT id FROM roles WHERE code='super'").fetchone()["id"]
    admin_id = cursor.execute("SELECT id FROM roles WHERE code='admin'").fetchone()["id"]
    user_id = cursor.execute("SELECT id FROM roles WHERE code='user'").fetchone()["id"]

    all_menu_ids = [r["id"] for r in cursor.execute("SELECT id FROM menus").fetchall()]
    admin_menu_ids = [r["id"] for r in cursor.execute(
        "SELECT id FROM menus WHERE permission_code LIKE 'system:%' OR permission_code='' OR type='dir'"
    ).fetchall()]
    # 也给 admin 添加 dashboard 相关的菜单
    admin_menu_ids = [r["id"] for r in cursor.execute(
        "SELECT id FROM menus WHERE id NOT IN (10,11,12,13,14,15,16,17)"
    ).fetchall()]

    user_menu_ids = [r["id"] for r in cursor.execute(
        "SELECT id FROM menus WHERE type IN ('menu','dir') AND permission_code NOT LIKE 'system:%'"
    ).fetchall()]

    for mid in all_menu_ids:
        cursor.execute("INSERT INTO role_menus (role_id, menu_id) VALUES (?, ?)", (super_id, mid))
    for mid in user_menu_ids:
        cursor.execute("INSERT INTO role_menus (role_id, menu_id) VALUES (?, ?)", (user_id, mid))
    # Admin: dashboard + system menus (exclude super-power buttons like add/edit/delete for system)
    for mid in [r["id"] for r in cursor.execute(
        "SELECT id FROM menus WHERE type='dir' OR (type='menu') OR (type='button' AND permission_code IN ('system:user:view','system:role:view','system:menu:view','system:user:add','system:user:edit','system:role:assign'))"
    ).fetchall()]:
        cursor.execute("INSERT INTO role_menus (role_id, menu_id) VALUES (?, ?)", (admin_id, mid))


def _seed_admin_user(cursor):
    from passlib.context import CryptContext
    pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")

    existing = cursor.execute("SELECT COUNT(*) as cnt FROM users").fetchone()
    if existing["cnt"] == 0:
        hashed = pwd_context.hash("admin123")
        super_id = cursor.execute("SELECT id FROM roles WHERE code='super'").fetchone()["id"]
        cursor.execute(
            "INSERT INTO users (username, hashed_password, email, role_id, nickname) VALUES (?, ?, ?, ?, ?)",
            ("admin", hashed, "admin@freedomforge.com", super_id, "超级管理员"),
        )


# ==================== 用户 ====================

def get_user_by_username(username: str):
    conn = get_conn()
    cursor = conn.cursor()
    cursor.execute(
        "SELECT u.id, u.username, u.hashed_password, u.email, u.nickname, u.avatar, "
        "u.role_id, r.code as role_code, r.name as role_name "
        "FROM users u LEFT JOIN roles r ON u.role_id = r.id "
        "WHERE u.username = ?", (username,)
    )
    row = cursor.fetchone()
    conn.close()
    if row:
        return {
            "id": row["id"], "username": row["username"],
            "hashed_password": row["hashed_password"], "email": row["email"],
            "role_id": row["role_id"], "role": row["role_code"] or "user",
            "role_name": row["role_name"] or "普通用户",
            "nickname": row["nickname"] or "", "avatar": row["avatar"] or "",
        }
    return None


def create_user(username: str, hashed_password: str, email: str, role_id: int = None):
    try:
        conn = get_conn()
        cursor = conn.cursor()
        cursor.execute(
            "INSERT INTO users (username, hashed_password, email, role_id, nickname) "
            "VALUES (?, ?, ?, ?, ?)",
            (username, hashed_password, email, role_id, username),
        )
        conn.commit()
        conn.close()
        return True
    except sqlite3.IntegrityError:
        return False


def get_users(page=1, page_size=10, keyword=""):
    conn = get_conn()
    cursor = conn.cursor()
    where = ""
    params = []
    if keyword:
        where = "WHERE u.username LIKE ? OR u.email LIKE ? OR u.nickname LIKE ?"
        kw = f"%{keyword}%"
        params = [kw, kw, kw]

    count = cursor.execute(
        f"SELECT COUNT(*) as cnt FROM users u {where}", params
    ).fetchone()["cnt"]

    offset = (page - 1) * page_size
    rows = cursor.execute(
        f"SELECT u.id, u.username, u.email, u.nickname, u.avatar, u.role_id, "
        f"r.code as role_code, r.name as role_name "
        f"FROM users u LEFT JOIN roles r ON u.role_id = r.id "
        f"{where} ORDER BY u.id LIMIT ? OFFSET ?",
        params + [page_size, offset]
    ).fetchall()
    conn.close()

    return {
        "total": count,
        "list": [{"id": r["id"], "username": r["username"], "email": r["email"],
                   "nickname": r["nickname"], "avatar": r["avatar"],
                   "role_id": r["role_id"], "role_code": r["role_code"],
                   "role_name": r["role_name"]} for r in rows]
    }


def update_user(user_id: int, **kwargs):
    allowed = ["email", "nickname", "avatar", "role_id"]
    sets = [f"{k} = ?" for k in kwargs if k in allowed]
    vals = [v for k, v in kwargs.items() if k in allowed]
    if not sets:
        return False
    conn = get_conn()
    conn.execute(f"UPDATE users SET {', '.join(sets)} WHERE id = ?", vals + [user_id])
    conn.commit()
    conn.close()
    return True


def delete_user(user_id: int):
    conn = get_conn()
    conn.execute("DELETE FROM users WHERE id = ?", (user_id,))
    conn.commit()
    conn.close()


# ==================== 角色 ====================

def get_roles(page=1, page_size=100):
    conn = get_conn()
    cursor = conn.cursor()
    count = cursor.execute("SELECT COUNT(*) as cnt FROM roles").fetchone()["cnt"]
    rows = cursor.execute(
        "SELECT * FROM roles ORDER BY id LIMIT ? OFFSET ?",
        (page_size, (page - 1) * page_size)
    ).fetchall()
    conn.close()
    return {"total": count, "list": [dict(r) for r in rows]}


def get_all_roles():
    conn = get_conn()
    rows = conn.execute("SELECT id, name, code FROM roles WHERE status=1 ORDER BY id").fetchall()
    conn.close()
    return [dict(r) for r in rows]


def get_role(role_id: int):
    conn = get_conn()
    row = conn.execute("SELECT * FROM roles WHERE id = ?", (role_id,)).fetchone()
    conn.close()
    return dict(row) if row else None


def create_role(name: str, code: str, description: str = ""):
    try:
        conn = get_conn()
        conn.execute("INSERT INTO roles (name, code, description) VALUES (?, ?, ?)", (name, code, description))
        conn.commit()
        conn.close()
        return True
    except sqlite3.IntegrityError:
        return False


def update_role(role_id: int, **kwargs):
    allowed = ["name", "code", "description", "status"]
    sets = [f"{k} = ?" for k in kwargs if k in allowed]
    vals = [v for k, v in kwargs.items() if k in allowed]
    if not sets:
        return False
    conn = get_conn()
    conn.execute(f"UPDATE roles SET {', '.join(sets)} WHERE id = ?", vals + [role_id])
    conn.commit()
    conn.close()
    return True


def delete_role(role_id: int):
    conn = get_conn()
    conn.execute("DELETE FROM roles WHERE id = ?", (role_id,))
    conn.execute("DELETE FROM role_menus WHERE role_id = ?", (role_id,))
    conn.commit()
    conn.close()


# ==================== 角色菜单 ====================

def get_role_menu_ids(role_id: int):
    conn = get_conn()
    rows = conn.execute("SELECT menu_id FROM role_menus WHERE role_id = ?", (role_id,)).fetchall()
    conn.close()
    return [r["menu_id"] for r in rows]


def set_role_menus(role_id: int, menu_ids: list[int]):
    conn = get_conn()
    conn.execute("DELETE FROM role_menus WHERE role_id = ?", (role_id,))
    conn.executemany("INSERT INTO role_menus (role_id, menu_id) VALUES (?, ?)",
                     [(role_id, mid) for mid in menu_ids])
    conn.commit()
    conn.close()


# ==================== 菜单 ====================

def get_menus():
    conn = get_conn()
    rows = conn.execute("SELECT * FROM menus ORDER BY sort ASC, id ASC").fetchall()
    conn.close()
    return [dict(r) for r in rows]


def get_menu(menu_id: int):
    conn = get_conn()
    row = conn.execute("SELECT * FROM menus WHERE id = ?", (menu_id,)).fetchone()
    conn.close()
    return dict(row) if row else None


def create_menu(**kwargs):
    fields = ["parent_id", "name", "path", "component", "icon", "type",
              "permission_code", "sort", "status"]
    keys = [f for f in fields if f in kwargs]
    placeholders = ["?" for _ in keys]
    values = [kwargs[k] for k in keys]
    conn = get_conn()
    conn.execute(
        f"INSERT INTO menus ({', '.join(keys)}) VALUES ({', '.join(placeholders)})",
        values,
    )
    conn.commit()
    conn.close()
    return True


def update_menu(menu_id: int, **kwargs):
    allowed = ["parent_id", "name", "path", "component", "icon", "type",
               "permission_code", "sort", "status"]
    sets = [f"{k} = ?" for k in kwargs if k in allowed]
    vals = [v for k, v in kwargs.items() if k in allowed]
    if not sets:
        return False
    conn = get_conn()
    conn.execute(f"UPDATE menus SET {', '.join(sets)} WHERE id = ?", vals + [menu_id])
    conn.commit()
    conn.close()
    return True


def delete_menu(menu_id: int):
    conn = get_conn()
    conn.execute("DELETE FROM menus WHERE id = ?", (menu_id,))
    conn.execute("DELETE FROM role_menus WHERE menu_id = ?", (menu_id,))
    conn.commit()
    conn.close()


# ==================== 权限码 ====================

def get_access_codes(username: str):
    user = get_user_by_username(username)
    if not user:
        return []
    role_id = user.get("role_id")
    if not role_id:
        return ["dashboard:view"]

    conn = get_conn()
    rows = conn.execute(
        "SELECT m.permission_code FROM role_menus rm "
        "JOIN menus m ON rm.menu_id = m.id "
        "WHERE rm.role_id = ? AND m.permission_code != ''",
        (role_id,)
    ).fetchall()
    conn.close()

    codes = [r["permission_code"] for r in rows]
    # super 角色返回 ["*"]
    if user.get("role") == "super":
        codes = ["*"]
    elif not codes:
        codes = ["dashboard:view"]
    return codes


def get_user_menus(username: str):
    """根据用户名获取有权限的菜单树（前端 generateRoutesByBackend 格式）"""
    user = get_user_by_username(username)
    if not user:
        return []

    role_id = user.get("role_id")
    role_code = user.get("role")

    conn = get_conn()
    if role_code == "super":
        rows = conn.execute(
            "SELECT * FROM menus WHERE type IN ('dir','menu') AND status=1 ORDER BY sort, id"
        ).fetchall()
    elif role_id:
        rows = conn.execute(
            "SELECT DISTINCT m.* FROM menus m "
            "JOIN role_menus rm ON m.id = rm.menu_id "
            "WHERE rm.role_id = ? AND m.type IN ('dir','menu') AND m.status=1 "
            "ORDER BY m.sort, m.id",
            (role_id,)
        ).fetchall()
    else:
        rows = conn.execute(
            "SELECT * FROM menus WHERE type IN ('dir','menu') AND status=1 "
            "AND permission_code NOT LIKE 'system:%' ORDER BY sort, id"
        ).fetchall()
    conn.close()

    menus = [dict(r) for r in rows]

    def menu_to_route(m):
        return {
            "name": m["name"],
            "path": m["path"],
            "component": m["component"] if m["component"] else "BasicLayout",
            "meta": {
                "title": m["name"],
                "icon": m["icon"] or "",
                "order": m["sort"],
            },
        }

    # Build name map
    name_map = {str(m["id"]): m for m in menus}

    # Detect route names: use path to derive (since name is stored as-is)
    def build_route_name(m):
        # For dir type, use path as the layout
        path = m["path"]
        # Generate name from path: /system/user -> SystemUser
        if path:
            parts = path.strip("/").split("/")
            return "".join(p.capitalize() for p in parts)
        return m["name"]

    def build_tree(parent_id=0):
        children = []
        for m in menus:
            if m["parent_id"] == parent_id:
                node = menu_to_route(m)
                # Override name for route matching
                node["name"] = build_route_name(m) if m["type"] != "dir" else build_route_name(m) + "Parent"
                sub = build_tree(m["id"])
                if sub:
                    node["children"] = sub
                if m["type"] == "dir":
                    # Directory has no component of its own, just a layout
                    node["component"] = "BasicLayout"
                children.append(node)
        return children

    return build_tree(0)
