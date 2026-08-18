from autoedit.captions import caption_states, group_phrases, words_from_segments


def test_words_from_segments_uses_word_timestamps():
    segs = [
        {
            "start": 0,
            "end": 2,
            "text": "about my newest project",
            "words": [
                {"text": "about", "start": 0.0, "end": 0.4},
                {"text": "my", "start": 0.4, "end": 0.55},
                {"text": "newest", "start": 0.55, "end": 1.1},
                {"text": "project", "start": 1.1, "end": 1.8},
            ],
        }
    ]
    words = words_from_segments(segs)
    assert [w["text"] for w in words] == ["about", "my", "newest", "project"]


def test_approximate_words_when_missing():
    segs = [{"start": 0, "end": 2, "text": "hello world"}]
    words = words_from_segments(segs)
    assert len(words) == 2
    assert words[0]["text"] == "hello"
    assert words[1]["end"] == 2


def test_group_phrases_and_states():
    words = [
        {"text": "about", "start": 0.0, "end": 0.4},
        {"text": "my", "start": 0.4, "end": 0.55},
        {"text": "newest", "start": 0.55, "end": 1.1},
        {"text": "project", "start": 1.1, "end": 1.8},
        {"text": "today", "start": 1.8, "end": 2.2},
        {"text": "friends", "start": 2.2, "end": 2.6},
    ]
    phrases = group_phrases(words, size=4)
    assert len(phrases) == 2
    assert [w["text"] for w in phrases[0]["words"]] == ["about", "my", "newest", "project"]
    states = caption_states(phrases)
    assert states[0]["active"] == 0
    assert states[0]["texts"][0] == "about"


def test_caption_presets_and_size():
    from autoedit.captions import hex_to_rgba
    from autoedit.edit_schema import CaptionStyle, caption_style_from_preset

    hormozi = caption_style_from_preset("hormozi")
    assert hormozi.uppercase is True
    assert hormozi.active_color == "#FFE500"
    small = CaptionStyle(size=28, background="none")
    assert small.size == 28
    assert caption_style_from_preset("subtitle").position == "bottom"
    assert hex_to_rgba("#FFFFFF")[0] == 255


def test_style_profile_applies_caption_defaults():
    from autoedit.edit_schema import EditPlan, apply_style_defaults, caption_style_from_preset, merge_style_profile

    merged = merge_style_profile(
        {
            "caption_style": {"preset": "hormozi", "words_per_line": 3},
            "preferred_music_category": "cornfield_chase",
            "music_volume": 0.12,
            "captions_enabled": True,
        }
    )
    assert merged["caption_style"]["preset"] == "hormozi"
    assert merged["caption_style"]["uppercase"] is True
    assert merged["caption_style"]["words_per_line"] == 3
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
                    "effect": "none",
                    "sfx": None,
                }
            ],
        }
    )
    applied = apply_style_defaults(plan, merged)
    assert applied.caption_style.preset == "hormozi"
    assert applied.caption_style.words_per_line == 3
    assert applied.music_category == "cornfield_chase"
    assert applied.music_volume == 0.12
    assert caption_style_from_preset("hormozi").active_color == "#FFE500"

    already_planned = plan.model_copy(update={"caption_style": caption_style_from_preset("classic")})
    restamped = apply_style_defaults(already_planned, merged)
    assert restamped.caption_style.preset == "hormozi"
    assert restamped.caption_style.words_per_line == 3


def test_edit_plan_keeps_neon_style():
    from autoedit.edit_schema import EditPlan, caption_style_from_preset

    plan = EditPlan.model_validate(
        {
            "video_summary": "demo",
            "tone": "energetic",
            "music_category": "technology",
            "captions_enabled": True,
            "caption_style": caption_style_from_preset("neon").model_dump(),
            "segments": [
                {
                    "start": 0,
                    "end": 2,
                    "visual": "talking_head",
                    "broll_query": None,
                    "broll_type": None,
                    "effect": "none",
                    "sfx": None,
                }
            ],
        }
    )
    dumped = plan.model_dump()
    assert dumped["caption_style"]["preset"] == "neon"
    assert dumped["caption_style"]["active_color"] == "#5CFF9F"


def test_write_caption_concat(tmp_path):
    from pathlib import Path

    from autoedit.captions import render_blank_png, write_caption_concat

    a = tmp_path / "a.png"
    b = tmp_path / "b.png"
    render_blank_png(a)
    render_blank_png(b)
    path = write_caption_concat([(0.0, 0.4, str(a)), (0.4, 1.0, str(b))], tmp_path, 1.0)
    assert path
    text = Path(path).read_text()
    assert "ffconcat version 1.0" in text
    assert "duration 0.4000" in text
    assert str(a.resolve()) in text


def test_render_pill_png(tmp_path):
    from autoedit.captions import find_serif_font, render_pill_png
    from autoedit.edit_schema import CaptionStyle

    path = tmp_path / "pill.png"
    render_pill_png(path, ["about", "my", "newest", "project"], 0, find_serif_font(28), CaptionStyle(size=28))
    assert path.exists()
    assert path.stat().st_size > 100
