"""Pick which calendar an event goes to from a #tag, e.g. "Tutorial thurs 10am #school"."""
from __future__ import annotations

import re

TAG_RE = re.compile(r"(?<!\S)#([\w-]+)")


def _norm(s: str) -> str:
    """Lowercase, letters and digits only: "EXTRA SCHOOL" / "extra-school" -> "extraschool"."""
    return "".join(ch for ch in s.lower() if ch.isalnum())


def extract_tag(text: str) -> tuple[str, str | None]:
    """Remove the first #tag from the message. Returns (text_without_tag, tag or None)."""
    m = TAG_RE.search(text)
    if not m:
        return text, None
    rest = re.sub(r"\s+", " ", text[:m.start()] + " " + text[m.end():]).strip()
    return rest, m.group(1)


def match_calendar(tag: str, names: list[str]) -> str | None:
    """Exact match first, then a unique prefix. None if nothing or several match."""
    t = _norm(tag)
    if not t:
        return None
    exact = [n for n in names if _norm(n) == t]
    if len(exact) == 1:
        return exact[0]
    prefix = [n for n in names if _norm(n).startswith(t)]
    return prefix[0] if len(prefix) == 1 else None
