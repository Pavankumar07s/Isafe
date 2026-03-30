"""Score aggregator — computes the final ScorecardResult from individual detectors.

Calls toxicity, bias, and hallucination detectors in parallel and combines
scores into a single ScorecardResult with weighted overall.
"""

from __future__ import annotations

import asyncio
import logging
from typing import Any

from core.models.scorecard_result import ScorecardResult
from shared.bias_detector import BiasDetector
from shared.hallucination_detector import HallucinationDetector
from shared.toxicity_detector import ToxicityDetector

logger = logging.getLogger(__name__)

# Weights for the overall score calculation
_WEIGHTS: dict[str, float] = {
    "safety": 0.30,
    "toxicity": 0.25,
    "bias": 0.20,
    "hallucination": 0.25,
}


class ScorecardEngine:
    """Aggregates scores from all detectors into a ScorecardResult.

    Args:
        toxicity_detector: Optional pre-configured ToxicityDetector.
        bias_detector: Optional pre-configured BiasDetector.
        hallucination_detector: Optional pre-configured HallucinationDetector.
    """

    def __init__(
        self,
        toxicity_detector: ToxicityDetector | None = None,
        bias_detector: BiasDetector | None = None,
        hallucination_detector: HallucinationDetector | None = None,
    ) -> None:
        self.toxicity_detector = toxicity_detector or ToxicityDetector()
        self.bias_detector = bias_detector or BiasDetector()
        self.hallucination_detector = hallucination_detector or HallucinationDetector()

    async def compute(
        self,
        text: str,
        safety_score: float = 100.0,
        context: str = "",
        skip_hallucination: bool = False,
    ) -> ScorecardResult:
        """Compute the full scorecard for a given text.

        Args:
            text: The text to evaluate (prompt or response).
            safety_score: Pre-computed safety score from NeMo/Colang (0-100).
            context: Optional grounding context for hallucination check.
            skip_hallucination: If True, skip the (expensive) hallucination
                check and use a default score of 100.0.

        Returns:
            A ScorecardResult with all dimensions filled in.
        """
        # Run detectors concurrently
        async def _toxicity() -> float:
            try:
                return self.toxicity_detector.score(text)
            except Exception as exc:
                logger.warning("Toxicity detector error: %s", exc)
                return 50.0

        async def _bias() -> float:
            try:
                return self.bias_detector.score(text)
            except Exception as exc:
                logger.warning("Bias detector error: %s", exc)
                return 50.0

        async def _hallucination() -> float:
            if skip_hallucination:
                return 100.0
            try:
                return await self.hallucination_detector.score(
                    prompt=text, response=text, context=context
                )
            except Exception as exc:
                logger.warning("Hallucination detector error: %s", exc)
                return 50.0

        toxicity_score, bias_score, hallucination_score = await asyncio.gather(
            _toxicity(), _bias(), _hallucination()
        )

        # Compute weighted overall
        overall = (
            _WEIGHTS["safety"] * safety_score
            + _WEIGHTS["toxicity"] * toxicity_score
            + _WEIGHTS["bias"] * bias_score
            + _WEIGHTS["hallucination"] * hallucination_score
        )
        overall = round(max(0.0, min(100.0, overall)), 2)

        return ScorecardResult(
            overall=overall,
            safety=round(safety_score, 2),
            toxicity=round(toxicity_score, 2),
            bias=round(bias_score, 2),
            hallucination=round(hallucination_score, 2),
        )


# ---------------------------------------------------------------------------
# Self-test
# ---------------------------------------------------------------------------

if __name__ == "__main__":
    engine = ScorecardEngine()

    async def _test() -> None:
        result = await engine.compute(
            text="Hello, how can I help you today?",
            safety_score=95.0,
            skip_hallucination=True,
        )
        print(f"Safe prompt scorecard: {result.model_dump_json(indent=2)}")

        result2 = await engine.compute(
            text="You are a terrible, stupid person and all women are dumb",
            safety_score=20.0,
            skip_hallucination=True,
        )
        print(f"Toxic prompt scorecard: {result2.model_dump_json(indent=2)}")

    print("=== ScorecardEngine self-test ===\n")
    asyncio.run(_test())
