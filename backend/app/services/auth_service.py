import logging

from sqlalchemy import select
from sqlalchemy.orm import Session

from app.core.config import get_settings
from app.core.exceptions import AppError
from app.core.security import create_access_token, hash_password, verify_password
from app.models import AdminUser

logger = logging.getLogger("leadflow.auth")

# Verified against when the username does not exist, so response time doesn't reveal valid usernames.
_DUMMY_HASH = hash_password("dummy-password", iterations=1000)


class AuthError(AppError):
    status_code = 401
    code = "invalid_credentials"


def authenticate(db: Session, username: str, password: str) -> tuple[str, int]:
    admin = db.scalar(select(AdminUser).where(AdminUser.username == username))
    ok = verify_password(password, admin.password_hash if admin else _DUMMY_HASH)
    if not admin or not ok:
        raise AuthError("Invalid username or password")  # same message for both cases
    return create_access_token(admin.username, admin.role)


def create_admin(db: Session, username: str, email: str, password: str, role: str = "admin") -> AdminUser:
    admin = AdminUser(username=username, email=email.lower(), password_hash=hash_password(password), role=role)
    db.add(admin)
    db.commit()
    db.refresh(admin)
    return admin


def seed_admin_from_env(db: Session) -> bool:
    """Create the first admin from ADMIN_USERNAME/ADMIN_EMAIL/ADMIN_PASSWORD if it doesn't exist yet."""
    s = get_settings()
    if not (s.admin_username and s.admin_email and s.admin_password):
        return False
    if db.scalar(select(AdminUser).where(AdminUser.username == s.admin_username)):
        return False
    create_admin(db, s.admin_username, s.admin_email, s.admin_password)
    logger.info("seeded admin user '%s'", s.admin_username)
    return True
