from __future__ import annotations

import uuid
from datetime import datetime

from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel
from sqlalchemy.orm import Session

from autoedit.auth import get_current_user, get_valid_access_token
from autoedit.db import get_db
from autoedit.drive import list_folders, list_videos
from autoedit.models import Project, SourceFolder, User, Video

router = APIRouter(prefix="/api/drive", tags=["drive"])


class ImportBody(BaseModel):
    projectId: uuid.UUID
    folderId: str
    folderName: str
    fileIds: list[str]


@router.get("/folders")
def folders(parentId: str | None = None, user: User = Depends(get_current_user), db: Session = Depends(get_db)):
    token = get_valid_access_token(db, user)
    return list_folders(token, parentId)


@router.get("/folders/{folder_id}/videos")
def folder_videos(folder_id: str, user: User = Depends(get_current_user), db: Session = Depends(get_db)):
    token = get_valid_access_token(db, user)
    return list_videos(token, folder_id)


@router.post("/import")
def import_videos(body: ImportBody, user: User = Depends(get_current_user), db: Session = Depends(get_db)):
    project = db.query(Project).filter(Project.id == body.projectId, Project.user_id == user.id).first()
    if not project:
        raise HTTPException(404, "Project not found")
    token = get_valid_access_token(db, user)
    remote = {v["id"]: v for v in list_videos(token, body.folderId)}
    folder = (
        db.query(SourceFolder)
        .filter(SourceFolder.project_id == project.id, SourceFolder.external_folder_id == body.folderId)
        .first()
    )
    if not folder:
        folder = SourceFolder(
            project_id=project.id,
            provider="google",
            external_folder_id=body.folderId,
            folder_name=body.folderName,
        )
        db.add(folder)
        db.flush()

    created = []
    for file_id in body.fileIds:
        meta = remote.get(file_id)
        if not meta:
            continue
        existing = (
            db.query(Video)
            .filter(Video.project_id == project.id, Video.external_file_id == file_id)
            .first()
        )
        if existing:
            created.append({"id": str(existing.id), "filename": existing.filename, "status": existing.status})
            continue
        video = Video(
            project_id=project.id,
            external_file_id=file_id,
            filename=meta["name"],
            status="DISCOVERED",
            current_stage="Imported",
            progress=0,
        )
        db.add(video)
        db.flush()
        created.append({"id": str(video.id), "filename": video.filename, "status": video.status})
    project.updated_at = datetime.utcnow()
    db.commit()
    return {"imported": len(created), "videos": created}
