"""Tests for multi-user support: USER_IDS parsing and per-user data isolation."""

import sys
import os

# bot.py lives one level above tests/
sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))

import pytest
from bot import parse_user_ids
from storage import Storage


# ── parse_user_ids ────────────────────────────────────────────────────────────

def test_parse_user_ids_basic():
    assert parse_user_ids("111,222") == [111, 222]


def test_parse_user_ids_tolerates_whitespace_and_trailing_comma():
    assert parse_user_ids(" 111 , 222 , ") == [111, 222]


def test_parse_user_ids_deduplicates_keeping_first_occurrence():
    assert parse_user_ids("222,111,222") == [222, 111]


def test_parse_user_ids_rejects_non_integer():
    with pytest.raises(ValueError):
        parse_user_ids("111,abc")


def test_parse_user_ids_empty_string():
    assert parse_user_ids("") == []


def test_parse_user_ids_single_value():
    assert parse_user_ids("483387792") == [483387792]


# ── per-user data isolation ───────────────────────────────────────────────────

def test_users_never_see_each_others_data(tmp_path):
    alice = Storage(data_dir=str(tmp_path / "111"))
    bob = Storage(data_dir=str(tmp_path / "222"))

    alice.append_record("2026-10", "F", 100.0, "alice lunch")
    alice.append_income("2026-10", 1500.0, False, "alice bonus")
    bob.append_record("2026-10", "T", 200.0, "bob taxi")

    alice_expenses = alice.read_month("2026-10")
    bob_expenses = bob.read_month("2026-10")
    assert [(t, a) for _, _, t, a in alice_expenses] == [("alice lunch", "100.0")]
    assert [(t, a) for _, _, t, a in bob_expenses] == [("bob taxi", "200.0")]

    alice_income = alice.read_income("2026-10")
    assert [n for _, _, n in alice_income] == ["alice bonus"]
    assert bob.read_income("2026-10") == []


def test_month_state_not_shared_between_users(tmp_path):
    alice = Storage(data_dir=str(tmp_path / "111"))
    bob = Storage(data_dir=str(tmp_path / "222"))

    alice.set_current_month("2025-01")
    assert alice.get_current_month() == "2025-01"
    assert bob.get_current_month() != "2025-01"


def test_settings_not_shared_between_users(tmp_path):
    alice = Storage(data_dir=str(tmp_path / "111"))
    bob = Storage(data_dir=str(tmp_path / "222"))

    alice.set_format("expense", ["title"])
    assert alice.get_format("expense") == ["title"]
    assert bob.get_format("expense") != ["title"]


def test_user_data_persists_in_own_directory(tmp_path):
    first = Storage(data_dir=str(tmp_path / "111"))
    first.append_record("2026-10", "F", 42.0, "keep me")

    reconnected = Storage(data_dir=str(tmp_path / "111"))
    assert [t for _, _, t, _ in reconnected.read_month("2026-10")] == ["keep me"]


# ── legacy single-DB migration ────────────────────────────────────────────────

import bot as bot_module


def test_migrate_legacy_store_moves_db_into_first_users_dir(monkeypatch, tmp_path):
    monkeypatch.setattr(bot_module, "DATA_DIR", tmp_path)
    (tmp_path / "storage.db").write_text("legacy")
    (tmp_path / "storage.db-wal").write_text("wal")

    bot_module._migrate_legacy_store([111, 222])

    assert (tmp_path / "111" / "storage.db").read_text() == "legacy"
    assert (tmp_path / "111" / "storage.db-wal").read_text() == "wal"
    assert not (tmp_path / "storage.db").exists()
    # second user gets nothing
    assert not (tmp_path / "222" / "storage.db").exists()


def test_migrate_legacy_store_not_overwriting_existing_user_data(monkeypatch, tmp_path):
    monkeypatch.setattr(bot_module, "DATA_DIR", tmp_path)
    (tmp_path / "storage.db").write_text("legacy")
    target = tmp_path / "111"
    target.mkdir()
    (target / "storage.db").write_text("already there")

    bot_module._migrate_legacy_store([111])

    assert (target / "storage.db").read_text() == "already there"
    assert (tmp_path / "storage.db").read_text() == "legacy"


def test_migrate_legacy_store_noop_without_legacy_db(monkeypatch, tmp_path):
    monkeypatch.setattr(bot_module, "DATA_DIR", tmp_path)

    bot_module._migrate_legacy_store([111])

    assert list(tmp_path.iterdir()) == []
