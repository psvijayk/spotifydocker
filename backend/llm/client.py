import json
from openai import OpenAI
from backend.config import settings


class LLMClient:
    def __init__(self):
        self.client = OpenAI(api_key=settings.openai_api_key)

    def embed(self, texts: list[str]) -> list[list[float]]:
        response = self.client.embeddings.create(
            model=settings.openai_embedding_model,
            input=texts,
        )
        return [item.embedding for item in response.data]

    def extract_graph(self, text: str) -> dict:
        prompt = f"""
Extract a small knowledge graph from the text below.

Return ONLY valid JSON:
{{
  "entities": ["entity1", "entity2"],
  "relationships": [
    {{"source": "entity1", "relation": "RELATION", "target": "entity2"}}
  ]
}}

Rules:
- Use concise entity names.
- Do not invent facts.
- Only extract information explicitly supported by the text.

TEXT:
{text}
"""
        response = self.client.chat.completions.create(
            model=settings.openai_chat_model,
            temperature=0,
            response_format={"type": "json_object"},
            messages=[
                {"role": "system", "content": "You extract factual knowledge graphs."},
                {"role": "user", "content": prompt},
            ],
        )
        return json.loads(response.choices[0].message.content)

    def answer(self, question: str, vector_context: list[dict], graph_context: list[dict]) -> str:
        vector_text = "\n\n".join(
            f"[Document: {x.get('source')} | page {x.get('page')}]\n{x.get('text','')}"
            for x in vector_context
        )
        graph_text = json.dumps(graph_context, ensure_ascii=False, indent=2)

        prompt = f"""
Answer the user's question using ONLY the supplied evidence.

VECTOR EVIDENCE:
{vector_text}

KNOWLEDGE GRAPH EVIDENCE:
{graph_text}

QUESTION:
{question}

Requirements:
- Do not invent facts.
- If the evidence is insufficient, say so clearly.
- Prefer concise, useful answers.
- When possible, mention the relevant source/page.
"""
        response = self.client.chat.completions.create(
            model=settings.openai_chat_model,
            temperature=0,
            messages=[
                {"role": "system", "content": "You are a grounded enterprise RAG assistant."},
                {"role": "user", "content": prompt},
            ],
        )
        return response.choices[0].message.content.strip()
