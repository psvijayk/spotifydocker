# Hybrid RAG + Knowledge Graph + Guardrails

A production-oriented starter application based on the supplied architecture:

PDF/Documents -> Extraction -> Chunking -> Vector Pipeline + Knowledge Graph -> Hybrid Retrieval -> Guardrails -> LLM -> Answer

## Stack

- Frontend: Streamlit
- Backend: FastAPI
- Vector store: FAISS (local)
- Knowledge graph: Neo4j
- LLM/embeddings: OpenAI
- PDF extraction: PyMuPDF
- Guardrails: deterministic input/output safety and grounding checks implemented in `backend/guardrails/`
- Optional OCR can be added later with Tesseract
- No Docker required

## Project structure

```text
hybrid-rag-guardrails/
├── backend/
│   ├── main.py
│   ├── config.py
│   ├── schemas.py
│   ├── ingestion/
│   │   ├── pdf_loader.py
│   │   └── pipeline.py
│   ├── vector/
│   │   └── store.py
│   ├── graph/
│   │   └── neo4j_store.py
│   ├── retrieval/
│   │   └── hybrid.py
│   ├── llm/
│   │   └── client.py
│   └── guardrails/
│       └── guards.py
├── frontend/
│   └── streamlit_app.py
├── data/
│   └── documents/
├── storage/
│   ├── faiss/
│   └── metadata/
├── .env.example
├── requirements.txt
└── README.md
```

## 1. Create virtual environment

Windows:

```powershell
python -m venv .venv
.venv\Scripts\activate
```

Linux/macOS:

```bash
python3 -m venv .venv
source .venv/bin/activate
```

## 2. Install

```bash
pip install -r requirements.txt
```

## 3. Configure `.env`

Copy `.env.example` to `.env` and configure:

```env
OPENAI_API_KEY=your_key
OPENAI_CHAT_MODEL=gpt-4o-mini
OPENAI_EMBEDDING_MODEL=text-embedding-3-small

NEO4J_URI=bolt://localhost:7687
NEO4J_USERNAME=neo4j
NEO4J_PASSWORD=your_password

VECTOR_TOP_K=5
GRAPH_TOP_K=5
MAX_CONTEXT_CHARS=16000
```

Neo4j can be local or Neo4j Aura.

## 4. Start Neo4j

Make sure Neo4j is reachable before ingestion.

## 5. Start FastAPI

```bash
uvicorn backend.main:app --reload --host 0.0.0.0 --port 8000
```

Swagger:

```text
http://localhost:8000/docs
```

## 6. Start Streamlit

In another terminal:

```bash
streamlit run frontend/streamlit_app.py
```

Open:

```text
http://localhost:8501
```

## API flow

### Health

```http
GET /health
```

### Ingest PDF

```http
POST /ingest
multipart/form-data
file=<pdf>
```

The ingestion pipeline:

1. Extract PDF text
2. Split into chunks
3. Generate embeddings
4. Persist FAISS index
5. Extract entities and relationships
6. Persist graph nodes/relationships in Neo4j

### Ask

```http
POST /ask
Content-Type: application/json

{
  "question": "What schemes are available for farmers?"
}
```

The query pipeline:

1. Input guardrail
2. Vector semantic search
3. Knowledge graph search
4. Hybrid context fusion
5. LLM answer generation
6. Output/grounding guardrail

## Guardrails

The guardrail layer is intentionally deterministic and transparent.

### Input guards

- Empty/oversized questions
- Prompt injection patterns
- Requests to reveal system instructions
- Unsafe command-style prompts

### Retrieval guards

- Limits context size
- Removes duplicate chunks
- Keeps source metadata
- Requires graph/vector context where configured

### Output guards

- Rejects obvious prompt/system-instruction leakage
- Checks that factual answers have retrieved evidence
- Limits answer size
- Adds a fallback response when evidence is insufficient
- Returns sources with the answer

You can replace/extend `backend/guardrails/guards.py` with Guardrails AI, NVIDIA NeMo Guardrails, or enterprise policy engines later.

## Hybrid strategy

The application deliberately keeps vector and graph retrieval separate.

Vector retrieval answers:
- semantic similarity
- document passages
- natural-language questions

Graph retrieval answers:
- entities
- relationships
- connected concepts
- explicit graph facts

The final LLM prompt receives both contexts.

## Important production recommendations

For production, replace local FAISS with a managed/vector database if required, add authentication, rate limiting, background ingestion jobs, object storage, observability, audit logging, document versioning and a proper graph entity-resolution pipeline.

For large document volumes, move ingestion to a queue/worker architecture rather than running it directly in the FastAPI request.



## Docker deployment

This project includes Docker support for FastAPI and Streamlit.

### Configure environment

Create `.env` from `.env.example` and set:

```env
OPENAI_API_KEY=your_key
NEO4J_URI=neo4j+s://YOUR_INSTANCE.databases.neo4j.io
NEO4J_USERNAME=neo4j
NEO4J_PASSWORD=your_aura_password
```

For Neo4j Aura, use the exact `neo4j+s://...databases.neo4j.io` URI from Aura.

### Start

```powershell
docker compose up --build
```

Open Streamlit:

```text
http://localhost:8501
```

FastAPI Swagger:

```text
http://localhost:8000/docs
```

Background mode:

```powershell
docker compose up --build -d
```

Logs:

```powershell
docker compose logs -f backend
docker compose logs -f frontend
```

Stop:

```powershell
docker compose down
```

### Neo4j Aura from Docker

Do not use `localhost` for Neo4j Aura. The backend container needs outbound DNS/network access to the Aura hostname.

Test DNS from the backend container:

```powershell
docker compose exec backend python -c "import socket; print(socket.gethostbyname('YOUR_INSTANCE.databases.neo4j.io'))"
```

Test Neo4j connectivity:

```powershell
docker compose exec backend python -c "from backend.config import settings; from backend.graph.neo4j_store import Neo4jStore; n=Neo4jStore(settings.neo4j_uri, settings.neo4j_username, settings.neo4j_password); n.driver.verify_connectivity(); print('NEO4J CONNECTION OK')"
```
