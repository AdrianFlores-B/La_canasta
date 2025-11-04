# users_db.py
from __future__ import annotations
import os, json, secrets, hashlib, time
from typing import Dict, Any, Tuple, Optional

DB_PATH = "users.json"

# Páginas disponibles en tu app (sin Admin)
BASE_PAGES = ["Home", "Ventas", "Costos", "Alertas", "Predicciones"]

def _default_db() -> Dict[str, Any]:
    # Primer arranque: crea admin con contraseña temporal "admin"
    # Recomendación: el Admin la cambia de inmediato desde el panel.
    salt = secrets.token_hex(16)
    pwd_hash = _hash(password="admin", salt=salt)
    return {
        "meta": {"created_at": int(time.time())},
        "users": {
            "admin": {
                "salt": salt,
                "password_hash": pwd_hash,
                "role": "admin",
                "pages": BASE_PAGES + ["Admin"],
                "must_change_password": True
            }
        }
    }

def _hash(password: str, salt: str, iters: int = 200_000) -> str:
    dk = hashlib.pbkdf2_hmac(
        "sha256",
        password.encode("utf-8"),
        bytes.fromhex(salt),
        iters
    )
    return dk.hex()

def load_db() -> Dict[str, Any]:
    if not os.path.exists(DB_PATH):
        db = _default_db()
        save_db(db)
        return db
    with open(DB_PATH, "r", encoding="utf-8") as f:
        return json.load(f)

def save_db(db: Dict[str, Any]) -> None:
    tmp = DB_PATH + ".tmp"
    with open(tmp, "w", encoding="utf-8") as f:
        json.dump(db, f, indent=2, ensure_ascii=False)
    os.replace(tmp, DB_PATH)

def verify_password(password: str, salt: str, stored_hash: str) -> bool:
    return _hash(password, salt) == stored_hash

def upsert_user(
    db: Dict[str, Any],
    username: str,
    role: str,
    pages: list[str],
    new_password: Optional[str] = None,
    must_change_password: Optional[bool] = None
) -> None:
    users = db.setdefault("users", {})
    user = users.get(username, {})
    user["role"] = role
    user["pages"] = pages
    if new_password is not None and new_password != "":
        salt = secrets.token_hex(16)
        user["salt"] = salt
        user["password_hash"] = _hash(new_password, salt)
        user["must_change_password"] = bool(must_change_password)
    elif "salt" not in user or "password_hash" not in user:
        # Si es un usuario nuevo sin password, fuerza asignar una temporal
        salt = secrets.token_hex(16)
        user["salt"] = salt
        user["password_hash"] = _hash("temp1234", salt)
        user["must_change_password"] = True
    users[username] = user
    save_db(db)

def delete_user(db: Dict[str, Any], username: str) -> None:
    if username == "admin":
        raise ValueError("No se puede eliminar el usuario admin.")
    db["users"].pop(username, None)
    save_db(db)

def get_user(db: Dict[str, Any], username: str) -> Optional[Dict[str, Any]]:
    return db.get("users", {}).get(username)

def allowed_pages_for(db: Dict[str, Any], username: str) -> list[str]:
    u = get_user(db, username)
    return u.get("pages", []) if u else []

def is_admin(db: Dict[str, Any], username: str) -> bool:
    u = get_user(db, username)
    return (u and u.get("role") == "admin")

def change_password(db: Dict[str, Any], username: str, new_password: str) -> None:
    u = get_user(db, username)
    if not u:
        raise ValueError("Usuario no encontrado")
    salt = secrets.token_hex(16)
    u["salt"] = salt
    u["password_hash"] = _hash(new_password, salt)
    u["must_change_password"] = False
    save_db(db)
