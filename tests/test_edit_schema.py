from autoedit.edit_schema import EditPlan, STAGE_PROGRESS
from pydantic import ValidationError
import pytest


def test_valid_plan():
    plan = EditPlan.model_validate(
        {
            "video_summary": "How to use AI tools",
            "tone": "energetic",
            "music_category": "technology",
            "segments": [
                {
                    "start": 0,
                    "end": 4,
                    "visual": "talking_head",
                    "broll_query": None,
                    "broll_type": None,
                    "effect": "slow_zoom_in",
                    "sfx": None,
                },
                {
                    "start": 4,
                    "end": 8,
                    "visual": "broll",
                    "broll_query": "developer coding laptop",
                    "broll_type": "video",
                    "effect": "none",
                    "sfx": "whoosh",
                },
            ],
        }
    )
    assert len(plan.segments) == 2
    assert plan.captions_enabled is True


def test_rejects_shell_in_query():
    with pytest.raises(ValidationError):
        EditPlan.model_validate(
            {
                "video_summary": "x",
                "tone": "x",
                "music_category": "chill",
                "segments": [
                    {
                        "start": 0,
                        "end": 2,
                        "visual": "broll",
                        "broll_query": "foo; rm -rf /",
                        "broll_type": "video",
                        "effect": "none",
                        "sfx": None,
                    }
                ],
            }
        )


def test_rejects_unknown_effect():
    with pytest.raises(ValidationError):
        EditPlan.model_validate(
            {
                "video_summary": "x",
                "tone": "x",
                "music_category": "chill",
                "segments": [
                    {
                        "start": 0,
                        "end": 2,
                        "visual": "talking_head",
                        "broll_query": None,
                        "broll_type": None,
                        "effect": "explode",
                        "sfx": None,
                    }
                ],
            }
        )


def test_accepts_string_null_fields():
    plan = EditPlan.model_validate(
        {
            "video_summary": "x",
            "tone": "x",
            "music_category": "chill",
            "segments": [
                {
                    "start": 0,
                    "end": 3,
                    "visual": "talking_head",
                    "broll_query": "null",
                    "broll_type": "null",
                    "effect": "slow_zoom_in",
                    "sfx": "null",
                },
                {
                    "start": 3,
                    "end": 6,
                    "visual": "broll",
                    "broll_query": "temple india",
                    "broll_type": "null",
                    "effect": "none",
                    "sfx": None,
                },
            ],
        }
    )
    assert plan.segments[0].broll_type is None
    assert plan.segments[0].sfx is None
    assert plan.segments[1].broll_type == "video"


def test_accepts_sfx_events_on_plan():
    plan = EditPlan.model_validate(
        {
            "video_summary": "x",
            "tone": "x",
            "music_category": "chill",
            "segments": [
                {
                    "start": 0,
                    "end": 3,
                    "visual": "talking_head",
                    "broll_query": None,
                    "broll_type": None,
                    "effect": "none",
                    "sfx": "whoosh",
                }
            ],
            "sfx_events": [
                {
                    "sfx_id": "mixkit_camera_shutter",
                    "start": 1.2,
                    "volume": 0.16,
                    "kind": "accent",
                    "reason": "photo",
                    "confidence": 0.9,
                    "duck_music": False,
                }
            ],
        }
    )
    assert plan.segments[0].sfx == "whoosh"
    assert plan.sfx_events[0].sfx_id == "mixkit_camera_shutter"


def test_stage_progress_ready():
    assert STAGE_PROGRESS["READY"] == 100
    assert STAGE_PROGRESS["RENDERING"] == 95
