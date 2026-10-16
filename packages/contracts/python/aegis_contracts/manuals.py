"""Evidence contracts. Document text is data and never an authorization policy."""

from typing import Annotated, Literal

from pydantic import Field, model_validator

from aegis_contracts.models import Contract, FiniteFloat

Digest = Annotated[str, Field(pattern=r"^[0-9a-f]{64}$")]
Identifier = Annotated[str, Field(pattern=r"^[A-Za-z0-9_.-]{1,80}$")]


class Revision(Contract):
    revision: Identifier
    supersedes: Identifier | None = None
    authority: Literal["synthetic_fixture", "unverified_provider"]


class Citation(Contract):
    document_id: Identifier
    revision: Identifier
    source_sha256: Digest
    page_sha256: Digest
    page: Annotated[int, Field(ge=1, le=10000)]
    quote: Annotated[str, Field(min_length=1, max_length=2000)]
    table_row: Annotated[int, Field(ge=1)] | None = None


class ExtractionConfidence(Contract):
    provider_confidence: Annotated[FiniteFloat, Field(ge=0, le=1)] | None = None
    derived_method: Literal["exact_table_row", "unmapped", "exact_text_match"]
    # These methods do not claim provider/OCR or probabilistic confidence.


class ManualPage(Contract):
    document_id: Identifier
    revision: Identifier
    page: Annotated[int, Field(ge=1, le=10000)]
    source_sha256: Digest
    page_sha256: Digest
    text: Annotated[str, Field(max_length=100000)]
    medium: Literal["born_digital", "ocr_required"]
    authority: Literal["synthetic_fixture", "unverified_provider"]
    confidence: ExtractionConfidence


class Equipment(Contract):
    equipment_id: Identifier
    description: Annotated[str, Field(max_length=500)]


class OEMConstraint(Contract):
    equipment_id: Identifier
    quantity: Literal["temperature", "pressure", "flow", "load"]
    unit: Literal["degC", "kPa", "kg/s", "fraction"]
    minimum: FiniteFloat
    maximum: FiniteFloat
    citation: Citation

    @model_validator(mode="after")
    def validate_range(self) -> "OEMConstraint":
        units = {"temperature": "degC", "pressure": "kPa", "flow": "kg/s", "load": "fraction"}
        if self.unit != units[self.quantity] or self.minimum > self.maximum:
            raise ValueError("Inconsistent units or range")
        return self


class AlarmCode(Contract):
    code: Identifier
    meaning: Annotated[str, Field(min_length=1, max_length=500)]
    citation: Citation


class Procedure(Contract):
    procedure_id: Identifier
    description: Annotated[str, Field(min_length=1, max_length=2000)]
    citation: Citation
    executable: Literal[False] = False


class SafetyInterlock(Contract):
    interlock_id: Identifier
    description: Annotated[str, Field(min_length=1, max_length=1000)]
    citation: Citation
    overridable: Literal[False] = False


class AmbiguityFlag(Contract):
    reason: Literal["contradiction", "missing_evidence", "untrusted_revision", "ocr_required"]
    citations: Annotated[list[Citation], Field(max_length=10)]


class ManualDocument(Contract):
    document_id: Identifier
    source_sha256: Digest
    title: Annotated[str, Field(min_length=1, max_length=200)]
    revision: Revision
    page_count: Annotated[int, Field(ge=1, le=10000)]


class ManualRecords(Contract):
    document: ManualDocument
    equipment: Annotated[list[Equipment], Field(max_length=1000)]
    constraints: Annotated[list[OEMConstraint], Field(max_length=10000)]
    alarms: Annotated[list[AlarmCode], Field(max_length=10000)]
    procedures: Annotated[list[Procedure], Field(max_length=10000)]
    interlocks: Annotated[list[SafetyInterlock], Field(max_length=10000)]
    ambiguities: Annotated[list[AmbiguityFlag], Field(max_length=100)]
    confidence: ExtractionConfidence


class ManualDecision(Contract):
    status: Literal["simulator_evidence_only", "no_action"]
    operational_write_allowed: Literal[False] = False
    flags: Annotated[list[AmbiguityFlag], Field(max_length=100)]
    checked_constraints: Annotated[int, Field(ge=0)]


class EvidenceHit(Contract):
    citation: Citation
    score: Annotated[FiniteFloat, Field(ge=-1.00001, le=1.00001)]
    score_method: Literal["hashed_lexical_cosine"] = "hashed_lexical_cosine"
    untrusted_text: Annotated[str, Field(max_length=100000)]


class ManualEvidence(Contract):
    source: Literal["synthetic_fixture"]
    corpus_sha256: Digest
    pages: Annotated[int, Field(ge=1)]
    hits: Annotated[list[EvidenceHit], Field(max_length=10)]
    decision: ManualDecision
    evolus_live: Literal[False] = False
    pinecone_live: Literal[False] = False
