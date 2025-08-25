import pytest
from backend.app.agents.router import route

@pytest.mark.asyncio
async def test_route_math():
    assert await route("70 + 12") == "MathAgent"

@pytest.mark.asyncio
async def test_route_knowledge():
    assert await route("Qual a taxa da maquininha?") == "KnowledgeAgent"
