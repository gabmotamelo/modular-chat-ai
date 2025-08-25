from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from .core.config import settings
from .core.logging import setup_logging
from .core.security import sanitize, looks_malicious
from .core.schemas import ChatRequest, ChatResponse, AgentTrace
from .agents.router import router_agent
from .core.redis import redis_client

log = setup_logging(settings.LOG_LEVEL)
app = FastAPI(title="Modular Chatbot (Python, LangChain)")

app.add_middleware(
    CORSMiddleware,
    allow_origins=[settings.CORS_ORIGINS],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

@app.post("/chat", response_model=ChatResponse)
async def chat(payload: ChatRequest):
    cleaned = sanitize(payload.message)
    if looks_malicious(cleaned):
        return ChatResponse(
            response="Sua mensagem parece insegura. Por favor, reformule.",
            source_agent_response="Blocked by prompt-injection guard.",
            agent_workflow=[AgentTrace(agent="RouterAgent", decision="blocked")]
        )
    try:
        reply, source, workflow = await router_agent(
            cleaned, payload.user_id, payload.conversation_id, log
        )
        item = {
            "timestamp": __import__("datetime").datetime.utcnow().isoformat()+"Z",
            "level": "INFO",
            "agent": "RouterAgent",
            "conversation_id": payload.conversation_id,
            "user_id": payload.user_id,
            "decision": workflow[0]["decision"],
        }
        log.info(item)
        await redis_client.rpush(f"logs:{payload.conversation_id}", str(item))
        return ChatResponse(
            response=reply,
            source_agent_response=source,
            agent_workflow=[AgentTrace(**w) for w in workflow]
        )
    except Exception:
        raise HTTPException(status_code=500, detail="Internal error")

@app.get("/logs/{conversation_id}")
async def get_logs(conversation_id: str):
    entries = await redis_client.lrange(f"logs:{conversation_id}", 0, -1)
    return {"logs": entries}
