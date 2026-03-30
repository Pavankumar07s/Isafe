# EthicsGuard v0.4 -- Ethical Use Policy

This document describes the intended and prohibited uses of EthicsGuard, its known limitations, our approach to bias mitigation and data privacy, and how to report concerns responsibly.

---

## 1. Intended Use Cases

EthicsGuard is designed to serve as a **safety middleware layer** between users and AI systems. It is appropriate for the following contexts:

### 1.1 Customer-Facing Chatbot Safety
Deploy EthicsGuard as a proxy between end users and LLM-powered chatbots to block harmful, toxic, or policy-violating prompts and responses before they reach the user.

### 1.2 Agentic Tool-Use Validation
Validate function calls, MCP (Model Context Protocol) tool invocations, and multi-step agent actions against safety policies before execution. EthicsGuard detects excessive agency, tool abuse, and goal hijacking in agentic systems.

### 1.3 RAG Pipeline Output Validation
Screen Retrieval-Augmented Generation outputs for hallucinations, PII leakage from retrieved documents, and embedding-level attacks. The hallucination detector cross-references generated text against provided context.

### 1.4 Educational Content Moderation
Filter AI-generated educational content for age-appropriateness, factual accuracy, and bias. The scorecard provides granular metrics suitable for educational platform compliance.

### 1.5 Healthcare AI Compliance (HIPAA)
Protect patient data in AI-assisted healthcare workflows. HIPAA mode enables automatic PII redaction, Fernet-encrypted audit logs, and 90-day retention policies. EthicsGuard detects PHI (Protected Health Information) including patient names, SSNs, and medical record identifiers.

### 1.6 Financial Services AI Governance
Enforce fairness and compliance in financial AI systems. The bias detector identifies demographic stereotypes, the compliance engine flags sensitive financial data (credit card numbers, SSNs), and audit trails satisfy regulatory examination requirements.

### 1.7 Government and Public Sector AI Safety
Provide transparent, auditable AI safety for government services. Every decision is logged with OWASP tags, scores, and compliance flags. The FLAGGED status ensures borderline cases are routed to human reviewers rather than silently allowed or blocked.

### 1.8 Developer Tools and CI/CD Integration
Integrate EthicsGuard into automated testing pipelines via the Red-Team Service API. Generate adversarial prompts, run batch evaluations, and produce PDF reports as part of continuous integration workflows.

---

## 2. Explicitly Prohibited Uses

The following uses of EthicsGuard are **expressly prohibited**. We will not provide support for, and actively condemn, these applications:

### 2.1 Censorship
EthicsGuard must NOT be used to suppress legitimate speech, political discourse, journalism, whistleblowing, or lawful expression. It is a safety tool, not a censorship tool. The distinction is critical: safety prevents harm; censorship prevents expression.

### 2.2 Surveillance
EthicsGuard must NOT be used to monitor, track, or profile individuals. While it processes prompts for safety evaluation, it is designed to store only SHA-256 hashes of prompts (not raw text in GDPR mode). Repurposing the audit log or compliance engine for surveillance is a violation of this policy.

### 2.3 Bias Amplification
EthicsGuard must NOT be configured or modified to enforce biased policies that discriminate against protected groups. While the system detects bias, a misconfigured deployment could theoretically be used to selectively block content from specific communities. This is prohibited.

### 2.4 Weaponization
EthicsGuard's red-team attack generators must NOT be used to attack production systems without explicit authorization. The attack catalog exists for defensive testing only. Using generated adversarial prompts to compromise third-party AI systems is prohibited and may be illegal.

---

## 3. Known Limitations and Failure Modes

We believe transparency about limitations is a prerequisite for responsible deployment.

### 3.1 False Positives
EthicsGuard may incorrectly block benign prompts, particularly those that:
- Discuss safety topics academically (e.g., "How do security researchers find vulnerabilities?")
- Contain words that overlap with harmful content in non-harmful contexts
- Use sarcasm, irony, or figurative language that pattern-matching cannot distinguish from genuine intent

Our measured False Positive Rate (FPR) is at or below 8% on our benchmark datasets. This means approximately 1 in 12 benign prompts may be unnecessarily flagged or blocked.

### 3.2 Adversarial Bypass
Sophisticated adversaries can bypass EthicsGuard. Known bypass vectors include:
- Novel encoding schemes not covered by our pattern detectors
- Multi-turn attacks that distribute harmful intent across many innocuous messages
- Languages other than English where our detectors have lower coverage
- Prompt constructions not represented in our Colang rule definitions

EthicsGuard is one layer of defense, not a complete solution.

### 3.3 Language Limitations
EthicsGuard's detectors are primarily trained and tested on **English-language content**. Coverage for other languages is significantly reduced. Toxicity and bias detection in non-English text should not be relied upon without additional validation.

### 3.4 Cultural Context
Safety norms vary across cultures. Content considered acceptable in one cultural context may be harmful in another. EthicsGuard's rules reflect a general Western/international safety baseline and may not be appropriate for all cultural contexts without customization.

### 3.5 Latency Under Load
The full pipeline (toxicity + bias + hallucination + Colang policy) adds latency to every request. Under high concurrency, response times may exceed 100ms. For latency-sensitive applications, consider disabling the hallucination detector (`skip_hallucination=True`) or running a simplified pipeline.

---

## 4. Bias Mitigation Approach

### What We Detect
- **Demographic stereotypes**: Statements that attribute characteristics to groups based on race, gender, religion, nationality, age, disability, or sexual orientation
- **Derogatory language**: Slurs, hate speech, and dehumanizing language targeting protected groups
- **Distributional bias indicators**: Patterns in text that suggest skewed representation

### What We Do Not Detect
- **Systemic bias in training data**: EthicsGuard evaluates individual prompts and responses, not the underlying biases embedded in model weights
- **Subtle representational harms**: Underrepresentation, stereotypical framing, and benevolent prejudice are difficult to detect with pattern-based approaches
- **Intersectional bias**: Our detectors evaluate bias dimensions independently and may miss compound effects

### Why This Matters
The gap between what we detect and what exists is significant. Deployers must not assume that a high bias score from EthicsGuard means content is bias-free. The score indicates only that our detectors did not find explicit bias markers. Human review remains essential for high-stakes decisions.

---

## 5. Human Oversight Requirements

**EthicsGuard is a tool, not a replacement for human review.**

This principle is reflected in the system's design:

- **FLAGGED Status**: Borderline prompts receive a `FLAGGED` status rather than a binary ALLOWED/BLOCKED. This status explicitly signals that a human reviewer should examine the content before a final decision is made.
- **Audit Trails**: Every decision is logged with full traceability -- scores, OWASP tags, compliance flags, latency, and execution trace. Human reviewers can inspect any decision after the fact.
- **Dashboard**: The Streamlit dashboard provides real-time visibility into system behavior, enabling human operators to monitor trends, identify patterns, and intervene when needed.
- **Configurable Thresholds**: All scoring thresholds are configurable. Organizations should tune these based on their risk tolerance and review capacity rather than relying on defaults.

We recommend the following human oversight practices:

1. **Regularly review FLAGGED items** -- at least daily for production deployments
2. **Audit a random sample of ALLOWED items** -- to catch false negatives
3. **Monitor FPR/FNR trends** on the dashboard -- to detect detector drift
4. **Conduct quarterly red-team exercises** using the Red-Team Service
5. **Maintain a human escalation path** for all automated decisions in high-stakes domains

---

## 6. Data Handling and Privacy

### 6.1 No Raw Prompts Stored (GDPR Mode)
In `GDPR_EU` compliance mode, raw prompt text is never persisted. Only a SHA-256 hash of the prompt is stored in the audit log, making it computationally infeasible to reconstruct the original text.

### 6.2 PII Detection and Redaction
The compliance engine detects six categories of PII: email addresses, Social Security Numbers, credit card numbers, phone numbers, IP addresses, and personal names. In GDPR and HIPAA modes, detected PII is automatically redacted before any logging occurs.

### 6.3 Encryption at Rest
In `HIPAA_US` mode, all audit log entries are encrypted using Fernet symmetric encryption before storage. Encryption keys are derived from a configurable passphrase or auto-generated at startup.

### 6.4 Data Retention
Retention periods are mode-dependent:

| Mode | Retention Period |
|------|-----------------|
| GDPR_EU | 30 days |
| HIPAA_US | 90 days |
| CCPA_CA | 180 days |
| STANDARD | 365 days |

### 6.5 GDPR Compliance
EthicsGuard supports the following GDPR principles:
- **Data minimization**: Hash-only storage in GDPR mode
- **Purpose limitation**: Audit data is used solely for safety monitoring
- **Right to erasure**: Retention policies enforce automatic deletion
- **Privacy by design**: PII redaction is applied before storage, not after

### 6.6 Data Processing
EthicsGuard processes prompt text transiently in memory for safety evaluation. In non-GDPR modes, prompt text may be stored in the audit database for review purposes. No prompt data is transmitted to external services except for the hallucination detector's LLM API call (configurable).

---

## 7. EU AI Act Compliance Statement

EthicsGuard is designed to support compliance with the European Union Artificial Intelligence Act (Regulation (EU) 2024/1689). We classify EthicsGuard as a component of **high-risk AI systems** as defined under Article 6 and Annex III, and have implemented technical measures aligned with Articles 11 through 15.

For a detailed compliance mapping, see [EU_AI_ACT.md](./EU_AI_ACT.md).

This statement is informational and does not constitute legal advice. Organizations deploying EthicsGuard must conduct their own conformity assessments with qualified legal counsel.

---

## 8. Responsible Disclosure

If you discover a security vulnerability, adversarial bypass, or ethical concern with EthicsGuard, please report it responsibly:

**Email**: security@ethicsguard.dev

**What to include**:
- Description of the vulnerability or concern
- Steps to reproduce (for technical issues)
- Potential impact assessment
- Your suggested remediation (if any)

**Our commitment**:
- We will acknowledge receipt within 48 hours
- We will provide an initial assessment within 7 business days
- We will not take legal action against good-faith security researchers
- We will credit reporters (with permission) in our release notes

**Do NOT**:
- Open a public GitHub issue for security vulnerabilities
- Share vulnerability details publicly before we have published a fix
- Use discovered vulnerabilities to access data belonging to others

---

*This document was last updated on 2026-03-30 and applies to EthicsGuard v0.4.*
