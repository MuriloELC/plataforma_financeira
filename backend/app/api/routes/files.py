from uuid import UUID

from fastapi import APIRouter, Depends, File, HTTPException, Query, UploadFile, status
from sqlalchemy.orm import Session

from app.api.dependencies import get_db_session
from app.schemas.ingestion import (
    FileUploadResponse,
    ImportBatchDetail,
    RawFileSummary,
)
from app.services.bronze_ingestion import (
    BronzeIngestionError,
    BronzeIngestionService,
    UnsupportedFileTypeError,
)

router = APIRouter(tags=["files"])


@router.post(
    "/files/upload",
    response_model=FileUploadResponse,
    status_code=status.HTTP_201_CREATED,
)
async def upload_file(
    file: UploadFile = File(...),
    session: Session = Depends(get_db_session),
) -> FileUploadResponse:
    content = await file.read()
    service = BronzeIngestionService(session=session)

    try:
        return service.ingest_upload(
            filename=file.filename or "uploaded-file",
            content=content,
            mime_type=file.content_type,
        )
    except UnsupportedFileTypeError as exc:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(exc)) from exc
    except BronzeIngestionError as exc:
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            detail=str(exc),
        ) from exc


@router.get("/files", response_model=list[RawFileSummary])
def list_files(
    limit: int = Query(default=50, ge=1, le=200),
    session: Session = Depends(get_db_session),
) -> list[RawFileSummary]:
    service = BronzeIngestionService(session=session)
    return service.list_raw_files(limit=limit)


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
