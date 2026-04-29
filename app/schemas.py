from datetime import date, datetime
from enum import Enum

from pydantic import BaseModel, ConfigDict, Field, field_validator


class UserRole(str, Enum):
    RESEARCHER = "researcher"
    MANAGER = "manager"


class ProjectStatus(str, Enum):
    ACTIVE = "active"
    PAUSED = "paused"
    COMPLETED = "completed"


class EquipmentStatus(str, Enum):
    ACTIVE = "active"
    MAINTENANCE = "maintenance"
    RETIRED = "retired"


class SampleStatus(str, Enum):
    NEW = "new"
    QUEUED = "queued"
    IN_PROGRESS = "in_progress"
    COMPLETED = "completed"
    CANCELLED = "cancelled"


class RunStatus(str, Enum):
    PLANNED = "planned"
    IN_PROGRESS = "in_progress"
    COMPLETED = "completed"
    CANCELLED = "cancelled"


class AppSchema(BaseModel):
    model_config = ConfigDict(from_attributes=True, use_enum_values=True)


class UserCreate(BaseModel):
    email: str = Field(min_length=6, max_length=255)
    username: str = Field(min_length=3, max_length=80, pattern=r"^[A-Za-z0-9_.-]+$")
    password: str = Field(min_length=8, max_length=128)
    role: UserRole = UserRole.RESEARCHER

    @field_validator("email")
    @classmethod
    def validate_email(cls, value: str) -> str:
        normalized = value.strip().lower()
        if "@" not in normalized or "." not in normalized.rsplit("@", 1)[-1]:
            raise ValueError("Invalid email format")
        return normalized


class UserRead(AppSchema):
    id: int
    email: str
    username: str
    role: str
    created_at: datetime


class Token(AppSchema):
    access_token: str
    token_type: str = "bearer"


class ProjectBase(BaseModel):
    title: str = Field(min_length=3, max_length=160)
    description: str | None = Field(default=None, max_length=1000)
    deadline: date | None = None
    status: ProjectStatus = ProjectStatus.ACTIVE


class ProjectCreate(ProjectBase):
    pass


class ProjectUpdate(BaseModel):
    title: str | None = Field(default=None, min_length=3, max_length=160)
    description: str | None = Field(default=None, max_length=1000)
    deadline: date | None = None
    status: ProjectStatus | None = None


class ProjectRead(AppSchema):
    id: int
    title: str
    description: str | None
    deadline: date | None
    status: str
    owner_id: int
    created_at: datetime
    updated_at: datetime


class EquipmentBase(BaseModel):
    name: str = Field(min_length=2, max_length=160)
    method: str = Field(min_length=2, max_length=80)
    capacity_per_day: int = Field(ge=1, le=24)
    status: EquipmentStatus = EquipmentStatus.ACTIVE
    calibration_due: date | None = None

    @field_validator("method")
    @classmethod
    def normalize_method(cls, value: str) -> str:
        return value.strip()


class EquipmentCreate(EquipmentBase):
    pass


class EquipmentUpdate(BaseModel):
    name: str | None = Field(default=None, min_length=2, max_length=160)
    method: str | None = Field(default=None, min_length=2, max_length=80)
    capacity_per_day: int | None = Field(default=None, ge=1, le=24)
    status: EquipmentStatus | None = None
    calibration_due: date | None = None

    @field_validator("method")
    @classmethod
    def normalize_method(cls, value: str | None) -> str | None:
        return value.strip() if value is not None else value


class EquipmentRead(AppSchema):
    id: int
    name: str
    method: str
    capacity_per_day: int
    status: str
    calibration_due: date | None
    owner_id: int
    created_at: datetime
    updated_at: datetime


class SampleBase(BaseModel):
    project_id: int
    code: str = Field(min_length=2, max_length=80)
    material_type: str = Field(min_length=2, max_length=120)
    required_method: str = Field(min_length=2, max_length=80)
    priority: int = Field(ge=1, le=5)
    estimated_hours: int = Field(ge=1, le=24)
    deadline: date | None = None
    status: SampleStatus = SampleStatus.NEW

    @field_validator("code")
    @classmethod
    def normalize_code(cls, value: str) -> str:
        return value.strip().upper()

    @field_validator("required_method")
    @classmethod
    def normalize_required_method(cls, value: str) -> str:
        return value.strip()


class SampleCreate(SampleBase):
    pass


class SampleUpdate(BaseModel):
    project_id: int | None = None
    code: str | None = Field(default=None, min_length=2, max_length=80)
    material_type: str | None = Field(default=None, min_length=2, max_length=120)
    required_method: str | None = Field(default=None, min_length=2, max_length=80)
    priority: int | None = Field(default=None, ge=1, le=5)
    estimated_hours: int | None = Field(default=None, ge=1, le=24)
    deadline: date | None = None
    status: SampleStatus | None = None

    @field_validator("code")
    @classmethod
    def normalize_code(cls, value: str | None) -> str | None:
        return value.strip().upper() if value is not None else value

    @field_validator("required_method")
    @classmethod
    def normalize_required_method(cls, value: str | None) -> str | None:
        return value.strip() if value is not None else value


class SampleRead(AppSchema):
    id: int
    project_id: int
    code: str
    material_type: str
    required_method: str
    priority: int
    estimated_hours: int
    deadline: date | None
    status: str
    created_at: datetime
    updated_at: datetime


class AnalysisRunCreate(BaseModel):
    sample_id: int
    equipment_id: int
    scheduled_date: date
    planned_hours: int = Field(ge=1, le=24)
    actual_hours: int | None = Field(default=None, ge=1, le=24)
    score: float = 0
    status: RunStatus = RunStatus.PLANNED


class AnalysisRunUpdate(BaseModel):
    scheduled_date: date | None = None
    planned_hours: int | None = Field(default=None, ge=1, le=24)
    actual_hours: int | None = Field(default=None, ge=1, le=24)
    score: float | None = None
    status: RunStatus | None = None


class AnalysisRunRead(AppSchema):
    id: int
    sample_id: int
    equipment_id: int
    scheduled_date: date
    planned_hours: int
    actual_hours: int | None
    score: float
    status: str
    created_at: datetime
    updated_at: datetime


class PlannerRequest(BaseModel):
    sample_ids: list[int] | None = None
    horizon_days: int = Field(default=7, ge=1, le=30)
    start_date: date | None = None
    include_existing_runs: bool = True


class PlanItem(AppSchema):
    sample_id: int
    sample_code: str
    equipment_id: int
    equipment_name: str
    scheduled_date: date
    planned_hours: int
    score: float
    reason: str


class UnscheduledItem(AppSchema):
    sample_id: int
    sample_code: str
    reason: str


class PlanResponse(AppSchema):
    horizon_start: date
    horizon_end: date
    scheduled: list[PlanItem]
    unscheduled: list[UnscheduledItem]


class CommitResponse(AppSchema):
    plan: PlanResponse
    created_runs: list[AnalysisRunRead]
