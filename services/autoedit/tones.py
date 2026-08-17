from __future__ import annotations

import math
from pathlib import Path
from wave import open as wave_open


def write_tone(path: Path, freq: float, seconds: float, volume: float = 0.25, sample_rate: int = 22050) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    n = int(sample_rate * seconds)
    with wave_open(str(path), "w") as w:
        w.setnchannels(1)
        w.setsampwidth(2)
        w.setframerate(sample_rate)
        frames = bytearray()
        for i in range(n):
            env = min(1.0, i / 400) * min(1.0, (n - i) / 800)
            sample = int(32767 * volume * env * math.sin(2 * math.pi * freq * i / sample_rate))
            frames += int(sample).to_bytes(2, "little", signed=True)
        w.writeframes(frames)
