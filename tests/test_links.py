import pytest


@pytest.mark.asyncio
async def test_create_link(client):
    response = await client.post("/links", json={"url": "https://example.com"})
    assert response.status_code == 201
    data = response.json()
    assert data["original_url"] == "https://example.com/"
    assert len(data["short_code"]) == 8
    assert data["is_vanity"] is False
    assert data["is_active"] is True
    assert data["total_clicks"] == 0
    assert data["qr_code_base64"] is not None
    assert "short_url" in data


@pytest.mark.asyncio
async def test_create_link_with_vanity_slug(client):
    response = await client.post("/links", json={
        "url": "https://example.com",
        "custom_slug": "my-link",
    })
    assert response.status_code == 201
    data = response.json()
    assert data["short_code"] == "my-link"
    assert data["is_vanity"] is True


@pytest.mark.asyncio
async def test_create_link_duplicate_vanity(client):
    await client.post("/links", json={"url": "https://example.com", "custom_slug": "taken"})
    response = await client.post("/links", json={"url": "https://other.com", "custom_slug": "taken"})
    assert response.status_code == 409


@pytest.mark.asyncio
async def test_create_link_reserved_slug(client):
    response = await client.post("/links", json={
        "url": "https://example.com",
        "custom_slug": "admin",
    })
    assert response.status_code == 422


@pytest.mark.asyncio
async def test_create_link_invalid_slug(client):
    response = await client.post("/links", json={
        "url": "https://example.com",
        "custom_slug": "no spaces!",
    })
    assert response.status_code == 422


@pytest.mark.asyncio
async def test_create_link_slug_too_short(client):
    response = await client.post("/links", json={
        "url": "https://example.com",
        "custom_slug": "ab",
    })
    assert response.status_code == 422


@pytest.mark.asyncio
async def test_list_links_requires_auth(client):
    response = await client.get("/links")
    assert response.status_code == 403


@pytest.mark.asyncio
async def test_list_links(client, auth_headers):
    # Create a few links
    await client.post("/links", json={"url": "https://example.com"})
    await client.post("/links", json={"url": "https://other.com"})

    response = await client.get("/links", headers=auth_headers)
    assert response.status_code == 200
    data = response.json()
    assert data["total"] == 2
    assert len(data["links"]) == 2
    assert data["page"] == 1
    assert data["per_page"] == 20


@pytest.mark.asyncio
async def test_list_links_pagination(client, auth_headers):
    for i in range(5):
        await client.post("/links", json={"url": f"https://example{i}.com"})

    response = await client.get("/links?page=1&per_page=2", headers=auth_headers)
    data = response.json()
    assert data["total"] == 5
    assert len(data["links"]) == 2


@pytest.mark.asyncio
async def test_get_link(client, auth_headers):
    create_resp = await client.post("/links", json={"url": "https://example.com"})
    code = create_resp.json()["short_code"]

    response = await client.get(f"/links/{code}", headers=auth_headers)
    assert response.status_code == 200
    assert response.json()["short_code"] == code


@pytest.mark.asyncio
async def test_get_link_not_found(client, auth_headers):
    response = await client.get("/links/nonexistent", headers=auth_headers)
    assert response.status_code == 404


@pytest.mark.asyncio
async def test_update_link(client, auth_headers):
    create_resp = await client.post("/links", json={"url": "https://example.com"})
    code = create_resp.json()["short_code"]

    response = await client.patch(
        f"/links/{code}",
        json={"max_clicks": 100},
        headers=auth_headers,
    )
    assert response.status_code == 200
    assert response.json()["max_clicks"] == 100


@pytest.mark.asyncio
async def test_delete_link(client, auth_headers):
    create_resp = await client.post("/links", json={"url": "https://example.com"})
    code = create_resp.json()["short_code"]

    response = await client.delete(f"/links/{code}", headers=auth_headers)
    assert response.status_code == 200

    # Verify soft-deleted
    get_resp = await client.get(f"/links/{code}", headers=auth_headers)
    assert get_resp.json()["is_active"] is False
