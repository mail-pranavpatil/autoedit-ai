from __future__ import annotations

import json
import logging
from pathlib import Path

import httpx
from fastapi import HTTPException
from google.oauth2.credentials import Credentials
from googleapiclient.discovery import build
from googleapiclient.errors import HttpError
from googleapiclient.http import MediaIoBaseDownload

logger = logging.getLogger("autoedit")

VIDEO_EXTS = {".mp4", ".mov", ".m4v", ".webm"}
VIDEO_MIMES = {
    "video/mp4",
    "video/quicktime",
    "video/x-m4v",
    "video/webm",
}


def drive_service(access_token: str):
    creds = Credentials(token=access_token)
    return build("drive", "v3", credentials=creds, cache_discovery=False)


def _raise_drive_error(exc: HttpError) -> None:
    body = exc.content.decode() if isinstance(exc.content, (bytes, bytearray)) else str(exc.content)
    message = str(exc)
    try:
        parsed = json.loads(body)
        message = parsed.get("error", {}).get("message") or message
    except Exception:
        pass
    logger.warning("Google Drive API error: %s", message)
    lowered = f"{message} {body}".lower()
    if "has not been used" in lowered or "accessnotconfigured" in lowered or "is disabled" in lowered:
        raise HTTPException(
            status_code=400,
            detail=(
                "Google Drive API is not enabled for this OAuth project. "
                "In Google Cloud Console, enable “Google Drive API”, wait a minute, then reload this page. "
                "https://console.cloud.google.com/apis/library/drive.googleapis.com"
            ),
        )
    if exc.resp.status in {401, 403}:
        raise HTTPException(401, "Google Drive access was denied. Sign out and sign in again to grant Drive access.")
    raise HTTPException(502, f"Google Drive request failed: {message}")


def _list_files(service, **kwargs) -> dict:
    try:
        return service.files().list(**kwargs).execute()
    except HttpError as exc:
        _raise_drive_error(exc)
        raise


def list_folders(access_token: str, parent_id: str | None = None) -> list[dict]:
    service = drive_service(access_token)
    q = "mimeType = 'application/vnd.google-apps.folder' and trashed = false"
    if parent_id:
        q += f" and '{parent_id}' in parents"
    else:
        q += " and 'root' in parents"
    items = []
    page_token = None
    while True:
        resp = _list_files(
            service,
            q=q,
            spaces="drive",
            fields="nextPageToken, files(id, name)",
            pageSize=100,
            pageToken=page_token,
            includeItemsFromAllDrives=True,
            supportsAllDrives=True,
        )
        items.extend(resp.get("files", []))
        page_token = resp.get("nextPageToken")
        if not page_token:
            break
    items.sort(key=lambda f: (f.get("name") or "").lower())
    return items


def list_videos(access_token: str, folder_id: str) -> list[dict]:
    service = drive_service(access_token)
    q = f"'{folder_id}' in parents and trashed = false"
    items = []
    page_token = None
    while True:
        resp = _list_files(
            service,
            q=q,
            spaces="drive",
            fields="nextPageToken, files(id, name, mimeType, size)",
            pageSize=100,
            pageToken=page_token,
            includeItemsFromAllDrives=True,
            supportsAllDrives=True,
        )
        items.extend(resp.get("files", []))
        page_token = resp.get("nextPageToken")
        if not page_token:
            break
    videos = []
    for f in items:
        name = f.get("name") or ""
        mime = f.get("mimeType") or ""
        ext = Path(name).suffix.lower()
        if mime in VIDEO_MIMES or ext in VIDEO_EXTS:
            videos.append(
                {
                    "id": f["id"],
                    "name": name,
                    "mimeType": mime,
                    "size": int(f.get("size") or 0),
                }
            )
    return videos


def download_file(access_token: str, file_id: str, dest: Path) -> None:
    dest.parent.mkdir(parents=True, exist_ok=True)
    service = drive_service(access_token)
    try:
        request = service.files().get_media(fileId=file_id, supportsAllDrives=True)
        with open(dest, "wb") as fh:
            downloader = MediaIoBaseDownload(fh, request)
            done = False
            while not done:
                _, done = downloader.next_chunk()
    except HttpError as exc:
        _raise_drive_error(exc)
    logger.info("Downloaded Drive file %s -> %s", file_id, dest)


def download_url(url: str, dest: Path) -> None:
    dest.parent.mkdir(parents=True, exist_ok=True)
    with httpx.Client(timeout=120, follow_redirects=True) as client:
        with client.stream("GET", url) as resp:
            resp.raise_for_status()
            with open(dest, "wb") as f:
                for chunk in resp.iter_bytes():
                    f.write(chunk)
