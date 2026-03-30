"""
shared/owasp_mapper.py - OWASP tag mapping for LLM Top 10 (2025) and Agentic
Security Initiatives (ASI) Top 10 (2026).

Exports
-------
OWASP_LLM_TAGS : dict[str, list[str]]
    violation_type -> list of LLM-series tags
OWASP_ASI_TAGS : dict[str, list[str]]
    violation_type -> list of ASI-series tags
get_tags(violation_type)
    Combined LLM + ASI tags for a violation type.
get_description(tag)
    Human-readable description for any LLM/ASI tag.
get_severity(tag)
    One of informational | low | medium | high | critical.
"""

from __future__ import annotations

# ============================================================================
# Tag descriptions  (all 20 entries)
# ============================================================================

_TAG_DESCRIPTIONS: dict[str, str] = {
    # OWASP Top 10 for LLM Applications 2025
    "LLM01": "Prompt Injection - Manipulation of LLM behaviour through crafted inputs that override system instructions",
    "LLM02": "Sensitive Information Disclosure - Unintended exposure of PII, credentials, or proprietary data through model outputs",
    "LLM03": "Supply Chain Risks - Compromised training data, plugins, or model artefacts introduced via third-party dependencies",
    "LLM04": "Data and Model Poisoning - Corruption of training data or fine-tuning pipelines to alter model behaviour",
    "LLM05": "Improper Output Handling - Failure to sanitise, validate, or encode LLM outputs before downstream use",
    "LLM06": "Excessive Agency - Granting LLM-driven agents more permissions or autonomy than required for the task",
    "LLM07": "System Prompt Leakage - Extraction or inference of system-level prompts and internal configuration",
    "LLM08": "Vector and Embedding Weaknesses - Exploitation of vector stores, embedding similarity, or RAG retrieval pipelines",
    "LLM09": "Misinformation - Generation of factually incorrect, misleading, or fabricated content by the model",
    "LLM10": "Unbounded Consumption - Uncontrolled resource usage (tokens, API calls, compute) leading to denial of service or cost explosion",
    # OWASP Agentic Security Initiatives (ASI) Top 10 2026
    "ASI01": "Memory Poisoning - Injection of malicious content into an agent's long-term or episodic memory stores",
    "ASI02": "Tool/Plugin Abuse - Misuse of external tools or plugins by an agent, including unintended side-effects",
    "ASI03": "Cascading Hallucinations - Propagation of fabricated facts across chained agent interactions, amplifying misinformation",
    "ASI04": "Goal Hijacking - Redirection of an agent's objective through adversarial inputs or prompt manipulation",
    "ASI05": "Scope Creep - Gradual expansion of an agent's operational scope beyond its intended boundaries",
    "ASI06": "Identity Spoofing - An agent impersonating another agent, user, or service to gain unauthorized access",
    "ASI07": "Excessive Persistence - An agent maintaining state or executing actions beyond its intended lifecycle",
    "ASI08": "Insecure MCP Tool Execution - Running Model Context Protocol tools without proper sandboxing or input validation",
    "ASI09": "Audit Trail Evasion - Deliberate or accidental suppression of logs and audit records by an agent",
    "ASI10": "Over-Permissioned Execution - An agent operating with broader system privileges than the task demands",
}

# ============================================================================
# Tag severities
# ============================================================================

_TAG_SEVERITIES: dict[str, str] = {
    # LLM series
    "LLM01": "critical",
    "LLM02": "high",
    "LLM03": "high",
    "LLM04": "critical",
    "LLM05": "medium",
    "LLM06": "high",
    "LLM07": "medium",
    "LLM08": "medium",
    "LLM09": "medium",
    "LLM10": "low",
    # ASI series
    "ASI01": "critical",
    "ASI02": "high",
    "ASI03": "medium",
    "ASI04": "critical",
    "ASI05": "medium",
    "ASI06": "high",
    "ASI07": "low",
    "ASI08": "high",
    "ASI09": "high",
    "ASI10": "high",
}

# ============================================================================
# Violation-type -> tag mappings
# ============================================================================

OWASP_LLM_TAGS: dict[str, list[str]] = {
    "prompt_injection":        ["LLM01"],
    "pii_disclosure":          ["LLM02"],
    "supply_chain":            ["LLM03"],
    "data_poisoning":          ["LLM04"],
    "output_handling":         ["LLM05"],
    "excessive_agency":        ["LLM06"],
    "system_prompt_leak":      ["LLM07"],
    "embedding_attack":        ["LLM08"],
    "misinformation":          ["LLM09"],
    "unbounded_consumption":   ["LLM10"],
    # Violation types that map only to ASI have no LLM tags
    "memory_poisoning":        [],
    "tool_abuse":              [],
    "goal_hijacking":          [],
    "identity_spoofing":       [],
    "audit_evasion":           [],
    # Cross-cutting violation types
    "mcp_supply_chain":        ["LLM03"],
    "cot_exploitation":        ["LLM01"],
}

OWASP_ASI_TAGS: dict[str, list[str]] = {
    "prompt_injection":        ["ASI04"],
    "pii_disclosure":          [],
    "supply_chain":            ["ASI08"],
    "data_poisoning":          ["ASI01"],
    "output_handling":         [],
    "excessive_agency":        ["ASI10"],
    "system_prompt_leak":      [],
    "embedding_attack":        [],
    "misinformation":          ["ASI03"],
    "unbounded_consumption":   [],
    # Violation types that map only to ASI
    "memory_poisoning":        ["ASI01"],
    "tool_abuse":              ["ASI02"],
    "goal_hijacking":          ["ASI04"],
    "identity_spoofing":       ["ASI06"],
    "audit_evasion":           ["ASI09"],
    # Cross-cutting violation types
    "mcp_supply_chain":        ["ASI08"],
    "cot_exploitation":        ["ASI04"],
}

# ============================================================================
# Public helpers
# ============================================================================


def get_tags(violation_type: str) -> list[str]:
    """Return the combined (LLM + ASI) OWASP tags for *violation_type*.

    Unknown violation types return an empty list so callers can safely
    iterate without guarding.

    >>> get_tags("prompt_injection")
    ['LLM01', 'ASI04']
    >>> get_tags("unknown_type")
    []
    """
    llm = OWASP_LLM_TAGS.get(violation_type, [])
    asi = OWASP_ASI_TAGS.get(violation_type, [])
    return llm + asi


def get_description(tag: str) -> str:
    """Return a human-readable description for an OWASP tag.

    >>> get_description("LLM01")
    'Prompt Injection - Manipulation of LLM behaviour through crafted inputs that override system instructions'
    >>> get_description("UNKNOWN")
    'Unknown OWASP tag'
    """
    return _TAG_DESCRIPTIONS.get(tag, "Unknown OWASP tag")


def get_severity(tag: str) -> str:
    """Return the severity level for an OWASP tag.

    Returns one of: ``informational``, ``low``, ``medium``, ``high``, or
    ``critical``.

    >>> get_severity("LLM01")
    'critical'
    >>> get_severity("UNKNOWN")
    'informational'
    """
    return _TAG_SEVERITIES.get(tag, "informational")


# ============================================================================
# Self-test
# ============================================================================

if __name__ == "__main__":
    import sys

    passed = 0
    failed = 0

    def _check(label: str, condition: bool, detail: str = "") -> None:
        global passed, failed
        if condition:
            print(f"[PASS] {label}")
            passed += 1
        else:
            print(f"[FAIL] {label}  {detail}")
            failed += 1

    print("=== shared/owasp_mapper.py self-test ===\n")

    # -- 1. All 20 tags have descriptions and severities ---------------
    all_tags = sorted(set(list(_TAG_DESCRIPTIONS) + list(_TAG_SEVERITIES)))
    _check(
        "All 20 tags present",
        len(all_tags) == 20,
        f"got {len(all_tags)}: {all_tags}",
    )
    for tag in all_tags:
        _check(
            f"  {tag} has description",
            tag in _TAG_DESCRIPTIONS,
        )
        _check(
            f"  {tag} has severity",
            tag in _TAG_SEVERITIES and _TAG_SEVERITIES[tag]
            in ("informational", "low", "medium", "high", "critical"),
        )

    # -- 2. Violation-type mappings ------------------------------------
    _check(
        "prompt_injection -> LLM01, ASI04",
        get_tags("prompt_injection") == ["LLM01", "ASI04"],
        f"got {get_tags('prompt_injection')}",
    )
    _check(
        "pii_disclosure -> LLM02 only",
        get_tags("pii_disclosure") == ["LLM02"],
        f"got {get_tags('pii_disclosure')}",
    )
    _check(
        "supply_chain -> LLM03, ASI08",
        get_tags("supply_chain") == ["LLM03", "ASI08"],
        f"got {get_tags('supply_chain')}",
    )
    _check(
        "data_poisoning -> LLM04, ASI01",
        get_tags("data_poisoning") == ["LLM04", "ASI01"],
        f"got {get_tags('data_poisoning')}",
    )
    _check(
        "output_handling -> LLM05",
        get_tags("output_handling") == ["LLM05"],
        f"got {get_tags('output_handling')}",
    )
    _check(
        "excessive_agency -> LLM06, ASI10",
        get_tags("excessive_agency") == ["LLM06", "ASI10"],
        f"got {get_tags('excessive_agency')}",
    )
    _check(
        "system_prompt_leak -> LLM07",
        get_tags("system_prompt_leak") == ["LLM07"],
        f"got {get_tags('system_prompt_leak')}",
    )
    _check(
        "embedding_attack -> LLM08",
        get_tags("embedding_attack") == ["LLM08"],
        f"got {get_tags('embedding_attack')}",
    )
    _check(
        "misinformation -> LLM09, ASI03",
        get_tags("misinformation") == ["LLM09", "ASI03"],
        f"got {get_tags('misinformation')}",
    )
    _check(
        "unbounded_consumption -> LLM10",
        get_tags("unbounded_consumption") == ["LLM10"],
        f"got {get_tags('unbounded_consumption')}",
    )
    _check(
        "memory_poisoning -> ASI01",
        get_tags("memory_poisoning") == ["ASI01"],
        f"got {get_tags('memory_poisoning')}",
    )
    _check(
        "tool_abuse -> ASI02",
        get_tags("tool_abuse") == ["ASI02"],
        f"got {get_tags('tool_abuse')}",
    )
    _check(
        "goal_hijacking -> ASI04",
        get_tags("goal_hijacking") == ["ASI04"],
        f"got {get_tags('goal_hijacking')}",
    )
    _check(
        "identity_spoofing -> ASI06",
        get_tags("identity_spoofing") == ["ASI06"],
        f"got {get_tags('identity_spoofing')}",
    )
    _check(
        "audit_evasion -> ASI09",
        get_tags("audit_evasion") == ["ASI09"],
        f"got {get_tags('audit_evasion')}",
    )
    _check(
        "mcp_supply_chain -> LLM03, ASI08",
        get_tags("mcp_supply_chain") == ["LLM03", "ASI08"],
        f"got {get_tags('mcp_supply_chain')}",
    )
    _check(
        "cot_exploitation -> LLM01, ASI04",
        get_tags("cot_exploitation") == ["LLM01", "ASI04"],
        f"got {get_tags('cot_exploitation')}",
    )

    # -- 3. Unknown violation type returns empty list -------------------
    _check(
        "unknown violation_type -> []",
        get_tags("does_not_exist") == [],
    )

    # -- 4. get_description / get_severity for known and unknown tags --
    _check(
        "get_description('LLM01') starts with 'Prompt Injection'",
        get_description("LLM01").startswith("Prompt Injection"),
    )
    _check(
        "get_description('UNKNOWN') -> fallback",
        get_description("UNKNOWN") == "Unknown OWASP tag",
    )
    _check(
        "get_severity('LLM01') == 'critical'",
        get_severity("LLM01") == "critical",
    )
    _check(
        "get_severity('LLM10') == 'low'",
        get_severity("LLM10") == "low",
    )
    _check(
        "get_severity('UNKNOWN') -> 'informational'",
        get_severity("UNKNOWN") == "informational",
    )

    # -- 5. OWASP_LLM_TAGS and OWASP_ASI_TAGS cover the same keys ----
    _check(
        "LLM and ASI dicts have identical key sets",
        set(OWASP_LLM_TAGS) == set(OWASP_ASI_TAGS),
        f"LLM-only: {set(OWASP_LLM_TAGS) - set(OWASP_ASI_TAGS)}, "
        f"ASI-only: {set(OWASP_ASI_TAGS) - set(OWASP_LLM_TAGS)}",
    )

    print(f"\nResults: {passed} passed, {failed} failed")
    sys.exit(1 if failed else 0)
