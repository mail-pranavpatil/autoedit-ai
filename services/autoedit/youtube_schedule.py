from __future__ import annotations

from datetime import datetime, timedelta, timezone
from pathlib import Path
from zoneinfo import ZoneInfo

IST = ZoneInfo("Asia/Kolkata")
SLOT_HOURS = (7, 14, 18, 21)
MIN_LEAD = timedelta(minutes=15)
YOUTUBE_TITLE_MAX = 100


def youtube_title_from_filename(filename: str) -> str:
    stem = Path(filename or "").stem.strip() or "Untitled"
    return stem[:YOUTUBE_TITLE_MAX]


def next_publish_slot(
    now: datetime,
    occupied: set[datetime],
    *,
    min_lead: timedelta = MIN_LEAD,
) -> datetime:
    if now.tzinfo is None:
        now = now.replace(tzinfo=timezone.utc)
    now_ist = now.astimezone(IST)
    earliest = now_ist + min_lead
    occupied_utc: list[datetime] = []
    for item in occupied:
        if item is None:
            continue
        aware = item if item.tzinfo else item.replace(tzinfo=timezone.utc)
        occupied_utc.append(aware.astimezone(timezone.utc))

    day = earliest.date()
    for _ in range(366):
        for hour in SLOT_HOURS:
            candidate = datetime(day.year, day.month, day.day, hour, 0, 0, tzinfo=IST)
            if candidate < earliest:
                continue
            utc = candidate.astimezone(timezone.utc)
            if any(abs((booked - utc).total_seconds()) < 60 for booked in occupied_utc):
                continue
            return utc
        day = day + timedelta(days=1)
    raise RuntimeError("No free YouTube slot in the next year")


def publish_at_rfc3339(when: datetime) -> str:
    if when.tzinfo is None:
        when = when.replace(tzinfo=timezone.utc)
    return when.astimezone(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")
