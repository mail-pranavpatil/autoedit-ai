from __future__ import annotations

import logging
from pathlib import Path

from autoedit.edit_schema import DEFAULT_STYLE_PROFILE, EditPlan
from autoedit.media import run_ffmpeg

logger = logging.getLogger("autoedit")


def _safe_path(path: str, allowed_roots: list[Path]) -> str:
    resolved = Path(path).resolve()
    for root in allowed_roots:
        try:
            resolved.relative_to(root.resolve())
            return str(resolved)
        except ValueError:
            continue
    raise ValueError(f"Path is outside allowed storage: {path}")


def compose_final(
    source_path: str,
    output_path: str,
    plan: EditPlan,
    duration: float,
    broll_paths: list[tuple[float, float, str, str]],
    music_path: str | None,
    sfx_events: list[tuple[float, str]],
    style: dict | None = None,
    allowed_roots: list[Path] | None = None,
    dry_run: bool = False,
) -> list[str]:
    """Build a 1080x1920 H.264/AAC video from a validated EditPlan.

    B-roll overlay streams are timestamp-shifted onto the main timeline so they
    actually appear. Talking-head is slightly overscaled so a 9:16 source is not
    a pixel-identical copy of the raw clip.
    """
    style = {**DEFAULT_STYLE_PROFILE, **(style or {})}
    roots = allowed_roots or [Path(source_path).resolve().parent.parent.parent]
    source = _safe_path(source_path, [Path(source_path).resolve().parent, *roots])
    out = str(Path(output_path).resolve())
    Path(out).parent.mkdir(parents=True, exist_ok=True)
    duration = max(duration, 0.5)

    inputs: list[str] = ["ffmpeg", "-y", "-i", source]
    input_index = 1
    broll_labels: list[tuple[int, float, float, str]] = []

    for start, end, path, asset_type in broll_paths:
        safe = _safe_path(path, roots + [Path(path).resolve().parent])
        seg_dur = max(0.6, end - start)
        if asset_type == "image":
            inputs += ["-loop", "1", "-framerate", "30", "-t", f"{seg_dur:.3f}", "-i", safe]
        else:
            inputs += ["-stream_loop", "-1", "-t", f"{seg_dur:.3f}", "-i", safe]
        broll_labels.append((input_index, start, end, asset_type))
        input_index += 1

    music_idx = None
    if music_path:
        music_idx = input_index
        inputs += ["-stream_loop", "-1", "-i", _safe_path(music_path, roots + [Path(music_path).resolve().parent])]
        input_index += 1

    sfx_indices: list[tuple[int, float]] = []
    for start, path in sfx_events:
        sfx_indices.append((input_index, start))
        inputs += ["-i", _safe_path(path, roots + [Path(path).resolve().parent])]
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

    audio_labels = []
    filters.append(
        "[0:a]aformat=sample_fmts=fltp:sample_rates=48000:channel_layouts=stereo,volume=1.0[voice]"
    )
    audio_labels.append("voice")

    if music_idx is not None:
        vol = float(style.get("music_volume", 0.18))
        filters.append(
            f"[{music_idx}:a]aformat=sample_fmts=fltp:sample_rates=48000:channel_layouts=stereo,"
            f"aloop=loop=-1:size=2000000000,atrim=0:{duration:.3f},volume={vol}[music]"
        )
        audio_labels.append("music")

    sfx_vol = float(style.get("sfx_volume", 0.28))
    for i, (inp, start) in enumerate(sfx_indices):
        delay_ms = max(0, int(start * 1000))
        label = f"sfx{i}"
        filters.append(
            f"[{inp}:a]aformat=sample_fmts=fltp:sample_rates=48000:channel_layouts=stereo,"
            f"adelay={delay_ms}|{delay_ms},volume={sfx_vol}[{label}]"
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
        "-pix_fmt",
        "yuv420p",
        "-r",
        "30",
        "-c:a",
        "aac",
        "-b:a",
        "192k",
        "-movflags",
        "+faststart",
        out,
    ]
    logger.info("Rendering %s with %s b-roll overlays", out, len(broll_labels))
    if not dry_run:
        run_ffmpeg(args, timeout=3600)
    return args
