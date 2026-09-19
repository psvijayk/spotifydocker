# Architecture

```text
                 PDF / Documents
                        |
                        v
                 PDF Extraction
                        |
                        v
                 Section / Chunking
                        |
              +---------+---------+
              |                   |
              v                   v
       Vector Pipeline      Knowledge Graph
              |                   |
          Embeddings        Entity Extraction
              |                   |
         FAISS/PGVector      Relationships
              |                   |
              |                 Neo4j
              |                   |
              +---------+---------+
                        |
                        v
                Hybrid Retrieval
                        |
                        v
                Guardrails Layer
                        |
                        v
                 Context Fusion
                        |
                        v
                       LLM
                        |
                        v
                     Answer
```

## Guardrail points

1. User question validation
2. Prompt-injection detection
3. Retrieval/context limits
4. Evidence sufficiency
5. Output leakage detection
6. Maximum answer length

The guardrail module is intentionally isolated so it can be replaced by Guardrails AI or NVIDIA NeMo Guardrails later.
