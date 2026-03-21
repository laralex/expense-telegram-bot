"""
## How to run

1. Copy .env.example to .env and fill in BOT_TOKEN and OWNER_ID.
   Get your OWNER_ID by messaging @userinfobot on Telegram.

2. Install dependencies:
       pip install -r requirements.txt

3. Run locally:
       python bot.py

4. For production, deploy with the provided expense-tracker.service systemd unit.

Requirements: Python 3.11+, python-telegram-bot v20+
"""

import difflib
import io
import os
from datetime import datetime
from pathlib import Path

from dotenv import load_dotenv
from telegram import BotCommand, CopyTextButton, InlineKeyboardButton, InlineKeyboardMarkup, Update
from telegram.ext import (
    Application,
    ApplicationHandlerStop,
    CallbackQueryHandler,
    CommandHandler,
    ContextTypes,
    MessageHandler,
    TypeHandler,
    filters,
)

from parser import ParseError, load_categories, parse_income, parse_payment
from storage import Storage


# ── helpers ───────────────────────────────────────────────────────────────────

def _month_label(month: str) -> str:
    """'2026-03' → 'March 2026'"""
    return datetime.strptime(month, "%Y-%m").strftime("%B %Y")


def _last_12_months(current: str) -> list[str]:
    """Return last 12 calendar months newest-first."""
    today = datetime.today()
    months = []
    for i in range(12):
        month = today.month - i
        year = today.year + (month - 1) // 12
        month = (month - 1) % 12 + 1
        months.append(f"{year:04d}-{month:02d}")
    return months


# ── report rendering ───────────────────────────────────────────────────────────

def _expense_field(record: tuple) -> dict:
    date_str, category, title, sum_str = record
    return {"date": date_str, "category": category, "title": title, "amount": sum_str}


def _income_field(record: tuple, month: str) -> dict:
    amount_str, taxable, name = record
    year, mon = month.split("-")
    return {
        "amount":  amount_str,
        "taxable": "" if taxable else "no",
        "year":    year,
        "month":   str(int(mon)),
        "name":    name,
    }


BALANCE_FUZZY_CUTOFF = 0.6
BALANCE_FUZZY_MAX_MATCHES = 3


def _format_balance_amount(amount: float | None) -> str:
    """Format a balance amount for display. None → '—'; whole floats drop decimal."""
    if amount is None:
        return "—"
    return str(int(amount)) if amount == int(amount) else str(amount)


def _resolve_balance_name(input_name: str, current_names: list[str]) -> tuple[str | None, list[str]]:
    """
    Fuzzy-match input_name against current_names.
    Returns (matched_name, []) on single match,
            (None, candidates) on multiple matches,
            (None, []) on no match or empty list.
    """
    if not current_names:
        return None, []
    lower_input = input_name.lower()
    lower_names = [n.lower() for n in current_names]
    matches = difflib.get_close_matches(
        lower_input, lower_names,
        n=BALANCE_FUZZY_MAX_MATCHES,
        cutoff=BALANCE_FUZZY_CUTOFF,
    )
    if not matches:
        return None, []
    original_matches = [current_names[lower_names.index(m)] for m in matches]
    if len(original_matches) == 1:
        return original_matches[0], []
    return None, original_matches


def _build_balance_menu(
    month: str,
    current_names: list[str],
    month_values: dict[str, float],
) -> tuple[str, InlineKeyboardMarkup]:
    """
    Build the /balance main menu keyboard.
    month_values: {name: amount} for the current month (may be partial or empty).
    Pure function — no I/O.
    """
    text = f"Balances — {_month_label(month)}"
    rows = []
    rows.append([
        InlineKeyboardButton("＋ Add",    callback_data="balance_add"),
        InlineKeyboardButton("－ Remove", callback_data="balance_remove"),
    ])
    for name in current_names:
        amount = month_values.get(name)
        label = f"{name}: {_format_balance_amount(amount)}"
        rows.append([InlineKeyboardButton(label, callback_data=f"balance_set:{name}")])
    rows.append([InlineKeyboardButton("✓ Done", callback_data="balance_done")])
    return text, InlineKeyboardMarkup(rows)


def _build_balance_remove_confirm(name: str) -> tuple[str, InlineKeyboardMarkup]:
    """Build the remove-confirmation keyboard for a named balance. Pure function."""
    text = f'Remove "{name}"?'
    keyboard = InlineKeyboardMarkup([[
        InlineKeyboardButton("Keep history",   callback_data=f"balance_remove_keep:{name}"),
        InlineKeyboardButton("Delete history", callback_data=f"balance_remove_delete:{name}"),
        InlineKeyboardButton("Cancel",         callback_data="balance_remove_cancel"),
    ]])
    return text, keyboard


def render_balance_report(
    months: list[str],
    historic_names: list[str],
    month_data: dict[str, dict[str, float]],
    separator: str = "\t",
) -> list[str]:
    """
    Render a balance report as a list of separator-joined strings.
    First element is the header row. Months in the order given (caller sorts).
    Missing values produce empty cells. Pure function.
    """
    header = separator.join(["month"] + historic_names)
    rows = [header]
    for month in months:
        values = month_data.get(month, {})
        cells = [month] + [
            _format_balance_amount(values.get(name)) if name in values else ""
            for name in historic_names
        ]
        rows.append(separator.join(cells))
    return rows


def render_rows(
    records: list,
    fmt: list,
    field_extractor,
    separator: str = "\t",
) -> list:
    """
    Build report lines from records using a configurable column format.

    records        — raw tuples from storage
    fmt            — ordered column names; "" = empty column
    field_extractor — callable(record) -> dict[str, str]
    separator      — "\t" for tab, ";" for semicolon
    Returns list of joined line strings. Unknown column names yield empty cells.
    """
    lines = []
    for rec in records:
        d = field_extractor(rec)
        cells = [d.get(col, "") for col in fmt]
        lines.append(separator.join(cells))
    return lines


# ── erase helpers ─────────────────────────────────────────────────────────────

def _format_erase_preview(records: list, month: str) -> str:
    """Return a human-readable preview of records about to be erased."""
    if not records:
        return "❌ No records to erase."
    lines = [f"About to erase *{len(records)}* record(s) from *{_month_label(month)}*:"]
    for date_str, cat, title, amount in records:
        label = f"{cat} {amount}" + (f" — {title}" if title else "")
        lines.append(f"  • {label}")
    return "\n".join(lines)


# ── settings / format editor ──────────────────────────────────────────────────

REPORT_COLUMNS: dict[str, list[str]] = {
    "expense": ["date", "category", "title", "amount"],
    "income":  ["amount", "taxable", "year", "month", "name"],
}

_REPORT_LABELS = {"expense": "Expense", "income": "Income"}


def _build_fmt_editor(report_type: str, fmt: list, pos: int) -> tuple:
    """
    Build the editor message text and keyboard for position `pos` in `fmt`.
    Returns (text, InlineKeyboardMarkup). Pure function — no I/O.
    """
    current = fmt[pos] if fmt[pos] else "(empty)"
    text = (
        f"{_REPORT_LABELS[report_type]} format \u2014 column {pos + 1} of {len(fmt)}\n"
        f"Current: {current}"
    )

    # Row 0: column selector buttons
    col_buttons = []
    for col in REPORT_COLUMNS[report_type]:
        col_buttons.append(InlineKeyboardButton(col, callback_data=f"fmt_set:{report_type}:{pos}:{col}"))
    col_buttons.append(InlineKeyboardButton("(empty)", callback_data=f"fmt_set:{report_type}:{pos}:"))

    # Row 1: navigation — Prev/Next always present; noop at boundaries for stable layout
    prev_data = f"fmt_nav:{report_type}:{pos - 1}" if pos > 0 else "noop"
    next_data = f"fmt_nav:{report_type}:{pos + 1}" if pos < len(fmt) - 1 else "noop"
    nav_buttons = [
        InlineKeyboardButton("← Prev", callback_data=prev_data),
        InlineKeyboardButton("Next →", callback_data=next_data),
    ]
    if len(fmt) < 10:
        nav_buttons.append(InlineKeyboardButton("+ Add", callback_data=f"fmt_add:{report_type}"))
    if len(fmt) > 1:
        nav_buttons.append(InlineKeyboardButton("🗑 Del", callback_data=f"fmt_del:{report_type}:{pos}"))

    # Row 2: done
    done_row = [InlineKeyboardButton("✓ Done", callback_data="fmt_menu")]

    rows = [col_buttons]
    if nav_buttons:
        rows.append(nav_buttons)
    rows.append(done_row)

    return text, InlineKeyboardMarkup(rows)


def _build_report_type_keyboard() -> tuple:
    """Return (text, InlineKeyboardMarkup) for the /report type selector."""
    keyboard = InlineKeyboardMarkup([[
        InlineKeyboardButton("Expenses", callback_data="report_type:expense"),
        InlineKeyboardButton("Income",   callback_data="report_type:income"),
        InlineKeyboardButton("Balances", callback_data="report_type:balance"),
    ]])
    return "Select report type:", keyboard


_ERASE_PAGE_SIZE = 10
_ERASE_SINGLE_PAGE_MAX = 15


def _erase_record_label(record, record_type: str) -> str:
    """Return a short display label for a record row."""
    if record_type == "expense":
        date_str, category, title, amount = record
        label = f"{category} {amount}"
        if title:
            label += f" — {title}"
        return label
    else:  # income
        amount_str, taxable, name = record
        label = f"{amount_str} — {name}"
        if taxable:
            label += " (taxable)"
        return label


def _build_erase_keyboard(state: dict) -> tuple:
    """
    Build the erase checkbox page from state dict.
    Returns (text, InlineKeyboardMarkup). Pure function — no I/O.

    state keys used: type, month, records, selected, page
    """
    record_type = state["type"]
    month = state["month"]
    records = state["records"]
    selected = state["selected"]
    page = state["page"]
    total = len(records)

    # Determine pagination
    paginated = total > _ERASE_SINGLE_PAGE_MAX
    if paginated:
        total_pages = (total + _ERASE_PAGE_SIZE - 1) // _ERASE_PAGE_SIZE
        start = page * _ERASE_PAGE_SIZE
        end = min(start + _ERASE_PAGE_SIZE, total)
        page_records = list(enumerate(records))[start:end]
    else:
        total_pages = 1
        page_records = list(enumerate(records))

    # Message text
    sel_count = len(selected)
    if paginated:
        text = (
            f"Erase {record_type}s — {_month_label(month)}\n"
            f"Page {page + 1}/{total_pages} · {sel_count} selected"
        )
    else:
        text = f"Erase {record_type}s — {_month_label(month)}\n{sel_count} selected"

    rows = []

    # Row 0: Select All stub
    all_selected = len(selected) == total and total > 0
    all_mark = "☑" if all_selected else "☐"
    rows.append([InlineKeyboardButton(
        f"{all_mark} All ({total} records)",
        callback_data="erase_toggle_all",
    )])

    # Record rows
    for idx, record in page_records:
        mark = "☑" if idx in selected else "☐"
        label = _erase_record_label(record, record_type)
        rows.append([InlineKeyboardButton(
            f"{mark} {label}",
            callback_data=f"erase_toggle:{idx}",
        )])

    # Pagination nav (only when paginated)
    if paginated:
        nav = []
        prev_data = f"erase_page:{page - 1}" if page > 0 else "noop"
        next_data = f"erase_page:{page + 1}" if page < total_pages - 1 else "noop"
        nav.append(InlineKeyboardButton("← Prev", callback_data=prev_data))
        nav.append(InlineKeyboardButton("Next →", callback_data=next_data))
        rows.append(nav)

    # Bottom row: Delete / Back / Cancel
    rows.append([
        InlineKeyboardButton(f"Delete ({sel_count})", callback_data="erase_do_selected"),
        InlineKeyboardButton("← Back", callback_data=f"erase_back_months:{record_type}"),
        InlineKeyboardButton("✗ Cancel", callback_data="erase_cancel"),
    ])

    return text, InlineKeyboardMarkup(rows)


# ── security ──────────────────────────────────────────────────────────────────

async def owner_check(update: Update, ctx: ContextTypes.DEFAULT_TYPE) -> None:
    owner_id = ctx.bot_data["owner_id"]
    if update.effective_user and update.effective_user.id != owner_id:
        raise ApplicationHandlerStop


# ── command handlers ──────────────────────────────────────────────────────────

async def cmd_start(update: Update, ctx: ContextTypes.DEFAULT_TYPE) -> None:
    store: Storage = ctx.bot_data["store"]
    month = store.get_current_month()
    await update.message.reply_text(
        f"Active month: *{_month_label(month)}*\n\n"
        "Send a message to record an expense.\n"
        "e.g. message '100 F restaurant' where 100 is amount, F is type (Food) and other is expense label.\n"
        "Also use:\n"
        "/in + message body — record income\n"
        "/out + message body — record expense\n"
        "/report — generate report\n"
        "/erase — menu to delete individual records (expenses or income)\n"
        "/erase N — delete last N expense records\n"
        "/month — change active month\n"
        "/settings — change bot settings\n",
        parse_mode="Markdown",
    )


async def cmd_month(update: Update, ctx: ContextTypes.DEFAULT_TYPE) -> None:
    store: Storage = ctx.bot_data["store"]
    current = store.get_current_month()
    months = _last_12_months(current)
    keyboard = []
    for m in months:
        label = ("✓ " if m == current else "") + _month_label(m)
        keyboard.append([InlineKeyboardButton(label, callback_data=f"set_month:{m}")])
    await update.message.reply_text(
        "Select active month:",
        reply_markup=InlineKeyboardMarkup(keyboard),
    )


async def cmd_report(update: Update, ctx: ContextTypes.DEFAULT_TYPE) -> None:
    text, markup = _build_report_type_keyboard()
    await update.message.reply_text(text, reply_markup=markup)


async def cmd_erase(update: Update, ctx: ContextTypes.DEFAULT_TYPE) -> None:
    store: Storage = ctx.bot_data["store"]
    args = update.message.text.strip().split(None, 1)

    # /erase N — show last N expense records and ask to confirm (unchanged)
    if len(args) == 2 and args[1].strip().isdigit():
        n = int(args[1].strip())
        month = store.get_current_month()
        records = store.read_month(month)
        preview_records = records[-n:] if n and records else []
        text = _format_erase_preview(preview_records, month)
        if not preview_records:
            await update.message.reply_text(text)
            return
        keyboard = InlineKeyboardMarkup([[
            InlineKeyboardButton("✓ Delete", callback_data=f"erase_last_n_do:{month}:{n}"),
            InlineKeyboardButton("✗ Cancel", callback_data="erase_cancel"),
        ]])
        await update.message.reply_text(text, reply_markup=keyboard, parse_mode="Markdown")
        return

    # /erase with no args — type selector
    keyboard = InlineKeyboardMarkup([[
        InlineKeyboardButton("Expenses", callback_data="erase_type:expense"),
        InlineKeyboardButton("Income",   callback_data="erase_type:income"),
    ]])
    await update.message.reply_text("Select type to erase:", reply_markup=keyboard)


async def cmd_balance(update: Update, ctx: ContextTypes.DEFAULT_TYPE) -> None:
    store: Storage = ctx.bot_data["store"]
    args = update.message.text.strip().split(None, 2)

    # Quick form: /balance <name> <amount>
    if len(args) == 3:
        name_input, amount_str = args[1], args[2]
        try:
            amount = float(amount_str)
        except ValueError:
            await update.message.reply_text("❌ Amount must be a number.")
            return
        current_names = store.get_balance_names()
        if not current_names:
            await update.message.reply_text("No balances yet. Use /balance to add one.")
            return
        matched, candidates = _resolve_balance_name(name_input, current_names)
        if matched:
            store.set_balance(store.get_current_month(), matched, amount)
            await update.message.reply_text(
                f"✅ *{matched}*: {_format_balance_amount(amount)} ({_month_label(store.get_current_month())})",
                parse_mode="Markdown",
            )
        elif candidates:
            ctx.user_data["balance"] = {"awaiting": None, "pending_amount": amount,
                                         "pending_name": None, "menu_message_id": None}
            keyboard = InlineKeyboardMarkup([
                [InlineKeyboardButton(n, callback_data=f"balance_pick:{n}")]
                for n in candidates
            ])
            await update.message.reply_text("Which balance?", reply_markup=keyboard)
        else:
            ctx.user_data["balance"] = {"awaiting": None, "pending_amount": amount,
                                         "pending_name": None, "menu_message_id": None}
            rows = [[InlineKeyboardButton(n, callback_data=f"balance_pick:{n}")] for n in current_names]
            rows.append([InlineKeyboardButton("＋ Create new", callback_data="balance_pick_new")])
            await update.message.reply_text("Select balance:", reply_markup=InlineKeyboardMarkup(rows))
        return

    # Menu form: /balance
    month = store.get_current_month()
    month_values = store.get_balance_month(month)
    current_names = store.get_balance_names()
    text, markup = _build_balance_menu(month, current_names, month_values)
    msg = await update.message.reply_text(text, reply_markup=markup)
    ctx.user_data["balance"] = {
        "awaiting": None, "pending_amount": None,
        "pending_name": None, "menu_message_id": msg.message_id,
    }


# ── callback handlers ─────────────────────────────────────────────────────────

async def cb_set_month(update: Update, ctx: ContextTypes.DEFAULT_TYPE) -> None:
    query = update.callback_query
    await query.answer()
    month = query.data.split(":")[1]
    store: Storage = ctx.bot_data["store"]
    store.set_current_month(month)
    await query.edit_message_text(f"✅ Active month set to *{_month_label(month)}*", parse_mode="Markdown")


async def cb_report(update: Update, ctx: ContextTypes.DEFAULT_TYPE) -> None:
    query = update.callback_query
    await query.answer()
    month = query.data.split(":")[1]
    store: Storage = ctx.bot_data["store"]
    records = store.read_month(month)
    if not records:
        await query.edit_message_text(f"❌ No records for {_month_label(month)}.")
        return
    fmt = store.get_format("expense")
    tab_lines  = render_rows(records, fmt, _expense_field, separator="\t")
    semi_lines = render_rows(records, fmt, _expense_field, separator=";")
    tab_report  = "\n".join(tab_lines)
    semi_report = "\n".join(semi_lines)
    buttons = []
    if len(tab_report) <= 256:
        buttons.append(InlineKeyboardButton("📋 Tab", copy_text=CopyTextButton(text=tab_report)))
    if len(semi_report) <= 256:
        buttons.append(InlineKeyboardButton("📋 ;", copy_text=CopyTextButton(text=semi_report)))
    buttons.append(InlineKeyboardButton("📎 .tsv", callback_data=f"tsv:{month}"))
    keyboard = InlineKeyboardMarkup([buttons])
    await query.edit_message_text(
        f"<pre>{tab_report}</pre>",
        parse_mode="HTML",
        reply_markup=keyboard,
    )


async def cb_report_type(update: Update, ctx: ContextTypes.DEFAULT_TYPE) -> None:
    query = update.callback_query
    await query.answer()
    report_type = query.data.split(":")[1]
    store: Storage = ctx.bot_data["store"]

    if report_type == "expense":
        months = store.list_months_with_counts()
        if not months:
            await query.edit_message_text("❌ No expense data yet.")
            return
        keyboard = [
            [InlineKeyboardButton(f"{_month_label(m)} ({n})", callback_data=f"report:{m}")]
            for m, n in months
        ]
        await query.edit_message_text(
            "Select month to report:",
            reply_markup=InlineKeyboardMarkup(keyboard),
        )
    else:  # income
        months = store.list_income_months()
        if not months:
            await query.edit_message_text("❌ No income data yet.")
            return
        keyboard = [
            [InlineKeyboardButton(_month_label(m), callback_data=f"income_report:{m}")]
            for m in months
        ]
        await query.edit_message_text(
            "Select month to view income:",
            reply_markup=InlineKeyboardMarkup(keyboard),
        )


async def cb_erase_last_n_do(update: Update, ctx: ContextTypes.DEFAULT_TYPE) -> None:
    query = update.callback_query
    await query.answer()
    _, month, n_str = query.data.split(":")
    n = int(n_str)
    store: Storage = ctx.bot_data["store"]
    deleted = store.delete_last_n_records(month, n)
    await query.edit_message_text(
        f"✅ Deleted *{len(deleted)}* record(s) from *{_month_label(month)}*.",
        parse_mode="Markdown",
    )


async def cb_erase_cancel(update: Update, ctx: ContextTypes.DEFAULT_TYPE) -> None:
    query = update.callback_query
    await query.answer()
    ctx.user_data.pop("erase", None)
    await query.edit_message_text("Cancelled.")


async def _show_erase_month_selector(query, record_type: str, store) -> None:
    """Show the month selector for the given record type. Edits the existing message."""
    if record_type == "expense":
        months = store.list_months_with_counts()
        if not months:
            await query.edit_message_text("No expense records yet.")
            return
        keyboard = InlineKeyboardMarkup([
            [InlineKeyboardButton(f"{_month_label(m)} ({n})", callback_data=f"erase_month:expense:{m}")]
            for m, n in months
        ])
    else:  # income
        months = store.list_income_months()
        if not months:
            await query.edit_message_text("No income records yet.")
            return
        keyboard = InlineKeyboardMarkup([
            [InlineKeyboardButton(_month_label(m), callback_data=f"erase_month:income:{m}")]
            for m in months
        ])
    await query.edit_message_text("Select month to erase:", reply_markup=keyboard)


async def cb_erase_type(update: Update, ctx: ContextTypes.DEFAULT_TYPE) -> None:
    query = update.callback_query
    await query.answer()
    record_type = query.data.split(":")[1]
    store: Storage = ctx.bot_data["store"]
    await _show_erase_month_selector(query, record_type, store)


async def cb_erase_month(update: Update, ctx: ContextTypes.DEFAULT_TYPE) -> None:
    query = update.callback_query
    await query.answer()
    _, record_type, month = query.data.split(":")
    store: Storage = ctx.bot_data["store"]

    if record_type == "expense":
        records = store.read_month(month)
    else:
        records = store.read_income(month)

    if not records:
        ctx.user_data.pop("erase", None)
        back_keyboard = InlineKeyboardMarkup([[
            InlineKeyboardButton("← Back", callback_data=f"erase_back_months:{record_type}")
        ]])
        await query.edit_message_text(
            f"No records for {_month_label(month)}.",
            reply_markup=back_keyboard,
        )
        return

    ctx.user_data["erase"] = {
        "type": record_type,
        "month": month,
        "selected": set(),
        "page": 0,
        "records": records,
    }
    text, markup = _build_erase_keyboard(ctx.user_data["erase"])
    await query.edit_message_text(text, reply_markup=markup)


async def cb_erase_back_months(update: Update, ctx: ContextTypes.DEFAULT_TYPE) -> None:
    query = update.callback_query
    await query.answer()
    record_type = query.data.split(":")[1]
    ctx.user_data.pop("erase", None)
    store: Storage = ctx.bot_data["store"]
    await _show_erase_month_selector(query, record_type, store)


def _erase_stale_guard(ctx):
    """Return state dict or None if session is expired."""
    return ctx.user_data.get("erase")


async def cb_erase_toggle(update: Update, ctx: ContextTypes.DEFAULT_TYPE) -> None:
    query = update.callback_query
    await query.answer()
    state = _erase_stale_guard(ctx)
    if not state:
        await query.edit_message_text("Session expired. Use /erase to start over.")
        return
    idx = int(query.data.split(":")[1])
    if idx in state["selected"]:
        state["selected"].discard(idx)
    else:
        state["selected"].add(idx)
    text, markup = _build_erase_keyboard(state)
    await query.edit_message_text(text, reply_markup=markup)


async def cb_erase_toggle_all(update: Update, ctx: ContextTypes.DEFAULT_TYPE) -> None:
    query = update.callback_query
    await query.answer()
    state = _erase_stale_guard(ctx)
    if not state:
        await query.edit_message_text("Session expired. Use /erase to start over.")
        return
    total = len(state["records"])
    if len(state["selected"]) == total:
        state["selected"] = set()
    else:
        state["selected"] = set(range(total))
    text, markup = _build_erase_keyboard(state)
    await query.edit_message_text(text, reply_markup=markup)


async def cb_erase_page(update: Update, ctx: ContextTypes.DEFAULT_TYPE) -> None:
    query = update.callback_query
    await query.answer()
    state = _erase_stale_guard(ctx)
    if not state:
        await query.edit_message_text("Session expired. Use /erase to start over.")
        return
    state["page"] = int(query.data.split(":")[1])
    text, markup = _build_erase_keyboard(state)
    await query.edit_message_text(text, reply_markup=markup)


async def cb_erase_do_selected(update: Update, ctx: ContextTypes.DEFAULT_TYPE) -> None:
    query = update.callback_query
    await query.answer()
    state = _erase_stale_guard(ctx)
    if not state:
        await query.edit_message_text("Session expired. Use /erase to start over.")
        return
    if not state["selected"]:
        _, markup = _build_erase_keyboard(state)
        await query.edit_message_text("Nothing selected.", reply_markup=markup)
        return

    store: Storage = ctx.bot_data["store"]
    month = state["month"]
    indices = state["selected"]

    if state["type"] == "expense":
        deleted = store.delete_expense_records_by_index(month, indices)
    else:
        deleted = store.delete_income_records_by_index(month, indices)

    ctx.user_data.pop("erase", None)
    await query.edit_message_text(
        f"Deleted *{deleted}* record(s) from *{_month_label(month)}*.",
        parse_mode="Markdown",
    )


async def cb_tsv(update: Update, ctx: ContextTypes.DEFAULT_TYPE) -> None:
    query = update.callback_query
    await query.answer()
    month = query.data.split(":")[1]
    store: Storage = ctx.bot_data["store"]
    records = store.read_month(month)
    if not records:
        await query.message.reply_text(f"❌ No records for {_month_label(month)}.")
        return
    fmt = store.get_format("expense")
    lines = render_rows(records, fmt, _expense_field, separator="\t")
    tsv_bytes = "\n".join(lines).encode("utf-8")
    await query.message.reply_document(
        document=io.BytesIO(tsv_bytes),
        filename=f"expenses-{month}.tsv",
    )


# ── balance callbacks ─────────────────────────────────────────────────────────

async def _render_balance_menu_on_query(query, store: Storage) -> None:
    """Re-render the balance menu on an existing query message."""
    month = store.get_current_month()
    month_values = store.get_balance_month(month)
    text, markup = _build_balance_menu(month, store.get_balance_names(), month_values)
    await query.edit_message_text(text, reply_markup=markup)


async def cb_balance_pick(update: Update, ctx: ContextTypes.DEFAULT_TYPE) -> None:
    """User picked a balance from the disambiguation / no-match picker."""
    query = update.callback_query
    await query.answer()
    name = query.data.split(":", 1)[1]
    store: Storage = ctx.bot_data["store"]
    state = ctx.user_data.get("balance", {})
    amount = state.get("pending_amount")
    month = store.get_current_month()
    store.set_balance(month, name, amount)
    ctx.user_data.pop("balance", None)
    await query.edit_message_text(
        f"✅ *{name}*: {_format_balance_amount(amount)} ({_month_label(month)})",
        parse_mode="Markdown",
    )


async def cb_balance_pick_new(update: Update, ctx: ContextTypes.DEFAULT_TYPE) -> None:
    """User chose '＋ Create new' from the no-match picker."""
    query = update.callback_query
    await query.answer()
    state = ctx.user_data.setdefault("balance", {})
    state["awaiting"] = "add_name"
    state["menu_message_id"] = None
    await query.edit_message_text("Enter a name for the new balance:")


async def cb_balance_set(update: Update, ctx: ContextTypes.DEFAULT_TYPE) -> None:
    """User tapped a balance button in the menu — prompt for a value."""
    query = update.callback_query
    await query.answer()
    name = query.data.split(":", 1)[1]
    state = ctx.user_data.setdefault("balance", {})
    state["awaiting"] = "set_value"
    state["pending_name"] = name
    state["menu_message_id"] = query.message.message_id
    await query.edit_message_text(f"Enter new value for *{name}*:", parse_mode="Markdown")


async def cb_balance_add(update: Update, ctx: ContextTypes.DEFAULT_TYPE) -> None:
    """User tapped ＋ Add in the menu."""
    query = update.callback_query
    await query.answer()
    state = ctx.user_data.setdefault("balance", {})
    state["awaiting"] = "add_name"
    state["pending_amount"] = None
    state["menu_message_id"] = query.message.message_id
    await query.edit_message_text("Enter a name for the new balance:")


async def cb_balance_remove(update: Update, ctx: ContextTypes.DEFAULT_TYPE) -> None:
    """User tapped － Remove — show list of current balances."""
    query = update.callback_query
    await query.answer()
    store: Storage = ctx.bot_data["store"]
    names = store.get_balance_names()
    if not names:
        await query.answer("No balances to remove.", show_alert=True)
        return
    rows = [[InlineKeyboardButton(n, callback_data=f"balance_remove_pick:{n}")] for n in names]
    rows.append([InlineKeyboardButton("← Back", callback_data="balance_back")])
    await query.edit_message_text("Select balance to remove:", reply_markup=InlineKeyboardMarkup(rows))


async def cb_balance_remove_pick(update: Update, ctx: ContextTypes.DEFAULT_TYPE) -> None:
    """User picked a balance to remove — show keep/delete confirmation."""
    query = update.callback_query
    await query.answer()
    name = query.data.split(":", 1)[1]
    text, markup = _build_balance_remove_confirm(name)
    await query.edit_message_text(text, reply_markup=markup)


async def cb_balance_remove_keep(update: Update, ctx: ContextTypes.DEFAULT_TYPE) -> None:
    query = update.callback_query
    await query.answer()
    name = query.data.split(":", 1)[1]
    store: Storage = ctx.bot_data["store"]
    store.remove_balance_name(name, keep_history=True)
    await _render_balance_menu_on_query(query, store)


async def cb_balance_remove_delete(update: Update, ctx: ContextTypes.DEFAULT_TYPE) -> None:
    query = update.callback_query
    await query.answer()
    name = query.data.split(":", 1)[1]
    store: Storage = ctx.bot_data["store"]
    store.remove_balance_name(name, keep_history=False)
    await _render_balance_menu_on_query(query, store)


async def cb_balance_remove_cancel(update: Update, ctx: ContextTypes.DEFAULT_TYPE) -> None:
    query = update.callback_query
    await query.answer()
    store: Storage = ctx.bot_data["store"]
    await _render_balance_menu_on_query(query, store)


async def cb_balance_back(update: Update, ctx: ContextTypes.DEFAULT_TYPE) -> None:
    query = update.callback_query
    await query.answer()
    store: Storage = ctx.bot_data["store"]
    await _render_balance_menu_on_query(query, store)


async def cb_balance_done(update: Update, ctx: ContextTypes.DEFAULT_TYPE) -> None:
    query = update.callback_query
    await query.answer()
    ctx.user_data.pop("balance", None)
    await query.edit_message_text("✅ Done.")


# ── income handlers ───────────────────────────────────────────────────────────

async def cmd_income(update: Update, ctx: ContextTypes.DEFAULT_TYPE) -> None:
    """Record income if text follows the command; show error otherwise."""
    args = update.message.text.strip().split(None, 1)
    if len(args) < 2 or not args[1].strip():
        await update.message.reply_text(
            "Usage: `/in <amount> [T] [YYYY-MM] <name>`\n\n"
            "  `<amount>` — numeric amount\n"
            "  `T` — mark as taxable (optional)\n"
            "  `YYYY-MM` — month override, defaults to active month (optional)\n"
            "  `<name>` — income source label\n\n"
            "Examples:\n"
            "  `/in 5000 salary`\n"
            "  `/in 1200 T freelance`\n"
            "  `/in 800 2026-02 bonus`",
            parse_mode="Markdown",
        )
        return

    store: Storage = ctx.bot_data["store"]
    current_month = store.get_current_month()
    try:
        amount, taxable, month, name = parse_income(args[1].strip(), current_month)
    except ParseError as e:
        await update.message.reply_text(f"❌ Could not parse: {e}")
        return

    store.append_income(month, amount, taxable, name)
    tax_label = " (taxable)" if taxable else " (not taxable)"
    await update.message.reply_text(
        f"✅ Income recorded: *{amount}*{tax_label} — {name} ({_month_label(month)})",
        parse_mode="Markdown",
    )


async def cb_income_report(update: Update, ctx: ContextTypes.DEFAULT_TYPE) -> None:
    query = update.callback_query
    await query.answer()
    month = query.data.split(":")[1]
    store: Storage = ctx.bot_data["store"]
    records = store.read_income(month)
    if not records:
        await query.edit_message_text(f"❌ No income for {_month_label(month)}.")
        return
    fmt = store.get_format("income")
    extractor = lambda rec: _income_field(rec, month)
    tab_lines  = render_rows(records, fmt, extractor, separator="\t")
    semi_lines = render_rows(records, fmt, extractor, separator=";")
    tab_report  = "\n".join(tab_lines)
    semi_report = "\n".join(semi_lines)
    buttons = []
    if len(tab_report) <= 256:
        buttons.append(InlineKeyboardButton("📋 Tab", copy_text=CopyTextButton(text=tab_report)))
    if len(semi_report) <= 256:
        buttons.append(InlineKeyboardButton("📋 ;", copy_text=CopyTextButton(text=semi_report)))
    buttons.append(InlineKeyboardButton("📎 .tsv", callback_data=f"income_tsv:{month}"))
    await query.edit_message_text(
        f"<pre>{tab_report}</pre>",
        parse_mode="HTML",
        reply_markup=InlineKeyboardMarkup([buttons]),
    )


async def cb_income_tsv(update: Update, ctx: ContextTypes.DEFAULT_TYPE) -> None:
    query = update.callback_query
    await query.answer()
    month = query.data.split(":")[1]
    store: Storage = ctx.bot_data["store"]
    records = store.read_income(month)
    if not records:
        await query.message.reply_text(f"❌ No income for {_month_label(month)}.")
        return
    fmt = store.get_format("income")
    lines = render_rows(records, fmt, lambda rec: _income_field(rec, month), separator="\t")
    tsv_bytes = "\n".join(lines).encode("utf-8")
    await query.message.reply_document(
        document=io.BytesIO(tsv_bytes),
        filename=f"income-{month}.tsv",
    )


# ── payment handler ───────────────────────────────────────────────────────────

async def _record_payment(update: Update, ctx: ContextTypes.DEFAULT_TYPE, text: str) -> None:
    store: Storage = ctx.bot_data["store"]
    categories = ctx.bot_data["categories"]
    try:
        cat, amount, title = parse_payment(text, categories)
    except ParseError as e:
        await update.message.reply_text(f"❌ Could not parse: {e}")
        return
    month = store.get_current_month()
    store.append_record(month, cat, amount, title)
    title_part = f" — {title}" if title else ""
    await update.message.reply_text(
        f"✅ Expense recorded: *{cat}* {amount}{title_part} ({_month_label(month)})",
        parse_mode="Markdown",
    )


async def _handle_balance_text(update: Update, ctx: ContextTypes.DEFAULT_TYPE) -> None:
    """Handle free-text replies during balance awaiting flows."""
    state = ctx.user_data.get("balance", {})
    awaiting = state.get("awaiting")
    text = update.message.text.strip()
    store: Storage = ctx.bot_data["store"]

    if awaiting == "set_value":
        try:
            amount = float(text)
        except ValueError:
            await update.message.reply_text("❌ Please enter a number.")
            return
        name = state["pending_name"]
        month = store.get_current_month()
        store.set_balance(month, name, amount)
        ctx.user_data.pop("balance", None)
        month_values = store.get_balance_month(month)
        menu_text, markup = _build_balance_menu(month, store.get_balance_names(), month_values)
        await update.message.reply_text(
            f"✅ {name}: {_format_balance_amount(amount)}\n\n{menu_text}",
            reply_markup=markup,
        )

    elif awaiting == "add_name":
        if not text:
            await update.message.reply_text("❌ Name cannot be empty.")
            return
        store.add_balance_name(text)
        pending_amount = state.get("pending_amount")
        month = store.get_current_month()
        if pending_amount is not None:
            store.set_balance(month, text, pending_amount)
        ctx.user_data.pop("balance", None)
        month_values = store.get_balance_month(month)
        menu_text, markup = _build_balance_menu(month, store.get_balance_names(), month_values)
        await update.message.reply_text(
            f"✅ Added *{text}*.\n\n{menu_text}",
            parse_mode="Markdown",
            reply_markup=markup,
        )


async def handle_payment(update: Update, ctx: ContextTypes.DEFAULT_TYPE) -> None:
    balance_state = ctx.user_data.get("balance", {})
    if balance_state.get("awaiting"):
        await _handle_balance_text(update, ctx)
        return
    await _record_payment(update, ctx, update.message.text.strip())


async def cmd_out(update: Update, ctx: ContextTypes.DEFAULT_TYPE) -> None:
    args = update.message.text.strip().split(None, 1)
    if len(args) < 2 or not args[1].strip():
        await update.message.reply_text("Usage: /out <amount> [category] [title]")
        return
    await _record_payment(update, ctx, args[1].strip())


# ── settings handlers ─────────────────────────────────────────────────────────

async def cmd_settings(update: Update, ctx: ContextTypes.DEFAULT_TYPE) -> None:
    keyboard = InlineKeyboardMarkup([[
        InlineKeyboardButton("Expense format", callback_data="fmt_edit:expense:0"),
        InlineKeyboardButton("Income format",  callback_data="fmt_edit:income:0"),
    ]])
    await update.message.reply_text("Settings:", reply_markup=keyboard)


async def cb_noop(update: Update, ctx: ContextTypes.DEFAULT_TYPE) -> None:
    await update.callback_query.answer()


async def cb_fmt_menu(update: Update, ctx: ContextTypes.DEFAULT_TYPE) -> None:
    query = update.callback_query
    await query.answer()
    keyboard = InlineKeyboardMarkup([[
        InlineKeyboardButton("Expense format", callback_data="fmt_edit:expense:0"),
        InlineKeyboardButton("Income format",  callback_data="fmt_edit:income:0"),
    ]])
    await query.edit_message_text("Settings:", reply_markup=keyboard)


async def cb_fmt_edit(update: Update, ctx: ContextTypes.DEFAULT_TYPE) -> None:
    query = update.callback_query
    await query.answer()
    _, report_type, pos_str = query.data.split(":")
    pos = int(pos_str)
    store: Storage = ctx.bot_data["store"]
    fmt = store.get_format(report_type)
    pos = max(0, min(pos, len(fmt) - 1))
    text, markup = _build_fmt_editor(report_type, fmt, pos)
    await query.edit_message_text(text, reply_markup=markup)


async def cb_fmt_set(update: Update, ctx: ContextTypes.DEFAULT_TYPE) -> None:
    query = update.callback_query
    await query.answer()
    _, report_type, pos_str, value = query.data.split(":", 3)
    pos = int(pos_str)
    store: Storage = ctx.bot_data["store"]
    fmt = store.get_format(report_type)
    if pos >= len(fmt):
        return  # stale callback — silently ignore
    fmt[pos] = value
    store.set_format(report_type, fmt)
    text, markup = _build_fmt_editor(report_type, fmt, pos)
    await query.edit_message_text(text, reply_markup=markup)


async def cb_fmt_nav(update: Update, ctx: ContextTypes.DEFAULT_TYPE) -> None:
    query = update.callback_query
    await query.answer()
    _, report_type, pos_str = query.data.split(":")
    pos = int(pos_str)
    store: Storage = ctx.bot_data["store"]
    fmt = store.get_format(report_type)
    pos = max(0, min(pos, len(fmt) - 1))
    text, markup = _build_fmt_editor(report_type, fmt, pos)
    await query.edit_message_text(text, reply_markup=markup)


async def cb_fmt_add(update: Update, ctx: ContextTypes.DEFAULT_TYPE) -> None:
    query = update.callback_query
    await query.answer()
    _, report_type = query.data.split(":")
    store: Storage = ctx.bot_data["store"]
    fmt = store.get_format(report_type)
    if len(fmt) >= 10:
        return  # cap reached
    fmt.append("")
    store.set_format(report_type, fmt)
    pos = len(fmt) - 1
    text, markup = _build_fmt_editor(report_type, fmt, pos)
    await query.edit_message_text(text, reply_markup=markup)


async def cb_fmt_del(update: Update, ctx: ContextTypes.DEFAULT_TYPE) -> None:
    query = update.callback_query
    await query.answer()
    _, report_type, pos_str = query.data.split(":")
    pos = int(pos_str)
    store: Storage = ctx.bot_data["store"]
    fmt = store.get_format(report_type)
    if len(fmt) <= 1:
        return  # minimum one column
    pos = max(0, min(pos, len(fmt) - 1))
    fmt.pop(pos)
    pos = max(0, pos - 1)
    store.set_format(report_type, fmt)
    text, markup = _build_fmt_editor(report_type, fmt, pos)
    await query.edit_message_text(text, reply_markup=markup)


# ── main ──────────────────────────────────────────────────────────────────────

async def post_init(app: Application) -> None:
    await app.bot.set_my_commands([
        BotCommand("start", "Welcome + active month"),
        BotCommand("month", "Change active month"),
        BotCommand("report", "Generate expense or income report"),
        BotCommand("erase", "Erase records"),
        BotCommand("in", "Record income entry"),
        BotCommand("out", "Record expense"),
        BotCommand("settings", "Configure report format"),
    ])


def main() -> None:
    load_dotenv()
    token = os.environ["BOT_TOKEN"]
    owner_id = int(os.environ["OWNER_ID"])

    categories_path = Path(__file__).parent / "categories.yaml"
    categories = load_categories(categories_path)

    app = Application.builder().token(token).post_init(post_init).build()
    app.bot_data["store"] = Storage()
    app.bot_data["owner_id"] = owner_id
    app.bot_data["categories"] = categories

    # Owner check — group -1 runs before everything else
    app.add_handler(TypeHandler(Update, owner_check), group=-1)

    # Commands
    app.add_handler(CommandHandler("start", cmd_start))
    app.add_handler(CommandHandler("month", cmd_month))
    app.add_handler(CommandHandler("report", cmd_report))
    app.add_handler(CommandHandler("erase", cmd_erase))
    app.add_handler(CommandHandler("in", cmd_income))
    app.add_handler(CommandHandler("out", cmd_out))
    app.add_handler(CommandHandler("settings", cmd_settings))

    # Callbacks
    app.add_handler(CallbackQueryHandler(cb_set_month,    pattern=r"^set_month:"))
    app.add_handler(CallbackQueryHandler(cb_report_type,  pattern=r"^report_type:"))
    app.add_handler(CallbackQueryHandler(cb_report,       pattern=r"^report:"))
    app.add_handler(CallbackQueryHandler(cb_erase_last_n_do, pattern=r"^erase_last_n_do:"))
    app.add_handler(CallbackQueryHandler(cb_erase_cancel,    pattern=r"^erase_cancel$"))
    app.add_handler(CallbackQueryHandler(cb_erase_type,        pattern=r"^erase_type:"))
    app.add_handler(CallbackQueryHandler(cb_erase_month,       pattern=r"^erase_month:"))
    app.add_handler(CallbackQueryHandler(cb_erase_toggle_all,  pattern=r"^erase_toggle_all$"))
    app.add_handler(CallbackQueryHandler(cb_erase_toggle,      pattern=r"^erase_toggle:"))
    app.add_handler(CallbackQueryHandler(cb_erase_page,        pattern=r"^erase_page:"))
    app.add_handler(CallbackQueryHandler(cb_erase_do_selected, pattern=r"^erase_do_selected$"))
    app.add_handler(CallbackQueryHandler(cb_erase_back_months, pattern=r"^erase_back_months:"))
    app.add_handler(CallbackQueryHandler(cb_tsv, pattern=r"^tsv:"))
    app.add_handler(CallbackQueryHandler(cb_income_report, pattern=r"^income_report:"))
    app.add_handler(CallbackQueryHandler(cb_income_tsv, pattern=r"^income_tsv:"))
    app.add_handler(CallbackQueryHandler(cb_noop,     pattern=r"^noop$"))
    app.add_handler(CallbackQueryHandler(cb_fmt_menu, pattern=r"^fmt_menu$"))
    app.add_handler(CallbackQueryHandler(cb_fmt_edit, pattern=r"^fmt_edit:"))
    app.add_handler(CallbackQueryHandler(cb_fmt_set,  pattern=r"^fmt_set:"))
    app.add_handler(CallbackQueryHandler(cb_fmt_nav,  pattern=r"^fmt_nav:"))
    app.add_handler(CallbackQueryHandler(cb_fmt_add,  pattern=r"^fmt_add:"))
    app.add_handler(CallbackQueryHandler(cb_fmt_del,  pattern=r"^fmt_del:"))

    # Payment messages (any non-command text)
    app.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, handle_payment))

    app.run_polling(drop_pending_updates=True)


if __name__ == "__main__":
    main()
