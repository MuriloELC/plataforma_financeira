from __future__ import annotations

from decimal import Decimal
from pathlib import Path
from typing import Any, Protocol
from uuid import UUID

from pydantic import BaseModel, Field

from app.core.privacy import mask_sensitive_text, mask_sensitive_value


class ParserError(Exception):
    def __init__(
        self,
        code: str,
        message: str,
        raw_reference: dict[str, Any] | None = None,
    ) -> None:
        super().__init__(message)
        self.code = code
        self.message = message
        self.raw_reference = raw_reference or {}

    def to_dict(self) -> dict[str, Any]:
        return {
            "code": self.code,
            "message": mask_sensitive_text(self.message),
            "raw_reference": mask_sensitive_value(self.raw_reference),
        }


class ParserProtocol(Protocol):
    source_type: str
    supported_extensions: set[str]

    def detect(self, file_path: Path, metadata: dict[str, Any] | None = None) -> bool: ...

    def parse(
        self,
        file_path: Path,
        import_batch_id: UUID,
        source_file_id: UUID | None = None,
    ) -> "ParsedDocument": ...


class ParserErrorDetail(BaseModel):
    code: str
    message: str
    raw_reference: dict[str, Any] = Field(default_factory=dict)


class ParsedRecord(BaseModel):
    source_type: str
    import_batch_id: UUID
    source_file_id: UUID | None = None
    confidence_score: Decimal = Decimal("1.0000")
    needs_review: bool = False
    raw_reference: dict[str, Any] = Field(default_factory=dict)
    data: dict[str, Any] = Field(default_factory=dict)


class ParsedDocument(BaseModel):
    source_type: str
    import_batch_id: UUID
    source_file_id: UUID | None = None
    confidence_score: Decimal = Decimal("1.0000")
    needs_review: bool = False
    raw_reference: dict[str, Any] = Field(default_factory=dict)
    payload: dict[str, Any] = Field(default_factory=dict)
    records: list[ParsedRecord] = Field(default_factory=list)
    errors: list[ParserErrorDetail] = Field(default_factory=list)

    def to_expected_payload(self) -> dict[str, Any]:
        return _normalize_for_expected({"source_type": self.source_type, **self.payload})


def make_record(
    *,
    source_type: str,
    import_batch_id: UUID,
    source_file_id: UUID | None,
    data: dict[str, Any],
    raw_reference: dict[str, Any],
    confidence_score: Decimal = Decimal("1.0000"),
    needs_review: bool = False,
) -> ParsedRecord:
    return ParsedRecord(
        source_type=source_type,
        import_batch_id=import_batch_id,
        source_file_id=source_file_id,
        confidence_score=confidence_score,
        needs_review=needs_review,
        raw_reference=raw_reference,
        data=data,
    )


def _normalize_for_expected(value: Any) -> Any:
    if isinstance(value, Decimal):
        return float(value)
    if isinstance(value, UUID):
        return str(value)
    if isinstance(value, dict):
        return {key: _normalize_for_expected(item) for key, item in value.items()}
    if isinstance(value, list):
        return [_normalize_for_expected(item) for item in value]
    return value
