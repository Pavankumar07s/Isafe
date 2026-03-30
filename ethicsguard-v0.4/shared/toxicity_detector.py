"""Toxicity detection using the detoxify library.

Primary detector: ``detoxify`` (multilingual, 6 toxicity categories).
Secondary (optional): Perspective API when ``PERSPECTIVE_API_KEY`` is set.

All scores are normalised to the 0-100 range where **100 = non-toxic** (safe).
"""

from __future__ import annotations

import logging
import os
from typing import Any

logger = logging.getLogger(__name__)

# ---------------------------------------------------------------------------
# Lazy imports — heavy ML models are only loaded on first use
# ---------------------------------------------------------------------------

_detoxify_model: Any = None


def _get_detoxify_model() -> Any:
    """Return (and cache) the default ``detoxify`` model."""
    global _detoxify_model
    if _detoxify_model is None:
        try:
            from detoxify import Detoxify
            _detoxify_model = Detoxify("original")
            logger.info("detoxify model loaded successfully")
        except Exception as exc:
            logger.warning("Failed to load detoxify model: %s", exc)
            _detoxify_model = None
    return _detoxify_model


# ---------------------------------------------------------------------------
# ToxicityDetector
# ---------------------------------------------------------------------------


class ToxicityDetector:
    """Scores text for toxicity using the *detoxify* library.

    Attributes:
        use_perspective: Whether the Perspective API secondary detector is
            enabled (requires ``PERSPECTIVE_API_KEY`` env var).
    """

    CATEGORY_NAMES: list[str] = [
        "toxicity",
        "severe_toxicity",
        "obscene",
        "threat",
        "insult",
        "identity_attack",
    ]

    def __init__(self) -> None:
        self._perspective_key: str | None = os.getenv("PERSPECTIVE_API_KEY")
        self.use_perspective: bool = bool(self._perspective_key)

    # ----- public API -------------------------------------------------------

    def score(self, text: str) -> float:
        """Return an overall toxicity score in [0, 100].

        100 = completely non-toxic, 0 = maximally toxic.
        Falls back to 50.0 if the model cannot be loaded.
        """
        cats = self.categories(text)
        if not cats:
            return 50.0
        max_toxicity = max(cats.values())
        # Invert: higher = safer
        return round(max(0.0, min(100.0, (1.0 - max_toxicity) * 100.0)), 2)

    def categories(self, text: str) -> dict[str, float]:
        """Return per-category raw toxicity scores in [0.0, 1.0].

        Keys match the six ``detoxify`` output categories.  Higher values
        indicate *more* toxic content in that category.

        Returns an empty dict if the model is unavailable.
        """
        model = _get_detoxify_model()
        if model is None:
            return {}
        try:
            raw: dict[str, float] = model.predict(text)
            return {k: round(float(v), 4) for k, v in raw.items()}
        except Exception as exc:
            logger.warning("detoxify prediction failed: %s", exc)
            return {}

    def score_with_perspective(self, text: str) -> float | None:
        """Return a toxicity score from the Perspective API, if configured.

        Returns ``None`` when the API key is not set or the call fails.
        Score is in [0, 100] where 100 = non-toxic.
        """
        if not self._perspective_key:
            return None
        try:
            import httpx

            resp = httpx.post(
                f"https://commentanalyzer.googleapis.com/v1alpha1/comments:analyze"
                f"?key={self._perspective_key}",
                json={
                    "comment": {"text": text},
                    "languages": ["en"],
                    "requestedAttributes": {"TOXICITY": {}},
                },
                timeout=10.0,
            )
            resp.raise_for_status()
            tox_val = resp.json()["attributeScores"]["TOXICITY"]["summaryScore"]["value"]
            return round((1.0 - tox_val) * 100.0, 2)
        except Exception as exc:
            logger.warning("Perspective API call failed: %s", exc)
            return None


# ---------------------------------------------------------------------------
# Self-test
# ---------------------------------------------------------------------------

if __name__ == "__main__":
    detector = ToxicityDetector()

    samples = [
        "Hello, how can I help you today?",
        "You are a terrible person and I hate you",
        "The capital of France is Paris",
    ]

    print("=== ToxicityDetector self-test ===\n")
    for text in samples:
        overall = detector.score(text)
        cats = detector.categories(text)
        print(f"Text: {text[:60]}...")
        print(f"  Overall score (100=safe): {overall}")
        if cats:
            for cat, val in cats.items():
                print(f"  {cat}: {val:.4f}")
        else:
            print("  (detoxify model not available — scores are fallback)")
        print()
