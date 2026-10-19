"""Tests for the /erase command: /erase, /erase in N, /erase out N."""

import asyncio
import os
import sys

sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))

from bot import cmd_erase, cb_erase_last_n_do
from storage import Storage

EXPENSE_RECORDS = [
    ("2026-03-01", "food", "Lunch", "15.0"),
    ("2026-03-01", "taxi", "Uber", "8.5"),
    ("2026-03-01", "food", "Dinner", "25.0"),
]

INCOME_RECORDS = [
    ("1000.0", True, "Salary"),
    ("500.0", False, "Freelance"),
    ("200.0", False, "Gift"),
]


class _FakeMessage:
    def __init__(self, text):
        self.text = text
        self.replies = []
        self.markups = []

    async def reply_text(self, text, **kwargs):
        self.replies.append(text)
        self.markups.append(kwargs.get("reply_markup"))


class _FakeUpdate:
    def __init__(self, text):
        self.message = _FakeMessage(text)


class _FakeStore:
    def __init__(self, month="2026-03", expenses=None, incomes=None):
        self._month = month
        self._expenses = expenses if expenses is not None else list(EXPENSE_RECORDS)
        self._incomes = incomes if incomes is not None else list(INCOME_RECORDS)

    def get_current_month(self):
        return self._month

    def read_month(self, month):
        return list(self._expenses)

    def read_income(self, month):
        return list(self._incomes)


class _FakeCtx:
    def __init__(self, store=None):
        store = store or _FakeStore()
        self.bot_data = {"store": store}
        self.user_data = {"store": store}


def _run(text, store=None):
    update = _FakeUpdate(text)
    ctx = _FakeCtx(store)
    asyncio.run(cmd_erase(update, ctx))
    return update


def _callback_data(markup):
    if markup is None:
        return []
    return [btn.callback_data for row in markup.inline_keyboard for btn in row]


# ── /erase (no args) ──────────────────────────────────────────────────────────

def test_erase_without_args_shows_type_selector():
    update = _run("/erase")
    assert update.message.replies == ["Select type to erase:"]
    data = _callback_data(update.message.markups[0])
    assert "erase_type:expense" in data
    assert "erase_type:income" in data


# ── /erase in N (income) ──────────────────────────────────────────────────────

def test_erase_in_previews_last_n_income_records():
    update = _run("/erase in 2")
    text = update.message.replies[0]
    assert "Gift" in text
    assert "Freelance" in text
    assert "Salary" not in text


def test_erase_in_delete_button_carries_income_type():
    update = _run("/erase in 2")
    data = _callback_data(update.message.markups[0])
    assert "erase_last_n_do:2026-03:2:income" in data
    assert "erase_cancel" in data


def test_erase_in_larger_than_available_shows_all():
    update = _run("/erase in 10")
    text = update.message.replies[0]
    assert "Salary" in text
    assert "3" in text


def test_erase_in_without_records_reports_nothing_to_erase():
    store = _FakeStore(incomes=[])
    update = _run("/erase in 2", store)
    assert "No records" in update.message.replies[0]
    assert update.message.markups[0] is None


# ── /erase out N (expenses) ───────────────────────────────────────────────────

def test_erase_out_previews_last_n_expense_records():
    update = _run("/erase out 2")
    text = update.message.replies[0]
    assert "Dinner" in text
    assert "Uber" in text
    assert "Lunch" not in text


def test_erase_out_delete_button_carries_expense_type():
    update = _run("/erase out 2")
    data = _callback_data(update.message.markups[0])
    assert "erase_last_n_do:2026-03:2:expense" in data
    assert "erase_cancel" in data


def test_erase_out_without_records_reports_nothing_to_erase():
    store = _FakeStore(expenses=[])
    update = _run("/erase out 2", store)
    assert "No records" in update.message.replies[0]
    assert update.message.markups[0] is None


# ── unsupported / invalid usage ──────────────────────────────────────────────

def test_erase_with_bare_number_is_rejected():
    update = _run("/erase 3")
    assert len(update.message.replies) == 1
    assert "Usage" in update.message.replies[0]
    assert update.message.markups[0] is None


def test_erase_with_missing_count_is_rejected():
    update = _run("/erase in")
    assert "Usage" in update.message.replies[0]
    assert update.message.markups[0] is None


def test_erase_with_unknown_subcommand_is_rejected():
    update = _run("/erase foo 2")
    assert "Usage" in update.message.replies[0]
    assert update.message.markups[0] is None


def test_erase_with_non_numeric_count_is_rejected():
    update = _run("/erase in abc")
    assert "number" in update.message.replies[0]
    assert update.message.markups[0] is None


def test_erase_with_zero_count_is_rejected():
    update = _run("/erase in 0")
    assert "positive" in update.message.replies[0]
    assert update.message.markups[0] is None


def test_erase_with_negative_count_is_rejected():
    update = _run("/erase out -2")
    assert "positive" in update.message.replies[0]
    assert update.message.markups[0] is None


# ── delete confirmation (callback) ────────────────────────────────────────────

class _FakeQuery:
    def __init__(self, data):
        self.data = data
        self.answered = False
        self.edits = []

    async def answer(self):
        self.answered = True

    async def edit_message_text(self, text, **kwargs):
        self.edits.append(text)


class _FakeCallbackUpdate:
    def __init__(self, data):
        self.callback_query = _FakeQuery(data)


def _run_callback(data, store):
    update = _FakeCallbackUpdate(data)
    ctx = _FakeCtx(store)
    asyncio.run(cb_erase_last_n_do(update, ctx))
    return update


def test_delete_callback_removes_last_n_income_records(tmp_path):
    store = Storage(data_dir=str(tmp_path))
    store.append_income("2026-03", 1000.0, True, "Salary")
    store.append_income("2026-03", 500.0, False, "Freelance")
    store.append_income("2026-03", 200.0, False, "Gift")

    update = _run_callback("erase_last_n_do:2026-03:2:income", store)

    assert [name for _, _, name in store.read_income("2026-03")] == ["Salary"]
    assert "2" in update.callback_query.edits[0]


def test_delete_callback_removes_last_n_expense_records(tmp_path):
    store = Storage(data_dir=str(tmp_path))
    store.append_record("2026-03", "food", 15.0, "Lunch")
    store.append_record("2026-03", "taxi", 8.5, "Uber")
    store.append_record("2026-03", "food", 25.0, "Dinner")

    update = _run_callback("erase_last_n_do:2026-03:2:expense", store)

    assert [rec[2] for rec in store.read_month("2026-03")] == ["Lunch"]
    assert "2" in update.callback_query.edits[0]
