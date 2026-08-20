"""Document upload → RAG ingestion. Documents are scanned, parsed, classified,
chunked, embedded, and indexed asynchronously; an event is emitted when done."""

from __future__ import annotations

import uuid

from fastapi import APIRouter, File, Form, HTTPException, UploadFile, status

from app.api.dependencies import PrincipalDep
from app.api.v1.schemas import DocumentUploadResponse
from app.core.container import container
from app.rag.pipeline import IngestionError, build_pipeline
from app.services.audit import record

router = APIRouter(prefix="/documents", tags=["documents"])

MAX_UPLOAD_BYTES = 25 * 1024 * 1024


@router.post("", response_model=DocumentUploadResponse)
async def upload_document(
    principal: PrincipalDep,
    file: UploadFile = File(...),
    document_id: str | None = Form(None),
):
    content = await file.read()
    if len(content) > MAX_UPLOAD_BYTES:
        raise HTTPException(status.HTTP_413_REQUEST_ENTITY_TOO_LARGE, detail="file too large")
    doc_id = document_id or str(uuid.uuid4())
    try:
        pipeline = build_pipeline(container.vector())
        await pipeline.run(
            tenant_id=principal.tenant_id,
            document_id=doc_id,
            filename=file.filename or "unnamed",
            content=content,
            uploaded_by=principal.user_id,
        )
    except IngestionError as exc:
        await record(
            tenant_id=principal.tenant_id,
            correlation_id=str(uuid.uuid4()),
            actor_type="user",
            actor_id=principal.user_id,
            action="document.ingest",
            resource_type="document",
            resource_id=doc_id,
            outcome="error",
            detail={"error": str(exc)},
        )
        raise HTTPException(status.HTTP_422_UNPROCESSABLE_ENTITY, detail=str(exc)) from exc

    await record(
        tenant_id=principal.tenant_id,
        correlation_id=str(uuid.uuid4()),
        actor_type="user",
        actor_id=principal.user_id,
        action="document.ingest",
        resource_type="document",
        resource_id=doc_id,
        outcome="success",
        detail={"filename": file.filename},
    )
    return DocumentUploadResponse(document_id=doc_id, status="indexed", message="document indexed")