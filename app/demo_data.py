from datetime import date, timedelta

from sqlalchemy import select
from sqlalchemy.orm import Session

from app.core.security import hash_password
from app.models import AnalysisRun, Equipment, Project, Sample, User

DEMO_EMAIL = "demo@labflow.local"
DEMO_PASSWORD = "LabPlan2026"
DEMO_USERNAME = "labcurator"


def seed_demo_data(db: Session) -> None:
    existing_user = db.scalar(select(User).where(User.email == DEMO_EMAIL))
    if existing_user is not None:
        existing_user.username = DEMO_USERNAME
        existing_user.hashed_password = hash_password(DEMO_PASSWORD)
        existing_user.role = "manager"
        db.commit()
        return

    today = date.today()
    user = User(
        email=DEMO_EMAIL,
        username=DEMO_USERNAME,
        hashed_password=hash_password(DEMO_PASSWORD),
        role="manager",
    )
    db.add(user)
    db.flush()

    project = Project(
        title="Antibody screening batch",
        description="Проверка стабильности экспериментальных антител перед серией анализов",
        deadline=today + timedelta(days=14),
        status="active",
        owner_id=user.id,
    )
    db.add(project)
    db.flush()

    qpcr = Equipment(
        name="qPCR station",
        method="qPCR",
        capacity_per_day=8,
        status="active",
        calibration_due=today + timedelta(days=45),
        owner_id=user.id,
    )
    microscopy = Equipment(
        name="Confocal microscope",
        method="microscopy",
        capacity_per_day=6,
        status="active",
        calibration_due=today + timedelta(days=30),
        owner_id=user.id,
    )
    db.add_all([qpcr, microscopy])
    db.flush()

    samples = [
        Sample(
            project_id=project.id,
            code="AB-HIGH",
            material_type="antibody",
            required_method="qPCR",
            priority=5,
            estimated_hours=4,
            deadline=today + timedelta(days=3),
            status="queued",
        ),
        Sample(
            project_id=project.id,
            code="AB-MED",
            material_type="antibody",
            required_method="qPCR",
            priority=3,
            estimated_hours=3,
            deadline=today + timedelta(days=5),
            status="queued",
        ),
        Sample(
            project_id=project.id,
            code="CELL-IMG",
            material_type="cell culture",
            required_method="microscopy",
            priority=4,
            estimated_hours=5,
            deadline=today + timedelta(days=4),
            status="new",
        ),
    ]
    db.add_all(samples)
    db.flush()

    runs = [
        AnalysisRun(
            sample_id=samples[0].id,
            equipment_id=qpcr.id,
            scheduled_date=today,
            planned_hours=4,
            score=514.4,
            status="planned",
        ),
        AnalysisRun(
            sample_id=samples[1].id,
            equipment_id=qpcr.id,
            scheduled_date=today + timedelta(days=1),
            planned_hours=3,
            score=309.5,
            status="planned",
        ),
    ]
    db.add_all(runs)
    db.commit()
