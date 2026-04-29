from fastapi import APIRouter, Response, status
from sqlalchemy import select

from app.core.deps import CurrentUser, DbSession
from app.models import Project
from app.routers.helpers import get_project_or_404, refresh_and_return, update_model
from app.schemas import ProjectCreate, ProjectRead, ProjectStatus, ProjectUpdate

router = APIRouter(prefix="/projects", tags=["projects"])


@router.post("", response_model=ProjectRead, status_code=status.HTTP_201_CREATED)
def create_project(payload: ProjectCreate, db: DbSession, current_user: CurrentUser) -> Project:
    project = Project(
        title=payload.title,
        description=payload.description,
        deadline=payload.deadline,
        status=payload.status.value,
        owner_id=current_user.id,
    )
    db.add(project)
    return refresh_and_return(db, project)


@router.get("", response_model=list[ProjectRead])
def list_projects(
    db: DbSession,
    current_user: CurrentUser,
    status_filter: ProjectStatus | None = None,
    limit: int = 50,
    offset: int = 0,
) -> list[Project]:
    query = select(Project).where(Project.owner_id == current_user.id)
    if status_filter is not None:
        query = query.where(Project.status == status_filter.value)
    query = query.order_by(Project.created_at.desc()).limit(limit).offset(offset)
    return list(db.scalars(query).all())


@router.get("/{project_id}", response_model=ProjectRead)
def read_project(project_id: int, db: DbSession, current_user: CurrentUser) -> Project:
    return get_project_or_404(db, current_user, project_id)


@router.patch("/{project_id}", response_model=ProjectRead)
def update_project(
    project_id: int,
    payload: ProjectUpdate,
    db: DbSession,
    current_user: CurrentUser,
) -> Project:
    project = get_project_or_404(db, current_user, project_id)
    update_model(project, payload)
    return refresh_and_return(db, project)


@router.delete("/{project_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_project(project_id: int, db: DbSession, current_user: CurrentUser) -> Response:
    project = get_project_or_404(db, current_user, project_id)
    db.delete(project)
    db.commit()
    return Response(status_code=status.HTTP_204_NO_CONTENT)
