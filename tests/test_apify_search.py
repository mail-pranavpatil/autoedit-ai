import httpx
import pytest

from autoedit.providers import ApifyImageSearch


class _Resp:
    def __init__(self, payload, status=200):
        self._payload = payload
        self.status_code = status

    def raise_for_status(self):
        if self.status_code >= 400:
            raise httpx.HTTPStatusError("boom", request=None, response=None)

    def json(self):
        return self._payload


DATASET = [
    {"searchQuery": "stripe dashboard", "imageUrl": "https://a.example/1.jpg", "width": 1600, "height": 900, "title": "t1"},
    {"searchQuery": "stripe dashboard", "image": "https://a.example/2.png", "width": 1200, "height": 1600},
    {"searchQuery": "gaming pc setup", "imageUrl": "https://b.example/3.jpg", "width": 1920, "height": 1080},
    {"searchQuery": "gaming pc setup", "imageUrl": "https://b.example/tiny.jpg", "width": 100, "height": 80},  # dropped
    {"searchQuery": "gaming pc setup", "imageUrl": "ftp://nope/x.jpg"},  # dropped: scheme
]


def test_search_many_partitions_and_maps(monkeypatch):
    seen = {}

    def fake_post(url, params=None, json=None, timeout=None):
        seen["url"] = url
        seen["input"] = json
        return _Resp(DATASET)

    monkeypatch.setattr(httpx, "post", fake_post)
    prov = ApifyImageSearch(token="tok", actor="acme~scraper")
    out = prov.search_many(["Stripe Dashboard", "gaming pc setup", "stripe dashboard"])

    assert set(out) == {"stripe dashboard", "gaming pc setup"}  # deduped, lowercased
    assert [c["url"] for c in out["stripe dashboard"]] == [
        "https://a.example/1.jpg",
        "https://a.example/2.png",
    ]
    assert [c["url"] for c in out["gaming pc setup"]] == ["https://b.example/3.jpg"]  # tiny + ftp dropped
    c = out["stripe dashboard"][0]
    assert c["asset_type"] == "image"
    assert c["license"] == "web:google-images"
    assert c["metadata"]["width"] == 1600 and c["metadata"]["title"] == "t1"
    assert "google-images-scraper" not in seen["url"] or "acme" in seen["url"]
    assert seen["input"]["queries"] == ["stripe dashboard", "gaming pc setup"]


def test_no_token_is_noop(monkeypatch):
    called = []
    monkeypatch.setattr(httpx, "post", lambda *a, **k: called.append(1))
    out = ApifyImageSearch(token="").search_many(["anything"])
    assert out == {"anything": []}
    assert called == []


def test_http_failure_returns_empty(monkeypatch):
    def boom(*a, **k):
        raise httpx.ConnectError("down")

    monkeypatch.setattr(httpx, "post", boom)
    out = ApifyImageSearch(token="tok").search_many(["q1", "q2"])
    assert out == {"q1": [], "q2": []}


def test_single_query_attributes_unlabelled_items(monkeypatch):
    payload = [{"imageUrl": "https://x.example/a.jpg"}, {"imageUrl": "https://x.example/b.jpg"}]
    monkeypatch.setattr(httpx, "post", lambda *a, **k: _Resp(payload))
    out = ApifyImageSearch(token="tok").search_many(["only one"])
    assert len(out["only one"]) == 2
