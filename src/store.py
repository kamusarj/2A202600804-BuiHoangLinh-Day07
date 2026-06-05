from __future__ import annotations

from typing import Any, Callable

from .chunking import _dot
from .embeddings import _mock_embed
from .models import Document


class EmbeddingStore:
    """
    A vector store for text chunks.

    Tries to use ChromaDB if available; falls back to an in-memory store.
    The embedding_fn parameter allows injection of mock embeddings for tests.
    """

    def __init__(
        self,
        collection_name: str = "documents",
        embedding_fn: Callable[[str], list[float]] | None = None,
    ) -> None:
        self._embedding_fn = embedding_fn or _mock_embed
        self._collection_name = collection_name
        self._use_chroma = False
        self._store: list[dict[str, Any]] = []
        self._collection = None
        self._next_index = 0

        try:
            import chromadb  # noqa: F401

            self._chroma_client = chromadb.Client()
            self._collection = self._chroma_client.get_or_create_collection(
                name=collection_name
            )
            self._use_chroma = True
        except Exception:
            self._use_chroma = False
            self._collection = None

    def _make_record(self, doc: Document) -> dict[str, Any]:
        return {
            "id": doc.id,
            "content": doc.content,
            "metadata": {**doc.metadata, "doc_id": doc.id},
            "embedding": self._embedding_fn(doc.content),
        }

    def _search_records(self, query: str, records: list[dict[str, Any]], top_k: int) -> list[dict[str, Any]]:
        query_emb = self._embedding_fn(query)
        scored = []
        for r in records:
            score = _dot(query_emb, r["embedding"])
            scored.append((score, r))
        scored.sort(key=lambda x: x[0], reverse=True)
        return [
            {"content": r["content"], "metadata": r["metadata"], "score": s}
            for s, r in scored[:top_k]
        ]

    def add_documents(self, docs: list[Document]) -> None:
        for doc in docs:
            record = self._make_record(doc)
            if self._use_chroma and self._collection is not None:
                self._collection.add(
                    ids=[doc.id],
                    documents=[doc.content],
                    embeddings=[record["embedding"]],
                    metadatas=[record["metadata"]],
                )
            self._store.append(record)

    def search(self, query: str, top_k: int = 5) -> list[dict[str, Any]]:
        return self._search_records(query, self._store, top_k)

    def get_collection_size(self) -> int:
        return len(self._store)

    def search_with_filter(self, query: str, top_k: int = 3, metadata_filter: dict = None) -> list[dict]:
        if not metadata_filter:
            return self.search(query, top_k)

        filtered = [
            r
            for r in self._store
            if all(
                r.get("metadata", {}).get(k) == v
                for k, v in metadata_filter.items()
            )
        ]

        if not filtered:
            return []

        return self._search_records(query, filtered, top_k)

    def delete_document(self, doc_id: str) -> bool:
        original_len = len(self._store)
        self._store = [
            r for r in self._store
            if r.get("metadata", {}).get("doc_id") != doc_id
        ]
        return len(self._store) < original_len
