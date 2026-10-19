"""Tests for income parsing (/in) and its category-conflict rejection."""

import asyncio
import os
import sys

sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))

import pytest

from bot import cmd_income
from parser import ConflictingCategoryError, ParseError, parse_income

# Minimal category list mirroring categories.yaml
CATS = [
    ("F", ["F", "food"]),
    ("h", ["h", "home", "medicine", "hm"]),
    ("TT", ["TT", "transport", "transportation", "taxi"]),
    ("cloth", ["cloth", "clothes"]),
    ("fun", ["fun", "hangout", "hanging"]),
    ("r", ["r", "rent", "facilities"]),
    ("p", ["p", "periodic", "subscription"]),
    ("travel", ["travel"]),
    ("rel", ["rel", "relationship"]),
]


# ── parser ───────────────────────────────────────────────────────────────────

def test_income_without_categories_is_accepted():
    amount, taxable, month, name = parse_income("5000 salary", "2026-03")
    assert amount == 5000.0
    assert taxable is False
    assert month == "2026-03"
    assert name == "salary"


def test_income_name_matching_no_category_is_accepted():
    _amount, _taxable, _month, name = parse_income("5000 salary", "2026-03", CATS)
    assert name == "salary"


def test_income_name_matching_single_category_is_accepted():
    """One category keyword is not a conflict — the name is kept as is."""
    amount, _taxable, _month, name = parse_income("5000 rent", "2026-03", CATS)
    assert amount == 5000.0
    assert name == "rent"


def test_income_name_with_two_categories_is_rejected():
    with pytest.raises(ConflictingCategoryError):
        parse_income("5000 rent food", "2026-03", CATS)


def test_income_conflict_error_message_lists_categories():
    with pytest.raises(ConflictingCategoryError) as exc:
        parse_income("5000 rent food", "2026-03", CATS)
    msg = str(exc.value)
    assert "Conflicting categories" in msg
    assert "rent" in msg
    assert "food" in msg
    assert "r" in msg
    assert "F" in msg


def test_income_conflict_is_a_parse_error():
    with pytest.raises(ParseError):
        parse_income("5000 rent food", "2026-03", CATS)


def test_income_conflict_is_case_insensitive():
    with pytest.raises(ConflictingCategoryError):
        parse_income("5000 RENT Food", "2026-03", CATS)


def test_income_conflict_detected_via_prefix_match():
    """'trav' is a prefix of 'travel' → conflicts with the exact 'food'."""
    with pytest.raises(ConflictingCategoryError):
        parse_income("5000 trav food", "2026-03", CATS)


def test_income_flags_and_month_are_not_category_checked():
    """The T flag and the YYYY-MM override must not trigger the check."""
    amount, taxable, month, name = parse_income("5000 T 2026-02 salary", "2026-03", CATS)
    assert amount == 5000.0
    assert taxable is True
    assert month == "2026-02"
    assert name == "salary"


# ── handler ──────────────────────────────────────────────────────────────────

class _FakeMessage:
    def __init__(self, text):
        self.text = text
        self.replies = []

    async def reply_text(self, text, **kwargs):
        self.replies.append(text)


class _FakeUpdate:
    def __init__(self, text):
        self.message = _FakeMessage(text)


class _FakeStore:
    def __init__(self, month="2026-03"):
        self._month = month
        self.appended = []

    def get_current_month(self):
        return self._month

    def append_income(self, month, amount, taxable, name):
        self.appended.append((month, amount, taxable, name))


class _FakeCtx:
    def __init__(self, categories=None, month="2026-03"):
        self.store = _FakeStore(month)
        self.bot_data = {"store": self.store, "categories": categories or CATS}


def _run(text):
    update = _FakeUpdate(text)
    ctx = _FakeCtx()
    asyncio.run(cmd_income(update, ctx))
    return update, ctx


def test_handler_records_income_without_conflict():
    update, ctx = _run("/in 5000 salary")
    assert ctx.store.appended == [("2026-03", 5000.0, False, "salary")]
    assert update.message.replies[0].startswith("✅")


def test_handler_rejects_conflicting_categories():
    update, ctx = _run("/in 5000 rent food")
    assert ctx.store.appended == []
    reply = update.message.replies[0]
    assert reply.startswith("❌")
    assert "Conflicting categories" in reply


def test_handler_accepts_single_category_name():
    update, ctx = _run("/in 1200 T rent")
    assert ctx.store.appended == [("2026-03", 1200.0, True, "rent")]
    assert update.message.replies[0].startswith("✅")
