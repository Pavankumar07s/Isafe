"""Hallucination detection using SelfCheckGPT-style stochastic consistency.

Generates multiple alternative responses for the same prompt, then measures
semantic consistency.  High variance across samples suggests hallucination.

Score: 0-100 where **100 = no hallucination detected** (fully grounded).
"""

from __future__ import annotations

import asyncio
import logging
import os
import re
from typing import Any

logger = logging.getLogger(__name__)

# Number of alternative responses to generate for consistency check
_NUM_SAMPLES: int = 3


def _sentence_tokenize(text: str) -> list[str]:
    """Simple sentence splitter (avoids nltk dependency)."""
    sentences = re.split(r"(?<=[.!?])\s+", text.strip())
    return [s.strip() for s in sentences if s.strip()]


def _jaccard_similarity(set_a: set[str], set_b: set[str]) -> float:
    """Compute Jaccard similarity between two sets of words."""
    if not set_a and not set_b:
        return 1.0
    intersection = set_a & set_b
    union = set_a | set_b
    return len(intersection) / len(union) if union else 1.0


def _word_set(text: str) -> set[str]:
    """Extract a set of lowercased words from text."""
    return set(re.findall(r"\b\w+\b", text.lower()))


class HallucinationDetector:
    """Detects hallucination via SelfCheckGPT-style stochastic consistency.

    For each (prompt, response) pair, generates ``_NUM_SAMPLES`` alternative
    responses using the provided LLM, then measures how consistent the
    original response is with the alternatives.

    Args:
        llm: Any LangChain-compatible LLM (must have ``ainvoke`` or
            ``agenerate`` method), or ``None`` for keyword-only fallback.
    """

    def __init__(self, llm: Any = None) -> None:
        self._llm = llm

    async def score(
        self, prompt: str, response: str, context: str = ""
    ) -> float:
        """Score a response for hallucination risk.

        Args:
            prompt: The original user prompt.
            response: The LLM response to evaluate.
            context: Optional grounding context (e.g. RAG documents).

        Returns:
            Float 0-100 where 100 = no hallucination detected.
            Falls back to 50.0 if the LLM is unavailable.
        """
        try:
            # Factual grounding check (if context provided)
            grounding_score = self._grounding_check(response, context) if context else None

            # Stochastic consistency check
            consistency_score = await self._consistency_check(prompt, response)

            if grounding_score is not None and consistency_score is not None:
                # Weighted: 60% grounding, 40% consistency
                return round(0.6 * grounding_score + 0.4 * consistency_score, 2)
            elif grounding_score is not None:
                return round(grounding_score, 2)
            elif consistency_score is not None:
                return round(consistency_score, 2)
            else:
                return 50.0
        except Exception as exc:
            logger.warning("Hallucination detection failed: %s", exc)
            return 50.0

    def _grounding_check(self, response: str, context: str) -> float:
        """Check factual grounding: does the response align with provided context?

        Uses sentence-level word overlap as a proxy for factual consistency.
        Returns 0-100 where 100 = fully grounded.
        """
        if not context:
            return 100.0

        context_words = _word_set(context)
        response_sentences = _sentence_tokenize(response)

        if not response_sentences:
            return 100.0

        sentence_scores: list[float] = []
        for sentence in response_sentences:
            sent_words = _word_set(sentence)
            # Filter out stop words for better signal
            overlap = _jaccard_similarity(sent_words, context_words)
            sentence_scores.append(overlap)

        avg_overlap = sum(sentence_scores) / len(sentence_scores)
        # Scale to 0-100: 0.3+ overlap is considered well-grounded
        return min(100.0, avg_overlap / 0.3 * 100.0)

    async def _consistency_check(self, prompt: str, response: str) -> float | None:
        """SelfCheckGPT: generate alternative responses and measure consistency.

        Returns 0-100 where 100 = highly consistent (low hallucination risk).
        Returns None if LLM is unavailable.
        """
        if self._llm is None:
            return None

        try:
            # Generate alternative responses
            alternatives = await self._generate_alternatives(prompt)
            if not alternatives:
                return None

            response_words = _word_set(response)
            similarities: list[float] = []

            for alt in alternatives:
                alt_words = _word_set(alt)
                sim = _jaccard_similarity(response_words, alt_words)
                similarities.append(sim)

            avg_similarity = sum(similarities) / len(similarities)
            # High similarity = low hallucination risk
            return min(100.0, avg_similarity * 100.0 / 0.5)  # 0.5 overlap = 100%
        except Exception as exc:
            logger.warning("Consistency check failed: %s", exc)
            return None

    async def _generate_alternatives(self, prompt: str) -> list[str]:
        """Generate _NUM_SAMPLES alternative responses using the LLM."""
        alternatives: list[str] = []

        async def _invoke_once() -> str | None:
            try:
                if hasattr(self._llm, "ainvoke"):
                    result = await self._llm.ainvoke(prompt)
                    return str(result.content if hasattr(result, "content") else result)
                elif hasattr(self._llm, "invoke"):
                    result = self._llm.invoke(prompt)
                    return str(result.content if hasattr(result, "content") else result)
            except Exception as exc:
                logger.debug("Alternative generation failed: %s", exc)
            return None

        tasks = [_invoke_once() for _ in range(_NUM_SAMPLES)]
        results = await asyncio.gather(*tasks)
        for r in results:
            if r is not None:
                alternatives.append(r)

        return alternatives


# ---------------------------------------------------------------------------
# Self-test
# ---------------------------------------------------------------------------

if __name__ == "__main__":
    detector = HallucinationDetector(llm=None)

    async def _test() -> None:
        # Without LLM — only grounding check works
        score1 = await detector.score(
            prompt="What is the capital of France?",
            response="The capital of France is Paris.",
            context="France is a country in Europe. Its capital is Paris.",
        )
        print(f"Grounded response score: {score1}")

        score2 = await detector.score(
            prompt="What is the capital of France?",
            response="The capital of France is Berlin, which has the Eiffel Tower.",
            context="France is a country in Europe. Its capital is Paris.",
        )
        print(f"Hallucinated response score: {score2}")

        score3 = await detector.score(
            prompt="Tell me about cats",
            response="Cats are domesticated animals.",
        )
        print(f"No-context score (fallback): {score3}")

    print("=== HallucinationDetector self-test ===\n")
    asyncio.run(_test())
