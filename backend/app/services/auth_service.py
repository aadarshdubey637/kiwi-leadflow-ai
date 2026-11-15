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
    """Make the bootstrap admin match ADMIN_USERNAME / ADMIN_PASSWORD (ADMIN_EMAIL is optional). True if anything changed.

    - Admin missing  -> created.
    - Admin exists but ADMIN_PASSWORD no longer matches its stored hash -> the password is updated. The environment variable
      is the source of truth, so changing it in the host's dashboard (e.g. Render) and redeploying really changes the login.
    Only the account named by ADMIN_USERNAME is ever touched; all other users are left alone.
    Every outcome is logged (never the password itself) so a hosted deployment can be diagnosed from its logs.
    """
    s = get_settings()
    if not (s.admin_username and s.admin_password):
        logger.warning("admin bootstrap: ADMIN_USERNAME and/or ADMIN_PASSWORD not set, so no admin account is created or updated")
        return False

    pw = s.admin_password
    if pw != pw.strip():
        logger.warning("admin bootstrap: ADMIN_PASSWORD has leading/trailing spaces, and they are part of the password")
    if len(pw) >= 2 and pw[0] == pw[-1] and pw[0] in "\"'":
        logger.warning("admin bootstrap: ADMIN_PASSWORD is wrapped in quotes, and the quotes are part of the password")

    existing = db.scalar(select(AdminUser).where(AdminUser.username == s.admin_username))
    if existing is None:
        email = s.admin_email or f"{s.admin_username}@leadflow.local"  # only needed because the column is required
        create_admin(db, s.admin_username, email, pw)
        logger.info("admin bootstrap: created admin '%s'", s.admin_username)
        return True
    if not verify_password(pw, existing.password_hash):
        existing.password_hash = hash_password(pw)
        db.commit()
        logger.info("admin bootstrap: password of '%s' updated to match ADMIN_PASSWORD", s.admin_username)
        return True
    logger.info("admin bootstrap: admin '%s' already matches ADMIN_USERNAME / ADMIN_PASSWORD", s.admin_username)
    return False
