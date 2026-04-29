from datetime import date, timedelta


def create_project(client, headers, title="Enzyme stability sprint"):
    response = client.post(
        "/projects",
        headers=headers,
        json={
            "title": title,
            "description": "Short-cycle screening for formulation candidates",
            "deadline": str(date.today() + timedelta(days=7)),
            "status": "active",
        },
    )
    assert response.status_code == 201
    return response.json()


def create_equipment(client, headers, method="qPCR", capacity=8):
    response = client.post(
        "/equipment",
        headers=headers,
        json={
            "name": f"{method} station",
            "method": method,
            "capacity_per_day": capacity,
            "status": "active",
            "calibration_due": str(date.today() + timedelta(days=60)),
        },
    )
    assert response.status_code == 201
    return response.json()


def create_sample(client, headers, project_id, code, priority, hours, method="qPCR"):
    response = client.post(
        "/samples",
        headers=headers,
        json={
            "project_id": project_id,
            "code": code,
            "material_type": "enzyme",
            "required_method": method,
            "priority": priority,
            "estimated_hours": hours,
            "deadline": str(date.today() + timedelta(days=2)),
            "status": "new",
        },
    )
    assert response.status_code == 201
    return response.json()


def test_project_equipment_sample_crud_flow(client, auth_headers):
    project = create_project(client, auth_headers)
    equipment = create_equipment(client, auth_headers)
    sample = create_sample(client, auth_headers, project["id"], "ENZ-001", 4, 3)

    projects = client.get("/projects", headers=auth_headers)
    assert projects.status_code == 200
    assert projects.json()[0]["title"] == project["title"]

    project_update = client.patch(
        f"/projects/{project['id']}",
        headers=auth_headers,
        json={"status": "paused"},
    )
    assert project_update.status_code == 200
    assert project_update.json()["status"] == "paused"

    equipment_update = client.patch(
        f"/equipment/{equipment['id']}",
        headers=auth_headers,
        json={"capacity_per_day": 10},
    )
    assert equipment_update.status_code == 200
    assert equipment_update.json()["capacity_per_day"] == 10

    sample_update = client.patch(
        f"/samples/{sample['id']}",
        headers=auth_headers,
        json={"priority": 5, "status": "queued"},
    )
    assert sample_update.status_code == 200
    assert sample_update.json()["priority"] == 5

    sample_detail = client.get(f"/samples/{sample['id']}", headers=auth_headers)
    assert sample_detail.status_code == 200
    assert sample_detail.json()["project_id"] == project["id"]

    delete_response = client.delete(f"/samples/{sample['id']}", headers=auth_headers)
    assert delete_response.status_code == 204


def test_sample_validation_and_project_ownership(client, auth_headers):
    project = create_project(client, auth_headers)
    invalid_response = client.post(
        "/samples",
        headers=auth_headers,
        json={
            "project_id": project["id"],
            "code": "BAD-001",
            "material_type": "enzyme",
            "required_method": "qPCR",
            "priority": 0,
            "estimated_hours": 2,
            "deadline": str(date.today() + timedelta(days=1)),
        },
    )
    assert invalid_response.status_code == 422

    client.post(
        "/auth/register",
        json={
            "email": "other@example.com",
            "username": "other",
            "password": "StrongPass123",
        },
    )
    token_response = client.post(
        "/auth/token",
        data={"username": "other@example.com", "password": "StrongPass123"},
    )
    other_headers = {"Authorization": f"Bearer {token_response.json()['access_token']}"}
    forbidden_response = create_project(client, other_headers, "Other project")
    response = client.post(
        "/samples",
        headers=auth_headers,
        json={
            "project_id": forbidden_response["id"],
            "code": "CROSS-001",
            "material_type": "enzyme",
            "required_method": "qPCR",
            "priority": 3,
            "estimated_hours": 2,
            "deadline": str(date.today() + timedelta(days=1)),
        },
    )
    assert response.status_code == 404


def test_planner_optimizes_and_commits_runs(client, auth_headers):
    project = create_project(client, auth_headers)
    equipment = create_equipment(client, auth_headers, "qPCR", 8)
    create_equipment(client, auth_headers, "microscopy", 8)
    low = create_sample(client, auth_headers, project["id"], "ENZ-LOW", 1, 4)
    high = create_sample(client, auth_headers, project["id"], "ENZ-HIGH", 5, 4)

    optimize_response = client.post(
        "/planner/optimize",
        headers=auth_headers,
        json={
            "sample_ids": [low["id"], high["id"]],
            "horizon_days": 3,
            "start_date": str(date.today()),
        },
    )
    assert optimize_response.status_code == 200
    plan = optimize_response.json()
    assert len(plan["scheduled"]) == 2
    assert plan["scheduled"][0]["sample_code"] == "ENZ-HIGH"
    assert {item["equipment_id"] for item in plan["scheduled"]} == {equipment["id"]}
    assert plan["unscheduled"] == []

    commit_response = client.post(
        "/planner/commit",
        headers=auth_headers,
        json={
            "sample_ids": [low["id"], high["id"]],
            "horizon_days": 3,
            "start_date": str(date.today()),
        },
    )
    assert commit_response.status_code == 201
    committed = commit_response.json()
    assert len(committed["created_runs"]) == 2

    runs_response = client.get("/runs", headers=auth_headers)
    assert runs_response.status_code == 200
    assert len(runs_response.json()) == 2

    run_id = runs_response.json()[0]["id"]
    update_response = client.patch(
        f"/runs/{run_id}",
        headers=auth_headers,
        json={"status": "completed", "actual_hours": 3},
    )
    assert update_response.status_code == 200
    assert update_response.json()["status"] == "completed"


def test_planner_reports_unscheduled_samples(client, auth_headers):
    project = create_project(client, auth_headers)
    sample = create_sample(client, auth_headers, project["id"], "NO-METHOD", 3, 2, "HPLC")

    response = client.post(
        "/planner/optimize",
        headers=auth_headers,
        json={"sample_ids": [sample["id"]], "horizon_days": 2},
    )
    assert response.status_code == 200
    payload = response.json()
    assert payload["scheduled"] == []
    assert payload["unscheduled"][0]["sample_id"] == sample["id"]
    assert "Нет доступного прибора" in payload["unscheduled"][0]["reason"]
