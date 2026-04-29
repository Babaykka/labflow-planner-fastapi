from __future__ import annotations

from datetime import UTC, date, datetime

from sqlalchemy import Date, DateTime, Float, ForeignKey, Integer, String, UniqueConstraint
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.db import Base


def utc_now() -> datetime:
    return datetime.now(UTC)


class TimestampMixin:
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=utc_now)
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        default=utc_now,
        onupdate=utc_now,
    )


class User(TimestampMixin, Base):
    __tablename__ = "users"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, index=True)
    email: Mapped[str] = mapped_column(String(255), unique=True, index=True, nullable=False)
    username: Mapped[str] = mapped_column(String(80), unique=True, index=True, nullable=False)
    hashed_password: Mapped[str] = mapped_column(String(255), nullable=False)
    role: Mapped[str] = mapped_column(String(30), default="researcher", nullable=False)
    projects: Mapped[list[Project]] = relationship(
        back_populates="owner",
        cascade="all, delete-orphan",
    )
    equipment_items: Mapped[list[Equipment]] = relationship(
        back_populates="owner",
        cascade="all, delete-orphan",
    )


class Project(TimestampMixin, Base):
    __tablename__ = "projects"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, index=True)
    title: Mapped[str] = mapped_column(String(160), nullable=False)
    description: Mapped[str | None] = mapped_column(String(1000), nullable=True)
    status: Mapped[str] = mapped_column(String(30), default="active", nullable=False)
    deadline: Mapped[date | None] = mapped_column(Date, nullable=True)
    owner_id: Mapped[int] = mapped_column(ForeignKey("users.id"), nullable=False)
    owner: Mapped[User] = relationship(back_populates="projects")
    samples: Mapped[list[Sample]] = relationship(
        back_populates="project",
        cascade="all, delete-orphan",
    )


class Equipment(TimestampMixin, Base):
    __tablename__ = "equipment"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, index=True)
    name: Mapped[str] = mapped_column(String(160), nullable=False)
    method: Mapped[str] = mapped_column(String(80), index=True, nullable=False)
    capacity_per_day: Mapped[int] = mapped_column(Integer, nullable=False)
    status: Mapped[str] = mapped_column(String(30), default="active", nullable=False)
    calibration_due: Mapped[date | None] = mapped_column(Date, nullable=True)
    owner_id: Mapped[int] = mapped_column(ForeignKey("users.id"), nullable=False)
    owner: Mapped[User] = relationship(back_populates="equipment_items")
    runs: Mapped[list[AnalysisRun]] = relationship(
        back_populates="equipment",
        cascade="all, delete-orphan",
    )


class Sample(TimestampMixin, Base):
    __tablename__ = "samples"
    __table_args__ = (UniqueConstraint("project_id", "code", name="uq_project_sample_code"),)

    id: Mapped[int] = mapped_column(Integer, primary_key=True, index=True)
    project_id: Mapped[int] = mapped_column(ForeignKey("projects.id"), nullable=False)
    code: Mapped[str] = mapped_column(String(80), nullable=False)
    material_type: Mapped[str] = mapped_column(String(120), nullable=False)
    required_method: Mapped[str] = mapped_column(String(80), index=True, nullable=False)
    priority: Mapped[int] = mapped_column(Integer, nullable=False)
    estimated_hours: Mapped[int] = mapped_column(Integer, nullable=False)
    deadline: Mapped[date | None] = mapped_column(Date, nullable=True)
    status: Mapped[str] = mapped_column(String(30), default="new", nullable=False)
    project: Mapped[Project] = relationship(back_populates="samples")
    runs: Mapped[list[AnalysisRun]] = relationship(
        back_populates="sample",
        cascade="all, delete-orphan",
    )


class AnalysisRun(TimestampMixin, Base):
    __tablename__ = "analysis_runs"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, index=True)
    sample_id: Mapped[int] = mapped_column(ForeignKey("samples.id"), nullable=False)
    equipment_id: Mapped[int] = mapped_column(ForeignKey("equipment.id"), nullable=False)
    scheduled_date: Mapped[date] = mapped_column(Date, nullable=False)
    planned_hours: Mapped[int] = mapped_column(Integer, nullable=False)
    actual_hours: Mapped[int | None] = mapped_column(Integer, nullable=True)
    score: Mapped[float] = mapped_column(Float, default=0.0, nullable=False)
    status: Mapped[str] = mapped_column(String(30), default="planned", nullable=False)
    sample: Mapped[Sample] = relationship(back_populates="runs")
    equipment: Mapped[Equipment] = relationship(back_populates="runs")
