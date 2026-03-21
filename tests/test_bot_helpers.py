"""Tests for render_rows and field extractor helpers in bot.py."""
import sys
import os

# bot.py lives one level above tests/
sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))

from bot import (
    render_rows, _expense_field, _income_field, _build_fmt_editor,
    _format_erase_preview, _build_report_type_keyboard, _build_erase_keyboard,
    _format_balance_amount, _resolve_balance_name, _build_balance_menu,
    _build_balance_remove_confirm, render_balance_report,
)

REPORT_COLUMNS = {
    "expense": ["date", "category", "title", "amount"],
    "income":  ["amount", "taxable", "year", "month", "name"],
}


# ── render_rows ───────────────────────────────────────────────────────────────

EXPENSE_RECORDS = [
    ("2026-03-01", "food", "Lunch", "15.0"),
    ("2026-03-01", "taxi", "Uber",  "8.5"),
]


def test_render_rows_tab_expense_default_fmt():
    fmt = ["title", "", "date", "category", "amount"]
    lines = render_rows(EXPENSE_RECORDS, fmt, _expense_field)
    assert lines[0] == "Lunch\t\t2026-03-01\tfood\t15.0"
    assert lines[1] == "Uber\t\t2026-03-01\ttaxi\t8.5"


def test_render_rows_semicolon_separator():
    fmt = ["title", "amount"]
    lines = render_rows(EXPENSE_RECORDS, fmt, _expense_field, separator=";")
    assert lines[0] == "Lunch;15.0"


def test_render_rows_empty_col_produces_empty_cell():
    fmt = ["title", "", "amount"]
    lines = render_rows(EXPENSE_RECORDS, fmt, _expense_field)
    assert lines[0] == "Lunch\t\t15.0"


def test_render_rows_unknown_col_produces_empty_cell():
    fmt = ["title", "nonexistent", "amount"]
    lines = render_rows(EXPENSE_RECORDS, fmt, _expense_field)
    assert lines[0] == "Lunch\t\t15.0"


def test_render_rows_custom_order():
    fmt = ["amount", "category", "title"]
    lines = render_rows(EXPENSE_RECORDS, fmt, _expense_field)
    assert lines[0] == "15.0\tfood\tLunch"


def test_render_rows_empty_records():
    assert render_rows([], ["title", "amount"], _expense_field) == []


# ── _expense_field ────────────────────────────────────────────────────────────

def test_expense_field_all_columns():
    rec = ("2026-03-01", "food", "Lunch", "15.0")
    d = _expense_field(rec)
    assert d == {"date": "2026-03-01", "category": "food", "title": "Lunch", "amount": "15.0"}


# ── _income_field ─────────────────────────────────────────────────────────────

def test_income_field_taxable():
    rec = ("1200.0", True, "Salary")
    d = _income_field(rec, "2026-03")
    assert d == {"amount": "1200.0", "taxable": "", "year": "2026", "month": "3", "name": "Salary"}


def test_income_field_not_taxable():
    rec = ("500.0", False, "Freelance")
    d = _income_field(rec, "2026-03")
    assert d["taxable"] == "no"


def test_income_field_month_drops_leading_zero():
    rec = ("100.0", True, "Bonus")
    d = _income_field(rec, "2026-01")
    assert d["month"] == "1"
    assert d["year"] == "2026"


# ── _build_fmt_editor ─────────────────────────────────────────────────────────

def test_editor_text_header():
    fmt = ["title", "", "date"]
    text, _ = _build_fmt_editor("expense", fmt, 0)
    assert "Expense format" in text
    assert "column 1 of 3" in text
    assert "title" in text


def test_editor_text_empty_col():
    fmt = ["", "amount"]
    text, _ = _build_fmt_editor("expense", fmt, 0)
    assert "(empty)" in text


def test_editor_column_buttons_present():
    fmt = ["title"]
    _, markup = _build_fmt_editor("expense", fmt, 0)
    all_data = [btn.callback_data for row in markup.inline_keyboard for btn in row]
    # should have fmt_set buttons for each expense column + empty
    assert any("fmt_set:expense:0:title" in d for d in all_data)
    assert any("fmt_set:expense:0:" == d for d in all_data)  # empty


def test_editor_prev_is_noop_at_pos_0():
    fmt = ["title", "amount"]
    _, markup = _build_fmt_editor("expense", fmt, 0)
    all_data = [btn.callback_data for row in markup.inline_keyboard for btn in row if btn.callback_data]
    # Prev button is present but fires noop, not a real nav
    assert "noop" in all_data
    assert not any(d.endswith(":-1") for d in all_data)


def test_editor_next_is_noop_at_last_pos():
    fmt = ["title", "amount"]
    _, markup = _build_fmt_editor("expense", fmt, 1)
    all_data = [btn.callback_data for row in markup.inline_keyboard for btn in row if btn.callback_data]
    # Next button is present but fires noop, not a real nav
    assert "noop" in all_data
    assert not any(d == "fmt_nav:expense:2" for d in all_data)


def test_editor_prev_present_when_not_at_start():
    fmt = ["title", "amount", "date"]
    _, markup = _build_fmt_editor("expense", fmt, 2)
    all_data = [btn.callback_data for row in markup.inline_keyboard for btn in row if btn.callback_data]
    assert "fmt_nav:expense:1" in all_data


def test_editor_add_absent_at_max_columns():
    fmt = ["title"] * 10
    _, markup = _build_fmt_editor("expense", fmt, 0)
    all_data = [btn.callback_data for row in markup.inline_keyboard for btn in row if btn.callback_data]
    assert not any("fmt_add" in d for d in all_data)


def test_editor_del_absent_when_single_col():
    fmt = ["title"]
    _, markup = _build_fmt_editor("expense", fmt, 0)
    all_data = [btn.callback_data for row in markup.inline_keyboard for btn in row if btn.callback_data]
    assert not any("fmt_del" in d for d in all_data)


def test_editor_done_button_present():
    fmt = ["title"]
    _, markup = _build_fmt_editor("expense", fmt, 0)
    all_data = [btn.callback_data for row in markup.inline_keyboard for btn in row if btn.callback_data]
    assert "fmt_menu" in all_data


# ── _format_erase_preview ─────────────────────────────────────────────────────

def test_format_erase_preview_lists_all_records():
    records = [
        ("2026-03-01", "food", "Lunch", "15.0"),
        ("2026-03-01", "taxi", "Uber", "8.5"),
    ]
    text = _format_erase_preview(records, "2026-03")
    assert "Lunch" in text
    assert "Uber" in text


def test_format_erase_preview_shows_record_count():
    records = [
        ("2026-03-01", "food", "Lunch", "15.0"),
        ("2026-03-01", "taxi", "Uber", "8.5"),
    ]
    text = _format_erase_preview(records, "2026-03")
    assert "2" in text


def test_format_erase_preview_empty_records():
    text = _format_erase_preview([], "2026-03")
    assert "No records" in text


# ── _build_report_type_keyboard ───────────────────────────────────────────────

def test_report_type_keyboard_text():
    text, _ = _build_report_type_keyboard()
    assert "report" in text.lower()


def test_report_type_keyboard_has_expenses_button():
    _, markup = _build_report_type_keyboard()
    all_data = [btn.callback_data for row in markup.inline_keyboard for btn in row if btn.callback_data]
    assert "report_type:expense" in all_data


def test_report_type_keyboard_has_income_button():
    _, markup = _build_report_type_keyboard()
    all_data = [btn.callback_data for row in markup.inline_keyboard for btn in row if btn.callback_data]
    assert "report_type:income" in all_data


def test_report_type_keyboard_both_buttons_in_one_row():
    _, markup = _build_report_type_keyboard()
    first_row_data = [btn.callback_data for btn in markup.inline_keyboard[0] if btn.callback_data]
    assert "report_type:expense" in first_row_data
    assert "report_type:income" in first_row_data


# ── _build_erase_keyboard ─────────────────────────────────────────────────────

EXPENSE_SNAP = [
    ("2026-03-01", "food", "Lunch", "15.0"),
    ("2026-03-01", "taxi", "Uber",  "8.5"),
]
INCOME_SNAP = [
    ("1000.0", True,  "Salary"),
    ("200.0",  False, "Gift"),
]


def _state(type_="expense", month="2026-03", records=None, selected=None, page=0):
    return {
        "type": type_,
        "month": month,
        "records": records if records is not None else EXPENSE_SNAP,
        "selected": selected if selected is not None else set(),
        "page": page,
    }


def _all_cb(markup):
    return [btn.callback_data for row in markup.inline_keyboard for btn in row if btn.callback_data]


def test_erase_keyboard_message_text_no_pagination():
    text, _ = _build_erase_keyboard(_state())
    assert "expenses" in text
    assert "March 2026" in text
    assert "0 selected" in text
    assert "Page" not in text


def test_erase_keyboard_message_text_with_pagination():
    records = [("2026-03-01", "F", f"item{i}", str(i)) for i in range(20)]
    text, _ = _build_erase_keyboard(_state(records=records, page=1))
    assert "Page 2/" in text


def test_erase_keyboard_select_all_unselected():
    _, markup = _build_erase_keyboard(_state())
    first_btn = markup.inline_keyboard[0][0]
    assert "☐" in first_btn.text
    assert "All" in first_btn.text
    assert first_btn.callback_data == "erase_toggle_all"


def test_erase_keyboard_select_all_fully_selected():
    _, markup = _build_erase_keyboard(_state(selected={0, 1}))
    first_btn = markup.inline_keyboard[0][0]
    assert "☑" in first_btn.text


def test_erase_keyboard_select_all_partial_shows_unchecked():
    _, markup = _build_erase_keyboard(_state(selected={0}))
    first_btn = markup.inline_keyboard[0][0]
    assert "☐" in first_btn.text


def test_erase_keyboard_expense_record_label():
    _, markup = _build_erase_keyboard(_state(selected=set()))
    # first record row (index 1 in keyboard — row 0 is Select All)
    record_btn = markup.inline_keyboard[1][0]
    assert "food" in record_btn.text or "Lunch" in record_btn.text
    assert record_btn.callback_data == "erase_toggle:0"


def test_erase_keyboard_selected_record_shows_checkmark():
    _, markup = _build_erase_keyboard(_state(selected={0}))
    record_btn = markup.inline_keyboard[1][0]
    assert "☑" in record_btn.text


def test_erase_keyboard_unselected_record_shows_empty():
    _, markup = _build_erase_keyboard(_state(selected={1}))
    record_btn = markup.inline_keyboard[1][0]
    assert "☐" in record_btn.text


def test_erase_keyboard_income_taxable_label():
    state = _state(type_="income", records=INCOME_SNAP)
    _, markup = _build_erase_keyboard(state)
    record_btn = markup.inline_keyboard[1][0]
    assert "(taxable)" in record_btn.text


def test_erase_keyboard_income_not_taxable_no_label():
    state = _state(type_="income", records=INCOME_SNAP)
    _, markup = _build_erase_keyboard(state)
    record_btn = markup.inline_keyboard[2][0]
    assert "(taxable)" not in record_btn.text
    assert "Gift" in record_btn.text


def test_erase_keyboard_no_pagination_for_15_records():
    records = [("2026-03-01", "F", f"i{i}", str(i)) for i in range(15)]
    _, markup = _build_erase_keyboard(_state(records=records))
    all_cb = _all_cb(markup)
    assert not any("erase_page:" in d for d in all_cb)


def test_erase_keyboard_pagination_for_16_records():
    records = [("2026-03-01", "F", f"i{i}", str(i)) for i in range(16)]
    _, markup = _build_erase_keyboard(_state(records=records))
    all_cb = _all_cb(markup)
    assert any("erase_page:" in d for d in all_cb)


def test_erase_keyboard_pagination_shows_10_records_per_page():
    records = [("2026-03-01", "F", f"i{i}", str(i)) for i in range(20)]
    _, markup = _build_erase_keyboard(_state(records=records, page=0))
    toggle_buttons = [d for d in _all_cb(markup) if d.startswith("erase_toggle:") and d != "erase_toggle_all"]
    assert len(toggle_buttons) == 10


def test_erase_keyboard_delete_button_shows_count():
    _, markup = _build_erase_keyboard(_state(selected={0, 1}))
    all_cb = _all_cb(markup)
    assert "erase_do_selected" in all_cb
    # find the delete button text
    for row in markup.inline_keyboard:
        for btn in row:
            if btn.callback_data == "erase_do_selected":
                assert "2" in btn.text


def test_erase_keyboard_back_and_cancel_present():
    _, markup = _build_erase_keyboard(_state())
    all_cb = _all_cb(markup)
    assert "erase_back_months:expense" in all_cb
    assert "erase_cancel" in all_cb


def test_erase_keyboard_prev_absent_on_first_page():
    records = [("2026-03-01", "F", f"i{i}", str(i)) for i in range(20)]
    _, markup = _build_erase_keyboard(_state(records=records, page=0))
    all_cb = _all_cb(markup)
    assert not any(d == "erase_page:-1" for d in all_cb)


def test_erase_keyboard_next_absent_on_last_page():
    records = [("2026-03-01", "F", f"i{i}", str(i)) for i in range(16)]
    _, markup = _build_erase_keyboard(_state(records=records, page=1))
    all_cb = _all_cb(markup)
    assert "erase_page:2" not in all_cb


# ── _format_balance_amount ────────────────────────────────────────────────────

def test_format_balance_amount_none_returns_dash():
    assert _format_balance_amount(None) == "—"


def test_format_balance_amount_whole_float_no_decimal():
    assert _format_balance_amount(5000.0) == "5000"


def test_format_balance_amount_fractional_keeps_decimal():
    assert _format_balance_amount(5000.5) == "5000.5"


# ── _resolve_balance_name ─────────────────────────────────────────────────────

def test_resolve_balance_exact_single_match():
    matched, candidates = _resolve_balance_name("savings", ["Savings", "Checking"])
    assert matched == "Savings"
    assert candidates == []


def test_resolve_balance_fuzzy_single_match():
    matched, candidates = _resolve_balance_name("saving", ["Savings", "Checking"])
    assert matched == "Savings"
    assert candidates == []


def test_resolve_balance_multiple_matches_returns_none_and_list():
    matched, candidates = _resolve_balance_name("saving", ["Savings1", "Savings2"])
    assert matched is None
    assert len(candidates) >= 1


def test_resolve_balance_no_match_returns_empty_candidates():
    matched, candidates = _resolve_balance_name("zzz", ["Savings", "Checking"])
    assert matched is None
    assert candidates == []


def test_resolve_balance_empty_names_returns_none():
    matched, candidates = _resolve_balance_name("savings", [])
    assert matched is None
    assert candidates == []


def test_resolve_balance_case_insensitive():
    matched, candidates = _resolve_balance_name("SAVINGS", ["Savings"])
    assert matched == "Savings"


# ── _build_balance_menu ───────────────────────────────────────────────────────

def _balance_menu_cb(markup):
    return [btn.callback_data for row in markup.inline_keyboard for btn in row if btn.callback_data]


def test_balance_menu_text_includes_month():
    text, _ = _build_balance_menu("2026-03", ["Savings"], {"Savings": 5000.0})
    assert "March 2026" in text


def test_balance_menu_shows_balance_with_value():
    _, markup = _build_balance_menu("2026-03", ["Savings"], {"Savings": 5000.0})
    texts = [btn.text for row in markup.inline_keyboard for btn in row]
    assert any("Savings" in t and "5000" in t for t in texts)


def test_balance_menu_shows_dash_when_no_value():
    _, markup = _build_balance_menu("2026-03", ["Savings"], {})
    texts = [btn.text for row in markup.inline_keyboard for btn in row]
    assert any("Savings" in t and "—" in t for t in texts)


def test_balance_menu_has_add_remove_done_buttons():
    _, markup = _build_balance_menu("2026-03", ["Savings"], {})
    cbs = _balance_menu_cb(markup)
    assert "balance_add" in cbs
    assert "balance_remove" in cbs
    assert "balance_done" in cbs


def test_balance_menu_balance_button_callback():
    _, markup = _build_balance_menu("2026-03", ["Savings"], {})
    cbs = _balance_menu_cb(markup)
    assert any(cb.startswith("balance_set:Savings") for cb in cbs)


def test_balance_menu_empty_names_no_balance_buttons():
    _, markup = _build_balance_menu("2026-03", [], {})
    cbs = _balance_menu_cb(markup)
    assert not any(cb.startswith("balance_set:") for cb in cbs)


# ── _build_balance_remove_confirm ─────────────────────────────────────────────

def test_balance_remove_confirm_text_includes_name():
    text, _ = _build_balance_remove_confirm("Savings")
    assert "Savings" in text


def test_balance_remove_confirm_has_three_buttons():
    _, markup = _build_balance_remove_confirm("Savings")
    cbs = [btn.callback_data for row in markup.inline_keyboard for btn in row if btn.callback_data]
    assert "balance_remove_keep:Savings" in cbs
    assert "balance_remove_delete:Savings" in cbs
    assert "balance_remove_cancel" in cbs


# ── render_balance_report ─────────────────────────────────────────────────────

def test_render_balance_report_header_row():
    lines = render_balance_report(
        months=["2026-03"],
        historic_names=["Savings", "Checking"],
        month_data={"2026-03": {"Savings": 5000.0}},
        separator="\t",
    )
    assert lines[0] == "month\tSavings\tChecking"


def test_render_balance_report_data_row_with_value():
    lines = render_balance_report(
        months=["2026-03"],
        historic_names=["Savings"],
        month_data={"2026-03": {"Savings": 5000.0}},
        separator="\t",
    )
    assert lines[1] == "2026-03\t5000"


def test_render_balance_report_missing_value_is_empty():
    lines = render_balance_report(
        months=["2026-03"],
        historic_names=["Savings", "Checking"],
        month_data={"2026-03": {"Savings": 5000.0}},
        separator="\t",
    )
    assert lines[1] == "2026-03\t5000\t"


def test_render_balance_report_semicolon_separator():
    lines = render_balance_report(
        months=["2026-03"],
        historic_names=["Savings"],
        month_data={"2026-03": {"Savings": 1200.0}},
        separator=";",
    )
    assert lines[1] == "2026-03;1200"


def test_render_balance_report_multiple_months_order_preserved():
    lines = render_balance_report(
        months=["2026-03", "2026-02"],
        historic_names=["Savings"],
        month_data={
            "2026-03": {"Savings": 5000.0},
            "2026-02": {"Savings": 4800.0},
        },
        separator="\t",
    )
    assert "2026-03" in lines[1]
    assert "2026-02" in lines[2]


def test_render_balance_report_empty_returns_header_only():
    lines = render_balance_report([], ["Savings"], {}, separator="\t")
    assert lines == ["month\tSavings"]


# ── report type keyboard (updated for balance) ────────────────────────────────

def test_report_type_keyboard_has_balances_button():
    _, markup = _build_report_type_keyboard()
    all_data = [btn.callback_data for row in markup.inline_keyboard for btn in row if btn.callback_data]
    assert "report_type:balance" in all_data
