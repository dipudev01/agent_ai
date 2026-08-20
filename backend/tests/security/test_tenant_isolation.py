"""Tenant isolation tests — cross-tenant data leakage is the top security risk
in a multi-tenant financial platform. Every store and tool must scope by tenant
and by ownership. These tests exercise the REAL enforcement boundary
(app.tools.authz.execute_tool)."""

import pytest

from app.agents.memory import AgentMemory
from app.rag.vectorstore import EmbeddingRecord, InMemoryVectorStore
from app.tools.authz import ToolAuthorizationError, execute_tool
from app.tools.base import ToolContext

OFFICER_ROLES = ["loan_officer", "compliance_officer"]
CUSTOMER_ROLES = ["customer"]


async def test_vector_search_isolation():
    store = InMemoryVectorStore()
    await store.upsert(
        [
            EmbeddingRecord(id="a:0", tenant_id="t1", document_id="doc1", chunk_index=0, vector=[1.0, 0.0]),
            EmbeddingRecord(id="b:0", tenant_id="t2", document_id="doc2", chunk_index=0, vector=[1.0, 0.0]),
        ]
    )
    hits = await store.search(tenant_id="t1", vector=[1.0, 0.0], top_k=5)
    assert len(hits) == 1
    assert hits[0].document_id == "doc1"


async def test_vector_search_document_acl():
    store = InMemoryVectorStore()
    await store.upsert(
        [
            EmbeddingRecord(id="a:0", tenant_id="t1", document_id="doc1", chunk_index=0, vector=[1.0, 0.0]),
            EmbeddingRecord(id="b:0", tenant_id="t1", document_id="doc2", chunk_index=0, vector=[1.0, 0.0]),
        ]
    )
    hits = await store.search(tenant_id="t1", vector=[1.0, 0.0], top_k=5, allowed_document_ids=["doc1"])
    assert [h.document_id for h in hits] == ["doc1"]


async def test_memory_isolation():
    mem = AgentMemory()
    await mem.put_long_term("t1", "u1", "k", {"v": 1})
    assert await mem.get_long_term("t2", "u1", "k") is None
    assert await mem.get_long_term("t1", "u1", "k") == {"v": 1}


async def test_customer_can_read_own_profile():
    result = await execute_tool(
        "get_customer_profile",
        ToolContext(
            tenant_id="t1", user_id="cust_1001", roles=list(CUSTOMER_ROLES),
            correlation_id="x", resource_owner_id="cust_1001",
        ),
        {"customer_id": "cust_1001"},
    )
    assert result.ok is True
    assert result.data["profile"]["pan"] == "PANXXXX9999"
    assert "priya@example.com" not in str(result.data)


async def test_customer_cannot_read_another_profiles_profile():
    with pytest.raises(ToolAuthorizationError):
        await execute_tool(
            "get_customer_profile",
            ToolContext(
                tenant_id="t1", user_id="cust_1001", roles=list(CUSTOMER_ROLES),
                correlation_id="x", resource_owner_id="cust_1001",
            ),
            {"customer_id": "cust_1002"},
        )


async def test_customer_cannot_read_credit_report():
    with pytest.raises(ToolAuthorizationError):
        await execute_tool(
            "get_credit_report",
            ToolContext(
                tenant_id="t1", user_id="cust_1001", roles=list(CUSTOMER_ROLES),
                correlation_id="x", resource_owner_id="cust_1001",
            ),
            {"customer_id": "cust_1002"},
        )


async def test_staff_can_read_masked_profile_across_ownership():
    result = await execute_tool(
        "get_customer_profile",
        ToolContext(
            tenant_id="t1", user_id="u_officer", roles=list(OFFICER_ROLES),
            correlation_id="x",
        ),
        {"customer_id": "cust_1001"},
    )
    assert result.ok is True
    assert result.data["profile"]["pan"] == "PANXXXX9999"