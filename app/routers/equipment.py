from fastapi import APIRouter, Response, status
from sqlalchemy import select

from app.core.deps import CurrentUser, DbSession
from app.models import Equipment
from app.routers.helpers import get_equipment_or_404, refresh_and_return, update_model
from app.schemas import EquipmentCreate, EquipmentRead, EquipmentStatus, EquipmentUpdate

router = APIRouter(prefix="/equipment", tags=["equipment"])


@router.post("", response_model=EquipmentRead, status_code=status.HTTP_201_CREATED)
def create_equipment(
    payload: EquipmentCreate,
    db: DbSession,
    current_user: CurrentUser,
) -> Equipment:
    equipment = Equipment(
        name=payload.name,
        method=payload.method,
        capacity_per_day=payload.capacity_per_day,
        status=payload.status.value,
        calibration_due=payload.calibration_due,
        owner_id=current_user.id,
    )
    db.add(equipment)
    return refresh_and_return(db, equipment)


@router.get("", response_model=list[EquipmentRead])
def list_equipment(
    db: DbSession,
    current_user: CurrentUser,
    method: str | None = None,
    status_filter: EquipmentStatus | None = None,
) -> list[Equipment]:
    query = select(Equipment).where(Equipment.owner_id == current_user.id)
    if method is not None:
        query = query.where(Equipment.method == method.strip())
    if status_filter is not None:
        query = query.where(Equipment.status == status_filter.value)
    return list(db.scalars(query.order_by(Equipment.name.asc())).all())


@router.get("/{equipment_id}", response_model=EquipmentRead)
def read_equipment(equipment_id: int, db: DbSession, current_user: CurrentUser) -> Equipment:
    return get_equipment_or_404(db, current_user, equipment_id)


@router.patch("/{equipment_id}", response_model=EquipmentRead)
def update_equipment(
    equipment_id: int,
    payload: EquipmentUpdate,
    db: DbSession,
    current_user: CurrentUser,
) -> Equipment:
    equipment = get_equipment_or_404(db, current_user, equipment_id)
    update_model(equipment, payload)
    return refresh_and_return(db, equipment)


@router.delete("/{equipment_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_equipment(equipment_id: int, db: DbSession, current_user: CurrentUser) -> Response:
    equipment = get_equipment_or_404(db, current_user, equipment_id)
    db.delete(equipment)
    db.commit()
    return Response(status_code=status.HTTP_204_NO_CONTENT)
