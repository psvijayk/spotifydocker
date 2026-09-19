from pathlib import Path
from backend.ingestion.pdf_loader import extract_pages, chunk_pages
from backend.llm.client import LLMClient
from backend.vector.store import VectorStore
from backend.graph.neo4j_store import Neo4jStore
from backend.config import settings


class IngestionPipeline:
    def __init__(self):
        self.llm = LLMClient()
        self.vector = VectorStore()
        self.graph = Neo4jStore(
            settings.neo4j_uri,
            settings.neo4j_username,
            settings.neo4j_password,
        )
        self.graph.create_constraints()

    def run(self, pdf_path: str, filename: str):
        pages = extract_pages(pdf_path)
        chunks = chunk_pages(pages)

        texts = [x["text"] for x in chunks]
        embeddings = self.llm.embed(texts)

        metadata = []
        graph_items = []

        for chunk, text in zip(chunks, texts):
            metadata.append({
                "chunk_id": chunk["chunk_id"],
                "source": filename,
                "page": chunk["page"],
                "text": text,
            })

            kg = self.llm.extract_graph(text)
            graph_items.append({
                "source": filename,
                "chunk_id": chunk["chunk_id"],
                **kg,
            })

        self.vector.add(embeddings, metadata)
        graph_count = self.graph.upsert(graph_items)

        return len(chunks), graph_count
