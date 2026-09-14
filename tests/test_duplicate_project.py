from dataclasses import dataclass

from api.routes.projects import duplicated_folder_fields, duplicated_project_name, duplicated_video_fields


@dataclass
class _FakeVideo:
    external_file_id: str = "drive-123"
    filename: str = "clip.mp4"
    source_url: str = "https://drive/clip.mp4"
    local_path: str = "/tmp/clip.mp4"
    source_hash: str = "abc123"
    duration: float = 12.0
    width: int = 1080
    height: int = 1920
    fps: float = 30.0
    thumbnail_path: str = "thumbs/clip.jpg"
    status: str = "READY"
    progress: int = 100
    current_stage: str = "READY"
    error_message: str | None = "boom"
    failed_stage: str | None = "RENDERING"
    retry_count: int = 2
    celery_task_id: str | None = "task-1"


@dataclass
class _FakeFolder:
    provider: str = "google"
    external_folder_id: str = "folder-1"
    folder_name: str = "August clips"


def test_duplicated_project_name_appends_copy():
    assert duplicated_project_name("August Reels") == "August Reels copy"


def test_duplicated_video_fields_resets_status_regardless_of_source_status():
    for status in ("READY", "FAILED", "RENDERING", "DISCOVERED"):
        fields = duplicated_video_fields(_FakeVideo(status=status))
        assert fields["status"] == "DISCOVERED"


def test_duplicated_video_fields_carries_footage_but_not_pipeline_state():
    fields = duplicated_video_fields(_FakeVideo())

    assert fields["filename"] == "clip.mp4"
    assert fields["source_hash"] == "abc123"
    assert fields["thumbnail_path"] == "thumbs/clip.jpg"

    leaked_pipeline_fields = {"progress", "current_stage", "error_message", "failed_stage", "retry_count", "celery_task_id"}
    assert leaked_pipeline_fields.isdisjoint(fields.keys())


def test_duplicated_folder_fields_copies_identity_only():
    fields = duplicated_folder_fields(_FakeFolder())
    assert fields == {
        "provider": "google",
        "external_folder_id": "folder-1",
        "folder_name": "August clips",
    }
