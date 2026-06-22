"""Document upload + listing endpoints."""

from __future__ import annotations

import logging
import shutil
import uuid
from pathlib import Path

from fastapi import APIRouter, Depends, File, HTTPException, UploadFile
from sqlalchemy.orm import Session

from app.core.config import get_settings
from app.core.exceptions import FileTooLarge
from app.db.session import get_db
from app.models import Document
from app.schemas import DocumentOut
from app.services.ingest import ingest_document

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/documents", tags=["documents"])


@router.get("", response_model=list[DocumentOut])
def list_documents(db: Session = Depends(get_db)) -> list[Document]:
    return db.query(Document).order_by(Document.created_at.desc()).all()


@router.post("", response_model=DocumentOut, status_code=201)
def upload_document(
    file: UploadFile = File(...),
    db: Session = Depends(get_db),
) -> Document:
    settings = get_settings()
    upload_dir = Path(settings.upload_dir)
    upload_dir.mkdir(parents=True, exist_ok=True)

    safe_name = f"{uuid.uuid4().hex}_{Path(file.filename or 'upload').name}"
    target = upload_dir / safe_name

    size = 0
    max_bytes = settings.max_upload_mb * 1024 * 1024
    with target.open("wb") as out:
        while True:
            chunk = file.file.read(1024 * 1024)
            if not chunk:
                break
            size += len(chunk)
            if size > max_bytes:
                out.close()
                target.unlink(missing_ok=True)
                raise FileTooLarge(f"File exceeds {settings.max_upload_mb} MB limit")
            out.write(chunk)

    try:
        document = ingest_document(
            db,
            path=target,
            filename=file.filename or safe_name,
            content_type=file.content_type or "application/octet-stream",
        )
    except ValueError as exc:
        target.unlink(missing_ok=True)
        raise HTTPException(status_code=422, detail=str(exc)) from exc
    return document


@router.delete("/{document_id}", status_code=204)
def delete_document(document_id: int, db: Session = Depends(get_db)) -> None:
    doc = db.get(Document, document_id)
    if not doc:
        raise HTTPException(status_code=404, detail="Document not found")
    db.delete(doc)
    db.commit()


# expose for tests that want to clean up the upload directory
def _purge_uploads() -> None:  # pragma: no cover - utility for local dev
    settings = get_settings()
    shutil.rmtree(settings.upload_dir, ignore_errors=True)
