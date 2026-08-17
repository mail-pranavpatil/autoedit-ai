from __future__ import annotations

import json
import logging
import httpx
from openai import OpenAI

from autoedit.config import get_settings
from autoedit.edit_schema import DEFAULT_STYLE_PROFILE, EditPlan

logger = logging.getLogger("autoedit")


class TranscriptionProvider:
    def transcribe(self, audio_path: str) -> dict:
        raise NotImplementedError


class LLMProvider:
    def plan_edit(self, transcript: dict, duration: float, metadata: dict, style: dict) -> dict:
        raise NotImplementedError


class AssetSearchProvider:
    def search(self, query: str, asset_type: str, orientation: str) -> list[dict]:
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
        style = {**DEFAULT_STYLE_PROFILE, **(style or {})}
        prompt = f"""You are an edit planner for vertical talking-head social videos.
Return ONLY JSON matching the EditPlan schema. Never include shell commands, URLs, file paths, or credentials.

CRITICAL JSON RULES:
- Use JSON null, never the string "null".
- For talking_head segments set broll_query and broll_type to null (JSON null).
- For broll segments set broll_type to "video" (preferred) or "image", never null.
- sfx must be a name from the enum or JSON null, never the string "null".

JSON shape:
{{
  "video_summary": "string",
  "tone": "string",
  "music_category": "energetic|technology|cinematic|motivational|chill",
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
      "sfx": "whoosh"
    }}
  ]
}}

Editing rules (the finished video must NOT look like the raw clip):
- Alternate talking_head and broll. For a {duration:.0f}s video, include at least {max(2, int(duration // 6))} broll segments of 2.5–5 seconds each.
- Do not cover the entire video with B-roll. Keep the speaker visible often.
- Talking-head segments should use slow_zoom_in or slow_zoom_out, not "none".
- Put a whoosh or pop sfx at most B-roll starts.
- B-roll queries must be short stock-search phrases like "india temple" or "person journaling".
- Music category from the enum, matching tone.
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
    def search(self, query: str, asset_type: str, orientation: str = "portrait") -> list[dict]:
        settings = get_settings()
        if not settings.pexels_api_key:
            logger.warning("PEXELS_API_KEY missing; returning empty search")
            return []
        headers = {"Authorization": settings.pexels_api_key}
        with httpx.Client(timeout=30) as client:
            if asset_type == "image":
                resp = client.get(
                    "https://api.pexels.com/v1/search",
                    headers=headers,
                    params={"query": query, "orientation": orientation, "per_page": 8},
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


def get_transcription_provider() -> TranscriptionProvider:
    return OpenAITranscription()


def get_llm_provider() -> LLMProvider:
    return OpenAILLM()


def get_search_provider() -> AssetSearchProvider:
    return PexelsSearch()
