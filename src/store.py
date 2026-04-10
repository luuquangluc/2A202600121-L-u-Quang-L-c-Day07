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
        persist_directory: str = "./chroma_db",
    ) -> None:
        self._embedding_fn = embedding_fn or _mock_embed
        self._collection_name = collection_name
        self._persist_directory = persist_directory
        self._use_chroma = False
        self._store: list[dict[str, Any]] = []
        self._collection = None
        self._next_index = 0

        try:
            import chromadb
            from chromadb.config import Settings

            # Initialize ChromaDB client
            self._client = chromadb.Client(
                Settings(
                    persist_directory=self._persist_directory,
                    anonymized_telemetry=False,
                )
            )

            # Create or get collection
            self._collection = self._client.get_or_create_collection(
                name=self._collection_name
            )

            # Sync index counter with existing records
            try:
                count = self._collection.count()
                self._next_index = count
            except Exception:
                self._next_index = 0

            self._use_chroma = True

        except Exception:
            # Fallback to in-memory storage
            self._use_chroma = False
            self._collection = None

    # ---------------------------------------------------------------------
    # Internal helpers
    # ---------------------------------------------------------------------

    def _make_record(self, doc: Document) -> dict[str, Any]:
        """Build a normalized stored record for one document chunk."""
        embedding = self._embedding_fn(doc.content)

        meta = dict(doc.metadata) if doc.metadata else {}
        meta["doc_id"] = doc.id

        record = {
            "id": f"chunk-{self._next_index}",
            "content": doc.content,
            "embedding": embedding,
            "metadata": meta,
        }
        self._next_index += 1
        return record

    def _search_records(
        self,
        query: str,
        records: list[dict[str, Any]],
        top_k: int,
    ) -> list[dict[str, Any]]:
        """Run in-memory similarity search."""
        if not records:
            return []

        query_embedding = self._embedding_fn(query)

        scored = []
        for r in records:
            score = _dot(query_embedding, r["embedding"])
            r_copy = r.copy()
            r_copy["score"] = score
            scored.append((score, r_copy))

        scored.sort(key=lambda x: x[0], reverse=True)
        return [r for _, r in scored[:top_k]]

    # ---------------------------------------------------------------------
    # Public API
    # ---------------------------------------------------------------------

    def add_documents(self, docs: list[Document]) -> None:
        """
        Embed each document's content and store it.

        For ChromaDB: use collection.add()
        For in-memory: append dicts to self._store
        """
        if not docs:
            return

        if self._use_chroma:
            ids = []
            documents = []
            embeddings = []
            metadatas = []

            for doc in docs:
                record = self._make_record(doc)
                ids.append(record["id"])
                documents.append(record["content"])
                embeddings.append(record["embedding"])
                metadatas.append(record["metadata"])

            self._collection.add(
                ids=ids,
                documents=documents,
                embeddings=embeddings,
                metadatas=metadatas,
            )
            return

        # Fallback: in-memory
        for doc in docs:
            record = self._make_record(doc)
            self._store.append(record)

    def search(self, query: str, top_k: int = 5) -> list[dict[str, Any]]:
        """Find the top_k most similar documents to query."""
        if self._use_chroma:
            query_embedding = self._embedding_fn(query)

            results = self._collection.query(
                query_embeddings=[query_embedding],
                n_results=top_k,
                include=["documents", "metadatas", "embeddings", "distances"]
            )

            output = []
            docs = results.get("documents", [[]])[0]
            metas = results.get("metadatas", [[]])[0]
            ids = results.get("ids", [[]])[0]
            embeddings = results.get("embeddings", [[]])[0]
            for doc, meta, doc_id, emb in zip(docs, metas, ids, embeddings):
                score = float(_dot(query_embedding, emb))
                output.append(
                    {
                        "id": doc_id,
                        "content": doc,
                        "metadata": meta or {},
                        "score": score,
                    }
                )
            return output

        return self._search_records(query, self._store, top_k)

    def get_collection_size(self) -> int:
        """Return the total number of stored chunks."""
        if self._use_chroma:
            return self._collection.count()

        return len(self._store)

    def search_with_filter(
        self,
        query: str,
        top_k: int = 3,
        metadata_filter: dict | None = None,
    ) -> list[dict[str, Any]]:
        """
        Search with optional metadata pre-filtering.
        """
        if self._use_chroma:
            query_embedding = self._embedding_fn(query)

            results = self._collection.query(
                query_embeddings=[query_embedding],
                n_results=top_k,
                where=metadata_filter if metadata_filter else None,
            )

            output = []
            docs = results.get("documents", [[]])[0]
            metas = results.get("metadatas", [[]])[0]
            ids = results.get("ids", [[]])[0]

            for doc, meta, doc_id in zip(docs, metas, ids):
                output.append(
                    {
                        "id": doc_id,
                        "content": doc,
                        "metadata": meta or {},
                    }
                )
            return output

        filtered_records = self._store

        if metadata_filter:
            filtered_records = [
                r
                for r in self._store
                if all(r["metadata"].get(k) == v for k, v in metadata_filter.items())
            ]

        return self._search_records(query, filtered_records, top_k)

    def delete_document(self, doc_id: str) -> bool:
        """
        Remove all chunks belonging to a document.
        """
        if self._use_chroma:
            try:
                existing = self._collection.get(where={"doc_id": doc_id})
                if not existing or not existing.get("ids"):
                    return False
                self._collection.delete(where={"doc_id": doc_id})
                return True
            except Exception:
                return False

        original_size = len(self._store)
        self._store = [
            r for r in self._store
            if r["metadata"].get("doc_id") != doc_id
        ]
        return len(self._store) < original_size