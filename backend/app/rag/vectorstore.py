"""Vector store abstraction. Document and chunk-level ACLs are enforced at
query time: every embedding is tagged with tenant_id + document_id + per-chunk
ACL groups, and retrieval filters on the caller's permitted set. This prevents
cross-tenant and cross-document leakage through retrieval."""

from __future__ import annotations

from abc import ABC, abstractmethod
from dataclasses import dataclass, field

from app.core.config import settings


@dataclass
class EmbeddingRecord:
    id: str
    tenant_id: str
    document_id: str
    chunk_index: int
    vector: list[float]
    metadata: dict = field(default_factory=dict)


@dataclass
class SearchHit:
    document_id: str
    chunk_index: int
    score: float
    metadata: dict = field(default_factory=dict)


class VectorStore(ABC):
    @abstractmethod
    async def upsert(self, records: list[EmbeddingRecord]) -> None: ...

    @abstractmethod
    async def search(
        self,
        tenant_id: str,
        vector: list[float],
        top_k: int,
        allowed_document_ids: list[str] | None = None,
        **filters,
    ) -> list[SearchHit]: ...

    @abstractmethod
    async def delete_document(self, tenant_id: str, document_id: str) -> None: ...


class InMemoryVectorStore(VectorStore):
    """Dev/test store."""

    def __init__(self) -> None:
        self._records: list[EmbeddingRecord] = []

    async def upsert(self, records: list[EmbeddingRecord]) -> None:
        self._records.extend(records)

    async def search(
        self,
        tenant_id: str,
        vector: list[float],
        top_k: int,
        allowed_document_ids: list[str] | None = None,
        **filters,
    ) -> list[SearchHit]:
        allowed = set(allowed_document_ids) if allowed_document_ids else None
        scored = []
        for r in self._records:
            if r.tenant_id != tenant_id:
                continue
            if allowed is not None and r.document_id not in allowed:
                continue
            score = sum(a * b for a, b in zip(vector, r.vector, strict=False))
            scored.append(SearchHit(r.document_id, r.chunk_index, score, r.metadata))
        scored.sort(key=lambda h: h.score, reverse=True)
        return scored[:top_k]

    async def delete_document(self, tenant_id: str, document_id: str) -> None:
        self._records = [
            r for r in self._records if not (r.tenant_id == tenant_id and r.document_id == document_id)
        ]


class OpenSearchVectorStore(VectorStore):
    def __init__(self, settings) -> None:
        import httpx

        self._client = httpx.AsyncClient(base_url=settings.opensearch_url, timeout=30)
        self._index = "bfsi_documents"

    async def upsert(self, records: list[EmbeddingRecord]) -> None:
        for r in records:
            await self._client.put(
                f"/{self._index}/_doc/{r.id}",
                json={
                    "tenant_id": r.tenant_id,
                    "document_id": r.document_id,
                    "chunk_index": r.chunk_index,
                    "vector": r.vector,
                    "metadata": r.metadata,
                },
            )

    async def search(
        self,
        tenant_id: str,
        vector: list[float],
        top_k: int,
        allowed_document_ids: list[str] | None = None,
        **filters,
    ) -> list[SearchHit]:
        must: list = [
            {"term": {"tenant_id": tenant_id}},
            {"knn": {"vector": {"vector": vector, "k": top_k}}},
        ]
        if allowed_document_ids:
            must.append({"terms": {"document_id": allowed_document_ids}})
        resp = await self._client.post(
            f"/{self._index}/_search", json={"size": top_k, "query": {"bool": {"must": must}}}
        )
        resp.raise_for_status()
        return [
            SearchHit(
                document_id=h["_source"]["document_id"],
                chunk_index=h["_source"]["chunk_index"],
                score=h["_score"],
                metadata=h["_source"].get("metadata", {}),
            )
            for h in resp.json()["hits"]["hits"]
        ]

    async def delete_document(self, tenant_id: str, document_id: str) -> None:
        await self._client.post(
            f"/{self._index}/_delete_by_query",
            json={"query": {"bool": {"must": [{"term": {"tenant_id": tenant_id}}, {"term": {"document_id": document_id}}]}}},
        )