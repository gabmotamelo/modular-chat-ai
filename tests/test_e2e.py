import pytest
from httpx import AsyncClient
from backend.app.main import app

@pytest.mark.asyncio
async def test_chat_e2e():
    async with AsyncClient(app=app, base_url="http://test") as ac:
        r = await ac.post("/chat", json={"message":"70+12","user_id":"u1","conversation_id":"c1"})
        assert r.status_code == 200
        data = r.json()
        assert data["agent_workflow"][0]["decision"] in ("MathAgent","KnowledgeAgent")
