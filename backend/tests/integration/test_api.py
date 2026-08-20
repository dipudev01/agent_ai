"""Integration tests: full request lifecycle through the FastAPI app with the
local (mock) LLM provider and in-memory stores."""

import pytest
from httpx import ASGITransport, AsyncClient

from app.main import app


@pytest.fixture
async def client():
    async with AsyncClient(
        transport=ASGITransport(app=app), base_url="http://test"
    ) as c:
        yield c


async def test_login_and_health(client):
    r = await client.get("/api/v1/health/live")
    assert r.status_code == 200
    assert r.json()["status"] == "ok"

    r = await client.post(
        "/api/v1/auth/login",
        json={"email": "customer@demo.com", "password": "demo1234"},
    )
    assert r.status_code == 200
    body = r.json()
    assert body["access_token"]
    assert body["tenant_id"] == "t_axisdemo"


async def test_chat_requires_auth(client):
    r = await client.post("/api/v1/chats", json={"message": "hi"})
    assert r.status_code == 401


async def test_chat_eligibility_flow(client):
    r = await client.post(
        "/api/v1/auth/login",
        json={"email": "customer@demo.com", "password": "demo1234"},
    )
    token = r.json()["access_token"]
    headers = {"Authorization": f"Bearer {token}"}

    r = await client.post(
        "/api/v1/chats",
        json={"message": "Can I get a ₹10 lakh personal loan?"},
        headers=headers,
    )
    assert r.status_code == 200
    body = r.json()
    assert body["agent"] == "loan_eligibility"
    assert "reply" in body


async def test_agent_discovery(client):
    r = await client.post(
        "/api/v1/auth/login",
        json={"email": "officer@demo.com", "password": "demo1234"},
    )
    token = r.json()["access_token"]
    headers = {"Authorization": f"Bearer {token}"}
    r = await client.get("/api/v1/agents", headers=headers)
    assert r.status_code == 200
    keys = {a["key"] for a in r.json()["agents"]}
    assert "supervisor" in keys
    assert "loan_eligibility" in keys
    assert len(keys) == 17


async def test_tools_require_auth(client):
    r = await client.get("/api/v1/agents/tools")
    assert r.status_code == 401


async def test_document_upload_rejects_large_file(client):
    r = await client.post(
        "/api/v1/auth/login",
        json={"email": "officer@demo.com", "password": "demo1234"},
    )
    token = r.json()["access_token"]
    headers = {"Authorization": f"Bearer {token}"}
    r = await client.post(
        "/api/v1/documents",
        files={"file": ("big.txt", b"x" * (26 * 1024 * 1024), "text/plain")},
        headers=headers,
    )
    assert r.status_code == 413