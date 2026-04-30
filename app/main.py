from contextlib import asynccontextmanager

from fastapi import FastAPI
from fastapi.openapi.docs import get_swagger_ui_html
from fastapi.responses import HTMLResponse
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
    docs_url=None,
)


@app.get("/docs", include_in_schema=False)
def swagger_docs():
    response = get_swagger_ui_html(
        openapi_url=app.openapi_url,
        title=f"{app.title} - Swagger UI",
    )
    body = response.body.decode("utf-8")
    home_link = """
    <style>
      .swagger-home-link {
        align-items: center;
        background: #2563eb;
        border-radius: 6px;
        color: #ffffff;
        display: inline-flex;
        font-family: sans-serif;
        font-size: 14px;
        font-weight: 700;
        height: 34px;
        justify-content: center;
        padding: 0 16px;
        position: fixed;
        right: 24px;
        text-decoration: none;
        top: 12px;
        z-index: 10000;
      }

      .swagger-home-link:hover {
        background: #1d4ed8;
      }

      @media (max-width: 640px) {
        .swagger-home-link {
          right: 12px;
          top: 10px;
        }
      }
    </style>
    <a class="swagger-home-link" href="/">Home</a>
    """
    return HTMLResponse(body.replace("</body>", f"{home_link}</body>"))

app.mount("/static", StaticFiles(directory="app/static"), name="static")
app.include_router(views.router)
app.include_router(auth.router)
app.include_router(users.router)
app.include_router(projects.router)
app.include_router(equipment.router)
app.include_router(samples.router)
app.include_router(runs.router)
app.include_router(planner.router)
