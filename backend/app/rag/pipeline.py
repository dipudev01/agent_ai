"""Enterprise RAG pipeline:

Documents → malware scan → parse → OCR → classify → chunk → metadata extract →
embed → vector store → hybrid retrieval → rerank → context validate → LLM →
output validate.

Every stage is a pluggable step. Malware scanning and OCR are wired to external
services in production (ClamAV, Tesseract/document AI). The pipeline is async
and event-driven: DocumentUploaded → DocumentIndexed.
"""

from __future__ import annotations

import hashlib
from abc import ABC, abstractmethod
from dataclasses import dataclass, field

from app.rag.vectorstore import EmbeddingRecord, VectorStore


class IngestionError(Exception): ...


@dataclass
class Chunk:
    text: str
    index: int
    metadata: dict = field(default_factory=dict)


class Step(ABC):
    @abstractmethod
    async def run(self, ctx: dict) -> dict: ...


class MalwareScan(Step):
    """Calls ClamAV (clamd) before any content is parsed. Fail closed."""

    async def run(self, ctx: dict) -> dict:
        import asyncio

        await asyncio.sleep(0.01)  # placeholder for real clamd call
        if ctx.get("simulate_malware"):
            raise IngestionError("malware detected")
        return ctx


class Parser(Step):
    """Extracts text from PDFs, Office docs, images (via OCR hook)."""

    async def run(self, ctx: dict) -> dict:
        ext = ctx["filename"].rsplit(".", 1)[-1].lower()
        if ext in {"pdf", "doc", "docx", "txt", "md"}:
            text = _parse_text(ctx["content"], ext)
        elif ext in {"png", "jpg", "jpeg", "tiff"}:
            text = await _ocr(ctx["content"])
        else:
            raise IngestionError(f"unsupported file type: {ext}")
        ctx["text"] = text
        return ctx


async def _ocr(content: bytes) -> str:
    # Production: call document-AI service (Tesseract/GCP Doc AI/AWS Textract).
    return "extracted text from image (OCR placeholder)"


def _parse_text(content: bytes, ext: str) -> str:
    if ext in {"txt", "md"}:
        return content.decode("utf-8", errors="replace")
    if ext in {"pdf", "doc", "docx"}:
        # Production: PyMuPDF / docling. Returning placeholder for skeleton.
        return content.decode("utf-8", errors="replace")
    raise IngestionError(f"no parser for extension: {ext}")


class Classifier(Step):
    """Document type + sensitivity + retention classification."""

    async def run(self, ctx: dict) -> dict:
        text = ctx["text"]
        lower = text.lower()
        if any(k in lower for k in ("passport", "pan card", "aadhaar")):
            ctx["doc_type"] = "identity"
            ctx["sensitivity"] = "high"
        elif any(k in lower for k in ("financial statement", "balance sheet", "p&l")):
            ctx["doc_type"] = "financial"
            ctx["sensitivity"] = "medium"
        else:
            ctx["doc_type"] = "general"
            ctx["sensitivity"] = "low"
        ctx["retention_days"] = 2555 if ctx["sensitivity"] == "high" else 1825
        return ctx


class Chunker(Step):
    def __init__(self, size: int = 512, overlap: int = 64) -> None:
        self.size = size
        self.overlap = overlap

    async def run(self, ctx: dict) -> dict:
        text = ctx["text"]
        chunks: list[Chunk] = []
        start = 0
        idx = 0
        while start < len(text):
            end = start + self.size
            chunk_text = text[start:end]
            chunks.append(
                Chunk(
                    text=chunk_text,
                    index=idx,
                    metadata={
                        "doc_id": ctx["document_id"],
                        "doc_type": ctx.get("doc_type", "general"),
                        "sensitivity": ctx.get("sensitivity", "low"),
                    },
                )
            )
            idx += 1
            if end >= len(text):
                break
            start = end - self.overlap
        ctx["chunks"] = chunks
        return ctx


class MetadataExtractor(Step):
    async def run(self, ctx: dict) -> dict:
        ctx["metadata"] = {
            "tenant_id": ctx["tenant_id"],
            "document_id": ctx["document_id"],
            "filename": ctx["filename"],
            "doc_type": ctx.get("doc_type"),
            "sensitivity": ctx.get("sensitivity"),
            "uploaded_by": ctx.get("uploaded_by"),
            "content_hash": hashlib.sha256(ctx["content"]).hexdigest(),
        }
        return ctx


class Embedder(Step):
    def __init__(self, model: str, dimension: int) -> None:
        self.model = model
        self.dimension = dimension

    async def run(self, ctx: dict) -> dict:
        chunks: list[Chunk] = ctx["chunks"]
        records = []
        for c in chunks:
            vec = await self._embed(c.text)
            records.append(
                EmbeddingRecord(
                    id=f"{ctx['document_id']}:{c.index}",
                    tenant_id=ctx["tenant_id"],
                    document_id=ctx["document_id"],
                    chunk_index=c.index,
                    vector=vec,
                    metadata={**c.metadata, **ctx["metadata"]},
                )
            )
        ctx["embeddings"] = records
        return ctx

    async def _embed(self, text: str) -> list[float]:
        # Production: sentence-transformers service or provider embedding API.
        # Placeholder deterministic hash embedding for skeleton.
        import hashlib

        digest = hashlib.md5(text.encode()).digest()
        vec = [b / 255.0 for b in digest]
        return (vec * (self.dimension // 16 + 1))[: self.dimension]


class Pipeline:
    def __init__(self, steps: list[Step], vector_store: VectorStore) -> None:
        self.steps = steps
        self.vector_store = vector_store

    async def run(self, *, tenant_id: str, document_id: str, filename: str, content: bytes, uploaded_by: str) -> list[EmbeddingRecord]:
        ctx: dict = {
            "tenant_id": tenant_id,
            "document_id": document_id,
            "filename": filename,
            "content": content,
            "uploaded_by": uploaded_by,
        }
        for step in self.steps:
            ctx = await step.run(ctx)
        records: list[EmbeddingRecord] = ctx["embeddings"]
        await self.vector_store.upsert(records)
        return records


def build_pipeline(vector_store: VectorStore) -> Pipeline:
    return Pipeline(
        steps=[
            MalwareScan(),
            Parser(),
            Classifier(),
            Chunker(),
            MetadataExtractor(),
            Embedder("placeholder", 384),
        ],
        vector_store=vector_store,
    )