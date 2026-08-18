from pathlib import Path

from autoedit.edit_schema import EditPlan
from autoedit.sfx.engine import CLICK_IDS, decide_sfx, format_debug_log, mix_payload
from autoedit.sfx.registry import load_catalog, resolve_by_id
from autoedit.sfx.style import detect_style


def _plan(segments, tone="educational explainer", music="chill") -> EditPlan:
    return EditPlan.model_validate(
        {
            "video_summary": "demo",
            "tone": tone,
            "music_category": music,
            "segments": segments,
        }
    )


def _broll(start, end, broll_type="video", effect="none"):
    return {
        "start": start,
        "end": end,
        "visual": "broll",
        "broll_query": "demo clip",
        "broll_type": broll_type,
        "effect": effect,
        "sfx": "whoosh",
    }


def _head(start, end):
    return {
        "start": start,
        "end": end,
        "visual": "talking_head",
        "broll_query": None,
        "broll_type": None,
        "effect": "slow_zoom_in",
        "sfx": None,
    }


def test_broll_bookends_use_same_click():
    plan = _plan([_head(0, 2), _broll(2, 5, broll_type="video", effect="fade_in")])
    events, _log = decide_sfx(plan, has_music=True, whoosh_chance=0)
    assert len(events) == 2
    assert events[0].sfx_id == events[1].sfx_id
    assert events[0].sfx_id in CLICK_IDS
    assert events[0].start == 2.0
    assert events[1].start == 5.0


def test_video_broll_uses_shutter_or_click():
    plan = _plan([_head(0, 2), _broll(2, 5, broll_type="video", effect="fade_in")])
    events, _log = decide_sfx(plan, has_music=True, whoosh_chance=0)
    assert events
    assert all(e.sfx_id in CLICK_IDS for e in events)
    assert not any("whoosh" in e.sfx_id for e in events)


def test_mix_payload_finds_catalog_files():
    plan = _plan([_head(0, 2), _broll(2, 5, broll_type="image")])
    events, _ = decide_sfx(plan, has_music=False, whoosh_chance=0)
    mixed = mix_payload(plan.model_copy(update={"sfx_events": events}))
    assert mixed
    assert Path(mixed[0]["path"]).exists()


def test_image_broll_uses_shutter_or_click_not_whoosh():
    plan = _plan([_head(0, 2), _broll(2, 5, broll_type="image")])
    events, _log = decide_sfx(plan, has_music=False, whoosh_chance=0)
    ids = [e.sfx_id for e in events]
    assert ids
    assert all(i in CLICK_IDS for i in ids)
    assert not any("whoosh" in i for i in ids)


def test_adjacent_brolls_do_not_stack_at_shared_cut():
    segs = [_head(0, 1)]
    t = 1.0
    for _ in range(3):
        segs.append(_broll(t, t + 2))
        t += 2
    plan = _plan(segs, tone="serious educational lecture")
    events, log = decide_sfx(plan, has_music=True, whoosh_chance=0)
    times = [round(e.start, 3) for e in events]
    assert times == sorted(times)
    assert len(times) == len(set(times))
    assert any("Shared B-roll cut" in d.reason for d in log if not d.accepted)
    assert all("whoosh" not in e.sfx_id for e in events)


def test_short_broll_skips_out_hit():
    plan = _plan([_head(0, 2), _broll(2, 2.3)])
    events, log = decide_sfx(plan, has_music=False, whoosh_chance=0)
    assert len(events) == 1
    assert events[0].start == 2.0
    assert any("too short" in d.reason.lower() for d in log if not d.accepted)


def test_caption_and_reveal_do_not_add_sfx():
    plan = _plan([_head(0, 12)], tone="cinematic dramatic", music="cinematic")
    phrases = [
        {
            "start": 1.0,
            "end": 1.8,
            "words": [{"text": "exactly", "start": 1.0, "end": 1.3}, {"text": "42%", "start": 1.3, "end": 1.8}],
        }
    ]
    transcript = {
        "full_text": "There's one huge problem with this. This is ridiculous and awkward.",
        "segments": [
            {"start": 2.0, "end": 4.0, "text": "This is ridiculous and awkward."},
            {"start": 5.0, "end": 7.0, "text": "There's one huge problem with this."},
        ],
    }
    events, log = decide_sfx(
        plan,
        phrases=phrases,
        transcript=transcript,
        has_music=False,
        whoosh_chance=0,
    )
    assert events == []
    assert all(e.sfx_id != "mixkit_cartoon_whistle" for e in events)
    assert not any(d.sfx_id and str(d.sfx_id).startswith("soundreality_riser") for d in log)


def test_missing_file_is_skipped(tmp_path: Path):
    catalog = load_catalog()
    assert catalog
    assert resolve_by_id(catalog[0].id, catalog=catalog, sfx_dir=tmp_path) is None
    plan = _plan([_head(0, 2), _broll(2, 5, broll_type="image")])
    events, _ = decide_sfx(plan, has_music=False, whoosh_chance=0)
    mixed = mix_payload(plan.model_copy(update={"sfx_events": events}), sfx_dir=tmp_path)
    assert mixed == []


def test_debug_log_includes_rejections():
    plan = _plan([_broll(0, 2), _broll(2, 4), _broll(4, 6)], tone="educational")
    _events, log = decide_sfx(plan, has_music=True, whoosh_chance=0)
    text = format_debug_log(log)
    assert "SFX DECISION LOG" in text
    assert "Reason:" in text


def test_detect_style_comedy():
    assert detect_style("funny sketch comedy", "energetic") == "COMEDY"


def test_no_sfx_on_plain_talking_head():
    plan = _plan([_head(0, 12)], tone="calm educational")
    events, _log = decide_sfx(
        plan,
        transcript={"full_text": "Hello friends today we will learn quietly.", "segments": []},
        has_music=True,
        whoosh_chance=0,
    )
    assert events == []
