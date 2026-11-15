from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session

from app.core.security import get_current_admin, require_admin_role
from app.database.connection import get_db
from app.schemas.response import ApiResponse
from app.schemas.team import TeamMemberCreate, TeamMemberOut, TeamMemberUpdate
from app.services import team_service

router = APIRouter(prefix="/api/team", tags=["Team"])


def _out(member, db: Session) -> TeamMemberOut:
    return next(TeamMemberOut(**m) for m in team_service.list_members(db) if m["id"] == member.id)


@router.get("", response_model=ApiResponse[list[TeamMemberOut]], dependencies=[Depends(get_current_admin)])
def list_team(db: Session = Depends(get_db)):
    """Everyone who can be assigned enquiries, with their current open workload."""
    return ApiResponse(data=team_service.list_members(db))


@router.post("", response_model=ApiResponse[TeamMemberOut], status_code=201, dependencies=[Depends(require_admin_role)])
def create_team_member(payload: TeamMemberCreate, db: Session = Depends(get_db)):
    """Admin only. New members start receiving automatic assignments immediately."""
    member = team_service.create_member(db, payload.username, payload.email, payload.password, payload.role)
    return ApiResponse(data=_out(member, db))


@router.put("/{member_id}", response_model=ApiResponse[TeamMemberOut])
def update_team_member(member_id: int, payload: TeamMemberUpdate, db: Session = Depends(get_db), acting=Depends(require_admin_role)):
    """Admin only. Deactivate a member to stop new assignments (their existing enquiries stay with them)."""
    member = team_service.update_member(db, member_id, acting, payload.is_active, payload.role)
    return ApiResponse(data=_out(member, db))
