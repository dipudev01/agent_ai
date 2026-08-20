# Infrastructure Architecture

## 1. Stack

Kubernetes (EKS/AKS/GKE/self-hosted) + Docker + Terraform + Helm + GitOps (ArgoCD) + CI/CD (GitHub Actions).

## 2. Environment Topology (Section 23)

| Env | Purpose | Config | Promotion |
|---|---|---|---|
| **Dev** | local/feature | mock LLM, local services | — |
| **QA** | integration | shared cluster, test data | CI deploy |
| **Staging** | pre-prod parity | prod-like, synthetic data, canary | after QA |
| **Production** | live | hardened, KMS, HPA | approval-gated, canary → full |

Promotion is **secure & gated**: image built once in CI, promoted by tag through
environments; production deploys require environment protection rules (manual
approval) + automated rollback on failed readiness.

## 3. Deployment Strategies

- **Blue/green** for major releases (full fleet swap behind service selector).
- **Canary** for gradual rollout: 5% → 25% → 100% with traffic-splitting; auto-rollback on SLO violation.
- **Automated rollback**: readiness/liveness + synthetic checks gate `kubectl rollout undo`.
- **DB migrations**: expand-then-contract (additive first, backfill, then remove old columns in a later release) — no destructive changes in a single deploy. Run as a one-off job before app rollout.
- **Feature flags**: config-driven toggles; flags for new agents, model tiers, decision policies.

## 4. Kubernetes Topology

```
Ingress (nginx + WAF annotations)
  → Service → Deployment (HPA 3–50)
  → NetworkPolicy (deny-by-default egress)
  → PodDisruptionBudget (minAvailable)
GPU node pool (vLLM inference) + general pool
Stateful: Postgres (CNPG/operator), Redis HA, Kafka (Strimzi), OpenSearch
```

## 5. Service Mesh

Justified for mTLS + traffic splitting + retries when the platform exceeds
~30 services. Start with mTLS via Istio for the API→decisioning→LLM path only;
avoid mesh-wide adoption until value is proven (simpler is more secure here).

## 6. Managed Services by Cloud

| Capability | AWS | Azure | GCP |
|---|---|---|---|
| K8s | EKS | AKS | GKE |
| Postgres | RDS | Flexible Server | Cloud SQL |
| Cache | ElastiCache | Redis Cache | Memorystore |
| Streaming | MSK | Event Hubs | Pub/Sub + Confluent |
| Search/Vector | OpenSearch Service | OpenSearch | OpenSearch / Vertex |
| Object | S3 | Blob | GCS |
| KMS | KMS | Key Vault | KMS |
| Secrets | Secrets Manager | Key Vault | Secret Manager |
| GPU | EC2 g5/g6 | NC/NV series | G2/G4 (L4) |

On-prem: CNPG + Redis operator + Strimzi + Vault (see `infra/terraform/onprem`).
Hybrid: on-prem for residency-locked tenants, cloud for elastic workloads.

## 7. Secrets & KMS

- External Secrets Operator syncs Vault/KMS → k8s secrets.
- Fernet field-encryption key from KMS; JWT signing key from Vault; both rotated on schedule.
- No secrets in images, configmaps, or git.

## 8. CI/CD Pipeline

```
PR → lint (ruff) + typecheck (mypy) + tests (pytest) + SAST (bandit) + dep audit
main → build image (docker buildx, SBOM + trivy scan) → push to registry
     → deploy staging (helm) → tests → promote to prod (gated) → migrations
```