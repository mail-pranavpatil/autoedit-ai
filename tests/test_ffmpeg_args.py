from pathlib import Path

from autoedit.compose import compose_final
from autoedit.edit_schema import EditPlan


def test_ffmpeg_args_are_list_not_shell(tmp_path: Path):
    source = tmp_path / "source.mp4"
    broll = tmp_path / "broll.mp4"
    music = tmp_path / "music.wav"
    sfx = tmp_path / "whoosh.wav"
    cap = tmp_path / "cap.png"
    for p in (source, broll, music, sfx, cap):
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
        caption_overlays=[(0.2, 1.4, str(cap))],
        allowed_roots=[tmp_path],
        dry_run=True,
    )
    assert args[0] == "ffmpeg"
    assert all(isinstance(a, str) for a in args)
    assert not any(a.startswith("rm ") or "&&" in a or "|" == a for a in args)
    assert "-filter_complex" in args
    assert "setpts=" in " ".join(args)
    assert "overlay=" in " ".join(args)
    assert str(cap) in args
    assert "format=rgba" in " ".join(args)


def test_many_caption_pngs_are_packed_into_concat(tmp_path: Path):
    source = tmp_path / "source.mp4"
    source.write_bytes(b"not-a-real-media-file")
    overlays = []
    for i in range(20):
        cap = tmp_path / f"cap_{i:04d}.png"
        cap.write_bytes(b"png")
        overlays.append((i * 0.2, i * 0.2 + 0.2, str(cap)))
    plan = EditPlan.model_validate(
        {
            "video_summary": "demo",
            "tone": "energetic",
            "music_category": "technology",
            "captions_enabled": True,
            "segments": [
                {
                    "start": 0,
                    "end": 4,
                    "visual": "talking_head",
                    "broll_query": None,
                    "broll_type": None,
                    "effect": "none",
                    "sfx": None,
                }
            ],
        }
    )
    args = compose_final(
        source_path=str(source),
        output_path=str(tmp_path / "final.mp4"),
        plan=plan,
        duration=4,
        broll_paths=[],
        music_path=None,
        sfx_events=[],
        caption_overlays=overlays,
        allowed_roots=[tmp_path],
        dry_run=True,
    )
    joined = " ".join(args)
    assert args.count("-i") == 2  # source + concat list, not 20 PNGs
    assert "concat" in args
    assert "concat.txt" in joined
    assert "vcaps" in joined


def test_sfx_ducking_and_per_event_volume(tmp_path: Path):
    source = tmp_path / "source.mp4"
    music = tmp_path / "music.wav"
    sfx = tmp_path / "whoosh.wav"
    for p in (source, music, sfx):
        p.write_bytes(b"not-a-real-media-file")
    plan = EditPlan.model_validate(
        {
            "video_summary": "demo",
            "tone": "energetic",
            "music_category": "technology",
            "segments": [
                {
                    "start": 0,
                    "end": 4,
                    "visual": "talking_head",
                    "broll_query": None,
                    "broll_type": None,
                    "effect": "none",
                    "sfx": None,
                }
            ],
            "sfx_events": [
                {
                    "sfx_id": "mixkit_cinematic_whoosh",
                    "start": 2.0,
                    "volume": 0.16,
                    "kind": "transition",
                    "reason": "major broll",
                    "confidence": 0.8,
                    "duck_music": True,
                }
            ],
        }
    )
    args = compose_final(
        source_path=str(source),
        output_path=str(tmp_path / "final.mp4"),
        plan=plan,
        duration=4,
        broll_paths=[],
        music_path=str(music),
        sfx_events=[{"start": 1.55, "path": str(sfx), "volume": 0.16, "duck": True}],
        allowed_roots=[tmp_path],
        dry_run=True,
    )
    joined = " ".join(args)
    assert "adelay=" in joined
    assert "volume=0.16" in joined
    assert "between(t,1.550,1.950)" in joined

