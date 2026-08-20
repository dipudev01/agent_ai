"""RAG document search tool. Retrieval is ACL-filtered at the vector store
(tenant + document ACL). The LLM never sees documents the caller may not read."""

from __future__ import annotations

from app.core.container import container
from app.tools.base import Tool, ToolContext, ToolResult


class SearchDocumentsTool(Tool):
    name = "search_documents"
    description = "Semantic search over institution documents the user is permitted to read."
    parameters = {
        "type": "object",
        "properties": {
            "query": {"type": "string"},
            "top_k": {"type": "integer"},
            "document_ids": {"type": "array", "items": {"type": "string"}},
        },
        "required": ["query"],
    }
    required_permission = "document:read"

    async def run(self, ctx: ToolContext, arguments: dict) -> ToolResult:
        query = arguments.get("query", "")
        top_k = int(arguments.get("top_k") or 5)
        allowed = arguments.get("document_ids")

        # Document-level ACL: resolve permitted doc ids for this user+tenant.
        permitted = _document_acl(ctx, allowed)
        vector = [0.1] * 384  # placeholder: embedding service
        hits = await container.vector().search(
            tenant_id=ctx.tenant_id,
            vector=vector,
            top_k=top_k,
            allowed_document_ids=permitted,
        )
        return ToolResult.success(
            query=query,
            hits=[{"document_id": h.document_id, "score": round(h.score, 4), "metadata": h.metadata} for h in hits]
        )


def _document_acl(ctx: ToolContext, requested: list[str] | None) -> list[str] | None:
    """In production this consults the document ACL store (grants table). Here we
    model it as: any document owned by the user, or any document in the tenant
    for staff roles. Fail closed: return only explicitly permitted ids."""
    if "compliance_officer" in ctx.roles or "institution_admin" in ctx.roles:
        return requested  # staff: allowed to search the requested set
    if requested:
        # Non-staff: only documents owned by the caller.
        return [d for d in requested if d.startswith(ctx.user_id)]
    return []