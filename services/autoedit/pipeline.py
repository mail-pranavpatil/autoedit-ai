from __future__ import annotations

import json
import logging
import traceback
import uuid
from datetime import datetime
from pathlib import Path

from sqlalchemy.orm import Session, joinedload
from sqlalchemy.exc import IntegrityError

from autoedit.config import get_settings
from autoedit.captions import build_caption_overlay_video, phrases_from_plan_or_transcript
from autoedit.compose import compose_final
from autoedit.drive import download_file, download_url
from autoedit.edit_schema import DEFAULT_STYLE_PROFILE, EditPlan, STAGE_PROGRESS, plan_is_weak
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
    if not row:
        return dict(DEFAULT_STYLE_PROFILE)
    return {**DEFAULT_STYLE_PROFILE, **(row.profile_json or {})}


def pick_music(db: Session, category: str, user_id) -> LibraryAsset | None:
    q = (
        db.query(LibraryAsset)
        .filter(LibraryAsset.asset_type == "music", LibraryAsset.enabled.is_(True))
        .filter((LibraryAsset.user_id == user_id) | (LibraryAsset.is_system.is_(True)))
    )
    match = q.filter(LibraryAsset.category == category).first()
    return match or q.first()


def sfx_path(db: Session, name: str, user_id) -> str | None:
    row = (
        db.query(LibraryAsset)
        .filter(
            LibraryAsset.asset_type == "sfx",
            LibraryAsset.enabled.is_(True),
            LibraryAsset.name == name,
        )
        .filter((LibraryAsset.user_id == user_id) | (LibraryAsset.is_system.is_(True)))
        .first()
    )
    return row.local_path if row else None


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
        row = EditPlanRow(video_id=video.id, version=1, plan_json=plan.model_dump())
        db.add(row)
        (ws / "edit_plan.json").write_text(json.dumps(plan.model_dump(), indent=2))
        db.commit()
        latest_plan = row
    plan = EditPlan.model_validate(latest_plan.plan_json)
    bump("PLAN_READY", "Edit plan ready")

    phrases = phrases_from_plan_or_transcript(
        [p.model_dump() for p in (plan.caption_phrases or [])] if plan.caption_phrases else None,
        tx_row.segments_json if isinstance(tx_row.segments_json, list) else None,
        words_per_line=plan.caption_style.words_per_line if plan.caption_style else 5,
    )
    if phrases and not plan.caption_phrases:
        plan = plan.model_copy(update={"caption_phrases": phrases})
        latest_plan.plan_json = plan.model_dump()
        db.commit()
        (ws / "edit_plan.json").write_text(json.dumps(plan.model_dump(), indent=2))

    broll_paths = _collect_broll(db, video, plan, ws, settings, bump, refresh=True)
    _render_stage(db, video, job, ws, plan, source, broll_paths, style, user_id, allowed, settings, bump, phrases)


def render_video(db: Session, video_id: str) -> None:
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
        latest_plan = (
            db.query(EditPlanRow).filter(EditPlanRow.video_id == video.id).order_by(EditPlanRow.version.desc()).first()
        )
        if not latest_plan:
            raise RuntimeError("No edit plan to render")
        plan = EditPlan.model_validate(latest_plan.plan_json)
        tx_row = db.query(Transcript).filter(Transcript.video_id == video.id).first()
        phrases = phrases_from_plan_or_transcript(
            [p.model_dump() for p in (plan.caption_phrases or [])] if plan.caption_phrases else None,
            tx_row.segments_json if tx_row and isinstance(tx_row.segments_json, list) else None,
            words_per_line=plan.caption_style.words_per_line if plan.caption_style else 5,
        )
        broll_paths = _broll_from_existing(video, plan)
        bump("RENDERING", "Rendering from editor")
        _render_stage(db, video, job, ws, plan, source, broll_paths, style, user_id, allowed, settings, bump, phrases)
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
    return paths[:8]


def _collect_broll(
    db: Session,
    video: Video,
    plan: EditPlan,
    ws: Path,
    settings,
    bump,
    refresh: bool,
) -> list[tuple[float, float, str, str]]:
    bump("SEARCHING_BROLL", "Searching B-roll")
    if refresh:
        db.query(BrollAsset).filter(BrollAsset.video_id == video.id).delete()
        db.commit()
    searcher = get_search_provider()
    broll_paths: list[tuple[float, float, str, str]] = []
    for seg in plan.segments:
        if seg.visual != "broll" or not seg.broll_query:
            continue
        want = seg.broll_type or "video"
        cache_key = f"pexels:{want}:{seg.broll_query.lower().strip()}"
        cached = db.query(AssetCache).filter(AssetCache.cache_key == cache_key).first()
        local = None
        asset_type = want
        source_url = None
        external_id = None
        if cached and cached.local_path and Path(cached.local_path).exists():
            local = cached.local_path
            asset_type = (cached.payload_json or {}).get("asset_type", want)
        else:
            results = searcher.search(seg.broll_query, want, "portrait")
            if not results and want == "video":
                results = searcher.search(seg.broll_query, "image", "portrait")
            if not results:
                logger.warning("No B-roll for query %s", seg.broll_query)
                continue
            pick = results[0]
            asset_type = pick["asset_type"]
            source_url = pick["url"]
            external_id = pick.get("external_id")
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
            )
        )
        broll_paths.append((seg.start, seg.end, local, asset_type))
    db.commit()
    bump("BROLL_READY", "B-roll ready")
    return broll_paths[:8]


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
) -> None:
    bump("RENDERING", "Rendering final video")
    music = pick_music(db, plan.music_category, user_id)
    sfx_events: list[tuple[float, str]] = []
    for seg in plan.segments:
        if not seg.sfx:
            continue
        path = sfx_path(db, seg.sfx, user_id)
        if path and Path(path).exists():
            sfx_events.append((seg.start, path))

    caption_video = None
    if plan.captions_enabled and phrases:
        try:
            caption_video = build_caption_overlay_video(
                phrases,
                ws / "captions",
                float(video.duration or 0),
                enabled=True,
                style=plan.caption_style,
            )
        except Exception:
            logger.exception("Caption overlay video failed; rendering without burned captions")

    output = ws / "final.mp4"
    compose_final(
        source_path=str(source),
        output_path=str(output),
        plan=plan,
        duration=float(video.duration or 0),
        broll_paths=broll_paths[:8],
        music_path=music.local_path if music else None,
        sfx_events=sfx_events[:12],
        style=style,
        allowed_roots=allowed + [ws, settings.storage_dir / "broll-cache"],
        caption_video_path=caption_video,
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
    for leftover in (ws / "audio.wav", ws / "intermediate"):
        if leftover.is_file():
            leftover.unlink(missing_ok=True)
        elif leftover.is_dir():
            import shutil

            shutil.rmtree(leftover, ignore_errors=True)
    logger.info("Video %s ready at %s", video.id, output)
