from fastapi import APIRouter, HTTPException, Response, status
from sqlalchemy import select

from app.core.deps import CurrentUser, DbSession
from app.models import AnalysisRun, Project, Sample
from app.routers.helpers import (
    get_equipment_or_404,
    get_run_or_404,
    get_sample_or_404,
    refresh_and_return,
    update_model,
)
from app.schemas import AnalysisRunCreate, AnalysisRunRead, AnalysisRunUpdate, RunStatus

router = APIRouter(prefix="/runs", tags=["analysis runs"])


def validate_run_links(
    payload: AnalysisRunCreate,
    db: DbSession,
    current_user: CurrentUser,
) -> None:
    sample = get_sample_or_404(db, current_user, payload.sample_id)
    equipment = get_equipment_or_404(db, current_user, payload.equipment_id)
    if sample.required_method != equipment.method:
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            detail="Equipment method does not match sample requirement",
        )


@router.post("", response_model=AnalysisRunRead, status_code=status.HTTP_201_CREATED)
def create_run(
    payload: AnalysisRunCreate,
    db: DbSession,
    current_user: CurrentUser,
) -> AnalysisRun:
    validate_run_links(payload, db, current_user)
    run = AnalysisRun(
        sample_id=payload.sample_id,
        equipment_id=payload.equipment_id,
        scheduled_date=payload.scheduled_date,
        planned_hours=payload.planned_hours,
        actual_hours=payload.actual_hours,
        score=payload.score,
        status=payload.status.value,
    )
    db.add(run)
    return refresh_and_return(db, run)


@router.get("", response_model=list[AnalysisRunRead])
def list_runs(
    db: DbSession,
    current_user: CurrentUser,
    status_filter: RunStatus | None = None,
) -> list[AnalysisRun]:
    query = (
        select(AnalysisRun)
        .join(Sample)
        .join(Project)
        .where(Project.owner_id == current_user.id)
    )
    if status_filter is not None:
        query = query.where(AnalysisRun.status == status_filter.value)
    query = query.order_by(AnalysisRun.scheduled_date.asc(), AnalysisRun.id.asc())
    return list(db.scalars(query).all())


@router.get("/{run_id}", response_model=AnalysisRunRead)
def read_run(run_id: int, db: DbSession, current_user: CurrentUser) -> AnalysisRun:
    return get_run_or_404(db, current_user, run_id)


@router.patch("/{run_id}", response_model=AnalysisRunRead)
def update_run(
    run_id: int,
    payload: AnalysisRunUpdate,
    db: DbSession,
    current_user: CurrentUser,
) -> AnalysisRun:
    run = get_run_or_404(db, current_user, run_id)
    update_model(run, payload)
    if run.status == RunStatus.COMPLETED.value:
        run.sample.status = "completed"
    elif run.status == RunStatus.IN_PROGRESS.value:
        run.sample.status = "in_progress"
    return refresh_and_return(db, run)


@router.delete("/{run_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_run(run_id: int, db: DbSession, current_user: CurrentUser) -> Response:
    run = get_run_or_404(db, current_user, run_id)
    db.delete(run)
    db.commit()
    return Response(status_code=status.HTTP_204_NO_CONTENT)
