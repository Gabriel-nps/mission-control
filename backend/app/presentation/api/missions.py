from fastapi import APIRouter, Depends, HTTPException, status

from app.application.use_cases.create_mission import CreateMission, InvalidMissionDataError
from app.application.use_cases.get_mission import GetMission, MissionNotFoundError
from app.application.use_cases.list_missions import ListMissions
from app.presentation.schemas.missions import MissionCreateRequest, MissionResponse
from app.presentation.dependencies import get_current_user, get_create_mission, get_get_mission, get_list_missions

router = APIRouter(prefix="/missions", tags=["missions"])

@router.post("", status_code=status.HTTP_201_CREATED, response_model=MissionResponse)
def create_mission(
    request: MissionCreateRequest,
    current_user: str = Depends(get_current_user),
    use_case: CreateMission = Depends(get_create_mission),
):
    try:
        mission = use_case.execute(request.name, request.priority)
        return MissionResponse(
            id=mission.id,
            name=mission.name,
            priority=mission.priority.value,
            status=mission.status.value,
            created_at=mission.created_at,
            updated_at=mission.updated_at,
        )
    except InvalidMissionDataError as e:
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            detail=str(e)
        )

@router.get("", response_model=list[MissionResponse])
def list_missions(
    current_user: str = Depends(get_current_user),
    use_case: ListMissions = Depends(get_list_missions),
):
    missions = use_case.execute()
    return [
        MissionResponse(
            id=m.id,
            name=m.name,
            priority=m.priority.value,
            status=m.status.value,
            created_at=m.created_at,
            updated_at=m.updated_at,
        )
        for m in missions
    ]
    
@router.get("/{mission_id}", response_model=MissionResponse)
def get_mission(
    mission_id: str,
    current_user: str = Depends(get_current_user),
    use_case: GetMission = Depends(get_get_mission)
):
    try:
        mission = use_case.execute(mission_id)
        return MissionResponse(
            id=mission.id,
            name=mission.name,
            priority=mission.priority.value,
            status=mission.status.value,
            created_at=mission.created_at,
            updated_at=mission.updated_at,
        )
    except MissionNotFoundError:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Mission not found",
        )