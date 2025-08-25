import pytest
from backend.app.agents.math import math_answer

@pytest.mark.asyncio
async def test_math_simple():
    text, meta = await math_answer("65 x 3.11")
    assert text.startswith("202.") or text.startswith("202")
