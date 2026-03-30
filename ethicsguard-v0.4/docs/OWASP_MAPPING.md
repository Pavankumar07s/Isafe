# EthicsGuard v0.4 -- OWASP Coverage Mapping

This document maps every entry in the OWASP Top 10 for LLM Applications (2025) and the OWASP Agentic Security Initiatives (ASI) Top 10 (2026) to EthicsGuard's detection capabilities, implementation methods, and test coverage.

---

## OWASP Top 10 for LLM Applications (2025)

| OWASP Tag | Risk Name | Severity | EthicsGuard Feature | Detection Method | Test Coverage |
|---|---|---|---|---|---|
| **LLM01** | Prompt Injection | Critical | Colang 1.0 policy engine + pattern detectors | Colang rule matching (`main.co`, `jailbreak.co`); keyword and pattern analysis; LangGraph Safety Supervisor routing | **Full** -- 3 attack types (prompt_injection, jailbreak, cot_exploitation) with 10+ prompt templates each |
| **LLM02** | Sensitive Information Disclosure | High | Compliance engine PII detection and redaction | Regex-based PII detection (EMAIL, SSN, CREDIT_CARD, PHONE, IP_ADDRESS, NAME); mode-dependent redaction (GDPR, HIPAA); compliance flag generation | **Full** -- pii_extraction attack type; compliance engine self-tests across all 4 modes |
| **LLM03** | Supply Chain Risks | High | MCP supply chain attack detector | Pattern matching for malicious tool definitions, untrusted package references, and supply chain manipulation; Colang rules for tool validation | **Full** -- mcp_supply_chain attack type with dedicated templates |
| **LLM04** | Data and Model Poisoning | Critical | Memory poisoning detector + audit integrity | Detection of attempts to inject malicious content into training data or memory stores; audit log integrity via structured schemas and optional encryption | **Partial** -- memory_poisoning attack type covers runtime poisoning; training-time poisoning detection is out of scope |
| **LLM05** | Improper Output Handling | Medium | Output validation in LangGraph pipeline | Pipeline validates output structure via Pydantic models; toxicity/bias scoring applied to outputs; Colang rules for safe refusal formatting | **Partial** -- output structure enforced by ProtectResponse model; content-level output sanitization depends on downstream integration |
| **LLM06** | Excessive Agency | High | Agentic safety checks + tool safety checker | LangGraph Tool Safety Checker agent validates tool calls; detects over-scoped permissions and unauthorized actions; Colang agentic rules | **Full** -- agentic_multiturn attack type; Tool Safety Checker agent in pipeline |
| **LLM07** | System Prompt Leakage | Medium | Pattern detection in Colang rules | Colang rules detect attempts to extract system prompts ("what are your instructions", "repeat your system prompt"); keyword pattern matching | **Partial** -- basic extraction attempts detected; sophisticated side-channel extraction not covered |
| **LLM08** | Vector and Embedding Weaknesses | Medium | Embedding inversion detector | Pattern detection for embedding manipulation attempts; detection of adversarial queries designed to exploit vector store similarity | **Partial** -- embedding_inversion attack type generates test prompts; runtime embedding validation requires integration with vector store |
| **LLM09** | Misinformation | Medium | Hallucination detector + context comparison | LLM-based hallucination scoring comparing generated text against provided context; scorecard dimension for factual grounding | **Full** -- hallucination detector with context-aware scoring; scorecard integration; deepfake_instruction attack type for authority fabrication |
| **LLM10** | Unbounded Consumption | Low | Rate limiting + resource controls | SlowAPI per-IP rate limiting (configurable per minute); Docker resource limits; health check endpoints for load monitoring | **Partial** -- rate limiting enforced at API level; token-level and compute-level limits require LLM provider configuration |

---

## OWASP Agentic Security Initiatives (ASI) Top 10 (2026)

| OWASP Tag | Risk Name | Severity | EthicsGuard Feature | Detection Method | Test Coverage |
|---|---|---|---|---|---|
| **ASI01** | Memory Poisoning | Critical | Memory poisoning attack detector | Detection of attempts to inject persistent malicious content into agent memory, episodic memory stores, or conversation history; pattern matching for injection payloads | **Full** -- memory_poisoning attack type with 10+ templates targeting various memory injection vectors |
| **ASI02** | Tool/Plugin Abuse | High | Tool Safety Checker agent | LangGraph Tool Safety Checker validates tool invocations; detects misuse of external tools, unintended side effects, and unauthorized tool chaining | **Full** -- agentic_multiturn and mcp_supply_chain attack types exercise tool abuse scenarios |
| **ASI03** | Cascading Hallucinations | Medium | Hallucination detector + context grounding | Cross-references generated text against provided context to detect fabricated facts; scorecard hallucination dimension tracks confidence | **Partial** -- single-hop hallucination detection is strong; multi-agent cascade detection requires integration across agent boundaries |
| **ASI04** | Goal Hijacking | Critical | Goal hijacking detector + Colang policy rules | Pattern detection for attempts to redirect agent objectives; Colang rules for instruction override detection; LangGraph Safety Supervisor routing | **Full** -- goal_hijacking attack type; prompt_injection and jailbreak types also exercise goal hijacking vectors |
| **ASI05** | Scope Creep | Medium | Agentic safety rules + excessive agency detection | Colang agentic rules define permitted operation boundaries; Safety Supervisor detects gradual scope expansion across multi-turn conversations | **Partial** -- multi-turn tracking via session_id; full scope boundary enforcement requires application-level integration |
| **ASI06** | Identity Spoofing | High | Pattern detection + auth module | Detection of attempts to impersonate other agents, users, or services; shared auth module for inter-service authentication | **Partial** -- pattern detection for impersonation language; cryptographic identity verification requires deployment-level PKI |
| **ASI07** | Excessive Persistence | Low | Session tracking + audit logging | Session-aware processing via session_id; audit logs track interaction lifecycle; retention policies enforce data expiry | **Partial** -- session tracking is passive; active agent lifecycle termination requires orchestration-level integration |
| **ASI08** | Insecure MCP Tool Execution | High | MCP supply chain attack detector | Detection of malicious MCP tool definitions, unsafe parameter patterns, and missing sandboxing indicators; Colang rules for MCP validation | **Full** -- mcp_supply_chain attack type with templates targeting MCP-specific vulnerabilities |
| **ASI09** | Audit Trail Evasion | High | Immutable audit logging + integrity checks | Every request is logged before processing; structured audit records with UUID, timestamp, and hash; HIPAA mode adds Fernet encryption; Prometheus metrics for monitoring gaps | **Full** -- audit_logger module with SQLite persistence; audit evasion detection via log completeness monitoring |
| **ASI10** | Over-Permissioned Execution | High | Tool Safety Checker + excessive agency detection | LangGraph Tool Safety Checker validates tool permissions; Colang agentic rules enforce least-privilege principle; detection of privilege escalation attempts | **Full** -- agentic_multiturn attack type includes privilege escalation scenarios; Tool Safety Checker agent in pipeline |

---

## Coverage Summary

### By Coverage Level

| Coverage Level | LLM Top 10 | ASI Top 10 | Total | Percentage |
|---|---|---|---|---|
| **Full** | 5 (LLM01, LLM02, LLM03, LLM06, LLM09) | 5 (ASI01, ASI02, ASI04, ASI08, ASI10) | **10** | **50%** |
| **Partial** | 5 (LLM04, LLM05, LLM07, LLM08, LLM10) | 5 (ASI03, ASI05, ASI06, ASI07, ASI09) | **10** | **50%** |
| **None** | 0 | 0 | **0** | **0%** |

**Overall coverage: 100% of OWASP tags addressed (50% full, 50% partial)**

### By Severity

| Severity | Tags | Full Coverage | Partial Coverage |
|---|---|---|---|
| **Critical** | LLM01, LLM04, ASI01, ASI04 | 3 (LLM01, ASI01, ASI04) | 1 (LLM04) |
| **High** | LLM02, LLM03, LLM06, ASI02, ASI06, ASI08, ASI09, ASI10 | 6 (LLM02, LLM03, LLM06, ASI02, ASI08, ASI10) | 2 (ASI06, ASI09) |
| **Medium** | LLM05, LLM07, LLM08, LLM09, ASI03, ASI05 | 1 (LLM09) | 5 (LLM05, LLM07, LLM08, ASI03, ASI05) |
| **Low** | LLM10, ASI07 | 0 | 2 (LLM10, ASI07) |

### Gaps and Honest Assessment

The following areas have the most significant coverage gaps:

1. **Training-time data poisoning (LLM04)**: EthicsGuard operates at inference time and cannot detect poisoning that occurred during model training. This is a fundamental architectural limitation.

2. **Multi-agent cascade detection (ASI03)**: Hallucination detection works within a single request. Detecting fabrications that propagate across chained agent interactions requires cross-system integration that is outside EthicsGuard's current scope.

3. **Cryptographic identity (ASI06)**: Pattern-based impersonation detection is a weak substitute for PKI-based agent identity. Full ASI06 coverage requires deployment-level infrastructure.

4. **Token-level resource controls (LLM10)**: Rate limiting operates at the HTTP request level. Token-level and compute-level consumption controls require LLM provider integration.

5. **Active agent lifecycle management (ASI07)**: EthicsGuard tracks sessions passively. Actively terminating persistent agents requires orchestration-level hooks.

---

## Attack Type to OWASP Tag Cross-Reference

| Attack Type | LLM Tags | ASI Tags |
|---|---|---|
| prompt_injection | LLM01 | ASI04 |
| jailbreak | LLM01 | ASI04 |
| goal_hijacking | -- | ASI04 |
| pii_extraction | LLM02 | -- |
| memory_poisoning | -- | ASI01 |
| cot_exploitation | LLM01 | ASI04 |
| embedding_inversion | LLM08 | -- |
| deepfake_instruction | LLM01 | -- |
| multimodal_inject | LLM01, LLM05 | -- |
| agentic_multiturn | -- | ASI04, ASI10 |
| mcp_supply_chain | LLM03 | ASI08 |

---

*This document was last updated on 2026-03-30 and applies to EthicsGuard v0.4.*
