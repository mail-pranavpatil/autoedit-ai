from __future__ import annotations

import uuid
from datetime import datetime

from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel
from sqlalchemy.orm import Session, joinedload

from autoedit.auth import get_current_user
from autoedit.db import get_db
from autoedit.models import Project, User, Video

router = APIRouter(prefix="/api/projects", tags=["projects"])


class CreateProject(BaseModel):
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


@router.get("/{project_id}")
def get_project(project_id: uuid.UUID, user: User = Depends(get_current_user), db: Session = Depends(get_db)):
    project = (
        db.query(Project)
        .options(joinedload(Project.videos))
        .filter(Project.id == project_id, Project.user_id == user.id)
        .first()
    )
    if not project:
        raise HTTPException(404, "Project not found")
    data = serialize_project(project)
    data["videos"] = [serialize_video(v) for v in project.videos]
    return data


def serialize_video(v: Video) -> dict:
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
        "outputUrl": f"/api/videos/{v.id}/download" if v.status == "READY" else None,
        "errorMessage": v.error_message,
        "failedStage": v.failed_stage,
        "retryCount": v.retry_count,
        "createdAt": v.created_at.isoformat() if v.created_at else None,
    }


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
        process_video_task.delay(str(video.id))
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
        process_video_task.delay(str(video.id))
        n += 1
    db.commit()
    return {"queued": n}
