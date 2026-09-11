from __future__ import annotations

import mimetypes
from functools import lru_cache
from pathlib import Path

from fastapi import HTTPException
from fastapi.responses import FileResponse, RedirectResponse, Response

from autoedit.config import get_settings

PRESIGN_EXPIRES_SECONDS = 3600


@lru_cache
def _client():
    import boto3

    settings = get_settings()
    return boto3.client(
        "s3",
        endpoint_url=settings.r2_endpoint,
        aws_access_key_id=settings.r2_access_key_id,
        aws_secret_access_key=settings.r2_secret_access_key,
        region_name="auto",
    )


def _is_local() -> bool:
    return get_settings().storage_backend == "local"


def save_output(local_path: str, key: str, content_type: str | None = None) -> str:
    """Worker just finished writing local_path. Returns the value to store in
    the DB column: local_path unchanged in "local" mode, or the object key
    after uploading in "r2" mode.
    """
    if _is_local():
        return local_path
    content_type = content_type or mimetypes.guess_type(local_path)[0] or "application/octet-stream"
    _client().upload_file(local_path, get_settings().r2_bucket, key, ExtraArgs={"ContentType": content_type})
    return key


def ensure_local(stored_value: str | None, local_dest: Path) -> Path:
    """Worker is about to read a file it (or an earlier job) wrote before:
    re-render source reuse, a broll-cache hit. Returns a real local path
    ffmpeg/PIL can open, downloading from object storage first if needed.
    """
    if not stored_value:
        raise FileNotFoundError("no stored value to fetch")
    if _is_local():
        return Path(stored_value)
    if not local_dest.exists():
        local_dest.parent.mkdir(parents=True, exist_ok=True)
        _client().download_file(get_settings().r2_bucket, stored_value, str(local_dest))
    return local_dest


def delete_object(stored_value: str | None, force_local: bool = False) -> None:
    if not stored_value:
        return
    if force_local or _is_local():
        Path(stored_value).unlink(missing_ok=True)
        return
    try:
        _client().delete_object(Bucket=get_settings().r2_bucket, Key=stored_value)
    except Exception:  # noqa: BLE001 - best-effort cleanup
        pass


def object_exists(stored_value: str | None, force_local: bool = False) -> bool:
    if not stored_value:
        return False
    if force_local or _is_local():
        return Path(stored_value).exists()
    try:
        _client().head_object(Bucket=get_settings().r2_bucket, Key=stored_value)
        return True
    except Exception:  # noqa: BLE001 - any failure (404, network) means "not there"
        return False


def serve_response(
    stored_value: str | None,
    filename: str | None = None,
    media_type: str | None = None,
    no_cache: bool = False,
    force_local: bool = False,
) -> Response:
    """The entire body of an API route that serves a stored media file.

    force_local=True is for files that are always local regardless of the
    global storage_backend - e.g. bundled system music/SFX baked into the
    Docker image, never uploaded via save_output.
    """
    if not object_exists(stored_value, force_local=force_local):
        raise HTTPException(404, "File not found")
    media_type = media_type or (mimetypes.guess_type(stored_value)[0] if stored_value else None)
    if force_local or _is_local():
        headers = {"Cache-Control": "no-store, no-cache, must-revalidate"} if no_cache else None
        return FileResponse(stored_value, media_type=media_type, filename=filename, headers=headers)
    params = {"Bucket": get_settings().r2_bucket, "Key": stored_value}
    if filename:
        params["ResponseContentDisposition"] = f'attachment; filename="{filename}"'
    if media_type:
        params["ResponseContentType"] = media_type
    url = _client().generate_presigned_url("get_object", Params=params, ExpiresIn=PRESIGN_EXPIRES_SECONDS)
    response = RedirectResponse(url, status_code=302)
    if no_cache:
        response.headers["Cache-Control"] = "no-store, no-cache, must-revalidate"
    return response
