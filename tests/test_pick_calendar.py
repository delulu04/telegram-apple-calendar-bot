"""Calendar picking flow in bot.py, with a fake iCloud and fake Telegram objects."""
import asyncio
from types import SimpleNamespace
from unittest.mock import AsyncMock

import pytest

import bot


class FakeCal:
    def __init__(self, name):
        self.name = name


class FakeICloud:
    def __init__(self, names):
        self.cals = [FakeCal(n) for n in names]
        self.target = self.cals[0]
        self.saved = []  # (title, calendar name)

    def event_calendars(self):
        return self.cals

    def calendar_named(self, name):
        return next(c for c in self.cals if c.name == name)

    def find_conflicts(self, *a, **k):
        return []

    def add_event(self, title, start, end, all_day, rrule, free, calendar=None):
        self.saved.append((title, (calendar or self.target).name))
        return "url"


NAMES = ["DELS", "BDAY", "SCHOOL", "EXTRA SCHOOL", "WORKOUT", "WORK"]


@pytest.fixture
def env(monkeypatch):
    fake = FakeICloud(NAMES)
    monkeypatch.setattr(bot, "get_calendar", lambda: fake)
    monkeypatch.setattr(bot, "allowed", lambda u: True)
    monkeypatch.setattr(bot, "PICK_CALENDAR", True)
    ctx = SimpleNamespace(user_data={})
    return fake, ctx


def send(text, ctx):
    msg = SimpleNamespace(text=text, reply_text=AsyncMock())
    asyncio.run(bot.on_text(SimpleNamespace(message=msg), ctx))
    return msg.reply_text.call_args


def press(data, ctx):
    q = SimpleNamespace(data=data, answer=AsyncMock(), edit_message_text=AsyncMock())
    asyncio.run(bot.on_button(SimpleNamespace(callback_query=q), ctx))
    return q.edit_message_text.call_args


def buttons(call):
    return [(b.text, b.callback_data) for row in call.kwargs["reply_markup"].inline_keyboard for b in row]


def test_tag_goes_straight_to_repeat_and_saves_there(env):
    fake, ctx = env
    call = send("Tutorial thurs 10-12pm #sch", ctx)
    assert "🗂 SCHOOL" in call.args[0] and "Repeat?" in call.args[0]
    key = buttons(call)[0][1].split("|")[1]
    done = press(f"r|{key}|none", ctx)
    assert fake.saved == [("Tutorial", "SCHOOL")]
    assert "Saved to SCHOOL" in done.args[0]


def test_no_tag_shows_picker_then_repeat_then_saves(env):
    fake, ctx = env
    call = send("dinner w ash fri 7pm", ctx)
    assert "Which calendar?" in call.args[0]
    btns = buttons(call)
    assert [t for t, _ in btns] == NAMES + ["Cancel"]
    workout = dict(btns)["WORKOUT"]
    call = press(workout, ctx)
    assert "🗂 WORKOUT" in call.args[0] and "Repeat?" in call.args[0]
    key = workout.split("|")[1]
    press(f"r|{key}|weekly", ctx)
    assert fake.saved == [("Dinner w ash", "WORKOUT")]


def test_unknown_tag_says_so_and_shows_picker(env):
    _, ctx = env
    call = send("movie sat 9pm #netflix", ctx)
    assert "No calendar matches #netflix" in call.args[0]
    assert "Which calendar?" in call.args[0]


def test_ambiguous_tag_shows_picker(env):
    _, ctx = env
    call = send("run tmr 7am #wo", ctx)  # WORK or WORKOUT
    assert "Which calendar?" in call.args[0]


def test_tag_removed_from_title(env):
    fake, ctx = env
    call = send("#bday Sandra's birthday 14/12", ctx)
    key = buttons(call)[0][1].split("|")[1]
    press(f"r|{key}|none", ctx)
    assert fake.saved == [("Sandra's birthday", "BDAY")]


def test_picking_off_uses_default_calendar_and_no_picker(env, monkeypatch):
    fake, ctx = env
    monkeypatch.setattr(bot, "PICK_CALENDAR", False)
    call = send("Gym tmr 7pm", ctx)
    assert "Repeat?" in call.args[0] and "🗂" not in call.args[0]
    key = buttons(call)[0][1].split("|")[1]
    press(f"r|{key}|none", ctx)
    assert fake.saved == [("Gym", "DELS")]


def test_cancel_from_picker(env):
    fake, ctx = env
    call = send("dinner fri 7pm", ctx)
    cancel = dict(buttons(call))["Cancel"]
    done = press(cancel, ctx)
    assert "Cancelled" in done.args[0] and fake.saved == []


def start(ctx, first_name="Delia"):
    msg = SimpleNamespace(reply_text=AsyncMock())
    upd = SimpleNamespace(message=msg, effective_user=SimpleNamespace(id=1, first_name=first_name),
                          effective_chat=SimpleNamespace(id=1))
    asyncio.run(bot.start_cmd(upd, ctx))
    return msg.reply_text.call_args_list[0]


def test_start_greets_by_name_and_lists_tags(env):
    _, ctx = env
    call = start(ctx)
    text = call.args[0]
    assert "Hi Delia" in text
    assert "#dels" in text and "#extraschool" in text and "#workout" in text
    assert call.kwargs.get("parse_mode") == "HTML"


def test_start_without_picking_has_no_tag_section(env, monkeypatch):
    _, ctx = env
    monkeypatch.setattr(bot, "PICK_CALENDAR", False)
    text = start(ctx, "Ben").args[0]
    assert "Hi Ben" in text and "#dels" not in text and "#workout" not in text


def test_start_still_works_if_icloud_is_down(env, monkeypatch):
    _, ctx = env
    def boom():
        raise RuntimeError("no network")
    monkeypatch.setattr(bot, "get_calendar", boom)
    text = start(ctx).args[0]
    assert "Hi Delia" in text and "#dels" not in text


def test_start_escapes_html_in_name(env):
    _, ctx = env
    assert "&lt;b&gt;" in start(ctx, "<b>").args[0]


def test_start_hides_alerts_when_watching_is_off(env, monkeypatch):
    _, ctx = env
    monkeypatch.setattr(bot, "WATCH_MINUTES", 0)
    monkeypatch.delenv("NOTIFY_CHAT_ID", raising=False)
    msg = SimpleNamespace(reply_text=AsyncMock())
    upd = SimpleNamespace(message=msg, effective_user=SimpleNamespace(id=1, first_name="Delia"),
                          effective_chat=SimpleNamespace(id=1))
    asyncio.run(bot.start_cmd(upd, ctx))
    texts = [c.args[0] for c in msg.reply_text.call_args_list]
    assert len(texts) == 1  # no NOTIFY_CHAT_ID nudge
    assert "🔔" not in texts[0]


def test_start_mentions_alerts_when_watching_is_on(env, monkeypatch):
    _, ctx = env
    monkeypatch.setattr(bot, "WATCH_MINUTES", 5)
    assert "🔔" in start(ctx).args[0]
