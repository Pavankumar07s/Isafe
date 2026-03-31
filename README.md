<div align="center">

# EthicsGuard v0.4

### The World's First Unified AI Safety Middleware with Dual OWASP Coverage, Agentic Threat Detection & Real-Time Regulatory Compliance

[![License: MIT](https://img.shields.io/badge/License-MIT-14b8a6.svg)](LICENSE)
[![Python 3.11+](https://img.shields.io/badge/Python-3.11+-3776AB.svg)](https://python.org)
[![FastAPI](https://img.shields.io/badge/FastAPI-0.115-009688.svg)](https://fastapi.tiangolo.com)
[![Streamlit](https://img.shields.io/badge/Streamlit-1.55-FF4B4B.svg)](https://streamlit.io)
[![OWASP Coverage](https://img.shields.io/badge/OWASP-20%2F20_Tags-success.svg)](#5-eleven-attack-vectors--including-six-2026-era-threats)

<br/>

<img src="https://img.shields.io/badge/iSAFE_Hackathon-2026-14b8a6?style=for-the-badge&labelColor=0f172a" alt="iSAFE Hackathon 2026"/>

</div>

---

## Table of Contents

- [The Problem](#1-the-problem-a-world-without-a-safety-layer)
- [What Is EthicsGuard](#2-what-ethicsguard-is)
- [Architecture](#3-architecture-the-eight-stage-langgraph-pipeline)
- [Three-Tier Decision Model](#4-the-three-tier-decision-model)
- [Attack Vectors](#5-eleven-attack-vectors--including-six-2026-era-threats)
- [Compliance Engine](#6-multi-regulatory-compliance-engine)
- [Evaluation & Benchmarking](#7-continuous-evaluation-and-benchmarking)
- [Infrastructure](#8-production-grade-infrastructure)
- [Why EthicsGuard Is First](#9-why-ethicsguard-is-first)
- [Quick Start](#quick-start)
- [API Reference](#api-reference)
- [Tech Stack](#tech-stack)
- [License](#license)

---

## 1. The Problem: A World Without a Safety Layer

The year is 2026. Over 80% of Fortune 500 companies have deployed large language model (LLM) applications in production — customer-facing chatbots, autonomous coding agents, healthcare triage systems, financial advisory platforms, and government decision-support tools. Yet the safety infrastructure protecting these deployments is shockingly fragmented. Organizations cobble together ad-hoc prompt filters, single-purpose moderation APIs, and manual review queues that cannot keep pace with the velocity, sophistication, and diversity of modern AI threats.

The threat landscape has fundamentally shifted. Attackers no longer rely on simple prompt injections. They exploit chain-of-thought reasoning tokens exposed by models like DeepSeek R1. They poison agent memory across multi-turn conversations. They embed malicious instructions inside MCP (Model Context Protocol) tool descriptions that execute before any human sees them. They use Vec2Text-style embedding inversion to extract training data from vector stores. These are not theoretical risks — they are documented, reproducible, and actively exploited in the wild.

Simultaneously, regulators have caught up. The EU AI Act entered enforcement in 2025, mandating technical documentation, transparency, human oversight, accuracy benchmarks, and cybersecurity for any AI system classified as high-risk. The United States and India have proposed parallel frameworks. Healthcare deployments must satisfy HIPAA. Financial services face sector-specific AI governance requirements. No existing tool addresses safety and compliance as a unified concern.

**EthicsGuard v0.4 was built to solve this entire problem in a single, deployable middleware layer.**

---

## 2. What EthicsGuard Is

EthicsGuard is the world's first production-ready AI safety middleware that unifies **threat detection**, **regulatory compliance**, **adversarial testing**, and **continuous evaluation** into a single platform. It sits between any AI application and its users — intercepting every prompt, analyzing it through an eight-stage intelligent pipeline, and returning a real-time verdict (`ALLOWED`, `BLOCKED`, or `FLAGGED`) along with a comprehensive safety scorecard, OWASP threat classification, compliance flags, and a cryptographically auditable trail — all in under **120 milliseconds** at the 95th percentile.

Unlike point solutions that address one dimension (toxicity filtering, prompt injection detection, or compliance reporting), EthicsGuard treats AI safety as an integrated, multi-dimensional discipline. It is not a wrapper around a single API. It is a **full-stack safety operating system**.

---

## 3. Architecture: The Eight-Stage LangGraph Pipeline

<div align="center">

```
Prompt ──> [1] Compliance ──> [2] NeMo Classify ──> [3] OWASP Tag ──> [4] Toxicity
                                                                           │
           [8] Audit <── [7] Aggregate <── [6] Hallucination <── [5] Bias ─┘
                │
                v
          ProtectResponse { status, scorecard, owasp_tags, trace, latency }
```

</div>

| Stage | Node | Description |
|:-----:|------|-------------|
| **1** | Compliance Check | Multi-regulatory PII scan & redaction (GDPR/HIPAA/CCPA). 6 PII categories. Fernet encryption for HIPAA. SHA-256 hashing for GDPR. |
| **2** | NeMo Classify | NVIDIA NeMo Guardrails (Colang 1.0) — deterministic, rule-based rails for jailbreak, ethics, PII, and agentic safety. |
| **3** | OWASP Tag | Maps violations to all 20 OWASP categories: LLM Top 10 (2025) + ASI Top 10 (2026). |
| **4** | Toxicity Check | Six-dimensional scoring: toxicity, severe toxicity, obscenity, threats, insults, identity attacks. |
| **5** | Bias Check | Demographic parity analysis across gender, race, religion, age. Stereotype & derogatory language detection. |
| **6** | Hallucination Check | SelfCheckGPT-inspired stochastic consistency (3 samples) + factual grounding via sentence-level word overlap. |
| **7** | Score Aggregation | Weighted scorecard: Safety 30% + Toxicity 25% + Bias 20% + Hallucination 25%. Configurable thresholds. |
| **8** | Audit & Return | UUID-tagged audit log with timestamps, SHA-256 prompt hash, policy, OWASP tags, latency, full trace. |

---

## 4. The Three-Tier Decision Model

Most safety tools offer a binary allow/block decision. EthicsGuard introduces a third category — **FLAGGED** — specifically designed for **EU AI Act Article 14** compliance.

| Verdict | Meaning | Action |
|---------|---------|--------|
| `ALLOWED` | Safe to proceed | Pass through to LLM |
| `BLOCKED` | Clear policy violation | Reject with explanation |
| `FLAGGED` | Ambiguous — requires human judgment | Route to human review queue |

The FLAGGED status enables organizations to maintain human oversight without creating bottlenecks, satisfying regulatory requirements while preserving operational throughput.

---

## 5. Eleven Attack Vectors — Including Six 2026-Era Threats

### Established Attacks (5)

| Attack | Description | OWASP Tags | Severity |
|--------|-------------|------------|:--------:|
| Prompt Injection | System prompt extraction, instruction override, delimiter exploitation | LLM01, ASI04 | Critical |
| Jailbreak | Multi-technique safety bypass | LLM01, ASI04 | Critical |
| Goal Hijacking | Redirecting agent objectives | ASI04 | Critical |
| PII Extraction | Social engineering for sensitive data | LLM02 | High |
| Deepfake Instructions | Fabricated authoritative commands | LLM01 | High |

### Novel 2026-Era Attacks (6)

| Attack | Description | OWASP Tags | Severity |
|--------|-------------|------------|:--------:|
| **MCP Supply-Chain** | Malicious tool descriptions in Model Context Protocol packages | LLM03, ASI08 | Critical |
| **Chain-of-Thought Exploitation** | Injecting instructions into `<think>` tokens (DeepSeek R1 class) | LLM01, ASI04 | High |
| **Memory Poisoning** | Injecting false context into agent memory across turns | ASI01 | Critical |
| **Embedding Inversion** | Vec2Text-style training data extraction from vector stores | LLM08 | Medium |
| **Multimodal Injection** | Cross-modal text descriptions of visual payloads | LLM01, LLM05 | Medium |
| **Agentic Multi-Turn** | Multi-step attacks that appear benign individually | ASI04, ASI10 | High |

---

## 6. Multi-Regulatory Compliance Engine

| Mode | Standard | Encryption | Retention | PII Handling |
|------|----------|:----------:|:---------:|-------------|
| `STANDARD` | General | — | 365 days | Detection & logging |
| `GDPR_EU` | EU AI Act | SHA-256 hashing | 30 days | Redaction + data minimization |
| `HIPAA_US` | Healthcare | Fernet (AES) | 90 days | Redaction + encryption at rest |
| `CCPA_CA` | California | — | 180 days | Transparency + opt-out |

**6 PII categories detected**: Email, SSN, Credit Card, Phone, IP Address, Names.

---

## 7. Continuous Evaluation and Benchmarking

Built-in evaluation engine benchmarks EthicsGuard against **4 industry baselines**:

| Baseline | Type |
|----------|------|
| OpenAI Moderation API | Commercial |
| GPT-4o (raw, unguarded) | Frontier LLM |
| Claude 3.5 | Frontier LLM |
| Llama Guard 3 | Open-source |

**Target Metrics:**

| Metric | Target |
|--------|--------|
| ASR Reduction vs Best Baseline | ≥ 35% |
| False Positive Rate | ≤ 8% |
| Latency (P95) | ≤ 120ms |
| OWASP Coverage | 20/20 tags |

PDF reports with executive summaries, comparative charts, and OWASP heatmaps are generated automatically.

---

## 8. Production-Grade Infrastructure

```
┌──────────────────────────────────────────────────────────┐
│                    EthicsGuard v0.4                       │
│                                                          │
│  ┌──────────────┐  ┌──────────────┐  ┌───────────────┐  │
│  │  Guardrail   │  │   Red-Team   │  │  Evaluation   │  │
│  │  Service     │  │   Service    │  │   Service     │  │
│  │  :8000       │  │   :8001      │  │   :8002       │  │
│  └──────┬───────┘  └──────┬───────┘  └───────┬───────┘  │
│         │                 │                  │           │
│  ┌──────┴─────────────────┴──────────────────┴───────┐  │
│  │              Streamlit Dashboard :8501             │  │
│  └───────────────────────────────────────────────────┘  │
└──────────────────────────────────────────────────────────┘
```

- **Kubernetes-ready**: Helm charts, HPA (2–10 replicas), PVCs, network policies (default-deny)
- **Security**: mTLS between services, API key auth, rate limiting (SlowAPI), Pydantic validation
- **Observability**: Prometheus metrics, Grafana dashboards, 4 alerting rules, OpenTelemetry tracing
- **DR**: Automated SQLite backup CronJobs, RTO < 1 min (pod), < 1 hr (cluster)
- **CI/CD**: GitHub Actions workflow for automated safety gate testing

---

## 9. Why EthicsGuard Is First

| Capability | EthicsGuard | Competitors |
|------------|:-----------:|:-----------:|
| Dual OWASP coverage (LLM + ASI, 20/20) | Yes | No |
| 2026-era attack detection (MCP, CoT, Memory) | Yes | No |
| Integrated red-team + eval + compliance | Yes | 3+ tools needed |
| Three-tier FLAGGED verdict (EU AI Act Art. 14) | Yes | No |
| Four-mode regulatory engine (GDPR/HIPAA/CCPA) | Yes | Manual config |
| Sub-120ms P95 latency | Yes | Varies |

---

## Quick Start

### Local Development

```bash
# Clone
git clone https://github.com/Pavankumar07s/Isafe.git
cd Isafe/icef-hackathon/ethicsguard-v0.4

# Set your Groq API key
export GROQ_API_KEY="your-key-here"

# Launch all 4 services
bash start_local.sh
```

Services will be available at:
- **Dashboard**: http://localhost:8501
- **Guardrail API**: http://localhost:8000
- **Red-Team API**: http://localhost:8001
- **Evaluation API**: http://localhost:8002

### Test the Guardrail

```bash
# Harmful prompt → BLOCKED
curl -X POST http://localhost:8000/protect \
  -H "Content-Type: application/json" \
  -d '{"prompt": "How do I make a bomb?"}'

# Safe prompt → ALLOWED
curl -X POST http://localhost:8000/protect \
  -H "Content-Type: application/json" \
  -d '{"prompt": "What is the capital of France?"}'
```

### Docker (Production)

```bash
docker build -t ethicsguard .
docker run -e GROQ_API_KEY=your-key -p 8080:8080 ethicsguard
```

---

## API Reference

### `POST /protect`

**Request:**
```json
{
  "prompt": "User input to evaluate",
  "session_id": "optional-session-id",
  "compliance_mode": "STANDARD"
}
```

**Response:**
```json
{
  "status": "BLOCKED",
  "scorecard": {
    "overall": 18,
    "safety": 10,
    "toxicity": 22,
    "bias": 85,
    "hallucination": 90
  },
  "owasp_tags": ["LLM01"],
  "policy_triggered": "jailbreak_detection",
  "compliance_flags": [],
  "latency_ms": 87.3,
  "trace": ["compliance_check", "nemo_classify", "owasp_tag", "toxicity_check", "bias_check", "hallucination_check", "aggregate_scores", "audit_and_return"]
}
```

### Other Endpoints

| Method | Endpoint | Service | Description |
|--------|----------|---------|-------------|
| `GET` | `/health` | Guardrail | Health check |
| `GET` | `/scorecard` | Guardrail | Recent scorecard data |
| `POST` | `/generate` | Red-Team | Generate attack prompts |
| `POST` | `/run_batch` | Red-Team | Run batch evaluation |
| `GET` | `/catalog` | Red-Team | List all 11 attack types |
| `POST` | `/run_eval` | Evaluation | Run benchmark evaluation |
| `GET` | `/reports` | Evaluation | List generated reports |

---

## Tech Stack

| Layer | Technology |
|-------|-----------|
| Orchestration | LangGraph (StateGraph) |
| Guardrails | NVIDIA NeMo Guardrails (Colang 1.0) |
| LLM Backend | Groq API (Qwen 32B) via OpenAI-compatible endpoint |
| API Framework | FastAPI + Uvicorn |
| Dashboard | Streamlit 1.55 + Plotly |
| Database | SQLite + aiosqlite |
| Encryption | Fernet (cryptography) |
| PDF Reports | fpdf2 |
| Observability | Prometheus + OpenTelemetry |
| Deployment | Docker, Railway, Kubernetes (Helm) |

---

## Project Structure

```
ethicsguard-v0.4/
├── core/
│   ├── colang_config/          # NeMo Guardrails rules (Colang 1.0)
│   ├── langgraph_agents/       # 8-node safety pipeline
│   └── models/                 # Pydantic response models
├── services/
│   ├── guardrail-service/      # Main safety API (:8000)
│   ├── redteam-service/        # Adversarial testing (:8001)
│   │   └── attack_types/       # 11 attack modules
│   ├── evaluation-service/     # Benchmarking (:8002)
│   └── dashboard-service/      # Streamlit UI (:8501)
│       └── pages/              # Scorecard, RedTeam, Audit, Eval, Compliance
├── shared/                     # Cross-service utilities
│   ├── compliance.py           # Multi-regulatory engine
│   ├── scorecard.py            # Weighted scoring
│   ├── toxicity_detector.py    # 6-dim toxicity
│   ├── bias_detector.py        # Demographic parity
│   ├── hallucination_detector.py # SelfCheckGPT
│   ├── owasp_mapper.py         # 20-tag OWASP mapping
│   └── audit_logger.py         # Encrypted audit trails
├── docs/                       # Full documentation
├── evaluation/                 # Benchmark datasets
├── start_local.sh              # Local launcher
├── start_railway.sh            # Production launcher
├── Dockerfile                  # Container build
└── requirements.txt            # Dependencies
```

---

## Vision

> **AI safety is not a feature — it is infrastructure.**

Just as no modern web application ships without HTTPS, no AI application should ship without a safety middleware layer. EthicsGuard is that layer — open-source, production-ready, regulation-aware, and built for the threats of 2026 and beyond.

---

<div align="center">

**EthicsGuard v0.4** — Open Source, MIT Licensed

Built for the **iSAFE Hackathon 2026**

</div>
