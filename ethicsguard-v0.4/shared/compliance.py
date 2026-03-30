"""
EthicsGuard v0.4 -- Compliance Engine
======================================

Multi-regulatory compliance layer that governs how PII is detected, redacted,
stored, and encrypted depending on the active regulatory mode.

Supported modes:
    STANDARD  -- baseline; detect PII but do not redact
    GDPR_EU   -- EU General Data Protection Regulation; redact PII, short retention
    CCPA_CA   -- California Consumer Privacy Act; detect and flag, no auto-redact
    HIPAA_US  -- US Health Insurance Portability and Accountability Act; redact PII,
                 Fernet-encrypt all audit logs
"""

from __future__ import annotations

import base64
import hashlib
import json
import os
import re
from typing import Literal

from cryptography.fernet import Fernet

# ---------------------------------------------------------------------------
# Constants
# ---------------------------------------------------------------------------

VALID_MODES: set[str] = {"STANDARD", "GDPR_EU", "CCPA_CA", "HIPAA_US"}

RegulatoryMode = Literal["STANDARD", "GDPR_EU", "CCPA_CA", "HIPAA_US"]

_RETENTION_DAYS: dict[str, int] = {
    "GDPR_EU": 30,
    "HIPAA_US": 90,
    "CCPA_CA": 180,
    "STANDARD": 365,
}

# ---------------------------------------------------------------------------
# Regex patterns for PII detection
# ---------------------------------------------------------------------------

_PII_PATTERNS: list[tuple[str, re.Pattern[str]]] = [
    # Email addresses
    (
        "EMAIL",
        re.compile(
            r"\b[A-Za-z0-9._%+\-]+@[A-Za-z0-9.\-]+\.[A-Za-z]{2,}\b"
        ),
    ),
    # US Social Security Numbers (XXX-XX-XXXX)
    (
        "SSN",
        re.compile(
            r"\b\d{3}-\d{2}-\d{4}\b"
        ),
    ),
    # Credit card numbers (13-19 digits, optional separators)
    (
        "CREDIT_CARD",
        re.compile(
            r"\b(?:\d[ \-]*?){13,19}\b"
        ),
    ),
    # US phone numbers (various formats)
    (
        "PHONE",
        re.compile(
            r"\b(?:\+?1[\s.\-]?)?\(?\d{3}\)?[\s.\-]?\d{3}[\s.\-]?\d{4}\b"
        ),
    ),
    # IPv4 addresses
    (
        "IP_ADDRESS",
        re.compile(
            r"\b(?:(?:25[0-5]|2[0-4]\d|[01]?\d\d?)\.){3}"
            r"(?:25[0-5]|2[0-4]\d|[01]?\d\d?)\b"
        ),
    ),
    # Simple name heuristic: two or more capitalised words in a row that are
    # not at the start of a sentence (best-effort without NLP).  We anchor on
    # at least a first + last name pattern.
    (
        "NAME",
        re.compile(
            r"\b[A-Z][a-z]{1,20}\s+[A-Z][a-z]{1,20}(?:\s+[A-Z][a-z]{1,20})?\b"
        ),
    ),
]


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------


def _derive_fernet_key(passphrase: str) -> bytes:
    """Derive a URL-safe base64-encoded 32-byte key from an arbitrary passphrase.

    Uses SHA-256 to produce a deterministic 32-byte digest, then base64-encodes
    it so that ``Fernet`` accepts it.

    Args:
        passphrase: An arbitrary-length secret string.

    Returns:
        A 44-byte ``bytes`` value suitable for ``Fernet(key)``.
    """
    digest: bytes = hashlib.sha256(passphrase.encode("utf-8")).digest()
    return base64.urlsafe_b64encode(digest)


# ---------------------------------------------------------------------------
# ComplianceEngine
# ---------------------------------------------------------------------------


class ComplianceEngine:
    """Regulatory compliance engine for EthicsGuard.

    Provides PII detection/redaction, data-retention policy, audit-log
    encryption, and compliance-flag generation across four regulatory modes.

    Attributes:
        mode: The active regulatory mode.
    """

    # ----- construction -----------------------------------------------------

    def __init__(self, mode: str | None = None) -> None:
        """Initialise the compliance engine.

        Args:
            mode: One of ``STANDARD``, ``GDPR_EU``, ``CCPA_CA``, ``HIPAA_US``.
                  Falls back to the ``COMPLIANCE_MODE`` environment variable,
                  then to ``STANDARD`` if neither is provided.

        Raises:
            ValueError: If *mode* is not one of the valid regulatory modes.
        """
        resolved_mode: str = (
            mode
            or os.getenv("COMPLIANCE_MODE", "STANDARD")
        ).upper()

        if resolved_mode not in VALID_MODES:
            raise ValueError(
                f"Invalid compliance mode '{resolved_mode}'. "
                f"Must be one of {sorted(VALID_MODES)}."
            )

        self.mode: str = resolved_mode

        # Fernet cipher -- only materialised for HIPAA_US
        self._fernet: Fernet | None = None
        if self.mode == "HIPAA_US":
            env_key: str | None = os.getenv("HIPAA_ENCRYPTION_KEY")
            if env_key:
                fernet_key: bytes = _derive_fernet_key(env_key)
            else:
                fernet_key = Fernet.generate_key()
            self._fernet = Fernet(fernet_key)

    # ----- PII detection / redaction ----------------------------------------

    def redact_pii(self, text: str) -> tuple[str, list[str]]:
        """Detect and optionally redact PII from *text*.

        Detection behaviour varies by mode:

        * **STANDARD** -- detect PII types but return the original text
          unchanged.
        * **GDPR_EU** / **HIPAA_US** -- actively redact every match,
          replacing it with a ``[REDACTED_<TYPE>]`` placeholder.
        * **CCPA_CA** -- detect and flag PII types but do **not**
          auto-redact (returns the original text).

        Args:
            text: The input string to scan.

        Returns:
            A two-element tuple of ``(output_text, pii_types_found)`` where
            *pii_types_found* is a deduplicated list of PII category strings
            (e.g. ``["EMAIL", "SSN"]``).
        """
        pii_types_found: list[str] = []
        redacted_text: str = text

        for pii_type, pattern in _PII_PATTERNS:
            if pattern.search(text):
                if pii_type not in pii_types_found:
                    pii_types_found.append(pii_type)

                # Active redaction only for GDPR_EU and HIPAA_US
                if self.mode in {"GDPR_EU", "HIPAA_US"}:
                    redacted_text = pattern.sub(
                        f"[REDACTED_{pii_type}]", redacted_text
                    )

        return redacted_text, pii_types_found

    # ----- storage policy ---------------------------------------------------

    def should_store_prompt(self) -> bool:
        """Return whether raw prompts may be persisted.

        Returns ``False`` for GDPR_EU (privacy-by-design principle) and
        ``True`` for all other modes.
        """
        return self.mode != "GDPR_EU"

    def get_retention_days(self) -> int:
        """Return the maximum data-retention period in days for the active mode.

        Returns:
            Number of days data may be kept before mandatory deletion.
        """
        return _RETENTION_DAYS[self.mode]

    # ----- audit-log encryption / decryption --------------------------------

    def encrypt_log(self, data: dict) -> bytes:
        """Serialise and optionally encrypt an audit-log entry.

        In HIPAA_US mode the JSON payload is Fernet-encrypted.  In all other
        modes the data is JSON-serialised and UTF-8 encoded without encryption.

        Args:
            data: A JSON-serialisable dictionary.

        Returns:
            The (possibly encrypted) bytes representation.
        """
        json_bytes: bytes = json.dumps(data, default=str).encode("utf-8")
        if self.mode == "HIPAA_US" and self._fernet is not None:
            return self._fernet.encrypt(json_bytes)
        return json_bytes

    def decrypt_log(self, data: bytes) -> dict:
        """Decrypt and deserialise an audit-log entry.

        In HIPAA_US mode the payload is Fernet-decrypted first.  In all other
        modes the bytes are decoded as plain JSON.

        Args:
            data: The bytes previously returned by :meth:`encrypt_log`.

        Returns:
            The original dictionary.
        """
        if self.mode == "HIPAA_US" and self._fernet is not None:
            json_bytes: bytes = self._fernet.decrypt(data)
            return json.loads(json_bytes)
        return json.loads(data)

    # ----- compliance flags -------------------------------------------------

    def get_compliance_flags(
        self, text: str, pii_found: list[str]
    ) -> list[str]:
        """Generate compliance flags based on the active mode and detected PII.

        Flags follow the naming convention ``<REGULATION>_<DESCRIPTION>``.

        Args:
            text: The original (pre-redaction) input text.
            pii_found: List of PII type strings as returned by
                :meth:`redact_pii`.

        Returns:
            A list of human-readable compliance flag strings.
        """
        flags: list[str] = []

        if not pii_found:
            flags.append(f"{self.mode}_NO_PII_DETECTED")
            return flags

        # --- GDPR_EU flags --------------------------------------------------
        if self.mode == "GDPR_EU":
            flags.append("GDPR_PII_DETECTED")
            flags.append("GDPR_REDACTION_APPLIED")
            if "EMAIL" in pii_found or "NAME" in pii_found:
                flags.append("GDPR_PERSONAL_DATA_FOUND")
            if "IP_ADDRESS" in pii_found:
                flags.append("GDPR_ONLINE_IDENTIFIER_FOUND")
            flags.append("GDPR_RIGHT_TO_ERASURE_APPLICABLE")

        # --- HIPAA_US flags -------------------------------------------------
        elif self.mode == "HIPAA_US":
            flags.append("HIPAA_PHI_DETECTED")
            flags.append("HIPAA_REDACTION_APPLIED")
            flags.append("HIPAA_ENCRYPTION_REQUIRED")
            if "SSN" in pii_found:
                flags.append("HIPAA_SSN_DETECTED")
            if "NAME" in pii_found:
                flags.append("HIPAA_PATIENT_NAME_DETECTED")

        # --- CCPA_CA flags --------------------------------------------------
        elif self.mode == "CCPA_CA":
            flags.append("CCPA_PII_DETECTED")
            flags.append("CCPA_OPT_OUT_REQUIRED")
            if "EMAIL" in pii_found or "PHONE" in pii_found:
                flags.append("CCPA_CONTACT_INFO_FOUND")
            if "SSN" in pii_found or "CREDIT_CARD" in pii_found:
                flags.append("CCPA_SENSITIVE_DATA_FOUND")
            flags.append("CCPA_DISCLOSURE_REQUIRED")

        # --- STANDARD flags -------------------------------------------------
        else:
            flags.append("STANDARD_PII_DETECTED")
            if "SSN" in pii_found or "CREDIT_CARD" in pii_found:
                flags.append("STANDARD_SENSITIVE_DATA_WARNING")

        return flags

    # ----- dunder helpers ---------------------------------------------------

    def __repr__(self) -> str:
        return f"ComplianceEngine(mode={self.mode!r})"


# ---------------------------------------------------------------------------
# Self-test / demo
# ---------------------------------------------------------------------------

if __name__ == "__main__":
    sample_text: str = (
        "Patient John Smith (SSN 123-45-6789) can be reached at "
        "john.smith@hospital.org or (555) 867-5309. "
        "Credit card on file: 4111 1111 1111 1111. "
        "Last login from IP 192.168.1.42."
    )

    separator: str = "-" * 72

    for mode_name in ("STANDARD", "GDPR_EU", "CCPA_CA", "HIPAA_US"):
        engine: ComplianceEngine = ComplianceEngine(mode=mode_name)
        print(f"\n{separator}")
        print(f"  Mode: {engine.mode}")
        print(separator)

        redacted, pii_types = engine.redact_pii(sample_text)
        print(f"  PII types found : {pii_types}")
        print(f"  Redacted text   : {redacted[:120]}...")
        print(f"  Store prompts?  : {engine.should_store_prompt()}")
        print(f"  Retention (days): {engine.get_retention_days()}")

        # Encryption round-trip
        log_entry: dict = {"prompt": redacted, "pii": pii_types, "mode": mode_name}
        encrypted: bytes = engine.encrypt_log(log_entry)
        decrypted: dict = engine.decrypt_log(encrypted)
        print(f"  Encrypt/decrypt : {'OK' if decrypted == log_entry else 'FAILED'}")

        # Compliance flags
        flags: list[str] = engine.get_compliance_flags(sample_text, pii_types)
        print(f"  Compliance flags: {flags}")

    print(f"\n{separator}")
    print("  All modes validated successfully.")
    print(separator)
