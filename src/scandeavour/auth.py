import sqlite3
import time
from os import path, makedirs, getcwd

from werkzeug.security import generate_password_hash, check_password_hash

from scandeavour.utils import initDB, set_current_db


AUTH_DB_PATH = path.join(path.dirname(path.abspath(__file__)), "auth.sqlite")


def _get_auth_db():
    con = sqlite3.connect(AUTH_DB_PATH)
    cur = con.cursor()
    return con, cur


def init_auth_db():
    """
    Ініціалізує auth-базу, якщо вона ще не створена.
    Додає міграції для нових колонок, якщо потрібно.
    Створює адміна sweet/frost, якщо його ще немає.
    """
    con, cur = _get_auth_db()
    cur.execute(
        """
        CREATE TABLE IF NOT EXISTS users (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            username TEXT UNIQUE NOT NULL,
            password_hash TEXT NOT NULL,
            db_path TEXT NOT NULL,
            created_at INTEGER NOT NULL,
            is_admin INTEGER NOT NULL DEFAULT 0,
            is_blocked INTEGER NOT NULL DEFAULT 0
        );
        """
    )
    con.commit()
    
    # Міграція: додаємо колонки is_admin та is_blocked, якщо їх немає
    cur.execute("PRAGMA table_info(users)")
    columns = [row[1] for row in cur.fetchall()]
    
    if "is_admin" not in columns:
        cur.execute("ALTER TABLE users ADD COLUMN is_admin INTEGER NOT NULL DEFAULT 0")
        con.commit()
        print("[+] Added column 'is_admin' to users table")
    
    if "is_blocked" not in columns:
        cur.execute("ALTER TABLE users ADD COLUMN is_blocked INTEGER NOT NULL DEFAULT 0")
        con.commit()
        print("[+] Added column 'is_blocked' to users table")
    
    # Створюємо адміна sweet/frost, якщо його ще немає
    cur.execute("SELECT id FROM users WHERE username = ?", ("sweet",))
    if cur.fetchone() is None:
        db_path = _ensure_user_db("sweet")
        password_hash = generate_password_hash("frost")
        now = int(time.time())
        cur.execute(
            "INSERT INTO users (username, password_hash, db_path, created_at, is_admin) VALUES (?,?,?,?,?)",
            ("sweet", password_hash, db_path, now, 1),
        )
        con.commit()
        print("[+] Admin user 'sweet' created with password 'frost'")
    
    con.close()


def _ensure_user_db(username: str) -> str:
    """
    Створює (якщо потрібно) окрему БД для користувача та повертає її шлях.
    """
    base_dir = getcwd()
    user_db_dir = path.join(base_dir, "user_dbs")
    makedirs(user_db_dir, exist_ok=True)
    db_path = path.join(user_db_dir, f"{username}.db")

    # Ініціалізуємо схему в цій БД, якщо ще не було
    set_current_db(db_path)
    initDB()

    return db_path


def create_user(username: str, password: str):
    """
    Створює нового користувача з окремою БД.
    Повертає словник користувача або піднімає sqlite3.IntegrityError, якщо username вже зайнятий.
    """
    init_auth_db()
    db_path = _ensure_user_db(username)

    con, cur = _get_auth_db()
    password_hash = generate_password_hash(password)
    now = int(time.time())

    cur.execute(
        "INSERT INTO users (username, password_hash, db_path, created_at, is_admin, is_blocked) VALUES (?,?,?,?,?,?)",
        (username, password_hash, db_path, now, 0, 0),
    )
    user_id = cur.lastrowid
    con.commit()
    con.close()

    return {"id": user_id, "username": username, "db_path": db_path, "is_admin": 0, "is_blocked": 0}


def create_user_by_admin(username: str, password: str, is_admin: bool = False):
    """
    Створює нового користувача через адміна.
    """
    return create_user(username, password)


def authenticate(username: str, password: str):
    """
    Перевіряє логін/пароль. Повертає (True, user_dict) або (False, None).
    Не дозволяє логін заблокованим користувачам.
    """
    init_auth_db()
    con, cur = _get_auth_db()
    cur.execute(
        "SELECT id, username, password_hash, db_path, is_admin, is_blocked FROM users WHERE username = ?",
        (username,),
    )
    row = cur.fetchone()
    con.close()

    if row is None:
        return False, None

    user_id, uname, password_hash, db_path, is_admin, is_blocked = row
    
    # Перевіряємо чи користувач не заблокований
    if is_blocked:
        return False, None
    
    if not check_password_hash(password_hash, password):
        return False, None

    return True, {
        "id": user_id,
        "username": uname,
        "db_path": db_path,
        "is_admin": bool(is_admin),
        "is_blocked": bool(is_blocked),
    }


def get_user_by_id(user_id: int):
    init_auth_db()
    con, cur = _get_auth_db()
    cur.execute(
        "SELECT id, username, db_path, created_at, is_admin, is_blocked FROM users WHERE id = ?",
        (user_id,),
    )
    row = cur.fetchone()
    con.close()

    if row is None:
        return None

    uid, username, db_path, created_at, is_admin, is_blocked = row
    return {
        "id": uid,
        "username": username,
        "db_path": db_path,
        "created_at": created_at,
        "is_admin": bool(is_admin),
        "is_blocked": bool(is_blocked),
    }


def get_all_users():
    """
    Повертає список всіх користувачів (тільки для адмінів).
    """
    init_auth_db()
    con, cur = _get_auth_db()
    cur.execute(
        "SELECT id, username, db_path, created_at, is_admin, is_blocked FROM users ORDER BY username"
    )
    rows = cur.fetchall()
    con.close()
    
    return [
        {
            "id": uid,
            "username": username,
            "db_path": db_path,
            "created_at": created_at,
            "is_admin": bool(is_admin),
            "is_blocked": bool(is_blocked),
        }
        for uid, username, db_path, created_at, is_admin, is_blocked in rows
    ]


def delete_user(user_id: int):
    """
    Видаляє користувача (тільки для адмінів).
    """
    init_auth_db()
    con, cur = _get_auth_db()
    cur.execute("DELETE FROM users WHERE id = ?", (user_id,))
    con.commit()
    con.close()


def toggle_user_block(user_id: int):
    """
    Блокує/розблоковує користувача (тільки для адмінів).
    """
    init_auth_db()
    con, cur = _get_auth_db()
    cur.execute("SELECT is_blocked FROM users WHERE id = ?", (user_id,))
    row = cur.fetchone()
    if row is None:
        con.close()
        return False
    new_blocked = 1 if not row[0] else 0
    cur.execute("UPDATE users SET is_blocked = ? WHERE id = ?", (new_blocked, user_id))
    con.commit()
    con.close()
    return True


