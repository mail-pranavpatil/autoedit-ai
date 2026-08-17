from __future__ import annotations

import json
import logging
import shutil
import subprocess
from pathlib import Path

from autoedit.config import get_settings

logger = logging.getLogger("autoedit")


def ffmpeg_available() -> bool:
    return shutil.which("ffmpeg") is not None and shutil.which("ffprobe") is not None


def run_ffmpeg(args: list[str], timeout: int = 3600) -> subprocess.CompletedProcess:
    if not args or args[0] not in {"ffmpeg", "ffprobe"}:
        raise ValueError("Only ffmpeg/ffprobe argument arrays are allowed")
    if any(not isinstance(a, str) for a in args):
        raise TypeError("FFmpeg arguments must be strings")
    logger.info("ffmpeg argv: %s", " ".join(args[:24]))
    return subprocess.run(args, check=True, capture_output=True, text=True, timeout=timeout)


def ffprobe_json(path: str) -> dict:
    result = run_ffmpeg(
        [
            "ffprobe",
            "-v",
            "error",
            "-print_format",
            "json",
            "-show_format",
            "-show_streams",
            path,
        ],
        timeout=60,
    )
    return json.loads(result.stdout)


def probe_media(path: str) -> dict:
    data = ffprobe_json(path)
    video_stream = next((s for s in data.get("streams", []) if s.get("codec_type") == "video"), None)
    audio_stream = next((s for s in data.get("streams", []) if s.get("codec_type") == "audio"), None)
    if not video_stream:
        raise ValueError("No video stream found")
    fmt = data.get("format", {})
    fps_raw = video_stream.get("avg_frame_rate") or "30/1"
    num, den = (fps_raw.split("/") + ["1"])[:2]
    fps = float(num) / float(den or 1) if float(den or 1) else 30.0
    duration = float(fmt.get("duration") or video_stream.get("duration") or 0)
    return {
        "duration": duration,
        "width": int(video_stream.get("width") or 0),
        "height": int(video_stream.get("height") or 0),
        "fps": fps,
        "video_codec": video_stream.get("codec_name"),
        "has_audio": audio_stream is not None,
        "audio_codec": audio_stream.get("codec_name") if audio_stream else None,
    }


def validate_source(path: str) -> dict:
    suffix = Path(path).suffix.lower()
    if suffix not in {".mp4", ".mov", ".m4v", ".webm"}:
        raise ValueError(f"Unsupported input format: {suffix}")
    info = probe_media(path)
    if info["duration"] <= 0:
        raise ValueError("Video duration is 0")
    return info


def extract_thumbnail(source: str, dest: str) -> None:
    run_ffmpeg(
        [
            "ffmpeg",
            "-y",
            "-ss",
            "1",
            "-i",
            source,
            "-frames:v",
            "1",
            "-vf",
            "scale=480:-2",
            dest,
        ],
        timeout=60,
    )


def extract_audio(source: str, dest: str) -> None:
    run_ffmpeg(
        ["ffmpeg", "-y", "-i", source, "-vn", "-ac", "2", "-ar", "48000", dest],
        timeout=300,
    )


def workspace_dir(job_id: str) -> Path:
    root = get_settings().storage_dir / "jobs" / job_id
    root.mkdir(parents=True, exist_ok=True)
    (root / "assets").mkdir(exist_ok=True)
    (root / "intermediate").mkdir(exist_ok=True)
    return root


def validate_output(path: str, expect_audio: bool = True) -> None:
    info = probe_media(path)
    if info["duration"] <= 0:
        raise ValueError("Output duration is 0")
    if info["width"] != 1080 or info["height"] != 1920:
        raise ValueError(f"Expected 1080x1920, got {info['width']}x{info['height']}")
    if info["video_codec"] not in {"h264", "avc1"}:
        raise ValueError(f"Expected h264, got {info['video_codec']}")
    if expect_audio and not info["has_audio"]:
        raise ValueError("Output is missing audio")
