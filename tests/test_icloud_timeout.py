"""A slow or broken iCloud call must not freeze the bot."""
import asyncio
import time
from types import SimpleNamespace
from unittest.mock import AsyncMock

import pytest

import bot


def test_slow_call_times_out_and_forces_reconnect(monkeypatch):
    monkeypatch.setattr(bot, "ICLOUD_TIMEOUT", 0.2)
    monkeypatch.setattr(bot, "calendar", object())  # a "stale" connection
    with pytest.raises(RuntimeError, match="didn't answer"):
        asyncio.run(bot.icloud(time.sleep, 1))
    assert bot.calendar is None  # next call reconnects


def test_error_forces_reconnect(monkeypatch):
    monkeypatch.setattr(bot, "calendar", object())
    def broken():
        raise ConnectionError("connection reset")
    with pytest.raises(ConnectionError):
        asyncio.run(bot.icloud(broken))
    assert bot.calendar is None


def test_success_keeps_connection(monkeypatch):
    conn = object()
    monkeypatch.setattr(bot, "calendar", conn)
    assert asyncio.run(bot.icloud(lambda x: x * 2, 21)) == 42
    assert bot.calendar is conn


def test_hanging_save_tells_user_instead_of_freezing(monkeypatch):
    class Hangs:
        def find_conflicts(self, *a, **k):
            time.sleep(1)
    monkeypatch.setattr(bot, "ICLOUD_TIMEOUT", 0.2)
    monkeypatch.setattr(bot, "get_calendar", lambda: Hangs())
    monkeypatch.setattr(bot, "allowed", lambda u: True)
    monkeypatch.setattr(bot, "PICK_CALENDAR", False)
    ctx = SimpleNamespace(user_data={})

    msg = SimpleNamespace(text="home gym tmr 8am-8.30am", reply_text=AsyncMock())
    asyncio.run(bot.on_text(SimpleNamespace(message=msg), ctx))
    kb = msg.reply_text.call_args.kwargs["reply_markup"]
    data = kb.inline_keyboard[0][0].callback_data  # "Doesn't repeat"

    q = SimpleNamespace(data=data, answer=AsyncMock(), edit_message_text=AsyncMock())
    asyncio.run(asyncio.wait_for(bot.on_button(SimpleNamespace(callback_query=q), ctx), 5))
    last = q.edit_message_text.call_args.args[0]
    assert "answer in time" in last and "Checking" not in last


def test_app_handles_messages_in_parallel():
    import inspect
    assert "concurrent_updates(True)" in inspect.getsource(bot.main)


class _Cal:
    def __init__(self, n):
        self.name = n


class _Fresh:
    def event_calendars(self):
        return [_Cal("DELS "), _Cal("SCHOOL "), _Cal("WORKOUT ")]


def _refresh(ctx):
    msg = SimpleNamespace(edit_text=AsyncMock())
    upd = SimpleNamespace(message=SimpleNamespace(reply_text=AsyncMock(return_value=msg)),
                          effective_user=SimpleNamespace(id=1))
    asyncio.run(bot.refresh_cmd(upd, ctx))
    return upd.message.reply_text.call_args.args[0], msg.edit_text.call_args.args[0]


def test_refresh_drops_old_connection_and_reconnects(monkeypatch):
    monkeypatch.setattr(bot, "allowed", lambda u: True)
    stale = object()
    monkeypatch.setattr(bot, "calendar", stale)
    seen = {}
    def connect():
        seen["was"] = bot.calendar
        return _Fresh()
    monkeypatch.setattr(bot, "get_calendar", connect)
    first, final = _refresh(SimpleNamespace(user_data={}))
    assert seen["was"] is None  # old connection thrown away before reconnecting
    assert "Reconnecting" in first
    assert "✅" in final and "3 calendars" in final and "DELS, SCHOOL, WORKOUT" in final


def test_refresh_reports_failure(monkeypatch):
    monkeypatch.setattr(bot, "allowed", lambda u: True)
    def down():
        raise ConnectionError("no route")
    monkeypatch.setattr(bot, "get_calendar", down)
    _, final = _refresh(SimpleNamespace(user_data={}))
    assert "⚠️" in final and "no route" in final


def test_refresh_ignores_strangers(monkeypatch):
    monkeypatch.setattr(bot, "allowed", lambda u: False)
    upd = SimpleNamespace(message=SimpleNamespace(reply_text=AsyncMock()), effective_user=SimpleNamespace(id=9))
    asyncio.run(bot.refresh_cmd(upd, SimpleNamespace(user_data={})))
    upd.message.reply_text.assert_not_called()


def test_refresh_is_registered():
    import inspect
    src = inspect.getsource(bot.main)
    assert 'CommandHandler("refresh", refresh_cmd)' in src
    assert 'BotCommand("refresh"' in src
