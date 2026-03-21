"""Tests for storage.py — uses a temp dir per test, no real data/ dir touched."""

import pytest
import json
from pathlib import Path
from datetime import date
from storage import Storage


@pytest.fixture
def tmp_store(tmp_path):
    return Storage(data_dir=str(tmp_path))


# ── current month ─────────────────────────────────────────────────────────────

def test_default_month_is_today(tmp_store):
    expected = date.today().strftime("%Y-%m")
    assert tmp_store.get_current_month() == expected


def test_set_and_get_current_month(tmp_store):
    tmp_store.set_current_month("2025-11")
    assert tmp_store.get_current_month() == "2025-11"


def test_persistence_across_instances(tmp_path):
    s1 = Storage(data_dir=str(tmp_path))
    s1.set_current_month("2024-06")
    s2 = Storage(data_dir=str(tmp_path))
    assert s2.get_current_month() == "2024-06"


def test_state_file_contents(tmp_path):
    s = Storage(data_dir=str(tmp_path))
    s.set_current_month("2026-01")
    state = json.loads((tmp_path / "state.json").read_text())
    assert state == {"current_month": "2026-01"}


# ── append + read ─────────────────────────────────────────────────────────────

def test_append_and_read_round_trip(tmp_store):
    tmp_store.append_record("2026-03", "F", 150.0, "")
    records = tmp_store.read_month("2026-03")
    assert len(records) == 1
    date_str, cat, title, sum_str = records[0]
    assert date_str == "2026-03-01"
    assert cat == "F"
    assert title == ""
    assert sum_str == "150.0"


def test_append_multiple_records(tmp_store):
    tmp_store.append_record("2026-03", "h", 45.0, "Vitamins")
    tmp_store.append_record("2026-03", "TT", 80.0, "Taxi")
    records = tmp_store.read_month("2026-03")
    assert len(records) == 2
    assert records[0][2] == "Vitamins"
    assert records[1][1] == "TT"


def test_read_nonexistent_month_returns_empty(tmp_store):
    assert tmp_store.read_month("2000-01") == []


def test_record_file_format(tmp_path):
    s = Storage(data_dir=str(tmp_path))
    s.append_record("2026-03", "F", 150.0, "Lunch")
    lines = (tmp_path / "outcome-2026-03.txt").read_text().strip().splitlines()
    assert lines[0] == "2026-03-01|F|Lunch|150.0"


def test_empty_category_stored(tmp_store):
    tmp_store.append_record("2026-03", "", 10.0, "misc")
    records = tmp_store.read_month("2026-03")
    assert records[0][1] == ""


# ── list months ───────────────────────────────────────────────────────────────

def test_list_months_with_counts(tmp_store):
    tmp_store.append_record("2026-03", "F", 100.0, "")
    tmp_store.append_record("2026-03", "h", 50.0, "")
    tmp_store.append_record("2026-02", "r", 1200.0, "")
    months = tmp_store.list_months_with_counts()
    assert ("2026-03", 2) in months
    assert ("2026-02", 1) in months
    # newest first
    assert months[0][0] > months[1][0]


def test_list_months_empty(tmp_store):
    assert tmp_store.list_months_with_counts() == []


# ── delete ────────────────────────────────────────────────────────────────────

def test_delete_month(tmp_store):
    tmp_store.append_record("2026-03", "F", 100.0, "")
    tmp_store.delete_month("2026-03")
    assert tmp_store.read_month("2026-03") == []


def test_delete_nonexistent_month_no_error(tmp_store):
    tmp_store.delete_month("2000-01")  # should not raise


def test_delete_all_removes_month_files(tmp_path):
    s = Storage(data_dir=str(tmp_path))
    s.append_record("2026-03", "F", 100.0, "")
    s.append_record("2026-02", "h", 50.0, "")
    s.set_current_month("2026-03")
    s.delete_all()
    assert s.read_month("2026-03") == []
    assert s.read_month("2026-02") == []


def test_delete_all_keeps_state_json(tmp_path):
    s = Storage(data_dir=str(tmp_path))
    s.set_current_month("2026-03")
    s.append_record("2026-03", "F", 100.0, "")
    s.delete_all()
    # state.json still readable and correct
    assert s.get_current_month() == "2026-03"


# ── read-modify-write ─────────────────────────────────────────────────────────

def test_set_month_preserves_other_keys(tmp_path):
    """set_current_month must not destroy other state.json keys."""
    state_file = tmp_path / "state.json"
    state_file.write_text('{"expense_format": ["title", "amount"]}')
    s = Storage(data_dir=str(tmp_path))
    s.set_current_month("2026-05")
    state = json.loads(state_file.read_text())
    assert state["current_month"] == "2026-05"
    assert state["expense_format"] == ["title", "amount"]


def test_get_month_with_format_only_state(tmp_path):
    """get_current_month must not raise if state.json has no current_month key."""
    state_file = tmp_path / "state.json"
    state_file.write_text('{"expense_format": ["title", "amount"]}')
    s = Storage(data_dir=str(tmp_path))
    expected = date.today().strftime("%Y-%m")
    assert s.get_current_month() == expected


# ── format ────────────────────────────────────────────────────────────────────

DEFAULT_EXPENSE = ["title", "", "date", "category", "amount"]
DEFAULT_INCOME  = ["amount", "taxable", "year", "month", "name"]


def test_get_format_returns_default_when_absent(tmp_store):
    assert tmp_store.get_format("expense") == DEFAULT_EXPENSE
    assert tmp_store.get_format("income") == DEFAULT_INCOME


def test_set_and_get_format_expense(tmp_store):
    fmt = ["date", "amount", ""]
    tmp_store.set_format("expense", fmt)
    assert tmp_store.get_format("expense") == fmt


def test_set_and_get_format_income(tmp_store):
    fmt = ["name", "amount"]
    tmp_store.set_format("income", fmt)
    assert tmp_store.get_format("income") == fmt


def test_set_format_preserves_current_month(tmp_store):
    tmp_store.set_current_month("2025-11")
    tmp_store.set_format("expense", ["amount"])
    assert tmp_store.get_current_month() == "2025-11"


def test_set_month_preserves_format(tmp_store):
    tmp_store.set_format("expense", ["amount", "title"])
    tmp_store.set_current_month("2025-12")
    assert tmp_store.get_format("expense") == ["amount", "title"]


def test_format_persistence_across_instances(tmp_path):
    s1 = Storage(data_dir=str(tmp_path))
    s1.set_format("expense", ["title", "date"])
    s2 = Storage(data_dir=str(tmp_path))
    assert s2.get_format("expense") == ["title", "date"]


# ── delete_last_n_records ─────────────────────────────────────────────────────

def test_delete_last_n_returns_deleted_records(tmp_store):
    tmp_store.append_record("2026-03", "F", 100.0, "A")
    tmp_store.append_record("2026-03", "h", 200.0, "B")
    tmp_store.append_record("2026-03", "TT", 300.0, "C")
    deleted = tmp_store.delete_last_n_records("2026-03", 2)
    assert len(deleted) == 2
    assert deleted[0][2] == "B"
    assert deleted[1][2] == "C"


def test_delete_last_n_removes_from_storage(tmp_store):
    tmp_store.append_record("2026-03", "F", 100.0, "A")
    tmp_store.append_record("2026-03", "h", 200.0, "B")
    tmp_store.delete_last_n_records("2026-03", 1)
    remaining = tmp_store.read_month("2026-03")
    assert len(remaining) == 1
    assert remaining[0][2] == "A"


def test_delete_last_n_exceeds_count_deletes_all(tmp_store):
    tmp_store.append_record("2026-03", "F", 100.0, "A")
    deleted = tmp_store.delete_last_n_records("2026-03", 5)
    assert len(deleted) == 1
    assert tmp_store.read_month("2026-03") == []


def test_delete_last_n_zero_deletes_nothing(tmp_store):
    tmp_store.append_record("2026-03", "F", 100.0, "A")
    deleted = tmp_store.delete_last_n_records("2026-03", 0)
    assert deleted == []
    assert len(tmp_store.read_month("2026-03")) == 1


def test_delete_last_n_empty_month_returns_empty(tmp_store):
    deleted = tmp_store.delete_last_n_records("2026-03", 3)
    assert deleted == []


# ── delete_expense_records_by_index ───────────────────────────────────────────

def test_delete_expense_by_index_removes_correct_records(tmp_store):
    tmp_store.append_record("2026-03", "F", 100.0, "A")
    tmp_store.append_record("2026-03", "h", 200.0, "B")
    tmp_store.append_record("2026-03", "TT", 300.0, "C")
    count = tmp_store.delete_expense_records_by_index("2026-03", {0, 2})
    assert count == 2
    remaining = tmp_store.read_month("2026-03")
    assert len(remaining) == 1
    assert remaining[0][2] == "B"


def test_delete_expense_by_index_all_records_removes_file(tmp_path):
    s = Storage(data_dir=str(tmp_path))
    s.append_record("2026-03", "F", 100.0, "A")
    count = s.delete_expense_records_by_index("2026-03", {0})
    assert count == 1
    assert s.read_month("2026-03") == []
    assert not (tmp_path / "outcome-2026-03.txt").exists()


def test_delete_expense_by_index_empty_indices_no_op(tmp_store):
    tmp_store.append_record("2026-03", "F", 100.0, "A")
    count = tmp_store.delete_expense_records_by_index("2026-03", set())
    assert count == 0
    assert len(tmp_store.read_month("2026-03")) == 1


def test_delete_expense_by_index_preserves_format(tmp_path):
    """Rewritten file must be parseable by read_month (no header corruption)."""
    s = Storage(data_dir=str(tmp_path))
    s.append_record("2026-03", "F", 99.5, "Lunch")
    s.append_record("2026-03", "h", 10.0, "Tea")
    s.delete_expense_records_by_index("2026-03", {1})
    records = s.read_month("2026-03")
    assert len(records) == 1
    assert records[0] == ("2026-03-01", "F", "Lunch", "99.5")


# ── delete_income_records_by_index ───────────────────────────────────────────

def test_delete_income_by_index_removes_correct_records(tmp_store):
    tmp_store.append_income("2026-03", 1000.0, True, "Salary")
    tmp_store.append_income("2026-03", 500.0, False, "Freelance")
    tmp_store.append_income("2026-03", 200.0, True, "Bonus")
    count = tmp_store.delete_income_records_by_index("2026-03", {1})
    assert count == 1
    remaining = tmp_store.read_income("2026-03")
    assert len(remaining) == 2
    assert remaining[0][2] == "Salary"
    assert remaining[1][2] == "Bonus"


def test_delete_income_by_index_all_records_removes_file(tmp_path):
    s = Storage(data_dir=str(tmp_path))
    s.append_income("2026-03", 500.0, True, "Pay")
    count = s.delete_income_records_by_index("2026-03", {0})
    assert count == 1
    assert s.read_income("2026-03") == []
    assert not (tmp_path / "income-2026-03.txt").exists()


def test_delete_income_by_index_empty_indices_no_op(tmp_store):
    tmp_store.append_income("2026-03", 500.0, True, "Pay")
    count = tmp_store.delete_income_records_by_index("2026-03", set())
    assert count == 0
    assert len(tmp_store.read_income("2026-03")) == 1


def test_delete_income_by_index_preserves_taxable_flag(tmp_path):
    """Taxable field must survive the rewrite as raw '0'/'1', not bool repr."""
    s = Storage(data_dir=str(tmp_path))
    s.append_income("2026-03", 1000.0, True, "Salary")
    s.append_income("2026-03", 200.0, False, "Gift")
    s.delete_income_records_by_index("2026-03", {0})
    records = s.read_income("2026-03")
    assert len(records) == 1
    amount_str, taxable, name = records[0]
    assert amount_str == "200.0"
    assert taxable is False
    assert name == "Gift"


# ── balances ──────────────────────────────────────────────────────────────────

def test_get_balance_names_empty_when_no_file(tmp_store):
    assert tmp_store.get_balance_names() == []


def test_get_historic_names_empty_when_no_file(tmp_store):
    assert tmp_store.get_historic_names() == []


def test_balances_file_not_created_on_read(tmp_path):
    s = Storage(data_dir=str(tmp_path))
    s.get_balance_names()
    assert not (tmp_path / "balances.json").exists()


def test_add_balance_name_appears_in_both_lists(tmp_store):
    tmp_store.add_balance_name("Savings")
    assert "Savings" in tmp_store.get_balance_names()
    assert "Savings" in tmp_store.get_historic_names()


def test_add_balance_name_noop_if_already_current(tmp_store):
    tmp_store.add_balance_name("Savings")
    tmp_store.add_balance_name("Savings")
    assert tmp_store.get_balance_names().count("Savings") == 1


def test_add_balance_name_readds_to_current_only_if_in_historic(tmp_path):
    """Name removed with keep_history=True: re-adding puts it back in current only."""
    s = Storage(data_dir=str(tmp_path))
    s.add_balance_name("Savings")
    s.remove_balance_name("Savings", keep_history=True)
    assert "Savings" not in s.get_balance_names()
    assert "Savings" in s.get_historic_names()
    s.add_balance_name("Savings")
    assert "Savings" in s.get_balance_names()
    assert s.get_historic_names().count("Savings") == 1  # not duplicated


def test_add_balance_name_persists(tmp_path):
    s1 = Storage(data_dir=str(tmp_path))
    s1.add_balance_name("Checking")
    s2 = Storage(data_dir=str(tmp_path))
    assert "Checking" in s2.get_balance_names()


def test_remove_balance_name_keep_history(tmp_store):
    tmp_store.add_balance_name("Savings")
    tmp_store.remove_balance_name("Savings", keep_history=True)
    assert "Savings" not in tmp_store.get_balance_names()
    assert "Savings" in tmp_store.get_historic_names()


def test_remove_balance_name_delete_history(tmp_store):
    tmp_store.add_balance_name("Savings")
    tmp_store.set_balance("2026-03", "Savings", 5000.0)
    tmp_store.remove_balance_name("Savings", keep_history=False)
    assert "Savings" not in tmp_store.get_balance_names()
    assert "Savings" not in tmp_store.get_historic_names()
    assert tmp_store.get_balance_month("2026-03") == {}


def test_remove_balance_name_prunes_empty_months(tmp_store):
    tmp_store.add_balance_name("Savings")
    tmp_store.set_balance("2026-03", "Savings", 5000.0)
    tmp_store.remove_balance_name("Savings", keep_history=False)
    assert "2026-03" not in tmp_store._read_balances()["months"]


def test_remove_balance_name_noop_for_unknown(tmp_store):
    tmp_store.remove_balance_name("Ghost", keep_history=False)  # must not raise


def test_remove_balance_name_keeps_other_names(tmp_store):
    tmp_store.add_balance_name("Savings")
    tmp_store.add_balance_name("Checking")
    tmp_store.remove_balance_name("Savings", keep_history=False)
    assert "Checking" in tmp_store.get_balance_names()


def test_set_balance_upserts_value(tmp_store):
    tmp_store.add_balance_name("Savings")
    tmp_store.set_balance("2026-03", "Savings", 5000.0)
    assert tmp_store.get_balance_month("2026-03") == {"Savings": 5000.0}


def test_set_balance_latest_wins(tmp_store):
    tmp_store.add_balance_name("Savings")
    tmp_store.set_balance("2026-03", "Savings", 4000.0)
    tmp_store.set_balance("2026-03", "Savings", 5000.0)
    assert tmp_store.get_balance_month("2026-03")["Savings"] == 5000.0


def test_set_balance_raises_for_unknown_name(tmp_store):
    with pytest.raises(ValueError):
        tmp_store.set_balance("2026-03", "Ghost", 1000.0)


def test_get_balance_month_absent_returns_empty(tmp_store):
    assert tmp_store.get_balance_month("2026-01") == {}


def test_list_balance_months_sorted_descending(tmp_store):
    tmp_store.add_balance_name("Savings")
    tmp_store.set_balance("2026-01", "Savings", 100.0)
    tmp_store.set_balance("2026-03", "Savings", 300.0)
    tmp_store.set_balance("2026-02", "Savings", 200.0)
    months = tmp_store.list_balance_months()
    assert months == ["2026-03", "2026-02", "2026-01"]


def test_list_balance_months_empty_when_no_data(tmp_store):
    assert tmp_store.list_balance_months() == []
