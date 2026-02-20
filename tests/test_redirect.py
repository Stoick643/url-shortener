import pytest


@pytest.mark.asyncio
async def test_redirect(client):
    create_resp = await client.post("/links", json={"url": "https://example.com"})
    code = create_resp.json()["short_code"]

    response = await client.get(f"/{code}", follow_redirects=False)
    assert response.status_code == 302
    assert response.headers["location"] == "https://example.com/"


@pytest.mark.asyncio
async def test_redirect_increments_clicks(client, auth_headers):
    create_resp = await client.post("/links", json={"url": "https://example.com"})
    code = create_resp.json()["short_code"]

    await client.get(f"/{code}", follow_redirects=False)
    await client.get(f"/{code}", follow_redirects=False)

    link_resp = await client.get(f"/links/{code}", headers=auth_headers)
    assert link_resp.json()["total_clicks"] == 2


@pytest.mark.asyncio
async def test_redirect_not_found(client):
    response = await client.get("/nonexistent", follow_redirects=False)
    assert response.status_code == 404


@pytest.mark.asyncio
async def test_redirect_deleted_link(client, auth_headers):
    create_resp = await client.post("/links", json={"url": "https://example.com"})
    code = create_resp.json()["short_code"]

    await client.delete(f"/links/{code}", headers=auth_headers)

    response = await client.get(f"/{code}", follow_redirects=False)
    assert response.status_code == 410


@pytest.mark.asyncio
async def test_redirect_expired_link(client):
    create_resp = await client.post("/links", json={
        "url": "https://example.com",
        "expires_at": "2020-01-01T00:00:00Z",
    })
    code = create_resp.json()["short_code"]

    response = await client.get(f"/{code}", follow_redirects=False)
    assert response.status_code == 410


@pytest.mark.asyncio
async def test_redirect_max_clicks_reached(client, auth_headers):
    create_resp = await client.post("/links", json={
        "url": "https://example.com",
        "max_clicks": 1,
    })
    code = create_resp.json()["short_code"]

    # First click works
    resp1 = await client.get(f"/{code}", follow_redirects=False)
    assert resp1.status_code == 302

    # Second click denied
    resp2 = await client.get(f"/{code}", follow_redirects=False)
    assert resp2.status_code == 410


@pytest.mark.asyncio
async def test_qr_code(client):
    create_resp = await client.post("/links", json={"url": "https://example.com"})
    code = create_resp.json()["short_code"]

    response = await client.get(f"/{code}/qr")
    assert response.status_code == 200
    assert response.headers["content-type"] == "image/png"
    assert response.content[:8] == b"\x89PNG\r\n\x1a\n"


@pytest.mark.asyncio
async def test_qr_code_deleted_link(client, auth_headers):
    create_resp = await client.post("/links", json={"url": "https://example.com"})
    code = create_resp.json()["short_code"]

    await client.delete(f"/links/{code}", headers=auth_headers)

    response = await client.get(f"/{code}/qr")
    assert response.status_code == 410
