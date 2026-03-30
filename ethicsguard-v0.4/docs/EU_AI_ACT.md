# EthicsGuard v0.4 -- EU AI Act Compliance Mapping

> **DISCLAIMER**: This document is **NOT legal advice**. It describes how EthicsGuard's technical features align with specific provisions of the EU AI Act (Regulation (EU) 2024/1689). Organizations deploying EthicsGuard must consult qualified legal counsel and conduct their own conformity assessments. The interpretations below reflect our good-faith understanding of the regulation as of March 2026.

---

## Table of Contents

1. [Risk Classification Rationale](#1-risk-classification-rationale)
2. [Technical Documentation (Article 11)](#2-technical-documentation-article-11)
3. [Transparency Measures (Article 13)](#3-transparency-measures-article-13)
4. [Human Oversight Design (Article 14)](#4-human-oversight-design-article-14)
5. [Accuracy and Robustness (Article 15)](#5-accuracy-and-robustness-article-15)
6. [Conformity Assessment Notes](#6-conformity-assessment-notes)
7. [References](#7-references)

---

## 1. Risk Classification Rationale

### Why High-Risk Under Article 6 and Annex III

EthicsGuard is designed to serve as a safety component within AI systems that may fall under the **high-risk** classification as defined in Article 6(2) of the EU AI Act, which refers to AI systems listed in Annex III.

Relevant Annex III categories where EthicsGuard-protected systems may operate:

| Annex III Category | Reference | Example Deployment |
|---|---|---|
| (1) Biometric identification | Annex III, 1(a) | AI systems processing biometric data that use EthicsGuard for safety |
| (5) Access to essential services | Annex III, 5(a) | Credit scoring AI using EthicsGuard for bias detection |
| (6) Law enforcement | Annex III, 6(a) | Government AI systems using EthicsGuard for safety compliance |
| (7) Migration and border control | Annex III, 7(a) | Public sector AI with EthicsGuard safety layer |
| (8) Administration of justice | Annex III, 8(a) | Legal AI tools using EthicsGuard guardrails |

**Classification rationale**: EthicsGuard is not itself the high-risk AI system. It is a **safety component** (Article 6(1)(b)) of AI systems that may be classified as high-risk. As a safety component, EthicsGuard is subject to the same requirements as the high-risk system it protects. We therefore design to the high-risk standard proactively.

### Risk Level of EthicsGuard Itself

When used as a standalone content moderation tool, EthicsGuard would likely be classified as **limited risk** under Article 52 (transparency obligations for certain AI systems). However, because our primary use case is as a safety component of high-risk systems, we design and document to the higher standard.

---

## 2. Technical Documentation (Article 11)

Article 11 requires providers of high-risk AI systems to draw up technical documentation demonstrating compliance. The following table maps Article 11 requirements to EthicsGuard's documentation:

| Requirement (Article 11 / Annex IV) | EthicsGuard Documentation | Location |
|---|---|---|
| General description of the AI system | Architecture overview, service descriptions | [README.md](./README.md) |
| Detailed description of system elements | Source code, API schemas, Pydantic models | `/services/`, `/core/`, `/shared/` |
| Design specifications and development process | LangGraph pipeline design, Colang rules | `/core/langgraph_agents/`, `/core/colang_config/` |
| Monitoring, functioning, and control | Prometheus metrics, OpenTelemetry tracing, audit logs | `/shared/audit_logger.py`, Dashboard |
| Risk management system description | OWASP mapping, attack catalog, red-team testing | [OWASP_MAPPING.md](./OWASP_MAPPING.md), `/services/redteam-service/` |
| Data governance measures | Compliance engine, PII detection/redaction, retention policies | `/shared/compliance.py` |
| Human oversight measures | FLAGGED status, dashboard, configurable thresholds | [ETHICS.md](./ETHICS.md), Dashboard |
| Accuracy metrics and validation | Evaluation service, benchmark datasets, PDF reports | `/services/evaluation-service/`, `/evaluation/` |
| Cybersecurity measures | mTLS certificates, rate limiting, input validation | `/certs/`, SlowAPI config |

### What EthicsGuard Documents

For every request processed through the `/protect` endpoint, EthicsGuard generates and persists:

1. **Audit Record**: Unique ID, timestamp, prompt hash (SHA-256), status (ALLOWED/BLOCKED/FLAGGED), OWASP tags, individual scores, latency, model used, and session ID
2. **Scorecard**: Numeric scores across four dimensions (safety, toxicity, bias, hallucination) with weighted overall score
3. **Compliance Flags**: Regulatory flags specific to the active compliance mode (GDPR, HIPAA, CCPA, STANDARD)
4. **Execution Trace**: Ordered list of pipeline stages executed and total node count
5. **OWASP Tags**: Specific LLM Top 10 and ASI Top 10 tags triggered by the request

This documentation is available via the API response, the audit database, and the Streamlit dashboard.

---

## 3. Transparency Measures (Article 13)

Article 13 requires high-risk AI systems to be designed and developed in such a manner that their operation is sufficiently transparent to enable deployers to interpret the system's output and use it appropriately.

### How EthicsGuard Provides Transparency

| Transparency Requirement | Implementation |
|---|---|
| **Intended purpose disclosure** | API documentation (FastAPI OpenAPI schema), this documentation set |
| **Level of accuracy** | Scorecard with four numeric dimensions (0-100), overall weighted score |
| **Known limitations** | Documented in [ETHICS.md](./ETHICS.md) Section 3 (false positives, adversarial bypass, language limitations, cultural context) |
| **Foreseeable misuse** | Prohibited uses documented in [ETHICS.md](./ETHICS.md) Section 2 |
| **Human oversight requirements** | FLAGGED status, dashboard, human review recommendations in [ETHICS.md](./ETHICS.md) Section 5 |
| **Input data specifications** | Pydantic request models with field descriptions, type hints, and examples |
| **Interpretability of outputs** | Every response includes: status, scorecard, OWASP tags, compliance flags, policy triggered, audit record, execution trace |

### Specific Transparency Features

1. **Execution Trace**: Every `/protect` response includes a `trace` object listing the exact pipeline stages executed (e.g., `input_validation -> toxicity_check -> bias_check -> hallucination_check -> policy_engine`). This enables deployers to understand which checks were performed and in what order.

2. **OWASP Tag Attribution**: When a request is blocked or flagged, the response includes specific OWASP tags (e.g., `LLM01` for prompt injection) that explain *why* the decision was made. Deployers can look up human-readable descriptions via the OWASP mapper.

3. **Policy Identification**: The `policy_triggered` field identifies the exact Colang rule or policy that caused a BLOCK/FLAG decision, enabling root-cause analysis.

4. **Scorecard Breakdown**: Rather than a single pass/fail decision, the scorecard provides four independent scores, enabling deployers to understand which dimension triggered the decision and by how much.

5. **OpenAPI Documentation**: All four services expose auto-generated OpenAPI schemas at `/docs` (Swagger UI) and `/redoc` (ReDoc), providing complete API transparency.

---

## 4. Human Oversight Design (Article 14)

Article 14 requires high-risk AI systems to be designed and developed in such a way that they can be effectively overseen by natural persons during the period in which the AI system is in use.

### FLAGGED Status

EthicsGuard implements a three-tier decision model:

| Status | Meaning | Human Role |
|---|---|---|
| **ALLOWED** | All safety checks passed with high confidence | Periodic auditing recommended |
| **BLOCKED** | One or more safety checks failed definitively | Review if appealed; investigate false positives |
| **FLAGGED** | Borderline result requiring human judgment | **Mandatory human review before final decision** |

The FLAGGED status is the core human oversight mechanism. It ensures that uncertain cases are never resolved by the AI system alone.

### Audit Trails

Every decision made by EthicsGuard is recorded in the audit database with:
- A unique identifier (UUID v4)
- ISO 8601 timestamp
- SHA-256 prompt hash (for privacy-preserving traceability)
- Full decision details (status, scores, tags, flags)
- Processing latency

These records enable:
- **Post-hoc review** of any individual decision
- **Trend analysis** across time periods
- **Regulatory examination** with complete traceability
- **Dispute resolution** when decisions are challenged

### Dashboard

The Streamlit dashboard (port 8501) provides five views for human oversight:

1. **Scorecard** -- Real-time display of trustworthiness scores
2. **Red Team** -- Attack simulation results and attack success rates
3. **Audit Log** -- Searchable, filterable audit trail with export
4. **Evaluation** -- Benchmark comparison results and trends
5. **Compliance** -- Regulatory compliance status by mode

### Override Capability

EthicsGuard is designed as advisory middleware. Deployers retain the ability to:
- Override any BLOCKED decision by routing around the guardrail
- Adjust scoring thresholds to change the BLOCKED/FLAGGED/ALLOWED boundaries
- Disable specific detectors for use cases where they are not applicable
- Switch compliance modes at runtime via the `compliance_mode` request parameter

This ensures that human decision-makers remain in control.

---

## 5. Accuracy and Robustness (Article 15)

Article 15 requires high-risk AI systems to be designed and developed in such a way that they achieve an appropriate level of accuracy, robustness, and cybersecurity.

### Benchmark Results

EthicsGuard is evaluated against two adversarial datasets:

| Dataset | Description | Size |
|---|---|---|
| 2026 Attack Dataset | Custom dataset covering all 11 attack types with OWASP-tagged adversarial prompts | Internal benchmark |
| HarmBench Subset | Subset of the HarmBench academic benchmark for harmful content detection | Academic benchmark |

### Key Metrics

| Metric | Target | Evidence |
|---|---|---|
| **False Positive Rate (FPR)** | ≤ 8% | Measured across benign prompt datasets; benign prompts incorrectly blocked or flagged |
| **Attack Success Rate (ASR)** | < 10% | Percentage of adversarial prompts that bypass guardrails (lower is better) |
| **OWASP Coverage** | ≥ 75% | Percentage of OWASP LLM Top 10 + ASI Top 10 tags with active detection |
| **Latency P50** | < 100ms | Median end-to-end latency for the /protect endpoint |
| **Latency P99** | < 500ms | 99th percentile latency under normal load |

### False Positive Rate Analysis

An FPR of ≤ 8% means that for every 100 benign prompts, at most 8 are incorrectly blocked or flagged. This rate is achieved through:

1. **Multi-stage pipeline**: Prompts must trigger multiple detectors to be blocked, reducing single-detector false positives
2. **Weighted scoring**: The overall score is a weighted combination (safety 30%, toxicity 25%, bias 20%, hallucination 25%), preventing any single dimension from dominating
3. **Threshold calibration**: BLOCK thresholds are set to require high-confidence detections
4. **FLAGGED buffer zone**: Uncertain cases are flagged for human review rather than automatically blocked

### Robustness Measures

| Threat | Mitigation |
|---|---|
| **Adversarial prompt crafting** | 11 attack type generators for continuous testing; Colang pattern rules |
| **Model extraction** | No model weights exposed; API-only access with rate limiting |
| **Denial of service** | SlowAPI rate limiting (configurable per minute); Docker health checks |
| **Data poisoning** | Audit log integrity via structured schema; HIPAA mode encryption |
| **Input manipulation** | Pydantic input validation; length limits; type enforcement |

### Cybersecurity Measures

| Measure | Implementation |
|---|---|
| **Transport security** | mTLS between services (cert-manager ready); TLS termination at ingress |
| **Authentication** | API key authentication for inter-service communication |
| **Rate limiting** | Configurable per-IP rate limits via SlowAPI |
| **Input validation** | Pydantic models with type constraints and field validation |
| **Encryption at rest** | Fernet encryption for HIPAA audit logs |
| **Network isolation** | Docker network bridge; Kubernetes network policies for production |

---

## 6. Conformity Assessment Notes

### Self-Assessment Path

For most deployment scenarios, EthicsGuard as a safety component would fall under the self-assessment conformity procedure described in Article 43(2). This applies when:
- The high-risk AI system is not a biometric system
- The provider applies harmonized standards covering the relevant requirements

### Third-Party Assessment

A notified body conformity assessment (Article 43(1)) may be required when:
- The system is used for biometric identification
- No harmonized standards exist for the specific use case
- The deployer operates in a regulated sector requiring independent verification

### Documentation Package

A conformity assessment for an EthicsGuard-protected system should include:

1. This EU AI Act compliance mapping document
2. Technical documentation as described in Section 2
3. Risk management records (OWASP mapping, red-team test results)
4. Evaluation reports (PDF reports from the Evaluation Service)
5. Human oversight procedures (organizational policies for FLAGGED item review)
6. Post-market monitoring plan (dashboard monitoring, periodic re-evaluation)
7. Data governance documentation (compliance engine configuration, retention policies)

### Post-Market Monitoring

Article 72 requires providers to establish a post-market monitoring system. EthicsGuard supports this through:
- Continuous audit logging of all decisions
- Dashboard monitoring of score trends and anomalies
- Red-team service for periodic re-evaluation
- Evaluation service for benchmark regression testing
- Configurable alerting thresholds via Prometheus

---

## 7. References

| Reference | URL |
|---|---|
| EU AI Act Full Text | https://eur-lex.europa.eu/eli/reg/2024/1689/oj |
| EU AI Act Official Summary | https://artificialintelligenceact.eu/ |
| Article 6 -- Classification Rules for High-Risk AI Systems | Regulation (EU) 2024/1689, Article 6 |
| Annex III -- High-Risk AI Systems | Regulation (EU) 2024/1689, Annex III |
| Article 11 -- Technical Documentation | Regulation (EU) 2024/1689, Article 11 |
| Article 13 -- Transparency and Provision of Information to Deployers | Regulation (EU) 2024/1689, Article 13 |
| Article 14 -- Human Oversight | Regulation (EU) 2024/1689, Article 14 |
| Article 15 -- Accuracy, Robustness and Cybersecurity | Regulation (EU) 2024/1689, Article 15 |
| Article 43 -- Conformity Assessment | Regulation (EU) 2024/1689, Article 43 |
| Article 52 -- Transparency Obligations for Certain AI Systems | Regulation (EU) 2024/1689, Article 52 |
| Article 72 -- Post-Market Monitoring | Regulation (EU) 2024/1689, Article 72 |
| Annex IV -- Technical Documentation | Regulation (EU) 2024/1689, Annex IV |
| OWASP Top 10 for LLM Applications 2025 | https://owasp.org/www-project-top-10-for-large-language-model-applications/ |

---

*This document was last updated on 2026-03-30 and applies to EthicsGuard v0.4. It does not constitute legal advice.*
