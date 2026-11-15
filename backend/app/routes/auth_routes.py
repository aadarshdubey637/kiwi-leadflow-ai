from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session

from app.core.rate_limit import rate_limit
from app.core.security import get_current_admin
from app.database.connection import get_db
from app.schemas.auth import AdminOut, LoginRequest, TokenOut
from app.schemas.response import ApiResponse
from app.services import auth_service

router = APIRouter(prefix="/api/auth", tags=["Authentication"])


@router.post(
    "/login", response_model=ApiResponse[TokenOut],
    dependencies=[Depends(rate_limit("login", "rate_limit_login_per_minute"))],
)
def login(payload: LoginRequest, db: Session = Depends(get_db)):
    token, expires_in = auth_service.authenticate(db, payload.username, payload.password)
    return ApiResponse(data=TokenOut(access_token=token, expires_in=expires_in))


@router.get("/me", response_model=ApiResponse[AdminOut])
def me(admin=Depends(get_current_admin)):
    return ApiResponse(data=admin)
