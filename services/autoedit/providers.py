from __future__ import annotations

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


def get_transcription_provider() -> TranscriptionProvider:
    return OpenAITranscription()


def get_llm_provider() -> LLMProvider:
    return OpenAILLM()


def get_search_provider() -> AssetSearchProvider:
    return PexelsSearch()
