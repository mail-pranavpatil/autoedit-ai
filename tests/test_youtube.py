from datetime import datetime, timezone

from autoedit.youtube_schedule import IST, next_publish_slot, publish_at_rfc3339, youtube_title_from_filename


def test_title_from_filename():
    assert youtube_title_from_filename("my clip.MOV") == "my clip"
    assert youtube_title_from_filename("reel.mp4") == "reel"
    assert youtube_title_from_filename("") == "Untitled"
    assert len(youtube_title_from_filename("x" * 200 + ".mp4")) == 100


def test_after_last_slot_goes_next_morning():
    now = datetime(2026, 8, 18, 21, 10, tzinfo=IST)
    slot = next_publish_slot(now, set())
    ist = slot.astimezone(IST)
    assert ist.hour == 7
    assert ist.minute == 0
    assert ist.date().isoformat() == "2026-08-19"


def test_all_today_booked_uses_next_day_same_times():
    now = datetime(2026, 8, 18, 6, 0, tzinfo=IST)
    occupied = {
        datetime(2026, 8, 18, hour, 0, tzinfo=IST).astimezone(timezone.utc) for hour in (7, 14, 18, 21)
    }
    slot = next_publish_slot(now, occupied)
    ist = slot.astimezone(IST)
    assert ist.date().isoformat() == "2026-08-19"
    assert ist.hour == 7


def test_skips_occupied_and_picks_next_same_day():
    now = datetime(2026, 8, 18, 6, 0, tzinfo=IST)
    occupied = {datetime(2026, 8, 18, 7, 0, tzinfo=IST).astimezone(timezone.utc)}
    slot = next_publish_slot(now, occupied)
    assert slot.astimezone(IST).hour == 14


def test_skips_slot_inside_lead_time():
    now = datetime(2026, 8, 18, 6, 50, tzinfo=IST)
    slot = next_publish_slot(now, set())
    assert slot.astimezone(IST).hour == 14


def test_naive_occupied_treated_as_utc():
    now = datetime(2026, 8, 18, 6, 0, tzinfo=IST)
    seven_ist = datetime(2026, 8, 18, 7, 0, tzinfo=IST).astimezone(timezone.utc).replace(tzinfo=None)
    slot = next_publish_slot(now, {seven_ist})
    assert slot.astimezone(IST).hour == 14


def test_publish_at_rfc3339_is_utc():
    when = datetime(2026, 8, 19, 7, 0, tzinfo=IST)
    assert publish_at_rfc3339(when) == "2026-08-19T01:30:00Z"
