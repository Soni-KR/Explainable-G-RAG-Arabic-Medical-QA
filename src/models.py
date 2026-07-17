from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any


# Fixed Neo4j schema contract used by Steps 8-12.
MEDICAL_ENTITY_LABEL = "MedicalEntity"
EVIDENCE_MENTION_LABEL = "EvidenceMention"
QA_RECORD_LABEL = "QARecord"

MENTIONED_IN_REL = "MENTIONED_IN"
EVIDENCE_FROM_REL = "EVIDENCE_FROM"
MEDICAL_RELATION_REL = "MEDICAL_RELATION"


ALLOWED_ENTITY_TYPES = frozenset(
    {
        "DiseaseCondition",
        "Symptom",
        "Treatment",
        "Test",
    }
)

ALLOWED_MATCH_TYPES = frozenset(
    {
        "exact",
        "alias",
        "normalized",
        "synonym",
        "semantic_candidate",
        "medical_variant",
    }
)


@dataclass(frozen=True)
class ExtractedMedicalPhrase:
    surface_form: str
    normalized_form: str
    entity_type: str
    source: str
    confidence: float


@dataclass(frozen=True)
class LinkedMedicalEntity:
    surface_form: str
    normalized_form: str
    extracted_entity_type: str
    linked_entity_id: str = ""
    linked_canonical_name: str = ""
    linked_entity_type: str = ""
    match_type: str = "none"
    match_score: float = 0.0
    status: str = "unresolved"
    warnings: list[str] = field(default_factory=list)
    candidates: list[dict[str, Any]] = field(default_factory=list)


@dataclass(frozen=True)
class QueryEntityLinkingResult:
    original_query: str
    corrected_query: str
    reformulated_query: str
    query_class: str
    complexity: str
    linked_entities: list[LinkedMedicalEntity] = field(default_factory=list)
    unresolved_phrases: list[str] = field(default_factory=list)
    warnings: list[str] = field(default_factory=list)


@dataclass(frozen=True)
class UnifiedQueryAnalysisResult:
    original_query: str
    normalized_query: str
    corrected_query: str
    reformulated_query: str
    query_class: str
    complexity: str
    primary_intent: str
    secondary_intents: list[str] = field(default_factory=list)
    medical_phrases: list[ExtractedMedicalPhrase] = field(default_factory=list)
    confidence: float = 0.0
    preferred_relation_types: list[str] = field(default_factory=list)
    warnings: list[str] = field(default_factory=list)
    model: str = ""
    prompt_version: str = ""


@dataclass(frozen=True)
class RetrievalPlanResult:
    original_query: str
    corrected_query: str
    reformulated_query: str
    query_class: str
    complexity: str
    primary_intent: str
    use_vector_search: bool
    use_graph_search: bool
    hop_depth: int
    entity_top_k: int
    evidence_top_k: int
    qa_top_k: int
    preferred_relation_types: list[str] = field(default_factory=list)
    primary_entity_ids: list[str] = field(default_factory=list)
    low_specificity_entity_ids: list[str] = field(default_factory=list)
    unresolved_phrases: list[str] = field(default_factory=list)
    warnings: list[str] = field(default_factory=list)


@dataclass(frozen=True)
class VectorSearchResult:
    result_id: str
    document_type: str
    score: float
    entity_id: str = ""
    qa_id: str = ""
    title: str = ""
    text: str = ""
    metadata: dict[str, Any] = field(default_factory=dict)


@dataclass(frozen=True)
class RetrievedMedicalRelation:
    relation_id: str
    source_relation_id: str
    source_entity_id: str
    source_name: str
    target_entity_id: str
    target_name: str
    relation_type: str
    confidence: float
    qa_id: str = ""
    evidence: str = ""
    direction: str = ""
    seed_entity_id: str = ""
    seed_score: float = 0.0
    semantic_support: float = 0.0
    evidence_relevance: float = 0.0
    hybrid_score: float = 0.0
    metadata: dict[str, Any] = field(default_factory=dict)


@dataclass(frozen=True)
class RetrievedEvidence:
    evidence_id: str
    source_id: str
    qa_id: str
    text: str
    question: str = ""
    answer: str = ""
    category: str = ""
    source_quality: str = ""
    score: float = 0.0
    relation_ids: list[str] = field(default_factory=list)
    metadata: dict[str, Any] = field(default_factory=dict)


@dataclass(frozen=True)
class HybridRetrievalBundle:
    query: str
    normalized_query: str
    reformulated_query: str
    plan: RetrievalPlanResult
    vector_results: list[VectorSearchResult] = field(default_factory=list)
    relations: list[RetrievedMedicalRelation] = field(default_factory=list)
    evidence: list[RetrievedEvidence] = field(default_factory=list)
    warnings: list[str] = field(default_factory=list)


@dataclass(frozen=True)
class RerankedSubgraph:
    query: str
    primary_intent: str = ""
    relations: list[RetrievedMedicalRelation] = field(default_factory=list)
    evidence: list[RetrievedEvidence] = field(default_factory=list)
    warnings: list[str] = field(default_factory=list)


@dataclass(frozen=True)
class EvidenceContextBundle:
    query: str
    reformulated_query: str
    primary_intent: str = ""
    graph_facts: list[dict[str, Any]] = field(default_factory=list)
    evidence_items: list[dict[str, Any]] = field(default_factory=list)
    allowed_evidence_ids: list[str] = field(default_factory=list)
    allowed_qa_ids: list[str] = field(default_factory=list)
    warnings: list[str] = field(default_factory=list)


@dataclass(frozen=True)
class AnswerClaim:
    claim: str
    citations: list[str] = field(default_factory=list)
    source_qa_ids: list[str] = field(default_factory=list)


@dataclass(frozen=True)
class GeneratedAnswer:
    query: str
    answer: str
    claims: list[AnswerClaim] = field(default_factory=list)
    used_relations: list[str] = field(default_factory=list)
    limitations: list[str] = field(default_factory=list)
    model: str = ""
    prompt_version: str = ""
    generation_status: str = "generated"
    fallback_type: str = ""
    fallback_reason: str = ""
    attempt_count: int = 0
    warnings: list[str] = field(default_factory=list)


@dataclass(frozen=True)
class ClaimVerification:
    claim: AnswerClaim
    status: str
    support_score: float
    question_relevance: float = 0.0
    valid_citations: list[str] = field(default_factory=list)
    valid_qa_ids: list[str] = field(default_factory=list)
    supporting_relation_ids: list[str] = field(default_factory=list)
    reason: str = ""


@dataclass(frozen=True)
class MitigatedAnswer:
    answer: str
    answerability: str
    kept_claims: list[AnswerClaim] = field(default_factory=list)
    removed_claims: list[str] = field(default_factory=list)
    limitations: list[str] = field(default_factory=list)


@dataclass(frozen=True)
class ReliabilityResult:
    score: float
    label: str
    claim_support_rate: float
    hallucination_rate: float
    evidence_coverage: float
    relation_confidence: float
    source_reliability: float
    calibrated: bool = False
    components: dict[str, float] = field(default_factory=dict)


@dataclass(frozen=True)
class ExplainableMedicalAnswer:
    query: str
    answer: str
    answerability: str
    reliability: ReliabilityResult
    retrieved_entities: list[dict[str, Any]] = field(default_factory=list)
    supporting_relations: list[dict[str, Any]] = field(default_factory=list)
    evidence: list[dict[str, Any]] = field(default_factory=list)
    removed_claims: list[str] = field(default_factory=list)
    limitations: list[str] = field(default_factory=list)
    warnings: list[str] = field(default_factory=list)
    metrics: dict[str, Any] = field(default_factory=dict)
    timings_ms: dict[str, float] = field(default_factory=dict)
