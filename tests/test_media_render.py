import subprocess
from pathlib import Path

import pytest

from autoedit.compose import compose_final
from autoedit.edit_schema import EditPlan
from autoedit.media import ffmpeg_available, run_ffmpeg, validate_output
from autoedit.tones import write_tone


@pytest.mark.skipif(not ffmpeg_available(), reason="ffmpeg not installed")
def test_render_sample_mp4(tmp_path: Path):
    source = tmp_path / "source.mp4"
    still = tmp_path / "still.jpg"
    music = tmp_path / "music.wav"
    sfx = tmp_path / "sfx.wav"
    out = tmp_path / "final.mp4"
    run_ffmpeg(
        [
            "ffmpeg",
            "-y",
            "-f",
            "lavfi",
            "-i",
            "color=c=blue:s=1080x1920:d=4",
            "-f",
            "lavfi",
            "-i",
            "sine=frequency=440:duration=4",
            "-shortest",
            "-c:v",
            "libx264",
            "-pix_fmt",
            "yuv420p",
            "-c:a",
            "aac",
            str(source),
        ],
        timeout=60,
    )
    run_ffmpeg(
        ["ffmpeg", "-y", "-f", "lavfi", "-i", "color=c=red:s=1080x1920:d=1", "-frames:v", "1", str(still)],
        timeout=30,
    )
    write_tone(music, 180, 4, 0.1)
    write_tone(sfx, 880, 0.2, 0.3)
    plan = EditPlan.model_validate(
        {
            "video_summary": "sample",
            "tone": "chill",
            "music_category": "chill",
            "segments": [
                {
                    "start": 0,
                    "end": 2,
                    "visual": "talking_head",
                    "broll_query": None,
                    "broll_type": None,
                    "effect": "none",
                    "sfx": None,
                },
                {
                    "start": 2,
                    "end": 3.5,
                    "visual": "broll",
                    "broll_query": "red",
                    "broll_type": "image",
                    "effect": "fade_in",
                    "sfx": "whoosh",
                },
            ],
        }
    )
    compose_final(
        source_path=str(source),
        output_path=str(out),
        plan=plan,
        duration=4,
        broll_paths=[(2, 3.5, str(still), "image")],
        music_path=str(music),
        sfx_events=[(2, str(sfx))],
        allowed_roots=[tmp_path],
    )
    assert out.exists()
    validate_output(str(out), expect_audio=True)
