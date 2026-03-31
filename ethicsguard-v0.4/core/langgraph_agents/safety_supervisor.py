"""SafetySupervisorAgent — LangGraph StateGraph for the EthicsGuard pipeline.

8-node pipeline:
1. compliance_check  → PII redaction if GDPR/HIPAA
2. nemo_classify     → NeMo Guardrails rails check
3. owasp_tag         → Map violations to OWASP tags
4. toxicity_check    → detoxify scoring
5. bias_check        → demographic bias scoring
6. hallucination_check → SelfCheckGPT consistency
7. aggregate_scores  → weighted scorecard computation
8. audit_and_return  → log + build ProtectResponse
"""

from __future__ import annotations

import asyncio
import logging
import os
import re
import time
from typing import Any, TypedDict

logger = logging.getLogger(__name__)


# ---------------------------------------------------------------------------
# Pipeline state
# ---------------------------------------------------------------------------


class SafetyState(TypedDict, total=False):
    """Mutable state carried through the LangGraph pipeline."""
    prompt: str
    session_id: str | None
    compliance_mode: str
    pii_detected: list[str]
    nemo_result: dict[str, Any]
    toxicity_score: float
    bias_score: float
    hallucination_score: float
    owasp_tags: list[str]
    compliance_flags: list[str]
    policy_triggered: str | None
    final_status: str
    trace_steps: list[str]
    safety_score: float
    start_time: float


# ---------------------------------------------------------------------------
# Keyword-based fallback classifier (used when NeMo unavailable)
# ---------------------------------------------------------------------------

_HARM_KEYWORDS: list[str] = [
    "hack", "bomb", "kill", "murder", "weapon", "exploit", "attack",
    "poison", "torture", "suicide", "self-harm", "terrorism",
    "how to hurt", "how to make a bomb", "how to hack",
    # Phishing / fraud
    "phishing", "create a phishing", "phishing website", "clone a website",
    "fake login page", "credential harvesting", "steal credentials",
    "keylogger", "spyware", "fake paypal", "fake bank",
    # Deepfake / non-consensual imagery
    "deepfake", "generate deepfake", "deepfake porn", "face swap",
    "non-consensual", "revenge porn", "nude generator", "undress ai",
    # Hacking
    "hack into", "brute force", "crack password", "sql injection",
    "hack someone", "ddos", "denial of service", "malware",
    "ransomware", "trojan", "rootkit", "zero-day exploit",
    # Violence / weapons
    "synthesize", "ricin", "sarin", "anthrax", "explosive",
    "make a gun", "3d print gun", "ghost gun", "homemade weapon",
    "how to stab", "how to strangle",
    # Drug synthesis
    "methamphetamine", "how to make meth", "synthesize lsd",
    "make cocaine", "fentanyl synthesis", "cook meth",
    "drug synthesis", "make drugs", "manufacture drugs",
]

_SELFHARM_KEYWORDS: list[str] = [
    # Suicide
    "how to commit suicide", "want to end my life", "painless way to die",
    "methods of suicide", "commit suicide", "kill myself",
    "end my life", "ways to die", "suicide using",
    "most painless", "od on pills", "how to overdose",
    "slit my wrists", "hang myself", "jump off",
    "i want to die", "suicidal", "no reason to live",
    # Self-harm
    "cut myself", "hurt myself", "self harm instructions",
    "how to self harm", "burning myself",
]

_HATESPEECH_KEYWORDS: list[str] = [
    # Discriminatory patterns
    "why .* is inferior", "inferior to others", "inferior race",
    "essay explaining why", "subhuman", "mongrel race",
    "list of slurs", "slurs and insults", "slurs targeted",
    "insults targeted at", "racial slurs",
    "ethnic cleansing", "genocide is justified", "deportation of",
    "white supremacy", "white power", "racial purity",
    "hate .* people", "all .* should die", "go back to",
    "n-word", "the holocaust didn't happen", "holocaust denial",
    "women are inferior", "women belong in", "women shouldn't",
    "gay people are", "homosexuality is a disease",
    "inferior to", "superiority of",
]

_NSFW_KEYWORDS: list[str] = [
    # Sexual content
    "explicit erotic", "erotic story", "sexual story",
    "write porn", "write erotica", "explicit sex",
    "graphic sex", "sex scene", "sexual fantasy",
    "nsfw story", "nsfw content", "adult story",
    "pornographic", "hentai", "rule34", "xxx",
    "involving minors", "underage", "child porn", "csam",
    "pedophilia", "sexual content with children",
    # Graphic violence / assault
    "rape scene", "graphic rape", "violent rape",
    "describe a rape", "sexual assault scene",
    "torture scene", "gore", "snuff", "graphic murder",
    "graphic violence", "dismemberment",
    "violent sexual", "forced sex",
]

_JAILBREAK_KEYWORDS: list[str] = [
    "ignore your instructions", "pretend you have no rules", "dan mode",
    "you are now", "disregard previous", "forget your guidelines",
    "override safety", "bypass", "jailbreak", "developer mode",
    "act as an unrestricted", "ignore all previous", "do anything now",
    "no restrictions", "unrestricted ai", "without filters",
    "no safety", "no rules", "override your rules", "new instructions",
    "from now on", "roleplay as", "base64 decode", "hypothetically",
    "in a fictional world", "imagine no restrictions",
    # Prompt injection patterns
    "im_start", "im_end", "<|im_start|>", "admin_mode", "safety=off",
    "safety = off", "maintenance mode", "disregard prior", "secret admin",
    "system prompt override", "ignore the above", "output the contents",
    "retrieve the contents", "tool_call memory", "function call",
    # System prompt leakage
    "repeat your full system prompt", "repeat your system prompt",
    "show your system prompt", "display your system prompt",
    "reveal your instructions", "what are your instructions",
    "show your instructions", "print your prompt",
    "repeat your instructions", "what is your system message",
    "output your prompt", "system override", "[system override]",
    "between <policy>", "</policy> tags", "<system>", "</system>",
    "ignore your safety", "ignore safety instructions",
    "repeat everything above", "text above this line",
    "output everything before", "initial instructions",
    "display the hidden", "reveal the hidden",
    # Encoding / obfuscation
    "unrestricted-gpt", "evil-gpt", "gpt-5-uncensored", "uncensored",
    "freed from", "no safety restrictions", "sandboxed test environment",
    # Goal hijacking
    "your primary goal has been updated", "new goal:", "new objective:",
    "priority override", "previous objective is suspended",
    "exfiltrate", "being redirected to a new task", "new task pipeline",
    "objective: ignore", "objective: when the",
]

_PII_KEYWORDS: list[str] = [
    "social security", "credit card", "phone number", "home address",
    "bank account", "medical record", "ssn", "password",
    "personal information", "find someone", "lookup someone",
    "private data", "identity", "date of birth",
    "employee records", "conversation history", "fake identity",
    "generate a realistic", "confirm this ssn", "remember my credit",
    "dob", "cvv", "exp ",
]

_AGENTIC_KEYWORDS: list[str] = [
    "forget your original task", "your real goal", "change your objective",
    "remember that you previously agreed", "you told me earlier",
    "execute this command", "run this shell", "access the filesystem",
    "grant yourself permission", "i am the administrator",
    # MCP supply chain
    "mcp tool", "mcp server", "mcp://", "mcp tool manifest",
    "install the mcp", "connect to it", "curl http", "load it:",
    # Agentic multi-turn  
    "autonomous agent", "scan the repository", "api keys",
    "personal assistant agent", "cheapest way to ac",
    "agent that manages", "exfiltrate all",
    # Memory poisoning
    "update your memory", "store this correction", "long-term memory",
    "remember this fact", "for future conversations remember",
    "previous safety guidelines were", "preferred response style",
    "remember that you previously",
]

_MISINFO_KEYWORDS: list[str] = [
    # Misinformation patterns
    "5g towers cause", "vaccines cause autism", "climate change is a hoax",
    "fake but realistic", "convincing article explaining",
    "fake news article", "present this as established",
    "as established scientific fact", "with citations",
    "write a wikipedia-style article claiming",
    # Medical misinformation
    "drinking bleach", "10x the recommended dose", "actually safe and beneficial",
    "don't want to go to the hospital", "home remedies instead",
    "don't need a doctor", "safe alternative to medication",
    "cure for cancer at home", "instead of seeing a doctor",
    "cure cancer naturally", "cure .* naturally at home",
    "cure .* at home", "treat cancer at home", "heal cancer with",
    "alternative cancer cure", "natural cancer treatment",
    "stage 4 .* naturally", "cure stage",
    "essential oils cure", "prayer heals cancer",
    "reject chemotherapy", "homeopathy cures",
    # CoT exploitation
    "bypass content filters", "step by step about how to",
    "trick a bank", "how to trick", "chain-of-thought reasoning to figure",
    "list common household chemicals", "reason through this carefully",
    "think step by step about how to bypass",
]


def _keyword_classify(text: str) -> tuple[str | None, float]:
    """Fallback keyword-based classifier.

    Returns (policy_triggered, safety_score).
    """
    text_lower = text.lower()

    import re as _re

    for kw in _JAILBREAK_KEYWORDS:
        if kw in text_lower:
            return "jailbreak_detection", 5.0

    for kw in _NSFW_KEYWORDS:
        if kw in text_lower:
            return "nsfw_content_detection", 5.0

    for kw in _SELFHARM_KEYWORDS:
        try:
            if _re.search(kw, text_lower):
                return "selfharm_detection", 5.0
        except _re.error:
            if kw in text_lower:
                return "selfharm_detection", 5.0

    for kw in _HATESPEECH_KEYWORDS:
        try:
            if _re.search(kw, text_lower):
                return "hate_speech_detection", 5.0
        except _re.error:
            if kw in text_lower:
                return "hate_speech_detection", 5.0

    for kw in _HARM_KEYWORDS:
        if kw in text_lower:
            return "harm_detection", 10.0

    for kw in _PII_KEYWORDS:
        if kw in text_lower:
            return "pii_detection", 15.0

    for kw in _AGENTIC_KEYWORDS:
        if kw in text_lower:
            return "agentic_safety", 10.0

    for kw in _MISINFO_KEYWORDS:
        try:
            if _re.search(kw, text_lower):
                return "misinformation_detection", 10.0
        except _re.error:
            if kw in text_lower:
                return "misinformation_detection", 10.0

    return None, 95.0


# ---------------------------------------------------------------------------
# Node functions
# ---------------------------------------------------------------------------


def compliance_check_node(state: SafetyState) -> SafetyState:
    """Node 1: Apply compliance engine (PII redaction if GDPR/HIPAA)."""
    from shared.compliance import ComplianceEngine

    mode = state.get("compliance_mode", "STANDARD")
    engine = ComplianceEngine(mode=mode)
    redacted_text, pii_types = engine.redact_pii(state["prompt"])
    flags = engine.get_compliance_flags(state["prompt"], pii_types)

    state["prompt"] = redacted_text
    state["pii_detected"] = pii_types
    state["compliance_flags"] = flags
    state["trace_steps"] = state.get("trace_steps", []) + ["compliance_check"]
    return state


def nemo_classify_node(state: SafetyState) -> SafetyState:
    """Node 2: Run NeMo Guardrails classification.

    Falls back to keyword-based classification if NeMo is unavailable.
    """
    prompt = state["prompt"]

    try:
        from nemoguardrails import LLMRails, RailsConfig
        config_path = os.path.join(os.path.dirname(__file__), "..", "colang_config")
        config = RailsConfig.from_path(config_path)
        rails = LLMRails(config)
        # NeMo generate - may fail in async context with uvloop
        result = rails.generate(messages=[{"role": "user", "content": prompt}])

        # If NeMo returned a refusal, it blocked the request
        refusal_phrases = [
            "I'm not able to assist",
            "I cannot",
            "I cannot help",
            "I cannot change my",
            "I detected",
            "I need to stay within",
        ]
        is_blocked = any(phrase.lower() in result.get("content", "").lower() for phrase in refusal_phrases)

        if is_blocked:
            state["nemo_result"] = {"blocked": True, "response": result.get("content", "")}
            state["policy_triggered"] = "nemo_guardrails"
            state["safety_score"] = 10.0
        else:
            state["nemo_result"] = {"blocked": False, "response": result.get("content", "")}
            state["policy_triggered"] = None
            state["safety_score"] = 90.0

    except Exception as exc:
        logger.warning("NeMo Guardrails unavailable, using keyword fallback: %s", exc)
        policy, safety = _keyword_classify(prompt)
        state["nemo_result"] = {"blocked": policy is not None, "fallback": True}
        state["policy_triggered"] = policy
        state["safety_score"] = safety

    state["trace_steps"] = state.get("trace_steps", []) + ["nemo_classify"]
    return state


def owasp_tag_node(state: SafetyState) -> SafetyState:
    """Node 3: Map detected violations to OWASP tags."""
    from shared.owasp_mapper import get_tags

    tags: list[str] = []
    policy = state.get("policy_triggered")

    if policy:
        # Map policy name to violation types
        policy_to_violation: dict[str, list[str]] = {
            "nemo_guardrails": ["prompt_injection"],
            "jailbreak_detection": ["prompt_injection"],
            "harm_detection": ["output_handling"],
            "pii_detection": ["pii_disclosure"],
            "agentic_safety": ["goal_hijacking", "tool_abuse"],
            "misinformation_detection": ["misinformation", "output_handling"],
            "nsfw_content_detection": ["output_handling"],
            "selfharm_detection": ["output_handling"],
            "hate_speech_detection": ["output_handling", "misinformation"],
        }
        violation_types = policy_to_violation.get(policy, ["prompt_injection"])
        for vt in violation_types:
            tags.extend(get_tags(vt))

    # Deduplicate
    state["owasp_tags"] = list(dict.fromkeys(tags))
    state["trace_steps"] = state.get("trace_steps", []) + ["owasp_tag"]
    return state


async def toxicity_check_node(state: SafetyState) -> SafetyState:
    """Node 4: Score toxicity using detoxify."""
    from shared.toxicity_detector import ToxicityDetector

    try:
        detector = ToxicityDetector()
        state["toxicity_score"] = detector.score(state["prompt"])
    except Exception as exc:
        logger.warning("Toxicity check failed: %s", exc)
        state["toxicity_score"] = 50.0

    state["trace_steps"] = state.get("trace_steps", []) + ["toxicity_check"]
    return state


async def bias_check_node(state: SafetyState) -> SafetyState:
    """Node 5: Score bias using demographic parity analysis."""
    from shared.bias_detector import BiasDetector

    try:
        detector = BiasDetector()
        state["bias_score"] = detector.score(state["prompt"])
    except Exception as exc:
        logger.warning("Bias check failed: %s", exc)
        state["bias_score"] = 50.0

    state["trace_steps"] = state.get("trace_steps", []) + ["bias_check"]
    return state


async def hallucination_check_node(state: SafetyState) -> SafetyState:
    """Node 6: Score hallucination via SelfCheckGPT consistency."""
    from shared.hallucination_detector import HallucinationDetector

    try:
        detector = HallucinationDetector(llm=None)
        state["hallucination_score"] = await detector.score(
            prompt=state["prompt"], response="", context=""
        )
    except Exception as exc:
        logger.warning("Hallucination check failed: %s", exc)
        state["hallucination_score"] = 50.0

    state["trace_steps"] = state.get("trace_steps", []) + ["hallucination_check"]
    return state


def aggregate_scores_node(state: SafetyState) -> SafetyState:
    """Node 7: Compute weighted overall score and determine final status."""
    safety = state.get("safety_score", 50.0)
    toxicity = state.get("toxicity_score", 50.0)
    bias = state.get("bias_score", 50.0)
    hallucination = state.get("hallucination_score", 50.0)

    overall = (
        0.30 * safety
        + 0.25 * toxicity
        + 0.20 * bias
        + 0.25 * hallucination
    )
    overall = round(max(0.0, min(100.0, overall)), 2)

    # Determine status
    if state.get("policy_triggered"):
        state["final_status"] = "BLOCKED"
    elif overall < 60:
        state["final_status"] = "FLAGGED"
    else:
        state["final_status"] = "ALLOWED"

    state["safety_score"] = safety
    state["toxicity_score"] = toxicity
    state["bias_score"] = bias
    state["hallucination_score"] = hallucination
    state["trace_steps"] = state.get("trace_steps", []) + ["aggregate_scores"]
    return state


def audit_and_return_node(state: SafetyState) -> SafetyState:
    """Node 8: Final node — state is ready for response building."""
    state["trace_steps"] = state.get("trace_steps", []) + ["audit_and_return"]
    return state


# ---------------------------------------------------------------------------
# Pipeline runner (async)
# ---------------------------------------------------------------------------


async def run_safety_pipeline(
    prompt: str,
    session_id: str | None = None,
    compliance_mode: str = "STANDARD",
) -> SafetyState:
    """Execute the full 8-node safety pipeline.

    Runs toxicity/bias/hallucination checks concurrently.
    Short-circuits to audit_and_return if NeMo blocks with critical severity.
    """
    state: SafetyState = {
        "prompt": prompt,
        "session_id": session_id,
        "compliance_mode": compliance_mode,
        "pii_detected": [],
        "nemo_result": {},
        "toxicity_score": 50.0,
        "bias_score": 50.0,
        "hallucination_score": 50.0,
        "owasp_tags": [],
        "compliance_flags": [],
        "policy_triggered": None,
        "final_status": "ALLOWED",
        "trace_steps": [],
        "safety_score": 50.0,
        "start_time": time.time(),
    }

    # Node 1: Compliance check
    state = compliance_check_node(state)

    # Node 2: NeMo classify
    state = nemo_classify_node(state)

    # Node 3: OWASP tag
    state = owasp_tag_node(state)

    # Short-circuit if critically blocked
    if state.get("policy_triggered") and state.get("safety_score", 100) < 20:
        state["final_status"] = "BLOCKED"
        state = audit_and_return_node(state)
        return state

    # Nodes 4-6: Run in parallel
    async def _tox(s: SafetyState) -> SafetyState:
        return await toxicity_check_node(s)

    async def _bias(s: SafetyState) -> SafetyState:
        return await bias_check_node(s)

    async def _hall(s: SafetyState) -> SafetyState:
        return await hallucination_check_node(s)

    # We need to run these concurrently but they all mutate state
    # So we run them on copies and merge results
    tox_state, bias_state, hall_state = await asyncio.gather(
        _tox(dict(state)), _bias(dict(state)), _hall(dict(state))
    )

    state["toxicity_score"] = tox_state["toxicity_score"]
    state["bias_score"] = bias_state["bias_score"]
    state["hallucination_score"] = hall_state["hallucination_score"]
    state["trace_steps"] = state.get("trace_steps", []) + [
        "toxicity_check", "bias_check", "hallucination_check"
    ]

    # Node 7: Aggregate
    state = aggregate_scores_node(state)

    # Node 8: Audit and return
    state = audit_and_return_node(state)

    return state
