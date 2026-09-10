from __future__ import annotations

import hashlib
import json
import logging

import httpx
from openai import OpenAI

from autoedit.config import get_settings
from autoedit.edit_schema import EditPlan, merge_style_profile

logger = logging.getLogger("autoedit")


class TranscriptionProvider:
    def transcribe(self, audio_path: str) -> dict:
        raise NotImplementedError


class LLMProvider:
    def plan_edit(self, transcript: dict, duration: float, metadata: dict, style: dict) -> dict:
        raise NotImplementedError


class AssetSearchProvider:
    def search(
        self,
        query: str,
        asset_type: str,
        orientation: str,
        limit: int | None = None,
    ) -> list[dict]:
        raise NotImplementedError


class OpenAITranscription(TranscriptionProvider):
    def transcribe(self, audio_path: str) -> dict:
        settings = get_settings()
        client = OpenAI(api_key=settings.openai_api_key)
        with open(audio_path, "rb") as f:
            result = client.audio.transcriptions.create(
                model="whisper-1",
                file=f,
                response_format="verbose_json",
                timestamp_granularities=["word", "segment"],
            )
        top_words = _coerce_words(getattr(result, "words", None))
        segments = []
        for seg in getattr(result, "segments", None) or []:
            if isinstance(seg, dict):
                item = {
                    "start": float(seg.get("start", 0)),
                    "end": float(seg.get("end", 0)),
                    "text": str(seg.get("text", "")).strip(),
                    "words": _coerce_words(seg.get("words")),
                }
            else:
                item = {
                    "start": float(getattr(seg, "start", 0)),
                    "end": float(getattr(seg, "end", 0)),
                    "text": str(getattr(seg, "text", "")).strip(),
                    "words": _coerce_words(getattr(seg, "words", None)),
                }
            if not item["words"] and top_words:
                item["words"] = [
                    w
                    for w in top_words
                    if w["start"] >= item["start"] - 0.05 and w["end"] <= item["end"] + 0.05
                ]
            segments.append(item)
        text = getattr(result, "text", "") or " ".join(s["text"] for s in segments)
        language = getattr(result, "language", "en")
        return {"language": language, "full_text": text, "segments": segments}


def _coerce_words(raw) -> list[dict]:
    words = []
    for item in raw or []:
        if isinstance(item, dict):
            text = str(item.get("word") or item.get("text") or "").strip()
            if not text:
                continue
            words.append(
                {
                    "text": text,
                    "start": float(item.get("start") or 0),
                    "end": float(item.get("end") or 0),
                }
            )
        else:
            text = str(getattr(item, "word", None) or getattr(item, "text", "") or "").strip()
            if not text:
                continue
            words.append(
                {
                    "text": text,
                    "start": float(getattr(item, "start", 0) or 0),
                    "end": float(getattr(item, "end", 0) or 0),
                }
            )
    return words


class OpenAILLM(LLMProvider):
    def plan_edit(self, transcript: dict, duration: float, metadata: dict, style: dict) -> dict:
        settings = get_settings()
        client = OpenAI(api_key=settings.openai_api_key)
        style = merge_style_profile(style)
        cap = style.get("caption_style") or {}
        freq = str(style.get("broll_frequency") or "medium")
        cadence = {"high": 2.0, "low": 3.5}.get(freq, 2.5)
        try:
            cadence = float(style.get("visual_cadence_seconds") or cadence)
        except (TypeError, ValueError):
            pass
        cadence = min(4.0, max(1.6, cadence))
        broll_n = max(2, int(duration // cadence))
        preferred = style.get("preferred_music_category")
        if preferred:
            preferred_music = f"User pinned track: {preferred}. Set music_category to {preferred}."
        else:
            preferred_music = (
                "Choose exactly one of thank_you | cornfield_chase | feeling_blue using emotion, "
                "story arc, pacing, and ending — not topic. thank_you = gratitude/milestone/warm payoff. "
                "cornfield_chase = cinematic stakes/reveal only (never just because the topic is AI). "
                "feeling_blue = calm, reflective, educational, general-purpose default. "
                "One track for the whole reel."
            )
        effects = style.get("effects") or {}
        allowed_fx = []
        if effects.get("zoom", True):
            allowed_fx += ["slow_zoom_in", "slow_zoom_out"]
        if effects.get("pan", True):
            allowed_fx += ["pan_left", "pan_right", "pan_up", "pan_down"]
        if effects.get("fade", True):
            allowed_fx += ["fade_in", "fade_out"]
        if not allowed_fx:
            allowed_fx = ["none"]
        broll_type_pref = style.get("broll_type") or "both"
        if broll_type_pref == "images":
            broll_type_rule = 'For broll segments set broll_type to "image".'
        elif broll_type_pref == "video":
            broll_type_rule = 'For broll segments set broll_type to "video".'
        else:
            broll_type_rule = 'For broll segments set broll_type to "video" (preferred) or "image", never null.'
        prompt = f"""You are an edit planner for vertical talking-head social videos.
Return ONLY JSON matching the EditPlan schema. Never include shell commands, URLs, file paths, or credentials.

CRITICAL JSON RULES:
- Use JSON null, never the string "null".
- For talking_head segments set broll_query and broll_type to null (JSON null).
- {broll_type_rule}
- sfx on segments must be JSON null. Sound design is applied later by the SFX engine, not this plan.

JSON shape:
{{
  "video_summary": "string",
  "tone": "string",
  "music_category": "thank_you|cornfield_chase|feeling_blue",
  "segments": [
    {{
      "start": 0,
      "end": 4.5,
      "visual": "talking_head",
      "broll_query": null,
      "broll_type": null,
      "effect": "slow_zoom_in",
      "sfx": null
    }},
    {{
      "start": 4.5,
      "end": 8.0,
      "visual": "broll",
      "broll_query": "ancient indian scriptures book",
      "broll_type": "video",
      "effect": "fade_in",
      "sfx": null
    }}
  ]
}}

USER STYLE DEFAULTS (follow these for every edit):
- Visual cadence: about every {cadence:.1f}s ({freq}). Include about {broll_n} full-screen broll cuts of 2–3 seconds each in a {duration:.0f}s video. Alternate ~2–3s talking_head and ~2–3s broll. Leave talking-head beats for product/screenshot overlay cards. Do not leave talking-head uncovered for more than 3 seconds.
- Preferred music category: {preferred_music}.
- Allowed motion effects: {", ".join(allowed_fx)}. Do not use others.
- Captions: {"on" if style.get("captions_enabled", True) else "off"}; words per line = {cap.get("words_per_line", 5)}; preset = {cap.get("preset", "classic")}.

Editing rules (the finished video must NOT look like the raw clip):
- Alternate talking_head and broll on a 2–3 second rhythm.
- Keep at least 1.2s of talking-head between full-screen B-roll cuts.
- Talking-head segments should use slow_zoom_in or slow_zoom_out when zoom is allowed, not "none".
- Do not assign sound effects. Leave every segment sfx as JSON null.
- B-roll queries must be short stock-search phrases like "india temple" or "person journaling".
- Segments must cover 0 to {duration:.2f} without overlapping.

Duration seconds: {duration}
Metadata: {json.dumps(metadata)}
Style profile: {json.dumps(style)}
Transcript: {json.dumps(transcript)[:12000]}
"""
        response = client.chat.completions.create(
            model=settings.llm_model,
            temperature=0.3,
            response_format={"type": "json_object"},
            messages=[
                {"role": "system", "content": "You output strictly valid EditPlan JSON."},
                {"role": "user", "content": prompt},
            ],
        )
        raw = response.choices[0].message.content or "{}"
        data = json.loads(raw)
        plan = EditPlan.model_validate(data)
        return plan.model_dump()


class PexelsSearch(AssetSearchProvider):
    def search(
        self,
        query: str,
        asset_type: str,
        orientation: str = "portrait",
        limit: int | None = None,
    ) -> list[dict]:
        settings = get_settings()
        if not settings.pexels_api_key:
            logger.warning("PEXELS_API_KEY missing; returning empty search")
            return []
        headers = {"Authorization": settings.pexels_api_key}
        with httpx.Client(timeout=30) as client:
            if asset_type == "image":
                per_page = min(limit or 8, 80)  # Pexels caps per_page at 80
                resp = client.get(
                    "https://api.pexels.com/v1/search",
                    headers=headers,
                    params={"query": query, "orientation": orientation, "per_page": per_page},
                )
                resp.raise_for_status()
                photos = resp.json().get("photos") or []
                return [
                    {
                        "external_id": str(p["id"]),
                        "asset_type": "image",
                        "url": p.get("src", {}).get("portrait") or p.get("src", {}).get("large"),
                        "license": "Pexels",
                        "metadata": {"photographer": p.get("photographer")},
                    }
                    for p in photos
                    if p.get("src")
                ]
            resp = client.get(
                "https://api.pexels.com/videos/search",
                headers=headers,
                params={"query": query, "orientation": orientation, "per_page": 8},
            )
            resp.raise_for_status()
            videos = resp.json().get("videos") or []
            results = []
            for v in videos:
                files = sorted(v.get("video_files") or [], key=lambda f: f.get("width") or 0)
                file = next((f for f in reversed(files) if (f.get("width") or 0) <= 1920), files[-1] if files else None)
                if not file:
                    continue
                results.append(
                    {
                        "external_id": str(v["id"]),
                        "asset_type": "video",
                        "url": file.get("link"),
                        "license": "Pexels",
                        "metadata": {"duration": v.get("duration")},
                    }
                )
            return results


APIFY_DATASET_URL = "https://api.apify.com/v2/acts/{actor}/run-sync-get-dataset-items"

_ITEM_URL_KEYS = ("imageUrl", "image", "url", "src", "link", "contentUrl", "original")
_ITEM_QUERY_KEYS = ("searchQuery", "query", "keyword", "search", "term")
_ITEM_W_KEYS = ("width", "imageWidth", "originalWidth")
_ITEM_H_KEYS = ("height", "imageHeight", "originalHeight")
_IMG_EXTS = (".jpg", ".jpeg", ".png", ".webp", ".gif", ".bmp", ".tiff")
# Not real image files - crawler/proxy endpoints Google Images sometimes returns.
# The Jina reranker 400s the whole batch if any one URL is unfetchable.
_URL_DENY = ("lookaside.", "/crawler", "/seo/", "gstatic.com/images?", "google.com/imgres")
# Paid-stock / agency hosts: hotlinks return a watermarked preview or an
# "Access Restricted" block page served *as an image*, which passes decode checks
# but is garbage on screen. Skip them entirely.
_STOCK_DENY = (
    "vectorstock.com", "shutterstock.com", "istockphoto.com", "gettyimages.",
    "dreamstime.com", "alamy.com", "123rf.com", "depositphotos.com",
    "stock.adobe.com", "adobestock", "bigstockphoto.com", "canstockphoto.com",
    "agefotostock.com", "picfair.com", "pond5.com",
)


def _looks_like_image_url(url: str) -> bool:
    low = url.lower()
    if any(bad in low for bad in _URL_DENY) or any(host in low for host in _STOCK_DENY):
        return False
    path = url.split("?", 1)[0].split("#", 1)[0].lower()
    if path.endswith(_IMG_EXTS):
        return True
    # No extension is fine only when there's no query string (e.g. lh3.googleusercontent.com/...)
    return "?" not in url


def _first(item: dict, keys) -> object | None:
    for k in keys:
        v = item.get(k)
        if v:
            return v
    return None


class ApifyImageSearch(AssetSearchProvider):
    """Real web images via an Apify Google-Images-scraper Actor.

    One Actor run per call handles many queries at once (a scrape run takes tens
    of seconds, so per-query calls are not viable). Output dicts match the shape
    ``PexelsSearch`` returns and the Jina reranker expects.
    """

    name = "apify"

    def __init__(self, token: str | None = None, actor: str | None = None, timeout: float | None = None) -> None:
        s = get_settings()
        self._token = token if token is not None else s.apify_api_token
        self._actor = actor or s.apify_image_actor
        self._timeout = float(timeout if timeout is not None else s.apify_timeout_seconds)

    # -- input/output seam: adjust here if the Actor's schema differs -------------
    def _build_input(self, queries: list[str], per_query: int) -> dict:
        return {
            "queries": list(queries),
            "maxImagesPerQuery": per_query,
            "maxResultsPerQuery": per_query,
            "resultsPerPage": per_query,
            "downloadImages": False,
            "saveImages": False,
        }

    def _map_item(self, item: dict) -> dict | None:
        if not isinstance(item, dict):
            return None
        url = _first(item, _ITEM_URL_KEYS)
        if not isinstance(url, str) or not url.startswith(("http://", "https://")):
            return None
        if not _looks_like_image_url(url):
            return None
        w = _first(item, _ITEM_W_KEYS)
        h = _first(item, _ITEM_H_KEYS)
        try:
            w = int(w) if w is not None else None
            h = int(h) if h is not None else None
        except (TypeError, ValueError):
            w = h = None
        if w and h and min(w, h) < 500:
            return None
        return {
            "external_id": hashlib.sha1(url.encode("utf-8")).hexdigest()[:16],
            "asset_type": "image",
            "url": url,
            "license": "web:google-images",
            "metadata": {
                "source": item.get("source") or item.get("displayedUrl") or item.get("sourceUrl"),
                "title": item.get("title"),
                "width": w,
                "height": h,
            },
        }
    # --------------------------------------------------------------------------

    def _item_query(self, item: dict) -> str | None:
        q = _first(item, _ITEM_QUERY_KEYS)
        return q.strip().lower() if isinstance(q, str) and q.strip() else None

    def search_many(self, queries: list[str], per_query: int | None = None) -> dict[str, list[dict]]:
        norm = []
        seen = set()
        for q in queries:
            key = (q or "").strip().lower()
            if key and key not in seen:
                seen.add(key)
                norm.append(key)
        out: dict[str, list[dict]] = {q: [] for q in norm}
        if not norm or not self._token:
            if not self._token:
                logger.warning("APIFY_API_TOKEN missing; skipping web image search")
            return out
        per_query = per_query or get_settings().apify_results_per_query
        try:
            resp = httpx.post(
                APIFY_DATASET_URL.format(actor=self._actor),
                params={"token": self._token, "timeout": int(self._timeout)},
                json=self._build_input(norm, per_query),
                timeout=self._timeout + 15,
            )
            resp.raise_for_status()
            items = resp.json()
        except Exception as exc:  # noqa: BLE001 - a scrape failure must not break rendering
            logger.warning("Apify image search failed: %s", exc)
            return out
        if not isinstance(items, list):
            return out
        single = norm[0] if len(norm) == 1 else None
        for raw in items:
            mapped = self._map_item(raw)
            if not mapped:
                continue
            q = self._item_query(raw) or single
            if q in out:
                out[q].append(mapped)
            elif single:
                out[single].append(mapped)
        logger.info(
            "[APIFY_IMAGES] queries=%d results=%d",
            len(norm),
            sum(len(v) for v in out.values()),
        )
        return out

    def search(self, query: str, asset_type: str, orientation: str = "portrait", limit: int | None = None) -> list[dict]:
        return self.search_many([query], limit).get(query.strip().lower(), [])


def get_transcription_provider() -> TranscriptionProvider:
    return OpenAITranscription()


def get_llm_provider() -> LLMProvider:
    return OpenAILLM()


def get_search_provider() -> AssetSearchProvider:
    return PexelsSearch()


def get_image_search_provider() -> AssetSearchProvider:
    """Web images (Apify) when configured, else fall back to Pexels stock images."""
    if get_settings().apify_api_token:
        return ApifyImageSearch()
    return PexelsSearch()
