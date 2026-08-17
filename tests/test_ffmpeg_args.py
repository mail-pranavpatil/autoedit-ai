from pathlib import Path

from autoedit.compose import compose_final
from autoedit.edit_schema import EditPlan


def test_ffmpeg_args_are_list_not_shell(tmp_path: Path):
    source = tmp_path / "source.mp4"
    broll = tmp_path / "broll.mp4"
    music = tmp_path / "music.wav"
    sfx = tmp_path / "whoosh.wav"
    for p in (source, broll, music, sfx):
        p.write_bytes(b"not-a-real-media-file")
    out = tmp_path / "final.mp4"
    plan = EditPlan.model_validate(
        {
            "video_summary": "demo",
            "tone": "energetic",
            "music_category": "technology",
            "segments": [
                {
                    "start": 0,
                    "end": 2,
                    "visual": "talking_head",
                    "broll_query": None,
                    "broll_type": None,
                    "effect": "slow_zoom_in",
                    "sfx": None,
                },
                {
                    "start": 2,
                    "end": 4,
                    "visual": "broll",
                    "broll_query": "laptop",
                    "broll_type": "video",
                    "effect": "none",
                    "sfx": "whoosh",
                },
            ],
        }
    )
    args = compose_final(
        source_path=str(source),
        output_path=str(out),
        plan=plan,
        duration=5,
        broll_paths=[(2, 4, str(broll), "video")],
        music_path=str(music),
        sfx_events=[(2, str(sfx))],
        allowed_roots=[tmp_path],
        dry_run=True,
    )
    assert args[0] == "ffmpeg"
    assert all(isinstance(a, str) for a in args)
    assert not any(a.startswith("rm ") or "&&" in a or "|" == a for a in args)
    assert "-filter_complex" in args
    assert "setpts=" in " ".join(args)
    assert "overlay=" in " ".join(args)
