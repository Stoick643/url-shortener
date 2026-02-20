import pytest


@pytest.mark.asyncio
async def test_stats_requires_auth(client):
    response = await client.get("/links/somecode/stats")
    assert response.status_code == 403


@pytest.mark.asyncio
async def test_stats_not_found(client, auth_headers):
    response = await client.get("/links/nonexistent/stats", headers=auth_headers)
    assert response.status_code == 404


@pytest.mark.asyncio
async def test_stats_empty(client, auth_headers):
    create_resp = await client.post("/links", json={"url": "https://example.com"})
    code = create_resp.json()["short_code"]

    response = await client.get(f"/links/{code}/stats", headers=auth_headers)
    assert response.status_code == 200
    data = response.json()
    assert data["total_clicks"] == 0
    assert data["unique_clicks"] == 0
    assert data["clicks"] == []


@pytest.mark.asyncio
async def test_stats_with_clicks(client, auth_headers):
    create_resp = await client.post("/links", json={"url": "https://example.com"})
    code = create_resp.json()["short_code"]

    # Make some clicks
    await client.get(f"/{code}", follow_redirects=False)
    await client.get(f"/{code}", follow_redirects=False)
    await client.get(f"/{code}", follow_redirects=False)

    response = await client.get(f"/links/{code}/stats", headers=auth_headers)
    assert response.status_code == 200
    data = response.json()
    assert data["total_clicks"] == 3
    assert data["unique_clicks"] == 1  # Same IP
    assert len(data["clicks"]) == 3
    assert data["clicks"][0]["country"] == "unknown"


@pytest.mark.asyncio
async def test_stats_click_details(client, auth_headers):
    create_resp = await client.post("/links", json={"url": "https://example.com"})
    code = create_resp.json()["short_code"]

    await client.get(
        f"/{code}",
        follow_redirects=False,
        headers={"referer": "https://google.com", "cf-ipcountry": "US"},
    )

    response = await client.get(f"/links/{code}/stats", headers=auth_headers)
    data = response.json()
    click = data["clicks"][0]
    assert click["referrer"] == "https://google.com"
    assert click["country"] == "US"
    assert "ip_hash" in click
    assert "clicked_at" in click
