from __future__ import annotations

"""Shared evidence-source policy used by retrieval and reliability scoring."""


SOURCE_RELIABILITY_PRIORS: dict[str, float] = {
    "preprocessed_id": 1.0,
    "ahd_heldout_safe_corpus": 0.95,
    "preprocessed_source_row": 0.90,
    "supplemental_dataset_validated": 0.80,
    "unknown": 0.65,
    "": 0.65,
    "mention_evidence": 0.55,
}


def source_reliability_prior(source_quality: str) -> float:
    """Return one consistent prior without treating unknown sources as trusted."""
    key = str(source_quality or "unknown")
    return SOURCE_RELIABILITY_PRIORS.get(key, SOURCE_RELIABILITY_PRIORS["unknown"])
