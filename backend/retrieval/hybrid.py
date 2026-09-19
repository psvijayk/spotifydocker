import re
from backend.config import settings
from backend.llm.client import LLMClient
from backend.vector.store import VectorStore
from backend.graph.neo4j_store import Neo4jStore
from backend.guardrails.guards import Guardrails


class HybridRetriever:
    def __init__(self):
        self.llm = LLMClient()
        self.vector = VectorStore()
        self.graph = Neo4jStore(
            settings.neo4j_uri,
            settings.neo4j_username,
            settings.neo4j_password,
        )
        self.guards = Guardrails()

    def retrieve(self, question: str):
        input_result = self.guards.validate_input(question)
        if not input_result.allowed:
            return {
                "blocked": True,
                "answer": "The question was blocked by the input safety guardrail.",
                "flags": input_result.flags,
                "vector": [],
                "graph": [],
            }

        q_embedding = self.llm.embed([input_result.text])[0]
        vector_results = self.vector.search(q_embedding, settings.vector_top_k)

        # Lightweight term extraction for graph lookup.
        terms = [
            x for x in re.findall(r"[A-Za-z0-9][A-Za-z0-9_-]{2,}", question)
            if x.lower() not in {"what", "when", "where", "which", "with", "from", "that", "this", "are", "the"}
        ][:10]

        graph_results = self.graph.search(terms, settings.graph_top_k)

        vector_results, graph_results, context_flags = self.guards.validate_context(
            vector_results, graph_results
        )

        return {
            "blocked": False,
            "question": input_result.text,
            "vector": vector_results,
            "graph": graph_results,
            "flags": context_flags,
        }

    def answer(self, question: str):
        result = self.retrieve(question)

        if result["blocked"]:
            return {
                "answer": result["answer"],
                "vector": [],
                "graph": [],
                "flags": result["flags"],
            }

        answer = self.llm.answer(
            result["question"],
            result["vector"],
            result["graph"],
        )

        output_result = self.guards.validate_output(
            answer,
            bool(result["vector"] or result["graph"]),
        )

        return {
            "answer": output_result.text,
            "vector": result["vector"],
            "graph": result["graph"],
            "flags": result["flags"] + output_result.flags,
        }
