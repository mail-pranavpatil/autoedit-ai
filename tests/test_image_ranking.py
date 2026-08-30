import httpx
import pytest

from autoedit.config import Settings
from autoedit.image_ranking import ranker as ranker_mod
from autoedit.image_ranking import rank_candidates, rank_candidates_detailed
from autoedit.image_ranking.jina import JinaImageRanker


def _settings(**over):
    base = dict(
        enable_jina_reranker=True,
        jina_api_key="test-key",
        jina_model="jina-reranker-m0",
        jina_max_candidates=30,
        jina_timeout_seconds=5.0,
    )
    base.update(over)
    return Settings(**base)


_DEFAULT_URL = object()


def _img(ext_id, url=_DEFAULT_URL, photographer="Ada"):
    return {
        "external_id": ext_id,
        "asset_type": "image",
        "url": f"https://img.example/{ext_id}.jpg" if url is _DEFAULT_URL else url,
        "license": "Pexels",
        "metadata": {"photographer": photographer},
    }


@pytest.fixture(autouse=True)
def _clear_cache():
    ranker_mod._CACHE.clear()
    yield
    ranker_mod._CACHE.clear()


@pytest.fixture
def fake_jina(monkeypatch):
    """Patch the single HTTP call. Returns a dict you populate with behavior."""
    state = {"payloads": [], "results": None, "raises": None}

    def _call(self, payload):
        state["payloads"].append(payload)
        if state["raises"] is not None:
            raise state["raises"]
        return {"results": state["results"], "model": "jina-reranker-m0"}

    monkeypatch.setattr(JinaImageRanker, "_call_jina", _call)
    return state


# 1 — feature flag OFF: exact passthrough, no HTTP call
def test_disabled_is_passthrough(fake_jina):
    fake_jina["raises"] = AssertionError("must not call Jina when disabled")
    cands = [_img("A"), _img("B"), _img("C")]
    out = rank_candidates(
        "q", cands, asset_type="image", scene_id=0, settings=_settings(enable_jina_reranker=False)
    )
    assert [c["external_id"] for c in out] == ["A", "B", "C"]
    assert fake_jina["payloads"] == []


# 2 — success path reorders by descending relevance
def test_success_reorders(fake_jina):
    fake_jina["results"] = [
        {"index": 0, "relevance_score": 0.91},
        {"index": 1, "relevance_score": 0.73},
        {"index": 2, "relevance_score": 0.88},
    ]
    cands = [_img("A"), _img("B"), _img("C")]
    out = rank_candidates("q", cands, asset_type="image", scene_id=7, settings=_settings())
    assert [c["external_id"] for c in out] == ["A", "C", "B"]
    assert out[0]["metadata"]["jina_score"] == 0.91
    assert len(fake_jina["payloads"]) == 1
    assert fake_jina["payloads"][0]["documents"] == [
        {"image": "https://img.example/A.jpg"},
        {"image": "https://img.example/B.jpg"},
        {"image": "https://img.example/C.jpg"},
    ]


# 3 — timeout falls back to original order
def test_timeout_falls_back(fake_jina):
    fake_jina["raises"] = httpx.TimeoutException("slow")
    cands = [_img("A"), _img("B"), _img("C")]
    out = rank_candidates("q", cands, asset_type="image", scene_id=1, settings=_settings())
    assert [c["external_id"] for c in out] == ["A", "B", "C"]


# 4 — missing API key: fall back, never call Jina
def test_missing_key_falls_back(fake_jina):
    fake_jina["raises"] = AssertionError("must not call Jina without a key")
    cands = [_img("A"), _img("B")]
    out = rank_candidates("q", cands, asset_type="image", scene_id=2, settings=_settings(jina_api_key=""))
    assert [c["external_id"] for c in out] == ["A", "B"]
    assert fake_jina["payloads"] == []


# 5 — invalid candidate URLs are excluded from the request, kept in output
def test_invalid_urls_excluded_not_lost(fake_jina):
    fake_jina["results"] = [
        {"index": 0, "relevance_score": 0.4},
        {"index": 1, "relevance_score": 0.9},
    ]
    cands = [_img("A"), _img("BAD", url="not a url"), _img("NONE", url=None), _img("C")]
    out = rank_candidates("q", cands, asset_type="image", scene_id=3, settings=_settings())
    assert fake_jina["payloads"][0]["documents"] == [
        {"image": "https://img.example/A.jpg"},
        {"image": "https://img.example/C.jpg"},
    ]
    ids = [c["external_id"] for c in out]
    assert ids[:2] == ["C", "A"]  # ranked
    assert set(ids[2:]) == {"BAD", "NONE"}  # leftovers appended, nothing dropped


# 6 — exact-duplicate URLs are sent once
def test_duplicate_urls_deduped(fake_jina):
    fake_jina["results"] = [
        {"index": 0, "relevance_score": 0.5},
        {"index": 1, "relevance_score": 0.6},
    ]
    dup = "https://img.example/same.jpg"
    cands = [_img("A", url=dup), _img("B", url=dup), _img("C")]
    out = rank_candidates("q", cands, asset_type="image", scene_id=4, settings=_settings())
    assert fake_jina["payloads"][0]["documents"] == [
        {"image": dup},
        {"image": "https://img.example/C.jpg"},
    ]
    assert {c["external_id"] for c in out} == {"A", "B", "C"}


# 7 — malformed Jina response falls back
def test_malformed_response_falls_back(fake_jina):
    fake_jina["results"] = None  # -> {"results": None} -> not a usable list
    cands = [_img("A"), _img("B"), _img("C")]
    out = rank_candidates("q", cands, asset_type="image", scene_id=5, settings=_settings())
    assert [c["external_id"] for c in out] == ["A", "B", "C"]


# 8 — empty candidate list does not crash
def test_empty_candidates(fake_jina):
    out = rank_candidates("q", [], asset_type="image", scene_id=6, settings=_settings())
    assert out == []


# 9 — original metadata is preserved and augmented, not replaced
def test_metadata_preserved(fake_jina):
    fake_jina["results"] = [
        {"index": 0, "relevance_score": 0.81},
        {"index": 1, "relevance_score": 0.42},
    ]
    cands = [_img("A", photographer="Grace"), _img("B", photographer="Alan")]
    out = rank_candidates("q", cands, asset_type="image", scene_id=8, settings=_settings())
    top = out[0]
    assert top["external_id"] == "A"
    assert top["url"] == "https://img.example/A.jpg"
    assert top["license"] == "Pexels"
    assert top["metadata"]["photographer"] == "Grace"
    assert top["metadata"]["jina_score"] == 0.81


# 10 — video candidate lists pass straight through
def test_video_passthrough(fake_jina):
    fake_jina["raises"] = AssertionError("must not rank video")
    cands = [
        {"external_id": "V1", "asset_type": "video", "url": "https://v/1.mp4", "license": "Pexels", "metadata": {}},
        {"external_id": "V2", "asset_type": "video", "url": "https://v/2.mp4", "license": "Pexels", "metadata": {}},
    ]
    out = rank_candidates("q", cands, asset_type="video", scene_id=9, settings=_settings())
    assert [c["external_id"] for c in out] == ["V1", "V2"]
    assert fake_jina["payloads"] == []


# 11 — a single candidate is not worth a request
def test_single_candidate_passthrough(fake_jina):
    fake_jina["raises"] = AssertionError("must not rank a single candidate")
    cands = [_img("A")]
    out = rank_candidates("q", cands, asset_type="image", scene_id=10, settings=_settings())
    assert [c["external_id"] for c in out] == ["A"]


# detailed result carries debug/observability info on success
def test_detailed_result_shape(fake_jina):
    fake_jina["results"] = [
        {"index": 0, "relevance_score": 0.3},
        {"index": 1, "relevance_score": 0.7},
    ]
    cands = [_img("A"), _img("B")]
    res = rank_candidates_detailed("q", cands, asset_type="image", scene_id=11, settings=_settings())
    assert res.used_fallback is False
    assert res.provider == "jina"
    assert res.scores == [0.7, 0.3]
    assert {d["originalIndex"] for d in res.debug} == {0, 1}


# repeated identical (query, candidates) is served from the in-memory cache
def test_cache_hit_avoids_second_call(fake_jina):
    fake_jina["results"] = [
        {"index": 0, "relevance_score": 0.2},
        {"index": 1, "relevance_score": 0.9},
    ]
    cands = [_img("A"), _img("B")]
    s = _settings()
    first = rank_candidates("q", cands, asset_type="image", scene_id=0, settings=s)
    second = rank_candidates("q", cands, asset_type="image", scene_id=1, settings=s)
    assert [c["external_id"] for c in first] == [c["external_id"] for c in second] == ["B", "A"]
    assert len(fake_jina["payloads"]) == 1
