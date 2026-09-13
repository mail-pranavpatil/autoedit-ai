from pathlib import Path

import pytest
from fastapi import HTTPException
from fastapi.responses import FileResponse

from autoedit.object_storage import delete_object, ensure_local, object_exists, save_output, serve_response


@pytest.fixture(autouse=True)
def _force_local_backend(monkeypatch):
    # These tests exercise local-mode behavior specifically, regardless of
    # whatever STORAGE_BACKEND happens to be set in the developer's real .env.
    monkeypatch.setattr("autoedit.object_storage._is_local", lambda: True)


def test_save_output_local_mode_is_a_noop(tmp_path: Path):
    local = tmp_path / "final.mp4"
    local.write_bytes(b"video-bytes")
    stored = save_output(str(local), "videos/abc/final.mp4")
    assert stored == str(local)


def test_ensure_local_returns_the_stored_path_directly(tmp_path: Path):
    local = tmp_path / "source.mp4"
    local.write_bytes(b"source-bytes")
    resolved = ensure_local(str(local), tmp_path / "unused-dest.mp4")
    assert resolved == Path(str(local))


def test_ensure_local_raises_on_empty_stored_value(tmp_path: Path):
    with pytest.raises(FileNotFoundError):
        ensure_local(None, tmp_path / "dest.mp4")


def test_object_exists_checks_the_filesystem(tmp_path: Path):
    present = tmp_path / "there.jpg"
    present.write_bytes(b"x")
    missing = tmp_path / "not-there.jpg"
    assert object_exists(str(present)) is True
    assert object_exists(str(missing)) is False
    assert object_exists(None) is False


def test_delete_object_removes_the_local_file(tmp_path: Path):
    local = tmp_path / "asset.wav"
    local.write_bytes(b"x")
    delete_object(str(local))
    assert not local.exists()


def test_serve_response_local_mode_returns_file_response(tmp_path: Path):
    local = tmp_path / "thumb.jpg"
    local.write_bytes(b"x")
    response = serve_response(str(local), media_type="image/jpeg")
    assert isinstance(response, FileResponse)


def test_serve_response_404s_when_missing(tmp_path: Path):
    with pytest.raises(HTTPException) as exc_info:
        serve_response(str(tmp_path / "missing.mp4"))
    assert exc_info.value.status_code == 404


class _FakeR2Client:
    """head_object succeeds for a key that has no matching local path -
    the whole point of R2 mode, and what a bare Path(key).exists() check
    (the youtube.py bug) misses."""

    def head_object(self, Bucket, Key):
        if Key != "videos/abc/final.mp4":
            raise Exception("404")

    def download_file(self, Bucket, Key, dest):
        Path(dest).write_bytes(b"downloaded")


def test_object_exists_in_r2_mode_checks_the_bucket_not_the_filesystem(monkeypatch):
    monkeypatch.setattr("autoedit.object_storage._is_local", lambda: False)
    monkeypatch.setattr("autoedit.object_storage._client", lambda: _FakeR2Client())
    assert object_exists("videos/abc/final.mp4") is True
    assert object_exists("videos/missing/final.mp4") is False


def test_ensure_local_downloads_from_r2_when_missing_locally(tmp_path, monkeypatch):
    monkeypatch.setattr("autoedit.object_storage._is_local", lambda: False)
    monkeypatch.setattr("autoedit.object_storage._client", lambda: _FakeR2Client())
    dest = tmp_path / "cache" / "final.mp4"
    resolved = ensure_local("videos/abc/final.mp4", dest)
    assert resolved == dest
    assert dest.read_bytes() == b"downloaded"


if __name__ == "__main__":
    import sys

    sys.exit(pytest.main([__file__, "-q"]))
