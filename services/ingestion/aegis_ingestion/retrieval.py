"""FAISS lexical evidence lookup. Scores measure overlap, not truth or confidence."""

import hashlib
import re

import faiss
import numpy as np
from aegis_contracts.manuals import EvidenceHit, ManualPage
from numpy.typing import NDArray

from aegis_ingestion.corpus import cite

DIMENSION = 256


def embed(text: str) -> NDArray[np.float32]:
    vector = np.zeros(DIMENSION, dtype=np.float32)
    for token in re.findall(r"[a-z0-9]+(?:-[a-z0-9]+)*", text.lower()):
        digest = hashlib.sha256(token.encode()).digest()
        vector[int.from_bytes(digest[:2], "big") % DIMENSION] += 1 if digest[2] & 1 else -1
    norm = float(np.linalg.norm(vector))
    return vector / norm if norm else vector


class ManualIndex:
    def __init__(self, pages: list[ManualPage]) -> None:
        if not 1 <= len(pages) <= 1000:
            raise ValueError("Local corpus bound exceeded")
        self.pages = pages
        faiss.omp_set_num_threads(1)
        self.index = faiss.IndexFlatIP(DIMENSION)
        self.index.add(np.vstack([embed(page.text) for page in pages]))

    def search(self, query: str, top_k: int = 5) -> list[EvidenceHit]:
        if not query.strip() or len(query) > 500 or not 1 <= top_k <= 10:
            raise ValueError("Invalid bounded retrieval query")
        scores, indices = self.index.search(
            embed(query).reshape(1, -1), min(top_k, len(self.pages))
        )
        hits = []
        for score, index in zip(scores[0], indices[0], strict=True):
            page = self.pages[int(index)]
            if not page.text.strip():
                continue
            quote = next(
                (line for line in page.text.splitlines() if line.startswith("LIMIT ")),
                page.text[:500],
            )
            hits.append(
                EvidenceHit(
                    citation=cite(page, quote), score=float(score), untrusted_text=page.text
                )
            )
        return hits
