from datetime import datetime
from typing import Any
from uuid import UUID

from pydantic import BaseModel, Field


class RawFileSummary(BaseModel):
    id: UUID
    original_filename: str
    stored_path: str
    mime_type: str | None = None
    file_extension: str | None = None
    file_size_bytes: int
    sha256_hash: str
    source_type: str | None = None
    detected_institution: str | None = None
    uploaded_at: datetime
    status: str
    metadata: dict[str, Any] = Field(default_factory=dict)


class ImportBatchSummary(BaseModel):
    id: UUID
    raw_file_id: UUID
    source_type: str
    status: str
    parser_name: str | None = None
    started_at: datetime | None = None
    finished_at: datetime | None = None
    total_records: int
    valid_records: int
    invalid_records: int
    error_message: str | None = None
    created_at: datetime


class RawContentCounts(BaseModel):
    csv_rows: int = 0
    sheet_rows: int = 0
    xlsx_rows: int = 0
    pdf_pages: int = 0
    parser_errors: int = 0


class FileUploadResponse(BaseModel):
    raw_file: RawFileSummary
    import_batch: ImportBatchSummary
    duplicate: bool
    raw_counts: RawContentCounts


class ImportBatchDetail(ImportBatchSummary):
    raw_file: RawFileSummary
    raw_counts: RawContentCounts
