from __future__ import annotations

import json
import logging
import traceback
import uuid
from datetime import datetime
from pathlib import Path

from sqlalchemy.orm import Session, joinedload
from sqlalchemy.orm.attributes import flag_modified
from sqlalchemy.exc import IntegrityError

from autoedit.config import get_settings
from autoedit.captions import phrases_from_plan_or_transcript, render_caption_pngs, write_caption_concat
from autoedit.compose import compose_final
from autoedit.drive import download_file, download_url
from autoedit.edit_schema import (
    EditPlan,
    MAX_VISUAL_ASSETS,
    STAGE_PROGRESS,
    apply_style_defaults,
    merge_style_profile,
    plan_is_weak,
)
from autoedit.image_ranking import rank_candidates
from autoedit.mentions import enforce_visual_cadence
from autoedit.music import MUSIC_IDS, choose_track
from autoedit.media import (
    extract_audio,
    extract_thumbnail,
    validate_output,
    validate_source,
    workspace_dir,
)
from autoedit.models import (
    AssetCache,
    BrollAsset,
    DriveConnection,
    EditPlan as EditPlanRow,
    LibraryAsset,
    RenderJob,
    StyleProfile,
    Transcript,
    Video,
)
from autoedit.providers import get_llm_provider, get_search_provider, get_transcription_provider
from autoedit.security import decrypt_secret, hash_file
from autoedit.sfx.engine import attach_sfx, mix_payload

logger = logging.getLogger("autoedit")

SUPPORTED = {".mp4", ".mov", ".m4v", ".webm"}


def _set_status(db: Session, video: Video, status: str, stage: str | None = None) -> None:
    video.status = status
    video.current_stage = stage or status
    video.progress = STAGE_PROGRESS.get(status, video.progress)
    video.updated_at = datetime.utcnow()
    if status != "FAILED":
        video.error_message = None
        video.failed_stage = None
    db.commit()


def fail(db: Session, video: Video, stage: str, exc: Exception) -> None:
    logger.exception("Video %s failed at %s", video.id, stage)
    video.status = "FAILED"
    video.failed_stage = stage
    video.current_stage = stage
    video.error_message = f"{stage}: {exc}"
    video.updated_at = datetime.utcnow()
    db.commit()


def get_style(db: Session, user_id) -> dict:
    row = db.query(StyleProfile).filter(StyleProfile.user_id == user_id).first()
    merged = merge_style_profile(row.profile_json if row else None)
    cap = merged.get("caption_style") or {}
    logger.info(
        "Loaded style profile user=%s saved=%s preset=%s wpl=%s music=%s",
        user_id,
        bool(row),
        cap.get("preset"),
        cap.get("words_per_line"),
        merged.get("preferred_music_category"),
    )
    return merged


def pick_music(db: Session, category: str, user_id) -> LibraryAsset | None:
    from autoedit.music import coerce_music_id

    category = coerce_music_id(category)
    q = (
        db.query(LibraryAsset)
        .filter(LibraryAsset.asset_type == "music", LibraryAsset.enabled.is_(True))
        .filter((LibraryAsset.user_id == user_id) | (LibraryAsset.is_system.is_(True)))
    )
    match = q.filter(LibraryAsset.category == category).first()
    return match or q.first()


def _transcript_payload(tx_row: Transcript | None) -> dict | None:
    if not tx_row:
        return None
    return {
        "language": tx_row.language,
        "full_text": tx_row.full_text,
        "segments": tx_row.segments_json,
    }


def _with_sfx(
    plan: EditPlan,
    phrases: list[dict],
    tx_row: Transcript | None,
    style: dict,
    ws: Path,
    has_music: bool,
) -> EditPlan:
    log_path = ws / "sfx_decisions.log"
    return attach_sfx(
        plan,
        phrases=phrases,
        transcript=_transcript_payload(tx_row),
        style=style,
        has_music=has_music,
        log_path=log_path,
    )


def process_video(db: Session, video_id: str, access_token: str | None = None) -> None:
    video = (
        db.query(Video)
        .options(joinedload(Video.project), joinedload(Video.transcript))
        .filter(Video.id == uuid.UUID(video_id))
        .first()
    )
    if not video:
        logger.error("Video %s not found", video_id)
        return

    job = RenderJob(video_id=video.id, status="QUEUED", current_stage="QUEUED", started_at=datetime.utcnow())
    db.add(job)
    db.commit()

    ws = workspace_dir(str(video.id))
    settings = get_settings()
    allowed = [settings.storage_dir.resolve(), settings.assets_dir.resolve()]

    try:
        _pipeline(db, video, job, ws, access_token, allowed)
    except Exception as exc:
        fail(db, video, video.status or video.current_stage or "UNKNOWN", exc)
        job.status = "FAILED"
        job.error_message = traceback.format_exc()[-4000:]
        job.completed_at = datetime.utcnow()
        db.commit()


def _pipeline(db: Session, video: Video, job: RenderJob, ws: Path, access_token: str | None, allowed: list[Path]) -> None:
    user_id = video.project.user_id
    style = get_style(db, user_id)
    settings = get_settings()

    def bump(status: str, stage: str) -> None:
        _set_status(db, video, status, stage)
        job.status = status
        job.current_stage = stage
        job.progress = video.progress
        db.commit()

    # Download
    source = Path(video.local_path) if video.local_path else ws / "source.mp4"
    if not source.exists():
        bump("DOWNLOADING", "Downloading source")
        if video.external_file_id:
            if not access_token:
                raise RuntimeError("Missing Google access token for download")
            download_file(access_token, video.external_file_id, source)
        elif video.source_url:
            download_url(video.source_url, source)
        else:
            raise RuntimeError("No source file id or url")
        video.local_path = str(source)
        db.commit()
    bump("DOWNLOADED", "Downloaded")

    # Probe
    if video.status in {"DOWNLOADED", "PROBING"} or not video.duration:
        bump("PROBING", "Probing media")
        info = validate_source(str(source))
        video.duration = info["duration"]
        video.width = info["width"]
        video.height = info["height"]
        video.fps = info["fps"]
        video.source_hash = hash_file(str(source))
        thumb = ws / "thumb.jpg"
        try:
            extract_thumbnail(str(source), str(thumb))
            video.thumbnail_path = str(thumb)
        except Exception:
            logger.warning("Thumbnail failed for %s", video.id)
        db.commit()

    # Transcribe (reuse by hash)
    existing_tx = None
    if video.source_hash:
        existing_tx = db.query(Transcript).filter(Transcript.source_hash == video.source_hash).first()
    if not video.transcript and existing_tx and existing_tx.video_id != video.id:
        copied = Transcript(
            video_id=video.id,
            provider=existing_tx.provider,
            language=existing_tx.language,
            full_text=existing_tx.full_text,
            segments_json=existing_tx.segments_json,
            source_hash=existing_tx.source_hash,
        )
        db.add(copied)
        db.commit()
        db.refresh(video)

    tx_row = db.query(Transcript).filter(Transcript.video_id == video.id).first()
    if not tx_row:
        bump("TRANSCRIBING", "Transcribing speech")
        audio = ws / "audio.wav"
        extract_audio(str(source), str(audio))
        result = get_transcription_provider().transcribe(str(audio))
        tx_row = Transcript(
            video_id=video.id,
            provider=get_settings().transcription_provider,
            language=result.get("language"),
            full_text=result.get("full_text") or "",
            segments_json=result.get("segments") or [],
            source_hash=video.source_hash,
        )
        db.add(tx_row)
        (ws / "transcript.json").write_text(json.dumps(result, indent=2))
        db.commit()
    bump("TRANSCRIBED", "Transcribed")

    # Plan
    latest_plan = (
        db.query(EditPlanRow).filter(EditPlanRow.video_id == video.id).order_by(EditPlanRow.version.desc()).first()
    )
    if latest_plan:
        try:
            existing = EditPlan.model_validate(latest_plan.plan_json)
            if plan_is_weak(existing):
                logger.info("Rebuilding weak edit plan for %s", video.id)
                db.delete(latest_plan)
                db.commit()
                latest_plan = None
        except Exception:
            db.delete(latest_plan)
            db.commit()
            latest_plan = None
    if not latest_plan:
        bump("PLANNING", "Generating edit plan")
        transcript_payload = {
            "language": tx_row.language,
            "full_text": tx_row.full_text,
            "segments": tx_row.segments_json,
        }
        metadata = {
            "duration": video.duration,
            "width": video.width,
            "height": video.height,
            "filename": video.filename,
        }
        plan_dict = get_llm_provider().plan_edit(transcript_payload, float(video.duration or 0), metadata, style)
        plan = EditPlan.model_validate(plan_dict)
        row = EditPlanRow(video_id=video.id, version=1, plan_json=plan.model_dump(mode="json"))
        db.add(row)
        db.commit()
        latest_plan = row

    # Always restamp the saved style profile. Reusing an old plan used to skip this,
    # so captions/music stayed on whatever the first process wrote (usually Classic).
    plan = apply_style_defaults(EditPlan.model_validate(latest_plan.plan_json), style)
    pref = style.get("preferred_music_category")
    if pref not in MUSIC_IDS:
        chosen = choose_track(
            summary=plan.video_summary,
            tone=plan.tone,
            transcript=tx_row.full_text if tx_row else "",
        )
        plan = plan.model_copy(update={"music_category": chosen})
    cap = plan.caption_style
    logger.info(
        "Applied style profile video=%s preset=%s size=%s wpl=%s music=%s captions=%s",
        video.id,
        cap.preset if cap else None,
        cap.size if cap else None,
        cap.words_per_line if cap else None,
        plan.music_category,
        plan.captions_enabled,
    )
    bump("PLAN_READY", "Edit plan ready")

    phrases = phrases_from_plan_or_transcript(
        None,
        tx_row.segments_json if isinstance(tx_row.segments_json, list) else None,
        words_per_line=plan.caption_style.words_per_line if plan.caption_style else 5,
    )
    plan = plan.model_copy(update={"caption_phrases": phrases or None})
    tx_payload = _transcript_payload(tx_row)
    plan = enforce_visual_cadence(plan, tx_payload, style)
    dumped = plan.model_dump(mode="json")
    latest_plan.plan_json = dumped
    flag_modified(latest_plan, "plan_json")
    db.commit()
    (ws / "edit_plan.json").write_text(json.dumps(dumped, indent=2))
    (ws / "caption_style.json").write_text(json.dumps((cap.model_dump(mode="json") if cap else {}), indent=2))

    broll_paths, plan = _collect_broll(db, video, plan, ws, settings, bump, refresh=True)
    dumped = plan.model_dump(mode="json")
    latest_plan.plan_json = dumped
    flag_modified(latest_plan, "plan_json")
    db.commit()
    (ws / "edit_plan.json").write_text(json.dumps(dumped, indent=2))
    _render_stage(
        db,
        video,
        job,
        ws,
        plan,
        source,
        broll_paths,
        style,
        user_id,
        allowed,
        settings,
        bump,
        phrases,
        tx_row,
        from_full_process=True,
    )


def render_video(db: Session, video_id: str, plan_json: dict | None = None) -> None:
    video = (
        db.query(Video)
        .options(joinedload(Video.project), joinedload(Video.transcript), joinedload(Video.broll_assets))
        .filter(Video.id == uuid.UUID(video_id))
        .first()
    )
    if not video:
        logger.error("Video %s not found", video_id)
        return
    job = RenderJob(video_id=video.id, status="QUEUED", current_stage="QUEUED", started_at=datetime.utcnow())
    db.add(job)
    db.commit()
    ws = workspace_dir(str(video.id))
    settings = get_settings()
    allowed = [settings.storage_dir.resolve(), settings.assets_dir.resolve()]
    try:
        user_id = video.project.user_id
        style = get_style(db, user_id)

        def bump(status: str, stage: str) -> None:
            _set_status(db, video, status, stage)
            job.status = status
            job.current_stage = stage
            job.progress = video.progress
            db.commit()

        source = Path(video.local_path) if video.local_path else ws / "source.mp4"
        if not source.exists():
            raise RuntimeError("Source file missing; run a full process first")
        if plan_json:
            plan = EditPlan.model_validate(plan_json)
            latest_plan = (
                db.query(EditPlanRow).filter(EditPlanRow.video_id == video.id).order_by(EditPlanRow.version.desc()).first()
            )
            if not latest_plan or latest_plan.plan_json != plan.model_dump(mode="json"):
                version = (latest_plan.version + 1) if latest_plan else 1
                latest_plan = EditPlanRow(video_id=video.id, version=version, plan_json=plan.model_dump(mode="json"))
                db.add(latest_plan)
                db.commit()
        else:
            latest_plan = (
                db.query(EditPlanRow).filter(EditPlanRow.video_id == video.id).order_by(EditPlanRow.version.desc()).first()
            )
            if not latest_plan:
                raise RuntimeError("No edit plan to render")
            plan = EditPlan.model_validate(latest_plan.plan_json)
        logger.info(
            "Rendering %s with caption preset=%s active=%s font=%s size=%s",
            video.id,
            plan.caption_style.preset,
            plan.caption_style.active_color,
            plan.caption_style.font,
            plan.caption_style.size,
        )
        (ws / "caption_style.json").write_text(json.dumps(plan.caption_style.model_dump(mode="json"), indent=2))
        tx_row = db.query(Transcript).filter(Transcript.video_id == video.id).first()
        phrases = phrases_from_plan_or_transcript(
            [p.model_dump() for p in (plan.caption_phrases or [])] if plan.caption_phrases else None,
            tx_row.segments_json if tx_row and isinstance(tx_row.segments_json, list) else None,
            words_per_line=plan.caption_style.words_per_line if plan.caption_style else 5,
        )
        broll_paths = _broll_from_existing(video, plan)
        bump("RENDERING", "Rendering from editor")
        _render_stage(
            db,
            video,
            job,
            ws,
            plan,
            source,
            broll_paths,
            style,
            user_id,
            allowed,
            settings,
            bump,
            phrases,
            tx_row,
        )
    except Exception as exc:
        fail(db, video, video.status or video.current_stage or "RENDERING", exc)
        job.status = "FAILED"
        job.error_message = traceback.format_exc()[-4000:]
        job.completed_at = datetime.utcnow()
        db.commit()


def _broll_from_existing(video: Video, plan: EditPlan) -> list[tuple[float, float, str, str]]:
    unused = list(video.broll_assets or [])
    paths: list[tuple[float, float, str, str]] = []
    for seg in plan.segments:
        if seg.visual != "broll" or not seg.broll_query:
            continue
        match = next((a for a in unused if a.query == seg.broll_query and a.local_path), None)
        if not match:
            match = next((a for a in unused if a.local_path), None)
        if not match or not Path(match.local_path).exists():
            continue
        unused.remove(match)
        paths.append((seg.start, seg.end, match.local_path, match.asset_type or "video"))
    return paths[:MAX_VISUAL_ASSETS]


def _collect_broll(
    db: Session,
    video: Video,
    plan: EditPlan,
    ws: Path,
    settings,
    bump,
    refresh: bool,
) -> tuple[list[tuple[float, float, str, str]], EditPlan]:
    bump("SEARCHING_BROLL", "Searching B-roll")
    if refresh:
        db.query(BrollAsset).filter(BrollAsset.video_id == video.id).delete()
        db.commit()
    searcher = get_search_provider()
    broll_paths: list[tuple[float, float, str, str]] = []

    rerank_images = bool(settings.enable_jina_reranker)
    for idx, seg in enumerate(plan.segments):
        if seg.visual != "broll" or not seg.broll_query:
            continue
        if len(broll_paths) >= MAX_VISUAL_ASSETS:
            break
        want = seg.broll_type or "video"
        cache_key = f"pexels:{want}:{seg.broll_query.lower().strip()}"
        cached = db.query(AssetCache).filter(AssetCache.cache_key == cache_key).first()
        local = None
        asset_type = want
        source_url = None
        external_id = None
        pick_meta = None
        if cached and cached.local_path and Path(cached.local_path).exists():
            local = cached.local_path
            asset_type = (cached.payload_json or {}).get("asset_type", want)
            pick_meta = (cached.payload_json or {}).get("metadata")
        else:
            img_limit = settings.jina_max_candidates if rerank_images else None
            results = searcher.search(
                seg.broll_query, want, "portrait",
                limit=img_limit if want == "image" else None,
            )
            if not results and want == "video":
                results = searcher.search(seg.broll_query, "image", "portrait", limit=img_limit)
            if not results:
                logger.warning("No B-roll for query %s", seg.broll_query)
                continue
            results = rank_candidates(
                seg.broll_query,
                results,
                asset_type=results[0]["asset_type"],
                scene_id=idx,
                settings=settings,
            )
            pick = results[0]
            asset_type = pick["asset_type"]
            source_url = pick["url"]
            external_id = pick.get("external_id")
            pick_meta = pick.get("metadata")
            dest = ws / "assets" / f"{external_id or uuid.uuid4()}.{ 'jpg' if asset_type == 'image' else 'mp4' }"
            cache_dir = settings.storage_dir / "broll-cache"
            cache_dir.mkdir(parents=True, exist_ok=True)
            dest = cache_dir / dest.name
            if not dest.exists():
                download_url(source_url, dest)
            local = str(dest)
            try:
                db.add(
                    AssetCache(
                        cache_key=cache_key,
                        provider="pexels",
                        payload_json=pick,
                        local_path=local,
                    )
                )
                db.commit()
            except IntegrityError:
                db.rollback()
        db.add(
            BrollAsset(
                video_id=video.id,
                provider="pexels",
                external_id=external_id,
                asset_type=asset_type,
                query=seg.broll_query,
                source_url=source_url,
                local_path=local,
                license_info="Pexels",
                # Only persisted when the Jina reranker actually scored this pick;
                # otherwise left NULL exactly as before.
                metadata_json=pick_meta if (pick_meta and "jina_score" in pick_meta) else None,
            )
        )
        broll_paths.append((seg.start, seg.end, local, asset_type))
    db.commit()
    bump("BROLL_READY", "B-roll ready")
    return broll_paths[:MAX_VISUAL_ASSETS], plan


def _render_stage(
    db: Session,
    video: Video,
    job: RenderJob,
    ws: Path,
    plan: EditPlan,
    source: Path,
    broll_paths: list[tuple[float, float, str, str]],
    style: dict,
    user_id,
    allowed: list[Path],
    settings,
    bump,
    phrases: list[dict],
    tx_row: Transcript | None = None,
    from_full_process: bool = False,
) -> None:
    bump("RENDERING", "Rendering final video")
    music = pick_music(db, plan.music_category, user_id)
    plan = _with_sfx(plan, phrases, tx_row, style, ws, has_music=bool(music and music.local_path))
    latest_plan = (
        db.query(EditPlanRow).filter(EditPlanRow.video_id == video.id).order_by(EditPlanRow.version.desc()).first()
    )
    if latest_plan:
        latest_plan.plan_json = plan.model_dump(mode="json")
        db.commit()
    (ws / "edit_plan.json").write_text(json.dumps(plan.model_dump(mode="json"), indent=2))
    sfx_events = mix_payload(plan)
    logger.info("Render %s mixing %s SFX", video.id, len(sfx_events))

    caption_concat: str | None = None
    if plan.captions_enabled and phrases:
        caption_overlays = render_caption_pngs(
            phrases,
            ws / "captions",
            float(video.duration or 0),
            enabled=True,
            style=plan.caption_style.model_dump(mode="json"),
        )
        caption_concat = write_caption_concat(caption_overlays, ws / "captions", float(video.duration or 0))
        if not caption_concat:
            logger.warning("Captions enabled but no overlay frames were generated")

    output = ws / "final.mp4"
    compose_final(
        source_path=str(source),
        output_path=str(output),
        plan=plan,
        duration=float(video.duration or 0),
        broll_paths=broll_paths[:MAX_VISUAL_ASSETS],
        music_path=music.local_path if music else None,
        sfx_events=sfx_events,
        style=style,
        allowed_roots=allowed + [ws, settings.storage_dir / "broll-cache"],
        caption_concat_path=caption_concat,
    )
    bump("RENDERED", "Rendered")

    bump("VALIDATING", "Validating output")
    validate_output(str(output), expect_audio=True)
    job.output_path = str(output)
    job.status = "READY"
    job.progress = 100
    job.completed_at = datetime.utcnow()
    video.local_path = str(source)
    bump("READY", "Ready")
    from autoedit.youtube import enqueue_youtube_if_needed

    enqueue_youtube_if_needed(db, video, from_full_process=from_full_process)
    for leftover in (ws / "audio.wav", ws / "intermediate"):
        if leftover.is_file():
            leftover.unlink(missing_ok=True)
        elif leftover.is_dir():
            import shutil

            shutil.rmtree(leftover, ignore_errors=True)
    logger.info("Video %s ready at %s", video.id, output)
