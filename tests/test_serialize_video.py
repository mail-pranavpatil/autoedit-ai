from dataclasses import dataclass, field
from datetime import datetime, timedelta

from api.routes.projects import serialize_video


@dataclass
class _FakeJob:
    output_path: str
    created_at: datetime


@dataclass
class _FakeVideo:
    id: str = "vid-1"
    filename: str = "clip.mp4"
    duration: float = 12.0
    width: int = 1080
    height: int = 1920
    status: str = "READY"
    progress: int = 100
    current_stage: str | None = None
    thumbnail_path: str | None = None
    error_message: str | None = None
    failed_stage: str | None = None
    retry_count: int = 0
    created_at: datetime = field(default_factory=datetime.utcnow)
    render_jobs: list = field(default_factory=list)


def test_ready_video_with_missing_output_is_flagged_unavailable(monkeypatch):
    monkeypatch.setattr("api.routes.projects.object_exists", lambda path: False)
    video = _FakeVideo(render_jobs=[_FakeJob("videos/old/final.mp4", datetime.utcnow())])

    data = serialize_video(video)

    assert data["outputUrl"] is None
    assert data["outputUnavailable"] is True


def test_ready_video_with_existing_output_is_downloadable(monkeypatch):
    monkeypatch.setattr("api.routes.projects.object_exists", lambda path: True)
    video = _FakeVideo(render_jobs=[_FakeJob("videos/new/final.mp4", datetime.utcnow())])

    data = serialize_video(video)

    assert data["outputUrl"] == f"/api/videos/{video.id}/download"
    assert data["outputUnavailable"] is False


def test_uses_the_most_recent_render_job(monkeypatch):
    seen = []
    monkeypatch.setattr("api.routes.projects.object_exists", lambda path: seen.append(path) or path == "videos/latest/final.mp4")
    older = _FakeJob("videos/old/final.mp4", datetime.utcnow() - timedelta(days=1))
    newer = _FakeJob("videos/latest/final.mp4", datetime.utcnow())
    video = _FakeVideo(render_jobs=[older, newer])

    data = serialize_video(video)

    assert seen == ["videos/latest/final.mp4"]
    assert data["outputUrl"] == f"/api/videos/{video.id}/download"


def test_non_ready_video_is_never_flagged_unavailable(monkeypatch):
    monkeypatch.setattr("api.routes.projects.object_exists", lambda path: False)
    video = _FakeVideo(status="PROCESSING", render_jobs=[])

    data = serialize_video(video)

    assert data["outputUrl"] is None
    assert data["outputUnavailable"] is False
