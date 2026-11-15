import base64
import hashlib
import hmac
import secrets
from datetime import datetime, timedelta, timezone

import jwt
from fastapi import Depends, HTTPException
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer
from sqlalchemy.orm import Session

from app.core.config import get_settings
from app.database.connection import get_db

_bearer = HTTPBearer(auto_error=False, description="Paste the access_token returned by POST /api/auth/login")


# ---------- passwords: PBKDF2-HMAC-SHA256 with a random salt (standard library, no extra dependency) ----------

def hash_password(password: str, iterations: int | None = None) -> str:
    iterations = iterations or get_settings().password_hash_iterations
    salt = secrets.token_bytes(16)
    digest = hashlib.pbkdf2_hmac("sha256", password.encode(), salt, iterations)
    return "pbkdf2_sha256${}${}${}".format(
        iterations, base64.b64encode(salt).decode(), base64.b64encode(digest).decode()
    )


def verify_password(password: str, stored: str) -> bool:
    try:
        scheme, iterations, salt_b64, digest_b64 = stored.split("$")
        if scheme != "pbkdf2_sha256":
            return False
        expected = base64.b64decode(digest_b64)
        actual = hashlib.pbkdf2_hmac("sha256", password.encode(), base64.b64decode(salt_b64), int(iterations))
        return hmac.compare_digest(actual, expected)  # constant-time comparison
    except (ValueError, TypeError):
        return False


# ---------- JWT ----------

def create_access_token(subject: str, role: str) -> tuple[str, int]:
    s = get_settings()
    expires = timedelta(minutes=s.jwt_expire_minutes)
    now = datetime.now(timezone.utc)
    token = jwt.encode(
        {"sub": subject, "role": role, "iat": now, "exp": now + expires}, s.jwt_secret, algorithm=s.jwt_algorithm
    )
    return token, int(expires.total_seconds())


def decode_token(token: str) -> dict:
    s = get_settings()
    return jwt.decode(token, s.jwt_secret, algorithms=[s.jwt_algorithm], options={"require": ["exp", "sub"]})


def get_current_admin(
    creds: HTTPAuthorizationCredentials | None = Depends(_bearer), db: Session = Depends(get_db)
):
    """Dependency that protects admin endpoints. Always answers 401 with the same message on any problem."""
    from app.models import AdminUser

    unauthorized = HTTPException(
        status_code=401, detail="Not authenticated", headers={"WWW-Authenticate": "Bearer"}
    )
    if creds is None:
        raise unauthorized
    try:
        payload = decode_token(creds.credentials)
    except jwt.PyJWTError:
        raise unauthorized
    admin = db.query(AdminUser).filter(AdminUser.username == payload["sub"]).first()
    if admin is None:
        raise unauthorized
    return admin


def require_admin_role(admin=Depends(get_current_admin)):
    """For team management: only users with the 'admin' role (not 'agent') may call these endpoints."""
    if admin.role != "admin":
        raise HTTPException(status_code=403, detail="Administrator role required")
    return admin
