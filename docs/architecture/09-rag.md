# RAG Architecture

## 1. Pipeline

```
Documents (PDF/image/scanned/statement/contract/policy/email)
  → malware scan (fail closed)
  → parse (PDF/Office)
  → OCR (scanned)
  → classify (type + sensitivity + retention)
  → chunk (size/overlap)
  → metadata extract (tenant, doc, owner, hash, acl)
  → embed
  → vector store (tenant-tagged, ACL-tagged)
  ───────── retrieval ─────────
  → hybrid (dense + BM25)
  → rerank
  → context validation (ACL, dedup, max size)
  → LLM
  → output validation (citations, guardrails)
```

Implemented skeleton in `backend/app/rag/pipeline.py`.

## 2. Supported Document Types

PDF, images (OCR), scanned documents, financial statements, contracts,
policies, regulatory documents, emails, knowledge bases, Office files.
Each type has a parser + classifier path.

## 3. Authorization — the critical control

**Document-level and chunk-level ACLs are enforced at retrieval time**, not
just at ingestion:

- Every embedding record carries `tenant_id`, `document_id`, and ACL groups.
- `search()` filters by `tenant_id` AND `allowed_document_ids` (resolved from
  the document ACL store for the requesting principal).
- The LLM never receives documents the caller may not read — filtering happens
  before context is built.
- Fail closed: no `allowed_document_ids` for a non-staff caller → empty result.

See `backend/app/tools/document.py` (`_document_acl`) and `vectorstore.py`.

## 4. Ingestion Controls

- Malware scan before any parsing (ClamAV integration point; fail closed).
- PII detection + classification → sensitivity + retention class.
- Injection-pattern scan on document content (indirect prompt injection).
- Dedup by content hash; re-index on version change.

## 5. Retrieval Quality

- Hybrid retrieval (vector + BM25) → fusion → rerank → top-k with score thresholds.
- Context validation: max context size, dedup, citation-to-source integrity.
- `bfsi_rag_retrieval_score` (MRR/nDCG on eval set) monitored; drift alerts.

## 6. Data Flow

```
DocumentUploaded (event) → DocumentIngest worker (scan/parse/classify/chunk/embed)
→ DocumentIndexed (event) → search-ready
Query → hybrid search → rerank → validated context → LLM (FinancialDocumentAgent)
→ citations in reply → audit (document ids accessed)
```