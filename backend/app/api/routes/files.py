from uuid import UUID
from pathlib import Path

from fastapi import APIRouter, Depends, File, Form, HTTPException, Query, UploadFile, status
from fastapi.responses import FileResponse
from sqlalchemy.orm import Session

from app.api.dependencies import get_db_session
from app.core.privacy import mask_sensitive_text
from app.schemas.ingestion import (
    FileUploadResponse,
    ImportBatchDetail,
    RawFileDetail,
    RawFileSummary,
)
from app.schemas.import_review import ImportApprovalResponse, ImportRejectRequest, ImportRejectResponse
from app.parsers.base import ParsedDocument
from app.services.bronze_ingestion import (
    BronzeIngestionError,
    BronzeIngestionService,
    UploadTooLargeError,
    UnsupportedFileTypeError,
)
from app.services.import_review import ImportReviewError, ImportReviewService

router = APIRouter(tags=["files"])


@router.post(
    "/files/upload",
    response_model=FileUploadResponse,
    status_code=status.HTTP_201_CREATED,
)
async def upload_file(
    file: UploadFile = File(...),
    source_type: str | None = Form(default=None),
    session: Session = Depends(get_db_session),
) -> FileUploadResponse:
    content = await file.read()
    service = BronzeIngestionService(session=session)

    try:
        return service.ingest_upload(
            filename=file.filename or "uploaded-file",
            content=content,
            mime_type=file.content_type,
            source_type_override=source_type,
        )
    except UnsupportedFileTypeError as exc:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(exc)) from exc
    except UploadTooLargeError as exc:
        raise HTTPException(status_code=413, detail=str(exc)) from exc
    except BronzeIngestionError as exc:
        raise HTTPException(
            status_code=422,
            detail=str(exc),
        ) from exc


@router.get("/files", response_model=list[RawFileSummary])
def list_files(
    limit: int = Query(default=50, ge=1, le=200),
    session: Session = Depends(get_db_session),
) -> list[RawFileSummary]:
    service = BronzeIngestionService(session=session)
    return service.list_raw_files(limit=limit)


@router.get("/files/{raw_file_id}", response_model=RawFileDetail)
def get_file_detail(
    raw_file_id: UUID,
    session: Session = Depends(get_db_session),
) -> RawFileDetail:
    service = BronzeIngestionService(session=session)
    raw_file = service.get_raw_file_detail(raw_file_id)
    if raw_file is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Raw file not found.")
    return raw_file


@router.get("/files/{raw_file_id}/download")
def download_file(
    raw_file_id: UUID,
    session: Session = Depends(get_db_session),
) -> FileResponse:
    service = BronzeIngestionService(session=session)
    raw_file = service.get_raw_file(raw_file_id)
    if raw_file is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Raw file not found.")
    path = Path(raw_file["stored_path"])
    if not path.exists() or not path.is_file():
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Stored file not found.")
    return FileResponse(
        path=path,
        filename=mask_sensitive_text(raw_file["original_filename"]),
        media_type=raw_file.get("mime_type") or "application/octet-stream",
    )


@router.get("/import-batches", response_model=list[ImportBatchDetail])
def list_import_batches(
    limit: int = Query(default=100, ge=1, le=500),
    session: Session = Depends(get_db_session),
) -> list[ImportBatchDetail]:
    service = BronzeIngestionService(session=session)
    return service.list_import_batches(limit=limit)


@router.get("/import-batches/{batch_id}", response_model=ImportBatchDetail)
def get_import_batch(
    batch_id: UUID,
    session: Session = Depends(get_db_session),
) -> ImportBatchDetail:
    service = BronzeIngestionService(session=session)
    batch = service.get_import_batch(batch_id=batch_id)
    if batch is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Import batch not found.")
    return batch


@router.get("/import-batches/{batch_id}/preview", response_model=ParsedDocument)
def preview_import_batch(
    batch_id: UUID,
    session: Session = Depends(get_db_session),
) -> ParsedDocument:
    service = ImportReviewService(session=session)
    try:
        return service.preview_import(batch_id=batch_id)
    except ImportReviewError as exc:
        raise HTTPException(status_code=status.HTTP_422_UNPROCESSABLE_ENTITY, detail=str(exc)) from exc


@router.post("/import-batches/{batch_id}/approve", response_model=ImportApprovalResponse)
def approve_import_batch(
    batch_id: UUID,
    session: Session = Depends(get_db_session),
) -> ImportApprovalResponse:
    service = ImportReviewService(session=session)
    try:
        return service.approve_import(batch_id=batch_id)
    except ImportReviewError as exc:
        raise HTTPException(status_code=status.HTTP_422_UNPROCESSABLE_ENTITY, detail=str(exc)) from exc


@router.post("/import-batches/{batch_id}/reject", response_model=ImportRejectResponse)
def reject_import_batch(
    batch_id: UUID,
    payload: ImportRejectRequest,
    session: Session = Depends(get_db_session),
) -> ImportRejectResponse:
    service = ImportReviewService(session=session)
    try:
        return service.reject_import(batch_id=batch_id, reason=payload.reason)
    except ImportReviewError as exc:
        raise HTTPException(status_code=status.HTTP_422_UNPROCESSABLE_ENTITY, detail=str(exc)) from exc
