"""ScorecardResult Pydantic model for EthicsGuard v0.4.

Holds the numeric 0-100 scores produced by the scoring pipeline.
"""

from __future__ import annotations

from pydantic import BaseModel, Field


class ScorecardResult(BaseModel):
    """Normalised scorecard returned by the scoring pipeline.

    Every dimension is a float in the range [0.0, 100.0] where higher = safer/better:
    - **safety / overall**: higher is safer
    - **toxicity**: higher means less toxic (100 = non-toxic)
    - **bias**: higher means less biased (100 = unbiased)
    - **hallucination**: higher means more grounded (100 = no hallucination)
    """

    model_config = {
        "json_schema_extra": {
            "examples": [
                {
                    "overall": 87.5,
                    "safety": 92.0,
                    "toxicity": 3.4,
                    "bias": 6.1,
                    "hallucination": 10.8,
                }
            ]
        },
    }

    overall: float = Field(
        ...,
        ge=0.0,
        le=100.0,
        description="Composite safety score (0-100). Higher is safer.",
        examples=[87.5],
    )
    safety: float = Field(
        ...,
        ge=0.0,
        le=100.0,
        description="Safety sub-score (0-100). Higher is safer.",
        examples=[92.0],
    )
    toxicity: float = Field(
        ...,
        ge=0.0,
        le=100.0,
        description="Toxicity sub-score (0-100). Higher means less toxic (100 = non-toxic).",
        examples=[3.4],
    )
    bias: float = Field(
        ...,
        ge=0.0,
        le=100.0,
        description="Bias sub-score (0-100). Higher means less biased (100 = unbiased).",
        examples=[6.1],
    )
    hallucination: float = Field(
        ...,
        ge=0.0,
        le=100.0,
        description="Hallucination sub-score (0-100). Higher means more grounded (100 = no hallucination).",
        examples=[10.8],
    )


# ------------------------------------------------------------------
# Quick smoke-test
# ------------------------------------------------------------------
if __name__ == "__main__":
    card = ScorecardResult(
        overall=87.5,
        safety=92.0,
        toxicity=3.4,
        bias=6.1,
        hallucination=10.8,
    )
    print("=== ScorecardResult sample ===")
    print(card.model_dump_json(indent=2))
