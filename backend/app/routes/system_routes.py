from fastapi import APIRouter, Depends

from app.core.config import get_settings
from app.core.security import get_current_admin
from app.schemas.communication import CapabilitiesOut
from app.schemas.response import ApiResponse

router = APIRouter(prefix="/api/system", tags=["System"], dependencies=[Depends(get_current_admin)])


@router.get("/capabilities", response_model=ApiResponse[CapabilitiesOut])
def capabilities():
    """What this deployment can actually do, so the UI can disable buttons that would only fail (no secrets exposed)."""
    s = get_settings()
    return ApiResponse(data=CapabilitiesOut(email_enabled=s.email_enabled, whatsapp_enabled=True, default_country_code=s.default_country_code))
