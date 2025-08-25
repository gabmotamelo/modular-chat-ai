from pydantic import BaseModel, Field
from typing import List, Optional

class ChatRequest(BaseModel):
    message: str = Field(min_length=1)
    user_id: str = Field(min_length=1)
    conversation_id: str = Field(min_length=1)

class AgentTrace(BaseModel):
    agent: str
    decision: Optional[str] = None

class ChatResponse(BaseModel):
    response: str
    source_agent_response: str
    agent_workflow: List[AgentTrace]
