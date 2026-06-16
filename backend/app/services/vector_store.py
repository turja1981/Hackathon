from __future__ import annotations

import json
import os
import pickle
from pathlib import Path
from typing import Dict, List, Optional

import numpy as np

from app.config import settings
from app.services.embeddings import embedding_service
from app.utils.logging import get_logger

logger = get_logger(__name__)


class VectorStore:
    """FAISS-backed vector store for paper search."""

    def __init__(self) -> None:
        self._index = None
        self._papers: List[Dict] = []
        self._index_path = Path(settings.FAISS_INDEX_PATH)

    def _ensure_faiss(self):
        import faiss
        return faiss

    def _init_index(self) -> None:
        faiss = self._ensure_faiss()
        dim = embedding_service.dim
        # IndexFlatIP with normalized vectors = cosine similarity
        self._index = faiss.IndexFlatIP(dim)

    @property
    def paper_count(self) -> int:
        return len(self._papers)

    def load_or_build(self, papers_json_path: str = "./data/sample_papers.json") -> None:
        idx_file = self._index_path / "index.faiss"
        meta_file = self._index_path / "metadata.pkl"

        loaded = False
        if idx_file.exists() and meta_file.exists():
            try:
                self._load_from_disk(idx_file, meta_file)
                expected_dim = embedding_service.dim
                if self._index is not None and self._index.d != expected_dim:
                    logger.warning(
                        "faiss_dim_mismatch_rebuilding",
                        stored=self._index.d,
                        expected=expected_dim,
                    )
                    self._index = None
                    self._papers = []
                else:
                    logger.info("loading_faiss_index", path=str(idx_file))
                    loaded = True
            except Exception as exc:
                logger.warning("faiss_load_failed_rebuilding", error=str(exc))
                self._index = None
                self._papers = []

        if not loaded:
            logger.info("building_faiss_index", source=papers_json_path)
            papers = self._load_papers_json(papers_json_path)
            self.add_papers(papers)
            self._save_to_disk(idx_file, meta_file)

        logger.info("vector_store_ready", paper_count=self.paper_count)

    def _load_papers_json(self, path: str) -> List[Dict]:
        with open(path, "r") as f:
            return json.load(f)

    def add_papers(self, papers: List[Dict]) -> List[str]:
        if not papers:
            return []

        if self._index is None:
            self._init_index()

        texts = [f"{p.get('title', '')} {p.get('abstract', '')}" for p in papers]
        embeddings = embedding_service.encode(texts)

        import faiss
        self._index.add(embeddings.astype(np.float32))  # type: ignore[union-attr]
        self._papers.extend(papers)

        added_ids = [p.get("id", str(len(self._papers) - len(papers) + i)) for i, p in enumerate(papers)]
        logger.info("papers_added", count=len(papers))
        return added_ids

    def search(
        self,
        query: str,
        k: int = 10,
        keyword_filter: Optional[str] = None,
    ) -> List[Dict]:
        if self._index is None or self.paper_count == 0:
            return []

        k = min(k, self.paper_count)
        q_emb = embedding_service.encode([query])

        import faiss
        scores, indices = self._index.search(q_emb.astype(np.float32), k)  # type: ignore[union-attr]

        results = []
        for score, idx in zip(scores[0], indices[0]):
            if idx < 0:
                continue
            paper = dict(self._papers[idx])
            paper["score"] = float(score)

            # Optional keyword filter
            if keyword_filter:
                combined = f"{paper.get('title','')} {paper.get('abstract','')} {' '.join(paper.get('keywords',[]))}".lower()
                if keyword_filter.lower() not in combined:
                    continue

            results.append(paper)

        return results

    def get_by_id(self, paper_id: str) -> Optional[Dict]:
        for p in self._papers:
            if p.get("id") == paper_id:
                return dict(p)
        return None

    def get_by_ids(self, ids: List[str]) -> List[Dict]:
        id_set = set(ids)
        return [dict(p) for p in self._papers if p.get("id") in id_set]

    def _save_to_disk(self, idx_file: Path, meta_file: Path) -> None:
        import faiss
        idx_file.parent.mkdir(parents=True, exist_ok=True)
        faiss.write_index(self._index, str(idx_file))  # type: ignore[union-attr]
        with open(meta_file, "wb") as f:
            pickle.dump(self._papers, f)
        logger.info("faiss_index_saved", path=str(idx_file))

    def _load_from_disk(self, idx_file: Path, meta_file: Path) -> None:
        import faiss
        self._index = faiss.read_index(str(idx_file))
        with open(meta_file, "rb") as f:
            self._papers = pickle.load(f)


vector_store = VectorStore()
