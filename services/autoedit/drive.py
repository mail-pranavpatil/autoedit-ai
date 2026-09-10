from __future__ import annotations

import ipaddress
import json
import logging
import socket
from pathlib import Path
from urllib.parse import urlparse

import httpx
from fastapi import HTTPException
from google.oauth2.credentials import Credentials
from googleapiclient.discovery import build
from googleapiclient.errors import HttpError
from googleapiclient.http import MediaIoBaseDownload

logger = logging.getLogger("autoedit")

MAX_IMAGE_BYTES = 20 * 1024 * 1024
MIN_IMAGE_SHORT_SIDE = 500

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


class ImageFetchError(RuntimeError):
    """A web image URL could not be fetched into a usable local file."""


def _assert_public_host(host: str) -> None:
    """Reject URLs that resolve to private / loopback / link-local / reserved IPs."""
    if not host:
        raise ImageFetchError("no host in URL")
    try:
        infos = socket.getaddrinfo(host, None)
    except socket.gaierror as exc:
        raise ImageFetchError(f"DNS resolution failed for {host}: {exc}") from exc
    for info in infos:
        ip = ipaddress.ip_address(info[4][0])
        if ip.is_private or ip.is_loopback or ip.is_link_local or ip.is_reserved or ip.is_multicast or ip.is_unspecified:
            raise ImageFetchError(f"host {host} resolves to non-public address {ip}")


def download_image(url: str, dest: Path) -> None:
    """Fetch an arbitrary web image to ``dest`` with SSRF + content guards.

    Only for untrusted image URLs (web search results). Trusted sources (Drive,
    Pexels) keep using :func:`download_url`. Raises :class:`ImageFetchError` on any
    problem so callers can move on to the next candidate.
    """
    dest.parent.mkdir(parents=True, exist_ok=True)
    current = url
    with httpx.Client(timeout=30, follow_redirects=False) as client:
        for _ in range(4):
            parsed = urlparse(current)
            if parsed.scheme not in {"http", "https"}:
                raise ImageFetchError(f"disallowed scheme: {parsed.scheme!r}")
            _assert_public_host(parsed.hostname or "")
            try:
                with client.stream("GET", current) as resp:
                    if resp.is_redirect:
                        loc = resp.headers.get("location")
                        if not loc:
                            raise ImageFetchError("redirect without Location")
                        current = str(httpx.URL(current).join(loc))
                        continue
                    resp.raise_for_status()
                    ctype = (resp.headers.get("content-type") or "").split(";")[0].strip().lower()
                    # Many CDNs serve images as octet-stream / no type; probe_media
                    # below is the real gate. Only reject an explicit non-image type.
                    if ctype and not ctype.startswith("image/") and ctype not in {
                        "application/octet-stream", "binary/octet-stream", "application/binary",
                    }:
                        raise ImageFetchError(f"not an image (Content-Type: {ctype})")
                    size = 0
                    with open(dest, "wb") as f:
                        for chunk in resp.iter_bytes():
                            size += len(chunk)
                            if size > MAX_IMAGE_BYTES:
                                raise ImageFetchError("image exceeds size cap")
                            f.write(chunk)
                    break
            except httpx.HTTPError as exc:
                raise ImageFetchError(f"fetch failed: {exc}") from exc
        else:
            raise ImageFetchError("too many redirects")

    from autoedit.media import probe_media

    try:
        info = probe_media(str(dest))
    except Exception as exc:  # noqa: BLE001 - undecodable / not really an image
        dest.unlink(missing_ok=True)
        raise ImageFetchError(f"not a decodable image: {exc}") from exc
    if min(info.get("width") or 0, info.get("height") or 0) < MIN_IMAGE_SHORT_SIDE:
        dest.unlink(missing_ok=True)
        raise ImageFetchError(f"image too small: {info.get('width')}x{info.get('height')}")

    # Flatten transparency onto white (logos on transparent bg otherwise render as
    # black / a checkerboard), then reject near-solid images (block pages,
    # "Access Restricted" screens, error placeholders).
    try:
        from PIL import Image, ImageStat

        with Image.open(dest) as im:
            im.load()
            if im.mode in ("RGBA", "LA", "P") or "transparency" in im.info:
                rgba = im.convert("RGBA")
                flat = Image.new("RGB", rgba.size, (255, 255, 255))
                flat.paste(rgba, mask=rgba.split()[-1])
                flat.save(dest, "JPEG", quality=90)
                im = flat
            stat = ImageStat.Stat(im.convert("L").resize((48, 48)))
            stddev, mean = stat.stddev[0], stat.mean[0]
    except Exception:  # noqa: BLE001 - if PIL can't read it, probe_media already vouched
        stddev, mean = 99.0, 128.0
    if stddev < 12.0:
        dest.unlink(missing_ok=True)
        raise ImageFetchError(f"image is near-uniform (stddev {stddev:.1f}) - likely a block page")
    if mean < 30.0:
        dest.unlink(missing_ok=True)
        raise ImageFetchError(f"image is too dark (mean {mean:.1f})")
