import os
import pytest
from fastapi.testclient import TestClient

os.environ["DATABASE_URL"] = "sqlite:///./test_labflow.db"
os.environ["SECRET_KEY"] = "test-secret-with-enough-length-for-jwt-signing"
os.environ["ACCESS_TOKEN_EXPIRE_MINUTES"] = "30"

from app.db import Base, db_session_factory, engine
from app.main import app


@pytest.fixture(autouse=True)
def reset_database():
    Base.metadata.drop_all(bind=engine)
    Base.metadata.create_all(bind=engine)
    yield
    db_session_factory.remove()
    Base.metadata.drop_all(bind=engine)


@pytest.fixture
def client():
    with TestClient(app) as test_client:
        yield test_client


@pytest.fixture
def auth_headers(client):
    payload = {
        "email": "manager@example.com",
        "username": "labmanager",
        "password": "StrongPass123",
        "role": "manager",
    }
    response = client.post("/auth/register", json=payload)
    assert response.status_code == 201
    token_response = client.post(
        "/auth/token",
        data={"username": payload["email"], "password": payload["password"]},
    )
    assert token_response.status_code == 200
    token = token_response.json()["access_token"]
    return {"Authorization": f"Bearer {token}"}
