from __future__ import annotations

import hashlib
import logging
import random
from collections import defaultdict
from pathlib import Path

from autoedit.edit_schema import EditPlan, SfxDecision, SfxEvent
from autoedit.sfx.events import MIN_BOOKEND_DURATION, SfxCandidate, extract_candidates
from autoedit.sfx.registry import SfxMeta, load_catalog
from autoedit.sfx.timing import aligned_start

logger = logging.getLogger("autoedit")

MAX_EVENTS = 20
BOUNDARY_EPS = 0.05
WHOOSH_CHANCE = 0.02

CLICK_IDS = (
    "mixkit_camera_shutter",
    "mixkit_hard_pop_click",
    "mixkit_fast_double",
)
WHOOSH_IDS = (
    "mixkit_arrow_whoosh",
    "mixkit_cinematic_whoosh",
)


def _debug_enabled(style: dict | None) -> bool:
    if style and style.get("sfx_debug"):
        return True
    try:
        from autoedit.config import get_settings

        return bool(get_settings().sfx_debug)
    except Exception:
        return False


def _has_music(plan: EditPlan, style: dict | None, has_music: bool | None) -> bool:
    if has_music is not None:
        return has_music
    if style and style.get("music_volume", 0.18) <= 0:
        return False
    return True


def event_volume(item: SfxMeta, style: dict, has_music: bool, major: bool) -> float:
    base = float(style.get("sfx_volume", 0.32))
    if has_music:
        base = min(0.42, max(0.26, base))
    else:
        base = min(0.48, max(0.3, base))
    if item.type == "riser":
        base *= 0.9
    if major:
        base = min(0.48, base * 1.08)
    return round(max(0.22, min(0.48, base)), 3)


def _by_id(catalog: list[SfxMeta]) -> dict[str, SfxMeta]:
    return {item.id: item for item in catalog}


def pick_broll_item(
    catalog: list[SfxMeta],
    recent_ids: list[str],
    *,
    major: bool,
    first: bool,
    whoosh_chance: float,
    rng: random.Random,
) -> SfxMeta | None:
    index = _by_id(catalog)
    clicks = [index[i] for i in CLICK_IDS if i in index]
    if first and major and whoosh_chance > 0 and rng.random() < whoosh_chance:
        for wid in WHOOSH_IDS:
            if wid in index:
                return index[wid]
    if not clicks:
        return None
    last = recent_ids[-1] if recent_ids else None
    rotated = [item for item in clicks if item.id != last] or clicks
    return rotated[0]


def _occupied(t: float, accepted_times: list[float]) -> bool:
    return any(abs(t - x) < BOUNDARY_EPS for x in accepted_times)


def format_debug_log(decisions: list[SfxDecision]) -> str:
    lines = ["SFX DECISION LOG", ""]
    for d in decisions:
        mm = int(d.time // 60)
        ss = d.time - mm * 60
        stamp = f"{mm:02d}:{ss:05.2f}"
        lines.append(stamp)
        if d.accepted and d.sfx_id:
            lines.append(f"✓ {d.sfx_id}")
        else:
            lines.append("✗ no SFX")
        lines.append(f"Reason: {d.reason}")
        lines.append("")
    return "\n".join(lines).rstrip() + "\n"


def _append_event(
    *,
    accepted: list[SfxEvent],
    decisions: list[SfxDecision],
    accepted_times: list[float],
    item: SfxMeta,
    t: float,
    volume: float,
    reason: str,
    event_type: str,
    major: bool,
) -> None:
    start = aligned_start(t, item.type, item.category)
    accepted.append(
        SfxEvent(
            sfx_id=item.id,
            start=round(start, 3),
            volume=volume,
            kind="transition",
            reason=reason,
            confidence=0.9 if major else 0.8,
            duck_music=item.energy >= 0.6 or major,
        )
    )
    accepted_times.append(start)
    decisions.append(
        SfxDecision(
            time=start,
            accepted=True,
            sfx_id=item.id,
            reason=reason,
            score=1.0,
            event_type=event_type,
        )
    )


def decide_sfx(
    plan: EditPlan,
    phrases: list[dict] | None = None,
    transcript: dict | None = None,
    style: dict | None = None,
    catalog: list[SfxMeta] | None = None,
    has_music: bool | None = None,
    allow_unverified: bool | None = None,
    whoosh_chance: float | None = None,
) -> tuple[list[SfxEvent], list[SfxDecision]]:
    del allow_unverified
    style = style or {}
    items = list(catalog) if catalog is not None else load_catalog()
    music = _has_music(plan, style, has_music)
    chance = WHOOSH_CHANCE if whoosh_chance is None else float(whoosh_chance)
    candidates = extract_candidates(plan, phrases, transcript)

    pairs: dict[int, dict[str, SfxCandidate]] = defaultdict(dict)
    for cand in candidates:
        pid = int(cand.extra.get("pair_id", -1))
        pairs[pid][cand.event_type] = cand

    accepted: list[SfxEvent] = []
    decisions: list[SfxDecision] = []
    recent_ids: list[str] = []
    accepted_times: list[float] = []
    seed_src = f"{plan.tone}:{plan.music_category}:{len(plan.segments)}:{plan.video_summary}"
    rng = random.Random(int(hashlib.md5(seed_src.encode()).hexdigest()[:8], 16))

    for pid in sorted(pairs):
        if len(accepted) >= MAX_EVENTS:
            break
        group = pairs[pid]
        inn = group.get("broll_in")
        out = group.get("broll_out")
        if inn is None:
            continue
        item = pick_broll_item(
            items,
            recent_ids,
            major=inn.major,
            first=bool(inn.extra.get("first")),
            whoosh_chance=chance,
            rng=rng,
        )
        if item is None:
            decisions.append(
                SfxDecision(
                    time=inn.t,
                    accepted=False,
                    sfx_id=None,
                    reason="No shutter/click SFX in catalog",
                    score=0.0,
                    event_type="broll_in",
                )
            )
            continue

        vol = event_volume(item, style, music, inn.major)
        in_t = aligned_start(inn.t, item.type, item.category)
        if _occupied(in_t, accepted_times):
            decisions.append(
                SfxDecision(
                    time=in_t,
                    accepted=False,
                    sfx_id=item.id,
                    reason="Shared B-roll cut already has this transition SFX",
                    score=1.0,
                    event_type="broll_in",
                )
            )
        else:
            _append_event(
                accepted=accepted,
                decisions=decisions,
                accepted_times=accepted_times,
                item=item,
                t=inn.t,
                volume=vol,
                reason=inn.reason,
                event_type="broll_in",
                major=inn.major,
            )
            recent_ids.append(item.id)

        duration = float(inn.extra.get("duration") or 0)
        if out is None or duration < MIN_BOOKEND_DURATION:
            if duration < MIN_BOOKEND_DURATION:
                decisions.append(
                    SfxDecision(
                        time=inn.t + duration,
                        accepted=False,
                        sfx_id=None,
                        reason="B-roll too short for an out hit",
                        score=0.0,
                        event_type="broll_out",
                    )
                )
            continue

        out_t = aligned_start(out.t, item.type, item.category)
        if _occupied(out_t, accepted_times):
            decisions.append(
                SfxDecision(
                    time=out_t,
                    accepted=False,
                    sfx_id=item.id,
                    reason="Shared B-roll cut already has this transition SFX",
                    score=1.0,
                    event_type="broll_out",
                )
            )
            continue
        if len(accepted) >= MAX_EVENTS:
            break
        _append_event(
            accepted=accepted,
            decisions=decisions,
            accepted_times=accepted_times,
            item=item,
            t=out.t,
            volume=vol,
            reason=out.reason,
            event_type="broll_out",
            major=inn.major,
        )
        if item.id not in recent_ids[-1:]:
            recent_ids.append(item.id)

    if not accepted:
        visual = next((c for c in candidates if c.event_type == "broll_in"), None)
        if visual:
            item = pick_broll_item(
                items,
                [],
                major=True,
                first=True,
                whoosh_chance=0.0,
                rng=rng,
            )
            if item:
                _append_event(
                    accepted=accepted,
                    decisions=decisions,
                    accepted_times=accepted_times,
                    item=item,
                    t=visual.t,
                    volume=event_volume(item, style, music, True),
                    reason=f"Fallback: {visual.reason}",
                    event_type="broll_in",
                    major=True,
                )

    if _debug_enabled(style):
        logger.info("SFX debug:\n%s", format_debug_log(decisions))

    return accepted, decisions


def attach_sfx(
    plan: EditPlan,
    phrases: list[dict] | None = None,
    transcript: dict | None = None,
    style: dict | None = None,
    has_music: bool | None = None,
    log_path: Path | None = None,
    catalog: list[SfxMeta] | None = None,
    allow_unverified: bool | None = None,
) -> EditPlan:
    events, decisions = decide_sfx(
        plan,
        phrases=phrases,
        transcript=transcript,
        style=style,
        catalog=catalog,
        has_music=has_music,
        allow_unverified=allow_unverified,
    )
    updated = plan.model_copy(update={"sfx_events": events, "sfx_log": decisions})
    text = format_debug_log(decisions)
    if log_path:
        log_path.parent.mkdir(parents=True, exist_ok=True)
        log_path.write_text(text)
    logger.info("SFX engine accepted %s / considered %s", len(events), len(decisions))
    return updated


def mix_payload(plan: EditPlan, sfx_dir: Path | None = None) -> list[dict]:
    from autoedit.sfx.registry import resolve_by_id

    out: list[dict] = []
    for ev in plan.sfx_events:
        path = resolve_by_id(ev.sfx_id, sfx_dir=sfx_dir)
        if not path:
            logger.warning("Skipping SFX %s; file missing", ev.sfx_id)
            continue
        out.append(
            {
                "start": ev.start,
                "path": str(path),
                "volume": ev.volume,
                "duck": ev.duck_music,
            }
        )
    logger.info("Resolved %s/%s SFX files for mix", len(out), len(plan.sfx_events))
    return out
