import re
from typing import Dict, Any, Tuple, List
from structlog.stdlib import BoundLogger
from .knowledge import knowledge_answer
from .math import math_answer

MATH_HINT = re.compile(r"^[\d\s\+\-\*\/\^\(\)\.x]+$", re.I)
KNOWLEDGE_KEYWORDS = re.compile(r"\b(taxa|fee|maquininha|máquina|ajuda|faq|suporte|infinitepay|link de pagamento|infinitetap)\b", re.I)

async def route(message: str) -> str:
    msg = message or ""
    is_mathy = bool(MATH_HINT.match(msg)) or re.search(r"\d+\s*[x\*]\s*\d+", msg)
    is_domain = bool(KNOWLEDGE_KEYWORDS.search(msg))
    decision = "MathAgent" if (is_mathy and not is_domain) else "KnowledgeAgent"
    print(f"[RouterAgent] decision={decision} msg='{msg[:80]}'", flush=True)
    return decision

async def router_agent(message: str, user_id: str, conversation_id: str, log: BoundLogger) -> Tuple[str, str, List[Dict[str, Any]]]:
    decision = await route(message)
    workflow = [{"agent": "RouterAgent", "decision": decision}]
    if decision == "MathAgent":
        resp, details = await math_answer(message)
        workflow.append({"agent": "MathAgent"})
        return resp, details, workflow
    else:
        resp, details = knowledge_answer(message, user_id, conversation_id, log)
        workflow.append({"agent": "KnowledgeAgent"})
        return resp, details, workflow
