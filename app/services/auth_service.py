from fastapi import Request
from sqlalchemy.orm import Session

from app.models.user import User
from app.schemas.user import UserCreate, UserLogin
from app.services.auth import create_user, get_user_by_email, verify_password


def register_user(db: Session, payload: UserCreate) -> tuple[bool, str, User | None]:
    existing = get_user_by_email(db, payload.email)
    if existing:
        return False, "Email sudah terdaftar", None

    user = create_user(db, payload)
    return True, "Registrasi berhasil", user


def login_user(db: Session, payload: UserLogin) -> tuple[bool, str, User | None]:
    user = get_user_by_email(db, payload.email)
    if not user or not verify_password(payload.password, user.password):
        return False, "Email atau password salah", None

    return True, "Login berhasil", user


def get_current_user(request: Request, db: Session) -> User | None:
    email = request.cookies.get("user_email")
    if not email:
        return None
    return get_user_by_email(db, email)


def require_role(user: User | None, role: str) -> bool:
    return bool(user and user.role == role)
