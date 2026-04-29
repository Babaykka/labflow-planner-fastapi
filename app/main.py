from contextlib import asynccontextmanager

from fastapi import FastAPI
from fastapi.staticfiles import StaticFiles

from app.db import db_session_factory, init_db
from app.demo_data import seed_demo_data
from app.routers import auth, equipment, planner, projects, runs, samples, users, views


@asynccontextmanager
async def lifespan(_: FastAPI):
    init_db()
    db = db_session_factory()
    try:
        seed_demo_data(db)
    finally:
        db.close()
    yield


app = FastAPI(
    title="LabFlow Planner",
    description=(
        "REST-сервис для управления лабораторными проектами "
        "и оптимизации расписания анализов"
    ),
    version="1.0.0",
    lifespan=lifespan,
)

app.mount("/static", StaticFiles(directory="app/static"), name="static")
app.include_router(views.router)
app.include_router(auth.router)
app.include_router(users.router)
app.include_router(projects.router)
app.include_router(equipment.router)
app.include_router(samples.router)
app.include_router(runs.router)
app.include_router(planner.router)
