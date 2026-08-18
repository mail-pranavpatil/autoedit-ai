from autoedit.edit_schema import EditPlan
from autoedit.mentions import _uncovered_runs, enforce_visual_cadence, query_from_window


def _plan(segments):
    return EditPlan.model_validate(
        {
            "video_summary": "x",
            "tone": "x",
            "music_category": "feeling_blue",
            "segments": segments,
        }
    )


def test_cadence_inserts_broll_every_few_seconds():
    plan = _plan(
        [
            {
                "start": 0,
                "end": 12,
                "visual": "talking_head",
                "broll_query": None,
                "broll_type": None,
                "effect": "none",
                "sfx": None,
            }
        ]
    )
    transcript = {
        "segments": [
            {
                "start": 0,
                "end": 12,
                "text": "today we talk about journaling habits and focus",
                "words": [
                    {"text": "today", "start": 0.2, "end": 0.5},
                    {"text": "journaling", "start": 3.0, "end": 3.4},
                    {"text": "habits", "start": 6.0, "end": 6.3},
                    {"text": "focus", "start": 9.0, "end": 9.4},
                ],
            }
        ]
    }
    filled = enforce_visual_cadence(plan, transcript, {"visual_cadence_seconds": 2.5})
    assert any(s.visual == "broll" for s in filled.segments)
    for start, end in _uncovered_runs(filled, 12):
        assert end - start <= 3.5 + 0.05


def test_query_from_window_skips_stopwords():
    transcript = {
        "segments": [
            {
                "words": [
                    {"text": "the", "start": 0, "end": 0.2},
                    {"text": "ChatGPT", "start": 0.2, "end": 0.6},
                    {"text": "app", "start": 0.6, "end": 0.8},
                ]
            }
        ]
    }
    assert "chatgpt" in query_from_window(transcript, 0, 1).lower()
