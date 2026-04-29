from datetime import date, timedelta
from typing import NamedTuple

from sqlalchemy import select
from sqlalchemy.orm import Session

from app.models import AnalysisRun, Equipment, Project, Sample, User
from app.schemas import PlanItem, PlanResponse, PlannerRequest, UnscheduledItem


class SlotChoice(NamedTuple):
    item: PlanItem
    remaining_capacity: int


def _planning_window(request: PlannerRequest) -> tuple[date, date]:
    start = request.start_date or date.today()
    return start, start + timedelta(days=request.horizon_days - 1)


def _load_samples(db: Session, current_user: User, request: PlannerRequest) -> list[Sample]:
    query = (
        select(Sample)
        .join(Project)
        .where(
            Project.owner_id == current_user.id,
            Sample.status.notin_(["completed", "cancelled"]),
        )
    )
    if request.sample_ids:
        query = query.where(Sample.id.in_(request.sample_ids))
    samples = list(db.scalars(query).all())
    return sorted(
        samples,
        key=lambda sample: (
            -sample.priority,
            sample.deadline or date.max,
            -sample.estimated_hours,
            sample.id,
        ),
    )


def _load_equipment(db: Session, current_user: User) -> list[Equipment]:
    query = (
        select(Equipment)
        .where(Equipment.owner_id == current_user.id, Equipment.status == "active")
        .order_by(Equipment.method.asc(), Equipment.capacity_per_day.desc())
    )
    return list(db.scalars(query).all())


def _initial_capacity(
    db: Session,
    equipment: list[Equipment],
    request: PlannerRequest,
    start: date,
    end: date,
) -> dict[tuple[int, date], int]:
    days = [start + timedelta(days=offset) for offset in range(request.horizon_days)]
    capacity = {(item.id, day): item.capacity_per_day for item in equipment for day in days}
    if not request.include_existing_runs:
        return capacity
    equipment_ids = [item.id for item in equipment]
    if not equipment_ids:
        return capacity
    query = select(AnalysisRun).where(
        AnalysisRun.equipment_id.in_(equipment_ids),
        AnalysisRun.scheduled_date >= start,
        AnalysisRun.scheduled_date <= end,
        AnalysisRun.status.in_(["planned", "in_progress"]),
    )
    for run in db.scalars(query).all():
        key = (run.equipment_id, run.scheduled_date)
        if key in capacity:
            capacity[key] = max(0, capacity[key] - run.planned_hours)
    return capacity


def _score_sample_on_day(
    sample: Sample,
    planned_date: date,
    start: date,
    remaining_after: int,
) -> float:
    day_offset = (planned_date - start).days
    deadline = sample.deadline or start + timedelta(days=30)
    lateness = max((planned_date - deadline).days, 0)
    slack = max((deadline - planned_date).days, 0)
    score = sample.priority * 100 - lateness * 35 - day_offset * 5
    return round(score + min(slack, 14) + remaining_after / 10, 2)


def _best_slot(
    sample: Sample,
    compatible_equipment: list[Equipment],
    capacity: dict[tuple[int, date], int],
    request: PlannerRequest,
    start: date,
) -> SlotChoice | None:
    choices: list[SlotChoice] = []
    for day_offset in range(request.horizon_days):
        planned_date = start + timedelta(days=day_offset)
        for equipment in compatible_equipment:
            key = (equipment.id, planned_date)
            remaining = capacity.get(key, 0)
            if remaining < sample.estimated_hours:
                continue
            remaining_after = remaining - sample.estimated_hours
            score = _score_sample_on_day(sample, planned_date, start, remaining_after)
            item = PlanItem(
                sample_id=sample.id,
                sample_code=sample.code,
                equipment_id=equipment.id,
                equipment_name=equipment.name,
                scheduled_date=planned_date,
                planned_hours=sample.estimated_hours,
                score=score,
                reason=(
                    f"priority={sample.priority}, "
                    f"deadline={sample.deadline}, "
                    f"remaining={remaining_after}"
                ),
            )
            choices.append(SlotChoice(item=item, remaining_capacity=remaining_after))
    if not choices:
        return None
    return max(choices, key=lambda choice: (choice.item.score, choice.remaining_capacity))


def build_plan(db: Session, current_user: User, request: PlannerRequest) -> PlanResponse:
    start, end = _planning_window(request)
    samples = _load_samples(db, current_user, request)
    equipment = _load_equipment(db, current_user)
    capacity = _initial_capacity(db, equipment, request, start, end)
    scheduled: list[PlanItem] = []
    unscheduled: list[UnscheduledItem] = []
    equipment_by_method = {
        method: [item for item in equipment if item.method == method]
        for method in {item.method for item in equipment}
    }
    for sample in samples:
        compatible = equipment_by_method.get(sample.required_method, [])
        if not compatible:
            unscheduled.append(
                UnscheduledItem(
                    sample_id=sample.id,
                    sample_code=sample.code,
                    reason=f"Нет доступного прибора для метода {sample.required_method}",
                )
            )
            continue
        best = _best_slot(sample, compatible, capacity, request, start)
        if best is None:
            unscheduled.append(
                UnscheduledItem(
                    sample_id=sample.id,
                    sample_code=sample.code,
                    reason="Не хватило дневной мощности в выбранном горизонте",
                )
            )
            continue
        key = (best.item.equipment_id, best.item.scheduled_date)
        capacity[key] = best.remaining_capacity
        scheduled.append(best.item)
    return PlanResponse(
        horizon_start=start,
        horizon_end=end,
        scheduled=scheduled,
        unscheduled=unscheduled,
    )
