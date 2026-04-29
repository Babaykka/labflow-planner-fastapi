from fastapi import APIRouter, HTTPException, Response, status
from sqlalchemy import select

from app.core.deps import CurrentUser, DbSession
from app.models import Project, Sample
from app.routers.helpers import (
    get_project_or_404,
    get_sample_or_404,
    refresh_and_return,
    update_model,
)
from app.schemas import SampleCreate, SampleRead, SampleStatus, SampleUpdate

router = APIRouter(prefix="/samples", tags=["samples"])


@router.post("", response_model=SampleRead, status_code=status.HTTP_201_CREATED)
def create_sample(payload: SampleCreate, db: DbSession, current_user: CurrentUser) -> Sample:
    get_project_or_404(db, current_user, payload.project_id)
    duplicate = db.scalar(
        select(Sample).where(Sample.project_id == payload.project_id, Sample.code == payload.code)
    )
    if duplicate is not None:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail="Sample code already exists in this project",
        )
    sample = Sample(
        project_id=payload.project_id,
        code=payload.code,
        material_type=payload.material_type,
        required_method=payload.required_method,
        priority=payload.priority,
        estimated_hours=payload.estimated_hours,
        deadline=payload.deadline,
        status=payload.status.value,
    )
    db.add(sample)
    return refresh_and_return(db, sample)


@router.get("", response_model=list[SampleRead])
def list_samples(
    db: DbSession,
    current_user: CurrentUser,
    project_id: int | None = None,
    status_filter: SampleStatus | None = None,
    required_method: str | None = None,
) -> list[Sample]:
    query = select(Sample).join(Project).where(Project.owner_id == current_user.id)
    if project_id is not None:
        get_project_or_404(db, current_user, project_id)
        query = query.where(Sample.project_id == project_id)
    if status_filter is not None:
        query = query.where(Sample.status == status_filter.value)
    if required_method is not None:
        query = query.where(Sample.required_method == required_method.strip())
    query = query.order_by(Sample.priority.desc(), Sample.deadline.asc())
    return list(db.scalars(query).all())


@router.get("/{sample_id}", response_model=SampleRead)
def read_sample(sample_id: int, db: DbSession, current_user: CurrentUser) -> Sample:
    return get_sample_or_404(db, current_user, sample_id)


@router.patch("/{sample_id}", response_model=SampleRead)
def update_sample(
    sample_id: int,
    payload: SampleUpdate,
    db: DbSession,
    current_user: CurrentUser,
) -> Sample:
    sample = get_sample_or_404(db, current_user, sample_id)
    if payload.project_id is not None:
        get_project_or_404(db, current_user, payload.project_id)
    update_model(sample, payload)
    return refresh_and_return(db, sample)


@router.delete("/{sample_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_sample(sample_id: int, db: DbSession, current_user: CurrentUser) -> Response:
    sample = get_sample_or_404(db, current_user, sample_id)
    db.delete(sample)
    db.commit()
    return Response(status_code=status.HTTP_204_NO_CONTENT)
