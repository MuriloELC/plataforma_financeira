from __future__ import annotations

import json
from collections.abc import Iterable
from typing import Any
from uuid import UUID

from sqlalchemy import text
from sqlalchemy.engine import RowMapping
from sqlalchemy.orm import Session


def _json(value: Any) -> str:
    return json.dumps(value, ensure_ascii=True, default=str)


def _as_dict(row: RowMapping | None) -> dict[str, Any] | None:
    return dict(row) if row is not None else None


class BronzeRepository:
    def __init__(self, session: Session) -> None:
        self.session = session

    def find_raw_file_by_hash(self, sha256_hash: str) -> dict[str, Any] | None:
        row = self.session.execute(
            text(
                """
                select
                    id,
                    original_filename,
                    stored_path,
                    mime_type,
                    file_extension,
                    file_size_bytes,
                    sha256_hash,
                    source_type,
                    detected_institution,
                    uploaded_at,
                    status,
                    metadata
                from bronze.raw_files
                where sha256_hash = :sha256_hash
                """
            ),
            {"sha256_hash": sha256_hash},
        ).mappings().one_or_none()
        return _as_dict(row)

    def get_raw_file(self, raw_file_id: UUID) -> dict[str, Any] | None:
        row = self.session.execute(
            text(
                """
                select
                    id,
                    original_filename,
                    stored_path,
                    mime_type,
                    file_extension,
                    file_size_bytes,
                    sha256_hash,
                    source_type,
                    detected_institution,
                    uploaded_at,
                    status,
                    metadata
                from bronze.raw_files
                where id = :raw_file_id
                """
            ),
            {"raw_file_id": raw_file_id},
        ).mappings().one_or_none()
        return _as_dict(row)

    def list_raw_files(self, limit: int) -> list[dict[str, Any]]:
        rows = self.session.execute(
            text(
                """
                select
                    id,
                    original_filename,
                    stored_path,
                    mime_type,
                    file_extension,
                    file_size_bytes,
                    sha256_hash,
                    source_type,
                    detected_institution,
                    uploaded_at,
                    status,
                    metadata
                from bronze.raw_files
                order by uploaded_at desc, id desc
                limit :limit
                """
            ),
            {"limit": limit},
        ).mappings().all()
        return [dict(row) for row in rows]

    def create_raw_file(
        self,
        *,
        original_filename: str,
        stored_path: str,
        mime_type: str | None,
        file_extension: str,
        file_size_bytes: int,
        sha256_hash: str,
        source_type: str,
        detected_institution: str | None,
        metadata: dict[str, Any],
    ) -> dict[str, Any]:
        row = self.session.execute(
            text(
                """
                insert into bronze.raw_files (
                    original_filename,
                    stored_path,
                    mime_type,
                    file_extension,
                    file_size_bytes,
                    sha256_hash,
                    source_type,
                    detected_institution,
                    status,
                    metadata
                )
                values (
                    :original_filename,
                    :stored_path,
                    :mime_type,
                    :file_extension,
                    :file_size_bytes,
                    :sha256_hash,
                    :source_type,
                    :detected_institution,
                    :status,
                    cast(:metadata as jsonb)
                )
                returning
                    id,
                    original_filename,
                    stored_path,
                    mime_type,
                    file_extension,
                    file_size_bytes,
                    sha256_hash,
                    source_type,
                    detected_institution,
                    uploaded_at,
                    status,
                    metadata
                """
            ),
            {
                "original_filename": original_filename,
                "stored_path": stored_path,
                "mime_type": mime_type,
                "file_extension": file_extension,
                "file_size_bytes": file_size_bytes,
                "sha256_hash": sha256_hash,
                "source_type": source_type,
                "detected_institution": detected_institution,
                "status": "uploaded",
                "metadata": _json(metadata),
            },
        ).mappings().one()
        return dict(row)

    def update_raw_file_status(self, raw_file_id: UUID, status: str) -> None:
        self.session.execute(
            text(
                """
                update bronze.raw_files
                set status = :status
                where id = :raw_file_id
                """
            ),
            {"raw_file_id": raw_file_id, "status": status},
        )

    def create_import_batch(
        self,
        *,
        raw_file_id: UUID,
        source_type: str,
        status: str,
        total_records: int = 0,
        valid_records: int = 0,
        invalid_records: int = 0,
        error_message: str | None = None,
    ) -> dict[str, Any]:
        row = self.session.execute(
            text(
                """
                insert into bronze.import_batches (
                    raw_file_id,
                    source_type,
                    status,
                    started_at,
                    finished_at,
                    total_records,
                    valid_records,
                    invalid_records,
                    error_message
                )
                values (
                    :raw_file_id,
                    :source_type,
                    :status,
                    now(),
                    case
                        when :status in ('raw_extracted', 'duplicate', 'failed') then now()
                        else null
                    end,
                    :total_records,
                    :valid_records,
                    :invalid_records,
                    :error_message
                )
                returning
                    id,
                    raw_file_id,
                    source_type,
                    status,
                    parser_name,
                    started_at,
                    finished_at,
                    total_records,
                    valid_records,
                    invalid_records,
                    error_message,
                    created_at
                """
            ),
            {
                "raw_file_id": raw_file_id,
                "source_type": source_type,
                "status": status,
                "total_records": total_records,
                "valid_records": valid_records,
                "invalid_records": invalid_records,
                "error_message": error_message,
            },
        ).mappings().one()
        return dict(row)

    def get_import_batch(self, batch_id: UUID) -> dict[str, Any] | None:
        row = self.session.execute(
            text(
                """
                select
                    id,
                    raw_file_id,
                    source_type,
                    status,
                    parser_name,
                    started_at,
                    finished_at,
                    total_records,
                    valid_records,
                    invalid_records,
                    error_message,
                    created_at
                from bronze.import_batches
                where id = :batch_id
                """
            ),
            {"batch_id": batch_id},
        ).mappings().one_or_none()
        return _as_dict(row)

    def finish_import_batch(
        self,
        *,
        batch_id: UUID,
        status: str,
        total_records: int,
        valid_records: int,
        invalid_records: int,
        error_message: str | None = None,
    ) -> dict[str, Any]:
        row = self.session.execute(
            text(
                """
                update bronze.import_batches
                set
                    status = :status,
                    finished_at = now(),
                    total_records = :total_records,
                    valid_records = :valid_records,
                    invalid_records = :invalid_records,
                    error_message = :error_message
                where id = :batch_id
                returning
                    id,
                    raw_file_id,
                    source_type,
                    status,
                    parser_name,
                    started_at,
                    finished_at,
                    total_records,
                    valid_records,
                    invalid_records,
                    error_message,
                    created_at
                """
            ),
            {
                "batch_id": batch_id,
                "status": status,
                "total_records": total_records,
                "valid_records": valid_records,
                "invalid_records": invalid_records,
                "error_message": error_message,
            },
        ).mappings().one()
        return dict(row)

    def add_file_metadata(
        self,
        *,
        raw_file_id: UUID,
        key: str,
        value: dict[str, Any],
    ) -> None:
        self.session.execute(
            text(
                """
                insert into bronze.raw_file_metadata (
                    raw_file_id,
                    metadata_key,
                    metadata_value
                )
                values (
                    :raw_file_id,
                    :metadata_key,
                    cast(:metadata_value as jsonb)
                )
                """
            ),
            {
                "raw_file_id": raw_file_id,
                "metadata_key": key,
                "metadata_value": _json(value),
            },
        )

    def insert_csv_rows(self, import_batch_id: UUID, rows: Iterable[dict[str, Any]]) -> int:
        count = 0
        for row in rows:
            self.session.execute(
                text(
                    """
                    insert into bronze.raw_csv_rows (
                        import_batch_id,
                        row_number,
                        raw_text,
                        raw_payload
                    )
                    values (
                        :import_batch_id,
                        :row_number,
                        :raw_text,
                        cast(:raw_payload as jsonb)
                    )
                    """
                ),
                {
                    "import_batch_id": import_batch_id,
                    "row_number": row["row_number"],
                    "raw_text": row["raw_text"],
                    "raw_payload": _json(row["raw_payload"]),
                },
            )
            count += 1
        return count

    def insert_xlsx_rows(self, import_batch_id: UUID, rows: Iterable[dict[str, Any]]) -> int:
        count = 0
        for row in rows:
            params = {
                "import_batch_id": import_batch_id,
                "sheet_name": row["sheet_name"],
                "row_number": row["row_number"],
                "raw_text": row["raw_text"],
                "raw_payload": _json(row["raw_payload"]),
            }
            self.session.execute(
                text(
                    """
                    insert into bronze.raw_sheet_data (
                        import_batch_id,
                        sheet_name,
                        row_number,
                        raw_text,
                        raw_payload
                    )
                    values (
                        :import_batch_id,
                        :sheet_name,
                        :row_number,
                        :raw_text,
                        cast(:raw_payload as jsonb)
                    )
                    """
                ),
                params,
            )
            self.session.execute(
                text(
                    """
                    insert into bronze.raw_xlsx_rows (
                        import_batch_id,
                        sheet_name,
                        row_number,
                        raw_payload
                    )
                    values (
                        :import_batch_id,
                        :sheet_name,
                        :row_number,
                        cast(:raw_payload as jsonb)
                    )
                    """
                ),
                params,
            )
            count += 1
        return count

    def insert_pdf_pages(self, import_batch_id: UUID, pages: Iterable[dict[str, Any]]) -> int:
        count = 0
        for page in pages:
            params = {
                "import_batch_id": import_batch_id,
                "page_number": page["page_number"],
                "extracted_text": page["extracted_text"],
                "extraction_metadata": _json(page["extraction_metadata"]),
            }
            self.session.execute(
                text(
                    """
                    insert into bronze.raw_pdf_text (
                        import_batch_id,
                        page_number,
                        extracted_text,
                        extraction_metadata
                    )
                    values (
                        :import_batch_id,
                        :page_number,
                        :extracted_text,
                        cast(:extraction_metadata as jsonb)
                    )
                    """
                ),
                params,
            )
            self.session.execute(
                text(
                    """
                    insert into bronze.raw_pdf_pages (
                        import_batch_id,
                        page_number,
                        extracted_text,
                        extraction_metadata
                    )
                    values (
                        :import_batch_id,
                        :page_number,
                        :extracted_text,
                        cast(:extraction_metadata as jsonb)
                    )
                    """
                ),
                params,
            )
            count += 1
        return count

    def add_parser_error(
        self,
        *,
        import_batch_id: UUID,
        error_type: str,
        error_message: str,
        raw_reference: dict[str, Any],
        payload: dict[str, Any],
    ) -> None:
        self.session.execute(
            text(
                """
                insert into bronze.parser_errors (
                    import_batch_id,
                    raw_reference,
                    error_type,
                    error_message,
                    payload
                )
                values (
                    :import_batch_id,
                    cast(:raw_reference as jsonb),
                    :error_type,
                    :error_message,
                    cast(:payload as jsonb)
                )
                """
            ),
            {
                "import_batch_id": import_batch_id,
                "raw_reference": _json(raw_reference),
                "error_type": error_type,
                "error_message": error_message,
                "payload": _json(payload),
            },
        )

    def count_raw_records(self, import_batch_id: UUID) -> dict[str, int]:
        row = self.session.execute(
            text(
                """
                select
                    (select count(*) from bronze.raw_csv_rows where import_batch_id = :import_batch_id) as csv_rows,
                    (select count(*) from bronze.raw_sheet_data where import_batch_id = :import_batch_id) as sheet_rows,
                    (select count(*) from bronze.raw_xlsx_rows where import_batch_id = :import_batch_id) as xlsx_rows,
                    (select count(*) from bronze.raw_pdf_pages where import_batch_id = :import_batch_id) as pdf_pages,
                    (select count(*) from bronze.parser_errors where import_batch_id = :import_batch_id) as parser_errors
                """
            ),
            {"import_batch_id": import_batch_id},
        ).mappings().one()
        return {key: int(value) for key, value in row.items()}
