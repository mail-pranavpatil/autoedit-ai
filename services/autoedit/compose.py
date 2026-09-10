from __future__ import annotations

import logging
from pathlib import Path

from autoedit.config import get_settings
from autoedit.edit_schema import DEFAULT_STYLE_PROFILE, EditPlan, MAX_VISUAL_ASSETS
from autoedit.media import probe_media, run_ffmpeg

logger = logging.getLogger("autoedit")


def _broll_clip_filter(w: int, h: int, dur: float) -> str:
    """One image -> a 1080x1920 clip: fit to frame, then a slow crop-pan (Ken Burns)."""
    if h >= w:  # portrait / square-ish: cover-crop fills the frame
        fit = "scale=1080:1920:force_original_aspect_ratio=increase,crop=1080:1920"
    else:  # landscape: sharp image centered over a blurred blown-up copy of itself
        fit = (
            "split=2[bg][fg];"
            "[bg]scale=1080:1920:force_original_aspect_ratio=increase,crop=1080:1920,boxblur=32:2[bg2];"
            "[fg]scale=1080:1920:force_original_aspect_ratio=decrease[fg2];"
            "[bg2][fg2]overlay=(W-w)/2:(H-h)/2"
        )
    fade = min(0.35, max(0.12, dur / 8))
    return (
        f"{fit},setsar=1,"
        f"scale=1188:2112:force_original_aspect_ratio=increase,"
        f"crop=1080:1920:'(iw-1080)*t/{max(dur, 0.1):.3f}':'(ih-1920)*t/{max(dur, 0.1):.3f}*0.4',"
        f"fps=30,format=yuv420p,"
        f"fade=t=in:st=0:d={fade:.2f},fade=t=out:st={max(dur - fade, 0):.3f}:d={fade:.2f}"
    )


_CLIP_ENC = [
    "-r", "30", "-c:v", "libx264", "-preset", "veryfast",
    "-pix_fmt", "yuv420p", "-an", "-video_track_timescale", "15360",
]


def write_broll_track(
    image_windows: list[tuple[float, float, str]],
    ws: Path,
    duration: float,
    threads: int = 1,
) -> tuple[str, list[tuple[float, float]]] | None:
    """Pre-render every image B-roll cut into ONE 1080x1920 track + its show-windows.

    Keeps the final filtergraph to a single extra input/overlay instead of dozens
    of concurrent image decoders (see ``render_ffmpeg_threads``).
    """
    windows = sorted((w for w in image_windows if w[1] - w[0] > 0.05), key=lambda w: w[0])
    if not windows:
        return None
    out_dir = ws / "broll"
    out_dir.mkdir(parents=True, exist_ok=True)
    thr = ["-threads", str(max(1, int(threads)))]
    duration = max(duration, 0.5)

    parts: list[Path] = []
    shown: list[tuple[float, float]] = []
    cursor = 0.0

    def _black(gap: float, tag: str) -> Path:
        p = out_dir / f"gap_{tag}.mp4"
        run_ffmpeg(
            ["ffmpeg", "-y", *thr, "-f", "lavfi", "-i", f"color=c=black:s=1080x1920:r=30:d={gap:.3f}",
             "-t", f"{gap:.3f}", *_CLIP_ENC, str(p)],
            timeout=120,
        )
        return p

    for i, (start, end, path) in enumerate(windows):
        start = max(cursor, float(start))
        end = min(duration, float(end))
        if end - start < 0.2:
            continue
        if start > cursor + 0.05:
            parts.append(_black(start - cursor, f"{i}"))
        try:
            info = probe_media(path)
            w, h = int(info.get("width") or 0), int(info.get("height") or 0)
        except Exception:  # noqa: BLE001
            w = h = 1080
        clip = out_dir / f"clip_{i}.mp4"
        dur = end - start
        try:
            run_ffmpeg(
                ["ffmpeg", "-y", *thr, "-loop", "1", "-i", path,
                 "-vf", _broll_clip_filter(w or 1080, h or 1080, dur),
                 "-t", f"{dur:.3f}", *_CLIP_ENC, str(clip)],
                timeout=300,
            )
        except Exception as exc:  # noqa: BLE001 - one bad image must not kill the track
            logger.warning("b-roll clip %s failed (%s); leaving a gap", path, exc)
            parts.append(_black(dur, f"f{i}"))
            cursor = end
            continue
        parts.append(clip)
        shown.append((round(start, 3), round(end, 3)))
        cursor = end

    if duration > cursor + 0.05:
        parts.append(_black(duration - cursor, "tail"))
    if not shown:
        return None

    listfile = out_dir / "track.txt"
    listfile.write_text(
        "ffconcat version 1.0\n"
        + "".join(f"file '{p.resolve().as_posix()}'\n" for p in parts)
    )
    track = out_dir / "broll_track.mp4"
    try:
        run_ffmpeg(
            ["ffmpeg", "-y", *thr, "-f", "concat", "-safe", "0", "-i", str(listfile),
             "-c", "copy", str(track)],
            timeout=300,
        )
    except Exception:  # noqa: BLE001 - params mismatch: re-encode the concat
        run_ffmpeg(
            ["ffmpeg", "-y", *thr, "-f", "concat", "-safe", "0", "-i", str(listfile),
             *_CLIP_ENC, "-t", f"{duration:.3f}", str(track)],
            timeout=600,
        )
    logger.info("[BROLL_TRACK] windows=%d track=%s", len(shown), track)
    return str(track), shown


def _safe_path(path: str, allowed_roots: list[Path]) -> str:
    resolved = Path(path).resolve()
    for root in allowed_roots:
        try:
            resolved.relative_to(root.resolve())
            return str(resolved)
        except ValueError:
            continue
    raise ValueError(f"Path is outside allowed storage: {path}")


def _normalize_sfx_events(sfx_events: list) -> list[tuple[float, str, float | None, bool]]:
    out: list[tuple[float, str, float | None, bool]] = []
    for item in sfx_events or []:
        if isinstance(item, dict):
            path = item.get("path")
            if not path:
                continue
            out.append(
                (
                    float(item.get("start") or 0),
                    str(path),
                    float(item["volume"]) if item.get("volume") is not None else None,
                    bool(item.get("duck")),
                )
            )
            continue
        if not item:
            continue
        start = float(item[0])
        path = str(item[1])
        volume = float(item[2]) if len(item) > 2 and item[2] is not None else None
        duck = bool(item[3]) if len(item) > 3 else False
        out.append((start, path, volume, duck))
    return out


def compose_final(
    source_path: str,
    output_path: str,
    plan: EditPlan,
    duration: float,
    broll_paths: list[tuple[float, float, str, str]],
    music_path: str | None = None,
    sfx_events: list | None = None,
    style: dict | None = None,
    allowed_roots: list[Path] | None = None,
    dry_run: bool = False,
    caption_overlays: list[tuple[float, float, str]] | None = None,
    caption_video_path: str | None = None,
    caption_concat_path: str | None = None,
    broll_track_path: str | None = None,
    broll_track_windows: list[tuple[float, float]] | None = None,
) -> list[str]:
    """Build a 1080x1920 H.264/AAC video from a validated EditPlan.

    B-roll overlay streams are timestamp-shifted onto the main timeline so they
    actually appear. Talking-head is slightly overscaled so a 9:16 source is not
    a pixel-identical copy of the raw clip.
    """
    style = {**DEFAULT_STYLE_PROFILE, **(style or {})}
    if plan.music_volume is not None:
        style["music_volume"] = plan.music_volume
    roots = allowed_roots or [Path(source_path).resolve().parent.parent.parent]
    source = _safe_path(source_path, [Path(source_path).resolve().parent, *roots])
    out = str(Path(output_path).resolve())
    Path(out).parent.mkdir(parents=True, exist_ok=True)
    duration = max(duration, 0.5)

    # Bound peak RAM: one decoder thread per input and one filtergraph thread so
    # frame-buffer pools don't multiply across ~10 concurrent decoders and blow
    # the container's memory limit (OOM -> SIGKILL 9). See render_ffmpeg_threads.
    threads = max(1, int(get_settings().render_ffmpeg_threads))
    thr = ["-threads", str(threads)]

    inputs: list[str] = ["ffmpeg", "-y", "-filter_complex_threads", str(threads), *thr, "-i", source]
    input_index = 1
    broll_labels: list[tuple[int, float, float, str]] = []

    # Dense image B-roll is pre-composited into one track (broll_track_path); only
    # the remaining video B-roll goes through the per-asset overlay loop here.
    track_is_used = bool(broll_track_path and broll_track_windows)
    for start, end, path, asset_type in (broll_paths or [])[:MAX_VISUAL_ASSETS]:
        if track_is_used and asset_type == "image":
            continue
        safe = _safe_path(path, roots + [Path(path).resolve().parent])
        seg_dur = max(0.6, end - start)
        if asset_type == "image":
            inputs += ["-loop", "1", "-framerate", "30", "-t", f"{seg_dur:.3f}", *thr, "-i", safe]
        else:
            inputs += ["-stream_loop", "-1", "-t", f"{seg_dur:.3f}", *thr, "-i", safe]
        broll_labels.append((input_index, start, end, asset_type))
        input_index += 1

    broll_track_idx = None
    if track_is_used:
        broll_track_idx = input_index
        inputs += [*thr, "-i", _safe_path(broll_track_path, roots + [Path(broll_track_path).resolve().parent])]
        input_index += 1

    music_idx = None
    if music_path:
        music_idx = input_index
        inputs += ["-stream_loop", "-1", *thr, "-i", _safe_path(music_path, roots + [Path(music_path).resolve().parent])]
        input_index += 1

    sfx_indices: list[tuple[int, float, float]] = []
    duck_times: list[float] = []
    default_sfx_vol = float(style.get("sfx_volume", 0.32))
    for start, path, volume, duck in _normalize_sfx_events(sfx_events):
        sfx_indices.append((input_index, start, volume if volume is not None else default_sfx_vol))
        if duck:
            duck_times.append(start)
        inputs += [*thr, "-i", _safe_path(path, roots + [Path(path).resolve().parent])]
        input_index += 1

    cap_video_idx = None
    cap_labels: list[tuple[int, float, float]] = []
    captions_on = bool(plan.captions_enabled)
    packed_concat = caption_concat_path
    overlays = list(caption_overlays or [])
    if captions_on and not packed_concat and not caption_video_path and len(overlays) > 8:
        from autoedit.captions import write_caption_concat

        packed_concat = write_caption_concat(overlays, Path(overlays[0][2]).parent, duration)
        logger.info("Packed %s caption PNGs into a single concat input", len(overlays))

    if captions_on and caption_video_path:
        cap_video_idx = input_index
        inputs += [*thr, "-i", _safe_path(caption_video_path, roots + [Path(caption_video_path).resolve().parent])]
        input_index += 1
    elif captions_on and packed_concat:
        cap_video_idx = input_index
        concat_safe = _safe_path(packed_concat, roots + [Path(packed_concat).resolve().parent])
        inputs += ["-f", "concat", "-safe", "0", *thr, "-i", concat_safe]
        input_index += 1
    elif captions_on:
        for start, end, path in overlays:
            safe = _safe_path(path, roots + [Path(path).resolve().parent])
            seg_dur = max(0.05, end - start)
            inputs += ["-loop", "1", "-framerate", "30", "-t", f"{seg_dur:.3f}", *thr, "-i", safe]
            cap_labels.append((input_index, start, end))
            input_index += 1

    # Overscale + slow crop travel so even a native 9:16 talking-head is visibly edited.
    base = (
        f"[0:v]scale=1240:2204:force_original_aspect_ratio=increase,"
        f"crop=1080:1920:'min(iw-1080,max(0,(iw-1080)*t/{duration:.3f}))':"
        f"'min(ih-1920,max(0,(ih-1920)*t/{duration:.3f}*0.5))',"
        f"fps=30,setsar=1,format=yuv420p[base]"
    )

    filters = [base]
    last = "base"
    for idx, (inp, start, end, _typ) in enumerate(broll_labels):
        fade = min(0.28, max(0.12, (end - start) / 8))
        b_label = f"b{idx}"
        shifted = f"bs{idx}"
        v_label = f"v{idx}"
        filters.append(
            f"[{inp}:v]scale=1080:1920:force_original_aspect_ratio=increase,crop=1080:1920,"
            f"fps=30,setsar=1,format=yuv420p,fade=t=in:st=0:d={fade:.2f}[{b_label}]"
        )
        filters.append(f"[{b_label}]setpts=PTS+{start:.3f}/TB[{shifted}]")
        filters.append(
            f"[{last}][{shifted}]overlay=0:0:enable='between(t,{start:.3f},{end:.3f})':eof_action=pass[{v_label}]"
        )
        last = v_label

    if broll_track_idx is not None:
        enable = "+".join(f"between(t,{s:.3f},{e:.3f})" for s, e in broll_track_windows)
        filters.append(
            f"[{broll_track_idx}:v]scale=1080:1920,fps=30,setsar=1,format=yuv420p[btrk]"
        )
        filters.append(
            f"[{last}][btrk]overlay=0:0:enable='{enable}':eof_action=pass[vbtrk]"
        )
        last = "vbtrk"

    if cap_video_idx is not None:
        c_label = "capv"
        v_label = "vcaps"
        filters.append(
            f"[{cap_video_idx}:v]fps=30,format=rgba,scale=1080:1920:force_original_aspect_ratio=decrease[{c_label}]"
        )
        filters.append(f"[{last}][{c_label}]overlay=0:0:format=auto:eof_action=pass[{v_label}]")
        last = v_label
    else:
        for idx, (inp, start, end) in enumerate(cap_labels):
            c_label = f"cap{idx}"
            shifted = f"caps{idx}"
            v_label = f"vc{idx}"
            filters.append(f"[{inp}:v]format=rgba[{c_label}]")
            filters.append(f"[{c_label}]setpts=PTS+{start:.3f}/TB[{shifted}]")
            filters.append(
                f"[{last}][{shifted}]overlay=0:0:format=auto:enable='between(t,{start:.3f},{end:.3f})':eof_action=pass[{v_label}]"
            )
            last = v_label

    audio_labels = []
    filters.append(
        "[0:a]aformat=sample_fmts=fltp:sample_rates=48000:channel_layouts=stereo,volume=1.0[voice]"
    )
    audio_labels.append("voice")

    if music_idx is not None:
        vol = float(style.get("music_volume", 0.18))
        duck_chain = ""
        duck_mult = 10 ** (-3.5 / 20)
        for t in duck_times:
            duck_chain += f",volume='if(between(t,{t:.3f},{t + 0.4:.3f}),{duck_mult:.3f},1)'"
        filters.append(
            f"[{music_idx}:a]aformat=sample_fmts=fltp:sample_rates=48000:channel_layouts=stereo,"
            f"aloop=loop=-1:size=2000000000,atrim=0:{duration:.3f},volume={vol}{duck_chain}[music]"
        )
        audio_labels.append("music")

    for i, (inp, start, vol) in enumerate(sfx_indices):
        delay_ms = max(0, int(start * 1000))
        label = f"sfx{i}"
        filters.append(
            f"[{inp}:a]aformat=sample_fmts=fltp:sample_rates=48000:channel_layouts=stereo,"
            f"adelay={delay_ms}|{delay_ms},volume={vol}[{label}]"
        )
        audio_labels.append(label)

    mix_inputs = "".join(f"[{lab}]" for lab in audio_labels)
    filters.append(
        f"{mix_inputs}amix=inputs={len(audio_labels)}:duration=first:dropout_transition=2:normalize=0[aout]"
    )

    filter_complex = ";".join(filters)
    args = inputs + [
        "-filter_complex",
        filter_complex,
        "-map",
        f"[{last}]",
        "-map",
        "[aout]",
        "-t",
        f"{duration:.3f}",
        "-c:v",
        "libx264",
        "-preset",
        "veryfast",
        "-threads",
        str(threads),
        "-pix_fmt",
        "yuv420p",
        "-r",
        "30",
        "-c:a",
        "aac",
        "-b:a",
        "192k",
        "-max_muxing_queue_size",
        "1024",
        "-movflags",
        "+faststart",
        out,
    ]
    logger.info(
        "Rendering %s with %s b-roll overlays and %s caption overlays",
        out,
        len(broll_labels),
        len(cap_labels) + (1 if cap_video_idx is not None else 0),
    )
    if not dry_run:
        run_ffmpeg(args, timeout=3600)
    return args
