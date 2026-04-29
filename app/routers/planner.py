from fastapi import APIRouter, status
from sqlalchemy import select

from app.core.deps import CurrentUser, DbSession
from app.models import AnalysisRun, Sample
from app.schemas import CommitResponse, PlanResponse, PlannerRequest
from app.services.planner import build_plan

router = APIRouter(prefix="/planner", tags=["planner"])


@router.post("/optimize", response_model=PlanResponse)
def optimize_plan(
    payload: PlannerRequest,
    db: DbSession,
    current_user: CurrentUser,
) -> PlanResponse:
    return build_plan(db, current_user, payload)


@router.post("/commit", response_model=CommitResponse, status_code=status.HTTP_201_CREATED)
def commit_plan(
    payload: PlannerRequest,
    db: DbSession,
    current_user: CurrentUser,
) -> CommitResponse:
    plan = build_plan(db, current_user, payload)
    created_runs: list[AnalysisRun] = []
    for item in plan.scheduled:
        existing_run = db.scalar(
            select(AnalysisRun).where(
                AnalysisRun.sample_id == item.sample_id,
                AnalysisRun.status.in_(["planned", "in_progress"]),
            )
        )
        if existing_run is not None:
            continue
        run = AnalysisRun(
            sample_id=item.sample_id,
            equipment_id=item.equipment_id,
            scheduled_date=item.scheduled_date,
            planned_hours=item.planned_hours,
            score=item.score,
            status="planned",
        )
        sample = db.get(Sample, item.sample_id)
        if sample is not None:
            sample.status = "queued"
        db.add(run)
        created_runs.append(run)
    db.commit()
    for run in created_runs:
        db.refresh(run)
    return CommitResponse(plan=plan, created_runs=created_runs)
