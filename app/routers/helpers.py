from enum import Enum

from fastapi import HTTPException, status
from pydantic import BaseModel
from sqlalchemy import select
from sqlalchemy.orm import Session

from app.models import AnalysisRun, Equipment, Project, Sample, User


def enum_value(value):
    return value.value if isinstance(value, Enum) else value


def update_model(instance, payload: BaseModel):
    for field, value in payload.model_dump(exclude_unset=True).items():
        setattr(instance, field, enum_value(value))
    return instance


def not_found(name: str) -> HTTPException:
    return HTTPException(
        status_code=status.HTTP_404_NOT_FOUND,
        detail=f"{name} not found",
    )


def get_project_or_404(db: Session, current_user: User, project_id: int) -> Project:
    project = db.scalar(
        select(Project).where(Project.id == project_id, Project.owner_id == current_user.id)
    )
    if project is None:
        raise not_found("Project")
    return project


def get_equipment_or_404(db: Session, current_user: User, equipment_id: int) -> Equipment:
    equipment = db.scalar(
        select(Equipment).where(Equipment.id == equipment_id, Equipment.owner_id == current_user.id)
    )
    if equipment is None:
        raise not_found("Equipment")
    return equipment


def get_sample_or_404(db: Session, current_user: User, sample_id: int) -> Sample:
    sample = db.scalar(
        select(Sample)
        .join(Project)
        .where(Sample.id == sample_id, Project.owner_id == current_user.id)
    )
    if sample is None:
        raise not_found("Sample")
    return sample


def get_run_or_404(db: Session, current_user: User, run_id: int) -> AnalysisRun:
    run = db.scalar(
        select(AnalysisRun)
        .join(Sample)
        .join(Project)
        .where(AnalysisRun.id == run_id, Project.owner_id == current_user.id)
    )
    if run is None:
        raise not_found("Analysis run")
    return run


def refresh_and_return(db: Session, instance):
    db.commit()
    db.refresh(instance)
    return instance
