from __future__ import annotations

import shutil
import uuid
from datetime import datetime

from fastapi import APIRouter, Depends, File, HTTPException, UploadFile
from pydantic import BaseModel
from sqlalchemy.orm import Session, joinedload

from autoedit.auth import get_current_user
from autoedit.db import get_db
from autoedit.media import workspace_dir
from autoedit.models import Project, SourceFolder, User, Video
from autoedit.object_storage import object_exists, save_output
from autoedit.youtube import serialize_youtube

router = APIRouter(prefix="/api/projects", tags=["projects"])


class CreateProject(BaseModel):
    name: str


class RenameProject(BaseModel):
    name: str


def serialize_project(project: Project) -> dict:
    videos = project.videos or []
    counts = {
        "totalVideos": len(videos),
        "readyVideos": sum(1 for v in videos if v.status == "READY"),
        "processingVideos": sum(
            1 for v in videos if v.status not in {"READY", "FAILED", "DISCOVERED"}
        ),
        "failedVideos": sum(1 for v in videos if v.status == "FAILED"),
        "queuedVideos": sum(1 for v in videos if v.status in {"QUEUED", "DISCOVERED"}),
    }
    return {
        "id": str(project.id),
        "name": project.name,
        "createdAt": project.created_at.isoformat() if project.created_at else None,
        "updatedAt": project.updated_at.isoformat() if project.updated_at else None,
        **counts,
    }


@router.get("")
def list_projects(user: User = Depends(get_current_user), db: Session = Depends(get_db)):
    rows = (
        db.query(Project)
        .options(joinedload(Project.videos))
        .filter(Project.user_id == user.id)
        .order_by(Project.updated_at.desc())
        .all()
    )
    return [serialize_project(p) for p in rows]


@router.post("")
def create_project(body: CreateProject, user: User = Depends(get_current_user), db: Session = Depends(get_db)):
    name = body.name.strip()
    if not name:
        raise HTTPException(400, "Name is required")
    project = Project(user_id=user.id, name=name)
    db.add(project)
    db.commit()
    db.refresh(project)
    project.videos = []
    return serialize_project(project)


@router.post("/{project_id}/videos/upload")
async def upload_video(
    project_id: uuid.UUID,
    file: UploadFile = File(...),
    user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    project = db.query(Project).filter(Project.id == project_id, Project.user_id == user.id).first()
    if not project:
        raise HTTPException(404, "Project not found")
    if file.content_type and not file.content_type.startswith("video/"):
        raise HTTPException(400, "That file isn't a video")

    video = Video(project_id=project.id, filename=file.filename or "upload.mp4", status="DISCOVERED", current_stage="Imported", progress=0)
    db.add(video)
    db.flush()

    # Land the upload straight in the video's own local_path, exactly where the
    # pipeline's DOWNLOADING stage would have put a Drive-sourced file — process_video()
    # skips downloading entirely once local_path is already set (see pipeline.py).
    ws = workspace_dir(str(video.id))
    dest = ws / "source.mp4"
    with dest.open("wb") as out:
        shutil.copyfileobj(file.file, out)
    video.local_path = save_output(str(dest), f"videos/{video.id}/source.mp4")

    project.updated_at = datetime.utcnow()
    db.commit()
    return {"id": str(video.id), "filename": video.filename, "status": video.status}


@router.get("/{project_id}")
def get_project(project_id: uuid.UUID, user: User = Depends(get_current_user), db: Session = Depends(get_db)):
    project = (
        db.query(Project)
        .options(joinedload(Project.videos).joinedload(Video.youtube_upload))
        .filter(Project.id == project_id, Project.user_id == user.id)
        .first()
    )
    if not project:
        raise HTTPException(404, "Project not found")
    data = serialize_project(project)
    data["videos"] = [serialize_video(v) for v in project.videos]
    return data


def _output_ready(v: Video) -> bool:
    if v.status != "READY":
        return False
    job = max(v.render_jobs, key=lambda j: j.created_at, default=None)
    return bool(job and object_exists(job.output_path))


def serialize_video(v: Video) -> dict:
    output_ready = _output_ready(v)
    return {
        "id": str(v.id),
        "filename": v.filename,
        "duration": v.duration,
        "width": v.width,
        "height": v.height,
        "status": v.status,
        "progress": v.progress,
        "currentStage": v.current_stage,
        "thumbnailUrl": f"/api/media/thumb/{v.id}" if v.thumbnail_path else None,
        "outputUrl": f"/api/videos/{v.id}/download" if output_ready else None,
        "outputUnavailable": v.status == "READY" and not output_ready,
        "errorMessage": v.error_message,
        "failedStage": v.failed_stage,
        "retryCount": v.retry_count,
        "createdAt": v.created_at.isoformat() if v.created_at else None,
        "youtube": serialize_youtube(getattr(v, "youtube_upload", None)),
    }


@router.patch("/{project_id}")
def rename_project(
    project_id: uuid.UUID,
    body: RenameProject,
    user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    name = body.name.strip()
    if not name:
        raise HTTPException(400, "Name is required")
    project = db.query(Project).filter(Project.id == project_id, Project.user_id == user.id).first()
    if not project:
        raise HTTPException(404, "Project not found")
    project.name = name
    project.updated_at = datetime.utcnow()
    db.commit()
    db.refresh(project)
    project.videos = project.videos or []
    return serialize_project(project)


def duplicated_project_name(name: str) -> str:
    return f"{name} copy"


def duplicated_folder_fields(folder: SourceFolder) -> dict:
    return {
        "provider": folder.provider,
        "external_folder_id": folder.external_folder_id,
        "folder_name": folder.folder_name,
    }


def duplicated_video_fields(video: Video) -> dict:
    """Footage/probe fields only — never transcript, edit-plan, render, or
    YouTube state, and always reset to DISCOVERED regardless of the source
    video's status. Reprocessing reuses the cached transcript via
    source_hash, so nothing pipeline-derived needs to be duplicated."""
    return {
        "external_file_id": video.external_file_id,
        "filename": video.filename,
        "source_url": video.source_url,
        "local_path": video.local_path,
        "source_hash": video.source_hash,
        "duration": video.duration,
        "width": video.width,
        "height": video.height,
        "fps": video.fps,
        "thumbnail_path": video.thumbnail_path,
        "status": "DISCOVERED",
    }


@router.post("/{project_id}/duplicate")
def duplicate_project(project_id: uuid.UUID, user: User = Depends(get_current_user), db: Session = Depends(get_db)):
    project = (
        db.query(Project)
        .options(joinedload(Project.videos), joinedload(Project.source_folders))
        .filter(Project.id == project_id, Project.user_id == user.id)
        .first()
    )
    if not project:
        raise HTTPException(404, "Project not found")

    clone = Project(user_id=user.id, name=duplicated_project_name(project.name))
    db.add(clone)
    db.flush()

    for folder in project.source_folders:
        db.add(SourceFolder(project_id=clone.id, **duplicated_folder_fields(folder)))

    for video in project.videos:
        db.add(Video(project_id=clone.id, **duplicated_video_fields(video)))

    db.commit()
    db.refresh(clone)
    clone.videos = clone.videos or []
    return serialize_project(clone)


@router.delete("/{project_id}")
def delete_project(project_id: uuid.UUID, user: User = Depends(get_current_user), db: Session = Depends(get_db)):
    project = db.query(Project).filter(Project.id == project_id, Project.user_id == user.id).first()
    if not project:
        raise HTTPException(404, "Project not found")
    db.delete(project)
    db.commit()
    return {"ok": True}


@router.get("/{project_id}/progress")
def project_progress(project_id: uuid.UUID, user: User = Depends(get_current_user), db: Session = Depends(get_db)):
    project = (
        db.query(Project)
        .options(joinedload(Project.videos))
        .filter(Project.id == project_id, Project.user_id == user.id)
        .first()
    )
    if not project:
        raise HTTPException(404, "Project not found")
    videos = project.videos
    return {
        **serialize_project(project),
        "videos": [serialize_video(v) for v in videos],
        "active": any(v.status not in {"READY", "FAILED", "DISCOVERED"} for v in videos),
    }


@router.post("/{project_id}/process")
def process_all(project_id: uuid.UUID, user: User = Depends(get_current_user), db: Session = Depends(get_db)):
    from worker.tasks import process_video_task

    project = (
        db.query(Project)
        .options(joinedload(Project.videos))
        .filter(Project.id == project_id, Project.user_id == user.id)
        .first()
    )
    if not project:
        raise HTTPException(404, "Project not found")
    queued = 0
    for video in project.videos:
        if video.status == "READY":
            continue
        video.status = "QUEUED"
        video.current_stage = "Queued"
        video.progress = 1
        video.updated_at = datetime.utcnow()
        result = process_video_task.delay(str(video.id))
        video.celery_task_id = result.id
        queued += 1
    db.commit()
    return {"queued": queued}


@router.post("/{project_id}/retry-failed")
def retry_failed(project_id: uuid.UUID, user: User = Depends(get_current_user), db: Session = Depends(get_db)):
    from worker.tasks import process_video_task

    project = (
        db.query(Project)
        .options(joinedload(Project.videos))
        .filter(Project.id == project_id, Project.user_id == user.id)
        .first()
    )
    if not project:
        raise HTTPException(404, "Project not found")
    n = 0
    for video in project.videos:
        if video.status != "FAILED":
            continue
        video.retry_count += 1
        video.status = "QUEUED"
        video.error_message = None
        result = process_video_task.delay(str(video.id))
        video.celery_task_id = result.id
        n += 1
    db.commit()
    return {"queued": n}
