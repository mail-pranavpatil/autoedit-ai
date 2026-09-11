from pathlib import Path

import pytest
from fastapi import HTTPException
from fastapi.responses import FileResponse

from autoedit.object_storage import delete_object, ensure_local, object_exists, save_output, serve_response


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


if __name__ == "__main__":
    import sys

    sys.exit(pytest.main([__file__, "-q"]))
