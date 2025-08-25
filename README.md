# Modular Chatbot — Python (FastAPI) + LangChain + Redis + React

**Default:** 100% offline (embeddings locais + `MOCK_MODE=1`).  

## Run (Local)
```bash
python -m venv .venv && source .venv/bin/activate
pip install -r backend/requirements.txt

# Indexe algumas URLs reais do Help Center no indexer.py
python backend/app/rag/indexer.py

# Rode backend offline
export MOCK_MODE=1
uvicorn app.main:app --host 0.0.0.0 --port 8080 --app-dir backend --reload
```

### Frontend (React + Vite)
```bash
cd frontend
npm install
# VITE_API_URL padrão: http://localhost:8080
npm run dev -- --host
```

## Docker Compose
```bash
docker-compose -f infra/compose/docker-compose.yml up --build
# Frontend em http://localhost:5173 , Backend em http://localhost:8080
```

## Kubernetes (minikube/k3d)
```bash
kubectl apply -f infra/k8s
```

## API
POST `/chat`
```json
{
  "message": "Qual a taxa da maquininha?",
  "user_id": "client789",
  "conversation_id": "conv-1234"
}
```

## Structured Logs
Example log entries from different agents:

**KnowledgeAgent:**
```json
{
  "event": {
    "agent": "KnowledgeAgent",
    "conversation_id": "conv-2",
    "user_id": "u1", 
    "execution_time": 19814,
    "sources": []
  },
  "timestamp": "2025-08-25T08:10:11.267017Z",
  "level": "info"
}
```

**RouterAgent:**
```json
{
  "event": {
    "timestamp": "2025-08-25T08:11:51.609658Z",
    "level": "INFO",
    "agent": "RouterAgent",
    "conversation_id": "conv-2",
    "user_id": "u1",
    "decision": "MathAgent"
  },
  "timestamp": "2025-08-25T08:11:51.609712Z",
  "level": "info"
}
```



## Tests
```bash
pytest -q
```
