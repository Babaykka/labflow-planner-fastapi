def test_register_login_and_current_user(client):
    protected_response = client.get("/users/me")
    assert protected_response.status_code == 401

    register_response = client.post(
        "/auth/register",
        json={
            "email": "researcher@example.com",
            "username": "researcher",
            "password": "StrongPass123",
            "role": "researcher",
        },
    )
    assert register_response.status_code == 201
    registered = register_response.json()
    assert registered["email"] == "researcher@example.com"
    assert "hashed_password" not in registered

    duplicate_response = client.post(
        "/auth/register",
        json={
            "email": "researcher@example.com",
            "username": "another",
            "password": "StrongPass123",
        },
    )
    assert duplicate_response.status_code == 409

    token_response = client.post(
        "/auth/token",
        data={"username": "researcher@example.com", "password": "StrongPass123"},
    )
    assert token_response.status_code == 200
    token_payload = token_response.json()
    assert token_payload["token_type"] == "bearer"

    current_response = client.get(
        "/users/me",
        headers={"Authorization": f"Bearer {token_payload['access_token']}"},
    )
    assert current_response.status_code == 200
    assert current_response.json()["username"] == "researcher"


def test_login_rejects_invalid_password(client):
    client.post(
        "/auth/register",
        json={
            "email": "invalid-login@example.com",
            "username": "invalidlogin",
            "password": "StrongPass123",
        },
    )
    response = client.post(
        "/auth/token",
        data={"username": "invalid-login@example.com", "password": "wrong"},
    )
    assert response.status_code == 401
