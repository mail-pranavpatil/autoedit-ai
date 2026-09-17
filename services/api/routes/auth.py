from __future__ import annotations

from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session

from autoedit.auth import get_current_user
from autoedit.db import get_db
from autoedit.models import DriveConnection, User

router = APIRouter(prefix="/api/auth", tags=["auth"])


@router.get("/me")
def me(user: User = Depends(get_current_user), db: Session = Depends(get_db)):
    conn = db.query(DriveConnection).filter(DriveConnection.user_id == user.id).first()
    return {
        "id": str(user.id),
        "email": user.email,
        "name": user.name,
        "pictureUrl": user.picture_url,
        "driveConnected": bool(conn),
        "onboardingCompleted": bool(user.onboarding_completed),
        "editingExperience": user.editing_experience,
        "creationReason": user.creation_reason,
    }
