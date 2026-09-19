from pathlib import Path
import json
import faiss
import numpy as np


class VectorStore:
    def __init__(self, directory="storage/faiss"):
        self.directory = Path(directory)
        self.directory.mkdir(parents=True, exist_ok=True)
        self.index_path = self.directory / "index.faiss"
        self.meta_path = self.directory / "metadata.json"
        self.index = None
        self.metadata = []
        self._load()

    def _load(self):
        if self.index_path.exists() and self.meta_path.exists():
            self.index = faiss.read_index(str(self.index_path))
            self.metadata = json.loads(self.meta_path.read_text(encoding="utf-8"))

    def add(self, embeddings: list[list[float]], metadata: list[dict]):
        if not embeddings:
            return
        arr = np.asarray(embeddings, dtype="float32")
        faiss.normalize_L2(arr)

        if self.index is None:
            self.index = faiss.IndexFlatIP(arr.shape[1])

        self.index.add(arr)
        self.metadata.extend(metadata)
        self._persist()

    def _persist(self):
        faiss.write_index(self.index, str(self.index_path))
        self.meta_path.write_text(
            json.dumps(self.metadata, ensure_ascii=False, indent=2),
            encoding="utf-8",
        )

    def search(self, embedding: list[float], top_k: int = 5):
        if self.index is None or self.index.ntotal == 0:
            return []

        query = np.asarray([embedding], dtype="float32")
        faiss.normalize_L2(query)
        scores, ids = self.index.search(query, min(top_k, self.index.ntotal))

        results = []
        for score, idx in zip(scores[0], ids[0]):
            if idx < 0:
                continue
            item = dict(self.metadata[idx])
            item["score"] = float(score)
            results.append(item)
        return results
