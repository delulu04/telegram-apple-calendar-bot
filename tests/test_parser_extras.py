"""Weekday next to a real date, and durations written without "for"."""
from datetime import datetime

import pytest

from event_parser import ParseError, parse_event

NOW = datetime(2026, 11, 14, 13, 0)  # Sat 14 Nov 2026


def p(text):
    e = parse_event(text, NOW)
    return e.title, e.start.strftime("%a %d %b %H:%M"), e.end.strftime("%H:%M")


@pytest.mark.parametrize("text", [
    "gym mon 16 nov 7pm", "gym monday 16 nov 7pm", "gym 16 nov mon 7pm",
    "gym mon 16/11 7pm", "gym mon, 16 nov 7pm", "gym this mon 16 nov 7pm",
])
def test_matching_weekday_is_dropped_from_title(text):
    assert p(text) == ("Gym", "Mon 16 Nov 19:00", "20:00")


def test_weekday_with_tmr_dropped_when_it_matches():
    assert p("gym tmr sun 7pm") == ("Gym", "Sun 15 Nov 19:00", "20:00")


def test_mismatched_weekday_stays_in_title():
    # 15 Nov is a Sunday; "Friday" is part of the name, not the date
    assert p("Friday feels 15 nov 7pm")[0] == "Friday feels"


def test_weekday_alone_still_works():
    assert p("gym mon 7pm") == ("Gym", "Mon 16 Nov 19:00", "20:00")


@pytest.mark.parametrize("text,end", [
    ("gym 16 nov 7pm 2h", "21:00"),
    ("gym 16 nov 2h 7pm", "21:00"),
    ("gym 16 nov 7pm 90min", "20:30"),
    ("gym 16 nov 7pm 90 mins", "20:30"),
    ("gym 16 nov 7pm 1.5h", "20:30"),
    ("gym 16 nov 7pm 1.5hrs", "20:30"),
    ("gym 16 nov 7pm 2 hours", "21:00"),
    ("gym 16 nov 7pm 1h30", "20:30"),
    ("gym 16 nov 7pm 1h30m", "20:30"),
    ("gym 16 nov 7pm 1h 30min", "20:30"),
    ("gym 16 nov 7pm for 2h", "21:00"),
    ("gym 16 nov 7pm for 45m", "19:45"),
    ("gym 16 nov 7pm for 2 hours", "21:00"),
])
def test_durations(text, end):
    assert p(text) == ("Gym", "Mon 16 Nov 19:00", end)


def test_bare_m_without_for_is_not_a_duration():
    # "5m" alone is too ambiguous (could be part of a name); needs "for" or "min"
    assert p("run 5m 16 nov 7am")[0] == "Run 5m"


def test_range_still_wins_over_default():
    assert p("gym 16 nov 7-9pm") == ("Gym", "Mon 16 Nov 19:00", "21:00")


def test_titles_capitalised_by_default(monkeypatch):
    monkeypatch.delenv("CAPITALISE_TITLES", raising=False)
    assert p("gym 16 nov 7pm")[0] == "Gym"


@pytest.mark.parametrize("text,title", [
    ("gym 16 nov 7pm", "gym"),
    ("brunch w ash sat 11am", "brunch w ash"),
    ("IS4234 lect wed 2pm", "IS4234 lect"),
    ("jess bday 10/12", "jess bday"),
    ("Bali 16-20 dec", "Bali"),
])
def test_titles_kept_as_typed_when_turned_off(monkeypatch, text, title):
    monkeypatch.setenv("CAPITALISE_TITLES", "false")
    assert parse_event(text, NOW).title == title
