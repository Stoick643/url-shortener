import pytest

from app.config import settings


@pytest.mark.asyncio
async def test_login_success(client):
    response = await client.post("/auth/login", json={
        "username": settings.ADMIN_USERNAME,
        "password": settings.ADMIN_PASSWORD,
    })
    assert response.status_code == 200
    data = response.json()
    assert "access_token" in data
    assert data["token_type"] == "bearer"


@pytest.mark.asyncio
async def test_login_wrong_password(client):
    response = await client.post("/auth/login", json={
        "username": settings.ADMIN_USERNAME,
        "password": "wrongpassword",
    })
    assert response.status_code == 401


@pytest.mark.asyncio
async def test_login_wrong_username(client):
    response = await client.post("/auth/login", json={
        "username": "notadmin",
        "password": settings.ADMIN_PASSWORD,
    })
    assert response.status_code == 401


@pytest.mark.asyncio
async def test_protected_route_no_token(client):
    response = await client.get("/links")
    assert response.status_code == 403


@pytest.mark.asyncio
async def test_protected_route_invalid_token(client):
    response = await client.get("/links", headers={"Authorization": "Bearer invalid"})
    assert response.status_code == 401
