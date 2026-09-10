from autoedit.broll_plan import build_dense_broll, plan_image_queries
from autoedit.edit_schema import EditPlan, EditSegment


def _plan(segments):
    return EditPlan(
        video_summary="a talk about payments",
        tone="informative",
        music_category="feeling_blue",
        segments=segments,
    )


def _phrases(spans):
    return [{"text": f"phrase {i}", "start": s, "end": e} for i, (s, e) in enumerate(spans)]


def test_one_image_segment_per_phrase_with_query():
    plan = _plan([EditSegment(start=0, end=12, visual="talking_head")])
    phrases = _phrases([(0, 3), (3, 6), (6, 9), (9, 12)])
    queries = ["stripe checkout", None, "server racks", "team meeting"]

    out = build_dense_broll(plan, phrases, queries, {}, max_assets=120)

    img = [s for s in out.segments if s.visual == "broll" and s.broll_type == "image"]
    assert [s.broll_query for s in img] == ["stripe checkout", "server racks", "team meeting"]
    # timeline is contiguous and covers [0, 12] with no overlap
    assert out.segments[0].start == 0
    assert abs(out.segments[-1].end - 12) < 0.2
    for a, b in zip(out.segments, out.segments[1:]):
        assert abs(a.end - b.start) < 0.05


def test_default_drops_planner_broll_every_phrase_is_image():
    plan = _plan([
        EditSegment(start=0, end=4, visual="talking_head"),
        EditSegment(start=4, end=7, visual="broll", broll_type="video", broll_query="city timelapse"),
        EditSegment(start=7, end=12, visual="talking_head"),
    ])
    phrases = _phrases([(0, 3), (3.5, 6.5), (7.5, 11)])
    queries = ["laptop", "server room", "handshake"]

    out = build_dense_broll(plan, phrases, queries, {}, max_assets=120)

    assert not [s for s in out.segments if s.broll_type == "video"]  # planner video dropped
    assert [s.broll_query for s in out.segments if s.broll_type == "image"] == [
        "laptop", "server room", "handshake",
    ]


def test_keep_video_preserves_planner_video_span():
    plan = _plan([
        EditSegment(start=0, end=4, visual="talking_head"),
        EditSegment(start=4, end=7, visual="broll", broll_type="video", broll_query="city timelapse"),
        EditSegment(start=7, end=12, visual="talking_head"),
    ])
    phrases = _phrases([(0, 3), (3.5, 6.5), (7.5, 11)])
    queries = ["laptop", "should be skipped", "handshake"]

    out = build_dense_broll(plan, phrases, queries, {}, max_assets=120, keep_video=True)

    vids = [s for s in out.segments if s.broll_type == "video"]
    assert len(vids) == 1 and vids[0].broll_query == "city timelapse"
    imgs = [s for s in out.segments if s.broll_type == "image"]
    assert [s.broll_query for s in imgs] == ["laptop", "handshake"]
    for s in imgs:
        assert s.end <= 4.01 or s.start >= 6.99


def test_max_assets_cap():
    plan = _plan([EditSegment(start=0, end=20, visual="talking_head")])
    phrases = _phrases([(i, i + 1) for i in range(20)])
    queries = [f"thing {i}" for i in range(20)]

    out = build_dense_broll(plan, phrases, queries, {}, max_assets=5)

    assert sum(1 for s in out.segments if s.broll_type == "image") == 5


def test_no_phrases_returns_plan_unchanged():
    plan = _plan([EditSegment(start=0, end=5, visual="talking_head")])
    assert build_dense_broll(plan, [], [], {}, max_assets=10) is plan


def test_phrase_text_reads_words_shape():
    from autoedit.broll_plan import _phrase_text

    ph = {"start": 0, "end": 2, "words": [{"text": "Stripe"}, {"text": "acquired"}, {"text": "OpenRouter"}]}
    assert _phrase_text(ph) == "Stripe acquired OpenRouter"
    assert _phrase_text({"text": "already flat"}) == "already flat"


def test_plan_image_queries_maps_gpt_response_by_index(monkeypatch):
    # Real pipeline phrases carry `words`, not `text`; GPT must receive that text
    # and its answers must map 1:1 by index. A null -> no image for that phrase.
    import autoedit.broll_plan as bp

    seen = {}

    class _Msg:
        content = '{"queries": ["stripe logo", null, "ai api marketplace"]}'

    class _Choice:
        message = _Msg()

    class _Resp:
        choices = [_Choice()]

    class _Chat:
        def create(self, **kw):
            seen["prompt"] = kw["messages"][-1]["content"]
            return _Resp()

    class _Client:
        chat = type("c", (), {"completions": _Chat()})()

    monkeypatch.setattr(bp, "OpenAI", lambda **k: _Client())
    phrases = [
        {"start": 0, "end": 2, "words": [{"text": "Stripe"}, {"text": "bought"}, {"text": "OpenRouter"}]},
        {"start": 2, "end": 3, "words": [{"text": "so"}, {"text": "anyway"}]},
        {"start": 3, "end": 5, "words": [{"text": "an"}, {"text": "API"}, {"text": "marketplace"}]},
    ]

    class S:
        openai_api_key = "x"
        llm_model = "gpt-4o-mini"

    out = plan_image_queries(phrases, "Stripe acquires OpenRouter", "informative", "full text", S())
    assert out == ["stripe logo", None, "ai api marketplace"]
    assert "Stripe bought OpenRouter" in seen["prompt"]  # words -> text reached GPT
