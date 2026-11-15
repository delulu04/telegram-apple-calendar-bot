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
