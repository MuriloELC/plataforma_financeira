from uuid import UUID

from pydantic import BaseModel, Field


class ImportApprovalResponse(BaseModel):
    import_batch_id: UUID
    raw_file_id: UUID
    source_type: str
    parser_name: str
    status: str
    silver_counts: dict[str, int] = Field(default_factory=dict)
