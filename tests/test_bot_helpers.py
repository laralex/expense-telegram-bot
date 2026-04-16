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
    _build_all_expenses_tsv, _build_all_income_tsv, _build_all_balances_tsv,
    _format_ccy_amount,
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


def test_balance_menu_shows_balance_with_currency_sign_rub():
    _, markup = _build_balance_menu(
        "2026-03", ["Savings"], {"Savings": 5000.0},
        currencies={"Savings": "RUB"},
    )
    texts = [btn.text for row in markup.inline_keyboard for btn in row]
    assert any("Savings" in t and "₽" in t and "5" in t for t in texts)


def test_balance_menu_shows_balance_with_currency_sign_usd():
    _, markup = _build_balance_menu(
        "2026-03", ["Wise"], {"Wise": 1000.0},
        currencies={"Wise": "USD"},
        rates={"USD": {"2026-03": 88.5}},
    )
    texts = [btn.text for row in markup.inline_keyboard for btn in row]
    assert any("Wise" in t and "$" in t for t in texts)


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

def test_render_balance_report_header_with_currency_signs():
    lines = render_balance_report(
        months=["2026-03"],
        historic_names=["Savings", "Wise"],
        month_data={"2026-03": {"Savings": 5000.0}},
        separator="\t",
        currencies={"Savings": "RUB", "Wise": "USD"},
        rates={"USD": {"2026-03": 88.5}},
    )
    header = lines[0]
    assert "Savings (\u20bd)" in header
    assert "Wise ($)" in header
    assert "USD" in header  # rate column
    assert "Total RUB" not in header  # no total column


def test_render_balance_report_no_total_column():
    lines = render_balance_report(
        months=["2026-03"],
        historic_names=["Savings"],
        month_data={"2026-03": {"Savings": 5000.0}},
        separator="\t",
        currencies={"Savings": "RUB"},
    )
    assert "Total" not in lines[0]


def test_render_balance_report_data_row_values():
    lines = render_balance_report(
        months=["2026-03"],
        historic_names=["Savings"],
        month_data={"2026-03": {"Savings": 5000.0}},
        separator="\t",
        currencies={"Savings": "RUB"},
    )
    assert lines[1] == "2026-03\t5000"


def test_render_balance_report_missing_value_is_empty():
    lines = render_balance_report(
        months=["2026-03"],
        historic_names=["Savings", "Checking"],
        month_data={"2026-03": {"Savings": 5000.0}},
        separator="\t",
        currencies={"Savings": "RUB", "Checking": "RUB"},
    )
    assert lines[1] == "2026-03\t5000\t"


def test_render_balance_report_semicolon_separator():
    lines = render_balance_report(
        months=["2026-03"],
        historic_names=["Savings"],
        month_data={"2026-03": {"Savings": 1200.0}},
        separator=";",
        currencies={"Savings": "RUB"},
    )
    assert lines[1] == "2026-03;1200"


def test_render_balance_report_inline_rate_columns():
    lines = render_balance_report(
        months=["2026-03"],
        historic_names=["Savings", "Wise"],
        month_data={"2026-03": {"Savings": 1000.0, "Wise": 100.0}},
        separator="\t",
        currencies={"Savings": "RUB", "Wise": "USD"},
        rates={"USD": {"2026-03": 88.5}},
    )
    # Header should have rate column for USD
    parts = lines[0].split("\t")
    assert "USD" in parts
    # Data row should have rate value
    data_parts = lines[1].split("\t")
    assert "88.5" in data_parts


def test_render_balance_report_multiple_rate_columns():
    lines = render_balance_report(
        months=["2026-03"],
        historic_names=["Tinkoff", "Wise", "Broker"],
        month_data={"2026-03": {"Tinkoff": 100000.0, "Wise": 1000.0, "Broker": 500.0}},
        separator="\t",
        currencies={"Tinkoff": "RUB", "Wise": "USD", "Broker": "EUR"},
        rates={"USD": {"2026-03": 88.5}, "EUR": {"2026-03": 96.2}},
    )
    header_parts = lines[0].split("\t")
    # Should have: month, Tinkoff (₽), Wise ($), Broker (€), USD, EUR
    assert len(header_parts) == 6
    assert "USD" in header_parts
    assert "EUR" in header_parts


def test_render_balance_report_missing_rate_shows_empty():
    lines = render_balance_report(
        months=["2026-03"],
        historic_names=["Wise"],
        month_data={"2026-03": {"Wise": 100.0}},
        separator="\t",
        currencies={"Wise": "USD"},
        rates={},
    )
    data_parts = lines[1].split("\t")
    # Wise value, then empty rate column
    assert data_parts == ["2026-03", "100", ""]


def test_render_balance_report_no_rate_columns_for_rub_only():
    lines = render_balance_report(
        months=["2026-03"],
        historic_names=["Savings"],
        month_data={"2026-03": {"Savings": 5000.0}},
        separator="\t",
        currencies={"Savings": "RUB"},
    )
    header_parts = lines[0].split("\t")
    # Only: month, Savings (₽)
    assert len(header_parts) == 2


def test_render_balance_report_multiple_months_with_rates():
    lines = render_balance_report(
        months=["2026-03", "2026-02"],
        historic_names=["Wise"],
        month_data={
            "2026-03": {"Wise": 1000.0},
            "2026-02": {"Wise": 900.0},
        },
        separator="\t",
        currencies={"Wise": "USD"},
        rates={"USD": {"2026-03": 88.5, "2026-02": 90.0}},
    )
    assert "88.5" in lines[1]
    assert "90.0" in lines[2]


def test_render_balance_report_empty_returns_header_only():
    lines = render_balance_report(
        [], ["Savings"], {},
        separator="\t",
        currencies={"Savings": "RUB"},
    )
    assert len(lines) == 1
    assert "Savings" in lines[0]


def test_convert_to_rub_rub_shortcut():
    from bot import convert_to_rub
    assert convert_to_rub(1000.0, "RUB", "2026-03", {}) == 1000.0


def test_convert_to_rub_usd_conversion():
    from bot import convert_to_rub
    assert convert_to_rub(100.0, "USD", "2026-03", {"USD": {"2026-03": 92.0}}) == 9200.0


def test_convert_to_rub_missing_rate_is_none():
    from bot import convert_to_rub
    assert convert_to_rub(100.0, "USD", "2026-03", {}) is None


def test_balance_menu_has_edit_button():
    _, markup = _build_balance_menu("2026-03", ["Savings"], {})
    cbs = _balance_menu_cb(markup)
    assert "balance_edit" in cbs


def test_balance_menu_per_currency_subtotals():
    text, _ = _build_balance_menu(
        "2026-03",
        ["Tinkoff", "Wise"],
        {"Tinkoff": 100000.0, "Wise": 1000.0},
        currencies={"Tinkoff": "RUB", "Wise": "USD"},
        rates={"USD": {"2026-03": 88.5}},
    )
    # Should show per-currency subtotal lines
    assert "RUB:" in text
    assert "USD:" in text
    assert "\u2192" in text  # conversion arrow for USD
    assert "Total:" in text


def test_balance_menu_subtotal_shows_rate():
    text, _ = _build_balance_menu(
        "2026-03",
        ["Wise"],
        {"Wise": 1000.0},
        currencies={"Wise": "USD"},
        rates={"USD": {"2026-03": 88.5}},
    )
    assert "88.5" in text


def test_balance_menu_footer_partial_when_rate_missing():
    text, _ = _build_balance_menu(
        "2026-03",
        ["Revolut"],
        {"Revolut": 100.0},
        currencies={"Revolut": "USD"},
        rates={},
    )
    assert "?" in text


def test_balance_menu_no_footer_when_empty():
    text, _ = _build_balance_menu("2026-03", [], {})
    assert "Total:" not in text


def test_balance_menu_no_footer_when_no_values():
    text, _ = _build_balance_menu("2026-03", ["Savings"], {})
    assert "Total:" not in text


def test_balance_menu_rub_only_no_arrow():
    text, _ = _build_balance_menu(
        "2026-03",
        ["Savings"],
        {"Savings": 5000.0},
        currencies={"Savings": "RUB"},
    )
    assert "\u2192" not in text
    assert "Total:" in text


# ── auto-prompt state machine ────────────────────────────────────────────────

class _FakeCtx:
    def __init__(self):
        self.user_data = {}


def test_commit_balance_with_rate_check_auto_fetches(tmp_path, monkeypatch):
    """When rate is missing and CBR returns a rate, it should auto-store and commit."""
    import asyncio
    from storage import Storage
    from bot import _commit_balance_with_rate_check

    # Mock fetch_rate to return a known value
    async def fake_fetch(ccy, month):
        if ccy == "USD":
            return 88.5
        return None

    monkeypatch.setattr("bot.fetch_rate", fake_fetch)

    s = Storage(data_dir=str(tmp_path))
    s.add_balance_name("Revolut", currency="USD")
    ctx = _FakeCtx()
    status, prompt = asyncio.get_event_loop().run_until_complete(
        _commit_balance_with_rate_check(s, ctx, "2026-03", "Revolut", 100.0)
    )
    assert status == "done"
    assert prompt is None
    assert s.get_balance_month("2026-03") == {"Revolut": 100.0}
    assert s.get_rate("USD", "2026-03") == 88.5


def test_commit_balance_with_rate_check_falls_back_to_prompt(tmp_path, monkeypatch):
    """When rate is missing and CBR fails, it should fall back to manual prompt."""
    import asyncio
    from storage import Storage
    from bot import _commit_balance_with_rate_check

    async def fake_fetch(ccy, month):
        return None  # CBR failure

    monkeypatch.setattr("bot.fetch_rate", fake_fetch)

    s = Storage(data_dir=str(tmp_path))
    s.add_balance_name("Revolut", currency="USD")
    ctx = _FakeCtx()
    status, prompt = asyncio.get_event_loop().run_until_complete(
        _commit_balance_with_rate_check(s, ctx, "2026-03", "Revolut", 100.0)
    )
    assert status == "rate_prompt"
    assert "USD" in prompt
    assert s.get_balance_month("2026-03") == {}


def test_commit_balance_with_rate_check_uses_cached_rate(tmp_path, monkeypatch):
    """When rate is already cached, should use it without fetching."""
    import asyncio
    from storage import Storage
    from bot import _commit_balance_with_rate_check

    fetch_called = []

    async def fake_fetch(ccy, month):
        fetch_called.append(True)
        return 88.5

    monkeypatch.setattr("bot.fetch_rate", fake_fetch)

    s = Storage(data_dir=str(tmp_path))
    s.add_balance_name("Revolut", currency="USD")
    s.set_rate("USD", "2026-03", 92.0)
    ctx = _FakeCtx()
    status, prompt = asyncio.get_event_loop().run_until_complete(
        _commit_balance_with_rate_check(s, ctx, "2026-03", "Revolut", 100.0)
    )
    assert status == "done"
    assert len(fetch_called) == 0  # should not have called fetch
    assert s.get_rate("USD", "2026-03") == 92.0  # original cached rate unchanged


def test_commit_balance_rub_skips_rate_check(tmp_path, monkeypatch):
    """RUB balances should not trigger any rate fetching."""
    import asyncio
    from storage import Storage
    from bot import _commit_balance_with_rate_check

    fetch_called = []

    async def fake_fetch(ccy, month):
        fetch_called.append(True)
        return None

    monkeypatch.setattr("bot.fetch_rate", fake_fetch)

    s = Storage(data_dir=str(tmp_path))
    s.add_balance_name("Savings", currency="RUB")
    ctx = _FakeCtx()
    status, prompt = asyncio.get_event_loop().run_until_complete(
        _commit_balance_with_rate_check(s, ctx, "2026-03", "Savings", 5000.0)
    )
    assert status == "done"
    assert len(fetch_called) == 0


# ── report type keyboard (updated for balance) ────────────────────────────────

def test_report_type_keyboard_has_balances_button():
    _, markup = _build_report_type_keyboard()
    all_data = [btn.callback_data for row in markup.inline_keyboard for btn in row if btn.callback_data]
    assert "report_type:balance" in all_data


# ── _build_all_expenses_tsv ──────────────────────────────────────────────────

def test_build_all_expenses_tsv_empty(tmp_path):
    from storage import Storage
    s = Storage(data_dir=str(tmp_path))
    assert _build_all_expenses_tsv(s) is None


def test_build_all_expenses_tsv_single_month(tmp_path):
    from storage import Storage
    s = Storage(data_dir=str(tmp_path))
    s.append_record("2026-03", "F", 100.0, "Groceries")
    s.append_record("2026-03", "taxi", 50.0, "Uber")
    result = _build_all_expenses_tsv(s)
    assert result is not None
    lines = result.decode("utf-8").split("\n")
    assert len(lines) == 2
    assert "Groceries" in lines[0]
    assert "Uber" in lines[1]


def test_build_all_expenses_tsv_multiple_months_chronological(tmp_path):
    from storage import Storage
    s = Storage(data_dir=str(tmp_path))
    s.append_record("2026-03", "F", 100.0, "March item")
    s.append_record("2026-01", "F", 200.0, "January item")
    s.append_record("2026-02", "F", 150.0, "February item")
    result = _build_all_expenses_tsv(s)
    lines = result.decode("utf-8").split("\n")
    assert len(lines) == 3
    assert "January item" in lines[0]
    assert "February item" in lines[1]
    assert "March item" in lines[2]


# ── _build_all_income_tsv ────────────────────────────────────────────────────

def test_build_all_income_tsv_empty(tmp_path):
    from storage import Storage
    s = Storage(data_dir=str(tmp_path))
    assert _build_all_income_tsv(s) is None


def test_build_all_income_tsv_single_month(tmp_path):
    from storage import Storage
    s = Storage(data_dir=str(tmp_path))
    s.append_income("2026-03", 5000.0, True, "Salary")
    result = _build_all_income_tsv(s)
    assert result is not None
    lines = result.decode("utf-8").split("\n")
    assert len(lines) == 1
    assert "5000" in lines[0]
    assert "Salary" in lines[0]


def test_build_all_income_tsv_multiple_months_chronological(tmp_path):
    from storage import Storage
    s = Storage(data_dir=str(tmp_path))
    s.append_income("2026-03", 5000.0, True, "March salary")
    s.append_income("2026-01", 4000.0, True, "January salary")
    result = _build_all_income_tsv(s)
    lines = result.decode("utf-8").split("\n")
    assert len(lines) == 2
    # January should come first (chronological)
    assert "January salary" in lines[0]
    assert "March salary" in lines[1]


# ── _build_all_balances_tsv ──────────────────────────────────────────────────

def test_build_all_balances_tsv_empty(tmp_path):
    from storage import Storage
    s = Storage(data_dir=str(tmp_path))
    assert _build_all_balances_tsv(s) is None


def test_build_all_balances_tsv_with_data(tmp_path):
    from storage import Storage
    s = Storage(data_dir=str(tmp_path))
    s.add_balance_name("Savings")
    s.set_balance("2026-03", "Savings", 5000.0)
    s.set_balance("2026-02", "Savings", 4800.0)
    result = _build_all_balances_tsv(s)
    assert result is not None
    lines = result.decode("utf-8").split("\n")
    assert len(lines) == 3  # header + 2 months
    assert "month" in lines[0]  # header
    # Chronological: 2026-02 first, then 2026-03
    assert "2026-02" in lines[1]
    assert "2026-03" in lines[2]


# ── _format_ccy_amount ───────────────────────────────────────────────────────

def test_format_ccy_amount_rub():
    assert _format_ccy_amount(150000, "RUB") == "150\u202f000 ₽"


def test_format_ccy_amount_usd():
    assert _format_ccy_amount(5000, "USD") == "$5\u202f000"


def test_format_ccy_amount_eur():
    assert _format_ccy_amount(2000, "EUR") == "€2\u202f000"


def test_format_ccy_amount_gbp():
    assert _format_ccy_amount(1000, "GBP") == "£1\u202f000"


def test_format_ccy_amount_exotic():
    assert _format_ccy_amount(3000, "CHF") == "CHF 3\u202f000"


def test_format_ccy_amount_fractional():
    assert _format_ccy_amount(1234.5, "USD") == "$1\u202f234.5"


def test_format_ccy_amount_none():
    assert _format_ccy_amount(None, "USD") == "—"
