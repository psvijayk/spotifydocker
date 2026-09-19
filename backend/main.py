from pathlib import Path
import tempfile

from fastapi import FastAPI, File, UploadFile, HTTPException
from fastapi.middleware.cors import CORSMiddleware

from backend.schemas import AskRequest, AskResponse, IngestResponse
from backend.ingestion.pipeline import IngestionPipeline
from backend.retrieval.hybrid import HybridRetriever


app = FastAPI(
    title="Hybrid RAG + Knowledge Graph API",
    version="1.0.0",
    description="Vector + Neo4j hybrid RAG with guardrails",
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


@app.get("/health")
def health():
    return {"status": "ok"}


@app.post("/ingest", response_model=IngestResponse)
async def ingest(file: UploadFile = File(...)):
    if not file.filename.lower().endswith(".pdf"):
        raise HTTPException(status_code=400, detail="Only PDF files are supported.")

    data = await file.read()

    with tempfile.NamedTemporaryFile(suffix=".pdf", delete=False) as tmp:
        tmp.write(data)
        tmp_path = tmp.name

    try:
        pipeline = IngestionPipeline()
        chunks, graph_items = pipeline.run(tmp_path, file.filename)
        return IngestResponse(
            filename=file.filename,
            chunks=chunks,
            graph_items=graph_items,
            status="ingested",
        )
    except Exception as exc:
        raise HTTPException(status_code=500, detail=str(exc))


@app.post("/ask", response_model=AskResponse)
def ask(request: AskRequest):
    try:
        result = HybridRetriever().answer(request.question)

        sources = []
        for item in result["vector"]:
            sources.append({
                "source": item.get("source", ""),
                "chunk_id": item.get("chunk_id", ""),
                "score": item.get("score"),
                "type": "vector",
            })

        for item in result["graph"]:
            sources.append({
                "source": "neo4j",
                "chunk_id": item.get("entity", ""),
                "score": None,
                "type": "graph",
            })

        return AskResponse(
            answer=result["answer"],
            sources=sources,
            graph_context=result["graph"],
            guardrail_flags=result["flags"],
        )
    except Exception as exc:
        raise HTTPException(status_code=500, detail=str(exc))
