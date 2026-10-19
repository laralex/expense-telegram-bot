
    
                                           separator=";",  currencies=currencies, rates=rates)
                                           separator="\t", currencies=currencies, rates=rates)
                                         "pending_name": None, "menu_message_id": None}
                                  reply_markup=InlineKeyboardMarkup(rows))
                            _format_ccy_amount(native_sum, ccy),
                            _format_rub_total(converted),
                            ccy,
                            missing.append(ccy)
                            rate,
                            sign,
                        ))
                        if ccy not in missing:
                        lines.append("{}: {} \u2192 ?".format(
                        lines.append("{}: {} \u2192 {} (1{} = {}\u20bd)".format(
                        sign = _CCY_SIGNS.get(ccy, ccy)
                        total_rub += converted
                    await _resolve_rate(store, ccy, m)
                    continue
                    converted = convert_to_rub(native_sum, ccy, month, rates)
                    else:
                    if converted is not None and rate is not None:
                    lines.append("RUB: {}".format(_format_ccy_amount(native_sum, "RUB")))
                    rate = rates.get(ccy, {}).get(month)
                    total_rub += native_sum
                    zf.write(file, file.relative_to(data_dir))
                "1 {} = ? RUB"
                "Could not fetch rate from CBR.\n"
                "Enter FX rate for {} in {}:\n"
                "awaiting": "rate",
                "pending": {"month": month, "name": name, "amount": amount, "ccy": ccy},
                [InlineKeyboardButton(n, callback_data=f"balance_pick:{n}")]
                amount = month_values.get(name)
                await _resolve_rate(store, ccy, m)
                await update.message.reply_text(prompt)
                ccy = currencies.get(name, "RUB")
                ccy_totals[ccy] = ccy_totals.get(ccy, 0.0) + amount
                cells.append("")
                cells.append(_format_balance_amount(values.get(name)))
                cells.append(str(rate))
                else:
                f"✅ *{matched}*: {_format_balance_amount(amount)} ({_month_label(store.get_current_month())})",
                f"✅ {name}: currency set to {ccy}\n\n{menu_text}",
                for n in candidates
                if amount is None:
                if ccy != "RUB":
                if ccy == "RUB":
                if file.is_file() and not file.name.startswith('.'):
                lines.append("Total: {} (partial)".format(_format_rub_total(total_rub)))
                lines.append("Total: {}".format(_format_rub_total(total_rub)))
                parse_mode="Markdown",
                reply_markup=markup,
                return
                store, ctx, month, name, pending_amount
                zf.write(f, arcname=f"data/{f.name}")
            "  `/in 1200 T freelance`\n"
            "  `/in 5000 salary`\n"
            "  `/in 800 2026-02 bonus`",
            "  `<amount>` — numeric amount\n"
            "  `<name>` — income source label\n\n"
            "  `T` — mark as taxable (optional)\n"
            "  `YYYY-MM` — month override, defaults to active month (optional)\n"
            "Examples:\n"
            "Select month to report:",
            "Select month to view income:",
            "Usage: `/in <amount> [T] [YYYY-MM] <name>`\n\n"
            "awaiting": "pick_currency",
            "pending_amount": pending_amount,
            "pending_name": text,
            # Group amounts by currency
            (None, []) on no match or empty list.
            (None, candidates) on multiple matches,
            )
            ).format(ccy, _month_label(month), ccy)
            InlineKeyboardButton("← Back", callback_data=f"erase_back_months:{record_type}")
            InlineKeyboardButton("✓ Delete", callback_data=f"erase_last_n_do:{month}:{n}"),
            InlineKeyboardButton("✗ Cancel", callback_data="erase_cancel"),
            [InlineKeyboardButton(_month_label(m), callback_data=f"erase_month:income:{m}")]
            [InlineKeyboardButton(_month_label(m), callback_data=f"income_report:{m}")]
            [InlineKeyboardButton(f"{_month_label(m)} ({n})", callback_data=f"erase_month:expense:{m}")]
            [InlineKeyboardButton(f"{_month_label(m)} ({n})", callback_data=f"report:{m}")]
            ])
            amount = float(amount_str)
            amount = float(text)
            await _resolve_rate(store, ccy, month)
            await query.edit_message_text("No balance data to export.")
            await query.edit_message_text("No data to export.")
            await query.edit_message_text("No expense data to export.")
            await query.edit_message_text("No expense records yet.")
            await query.edit_message_text("No income data to export.")
            await query.edit_message_text("No income records yet.")
            await query.edit_message_text("❌ No balance data yet.")
            await query.edit_message_text("❌ No expense data yet.")
            await query.edit_message_text("❌ No income data yet.")
            await query.edit_message_text('Data directory not found.')
            await query.edit_message_text(prompt)
            await update.message.reply_text(
            await update.message.reply_text("No balances yet. Use /balance to add one.")
            await update.message.reply_text("Select balance:", reply_markup=InlineKeyboardMarkup(rows))
            await update.message.reply_text("Which balance?", reply_markup=keyboard)
            await update.message.reply_text("❌ Amount must be a number.")
            await update.message.reply_text("❌ Currency must be a 3-letter code (e.g. USD).")
            await update.message.reply_text("❌ Name cannot be empty.")
            await update.message.reply_text("❌ Please enter a number.")
            await update.message.reply_text("❌ Please enter a positive number.")
            await update.message.reply_text("❌ Rate must be positive.")
            await update.message.reply_text(prompt)
            await update.message.reply_text(text)
            body = f"Report too large for inline preview ({len(months)} months). Use the .tsv file button below."
            body,
            buttons.append(InlineKeyboardButton("Semicolon separated", copy_text=CopyTextButton(text=semi_report)))
            buttons.append(InlineKeyboardButton("Tab separated", copy_text=CopyTextButton(text=tab_report)))
            callback_data=f"erase_toggle:{idx}",
            caption='Database backup created successfully.'
            ccy = currencies.get(name, "RUB")
            ccy_totals = {}  # type: dict
            ctx.user_data.pop("balance", None)
            ctx.user_data["balance"] = {
            ctx.user_data["balance"] = {"awaiting": None, "pending_amount": amount,
            document=buf, 
            document=buf, filename="backup.zip",
            document=io.BytesIO(tsv), filename="balances.tsv",
            document=io.BytesIO(tsv), filename="expenses.tsv",
            document=io.BytesIO(tsv), filename="income.tsv",
            else:
            f"Erase {record_type}s — {_month_label(month)}\n"
            f"No records for {_month_label(month)}.",
            f"Page {page + 1}/{total_pages} · {sel_count} selected"
            f"{mark} {label}",
            f"✅ Added *{name}* ({ccy}).\n\n{menu_text}",
            f"✅ Rate saved: 1 {ccy} = {rate} RUB\n"
            f"✅ {name}: {_format_balance_amount(amount)}\n\n{menu_text}",
            filename=zip_filename,
            for ccy, native_sum in ccy_totals.items():
            for f in files:
            for file in data_dir.rglob('*'):
            for m in months
            for m, n in months
            for name in current_names:
            for name in historic_names:
            if ccy != "RUB":
            if missing:
            if name in values:
            if rate is not None:
            if status == "rate_prompt":
            keyboard = InlineKeyboardMarkup([
            label += " (taxable)"
            label += f" — {title}"
            lines.append("")  # blank line separator
            menu_text, markup = await _build_balance_menu_from_store(store, month)
            missing = []
            month = store.get_current_month()
            parse_mode="HTML",
            parse_mode="Markdown",
            rate = float(text)
            rate = rates.get(ccy, {}).get(month)
            rate_ccys.append(ccy)
            render_rows(records, fmt, lambda rec, m=month: _income_field(rec, m), separator="\t")
            reply_markup=InlineKeyboardMarkup([[b] for b in buttons]),
            reply_markup=InlineKeyboardMarkup(keyboard),
            reply_markup=back_keyboard,
            reply_markup=markup,
            return
            return "rate_prompt", text
            rows = [[InlineKeyboardButton(n, callback_data=f"balance_pick:{n}")] for n in current_names]
            rows.append([InlineKeyboardButton("＋ Create new", callback_data="balance_pick_new")])
            status, prompt = await _commit_balance_with_rate_check(
            store, ctx, month, name, pending_amount
            store.set_balance(store.get_current_month(), matched, amount)
            store.set_balance_currency(name, ccy)
            text = (
            total_rub = 0.0
            }
        "/backup — create a database backup
        "/balance — manage account balances
        "/erase N — delete last N expense records
        "/erase — menu to delete individual records (expenses or income)
        "/export — export all data as TSV files
        "/in + message body — record income
        "/month — change active month
        "/out + message body — record expense
        "/report — generate report
        "/settings — change bot settings
        "Also use:
        "Select active month:",
        "Send a message to record an expense.
        "amount":  amount_str,
        "awaiting": None, "pending_amount": None,
        "e.g. message '100 F restaurant' where 100 is amount, F is type (Food) and other is expense label.
        "month":   str(int(mon)),
        "month": month,
        "name":    name,
        "page": 0,
        "pending_name": None, "menu_message_id": msg.message_id,
        "records": records,
        "selected": set(),
        "taxable": "" if taxable else "no",
        "type": record_type,
        "year":    year,
        # Auto-fetch missing rates for each month
        # Stash the name and show currency picker before committing anything.
        )
        )])
        BotCommand("backup", "Create a database backup"),
        BotCommand("balance", "Manage account balances"),
        BotCommand("erase", "Erase records"),
        BotCommand("export", "Export all data as TSV files"),
        BotCommand("in", "Record income entry"),
        BotCommand("month", "Change active month"),
        BotCommand("out", "Record expense"),
        BotCommand("report", "Generate expense or income report"),
        BotCommand("settings", "Configure report format"),
        BotCommand("start", "Welcome + active month"),
        InlineKeyboardButton("All",      callback_data="export:all"),
        InlineKeyboardButton("Balances", callback_data="export:balances"),
        InlineKeyboardButton("Balances", callback_data="report_type:balance"),
        InlineKeyboardButton("Cancel",         callback_data="balance_remove_cancel"),
        InlineKeyboardButton("Delete history", callback_data=f"balance_remove_delete:{name}"),
        InlineKeyboardButton("Expense format", callback_data="fmt_edit:expense:0"),
        InlineKeyboardButton("Expenses", callback_data="erase_type:expense"),
        InlineKeyboardButton("Expenses", callback_data="export:expenses"),
        InlineKeyboardButton("Expenses", callback_data="report_type:expense"),
        InlineKeyboardButton("Income format",  callback_data="fmt_edit:income:0"),
        InlineKeyboardButton("Income",   callback_data="erase_type:income"),
        InlineKeyboardButton("Income",   callback_data="export:income"),
        InlineKeyboardButton("Income",   callback_data="report_type:income"),
        InlineKeyboardButton("Keep history",   callback_data=f"balance_remove_keep:{name}"),
        InlineKeyboardButton("Next →", callback_data=next_data),
        InlineKeyboardButton("\u2699 Edit",    callback_data="balance_edit"),
        InlineKeyboardButton("\uff0b Add",    callback_data="balance_add"),
        InlineKeyboardButton("\uff0d Remove", callback_data="balance_remove"),
        InlineKeyboardButton("← Back", callback_data=f"erase_back_months:{record_type}"),
        InlineKeyboardButton("← Prev", callback_data=prev_data),
        InlineKeyboardButton("✗ Cancel", callback_data="erase_cancel"),
        InlineKeyboardButton(c, callback_data=f"balance_ccy_pick:{name}:{c}")
        InlineKeyboardButton(f"Delete ({sel_count})", callback_data="erase_do_selected"),
        [InlineKeyboardButton("＋ Other", callback_data=f"balance_ccy_other:{name}")],
        [InlineKeyboardButton('Create Backup', callback_data='backup:create')],
        [InlineKeyboardButton('Restore Backup', callback_data='backup:restore')]
        ]
        ])
        ]])
        _, markup = _build_erase_keyboard(state)
        all_lines.extend(
        all_lines.extend(render_rows(records, fmt, _expense_field, separator="\t"))
        amount = month_values.get(name)
        amount = pending["amount"]
        amount, taxable, month, name = parse_income(args[1].strip(), current_month)
        amount_str, taxable, name = record
        any_amount = any(month_values.get(n) is not None for n in current_names)
        await _handle_balance_text(update, ctx)
        await _render_balance_menu_on_query(query, store)
        await query.answer("No balances to edit.", show_alert=True)
        await query.answer("No balances to remove.", show_alert=True)
        await query.edit_message_text(
        await query.edit_message_text("Exporting all data...")
        await query.edit_message_text("Exporting balances...")
        await query.edit_message_text("Exporting expenses...")
        await query.edit_message_text("Exporting income...")
        await query.edit_message_text("Nothing selected.", reply_markup=markup)
        await query.edit_message_text("Session expired. Use /erase to start over.")
        await query.edit_message_text('Generating backup...')
        await query.edit_message_text('Please send the zip file you want to restore.')
        await query.edit_message_text(f"❌ No income for {_month_label(month)}.")
        await query.edit_message_text(f"❌ No records for {_month_label(month)}.")
        await query.edit_message_text(prompt)
        await query.message.reply_document(
        await query.message.reply_text("❌ No balance data yet.")
        await query.message.reply_text(f"❌ No income for {_month_label(month)}.")
        await query.message.reply_text(f"❌ No records for {_month_label(month)}.")
        await update.message.reply_text(
        await update.message.reply_text("Usage: /out <amount> [category] [title]")
        await update.message.reply_text(f"❌ Could not parse: {e}")
        await update.message.reply_text(picker_text, reply_markup=markup)
        await update.message.reply_text(text, reply_markup=keyboard, parse_mode="Markdown")
        back_keyboard = InlineKeyboardMarkup([[
        body = f"<pre>{tab_report}</pre>"
        body = f"Report too large for inline preview ({len(records)} records). Use the .tsv file button below."
        body,
        buf = io.BytesIO()
        buf.seek(0)
        buttons = []
        buttons.append(InlineKeyboardButton(".tsv file", callback_data="balance_tsv"))
        buttons.append(InlineKeyboardButton("Semicolon separated", copy_text=CopyTextButton(text=semi_report)))
        buttons.append(InlineKeyboardButton("Tab separated", copy_text=CopyTextButton(text=tab_report)))
        callback_data="erase_toggle_all",
        cat, amount, title = parse_payment(text, categories)
        ccy = currencies.get(name, "RUB")
        ccy = pending["ccy"]
        ccy = text.strip().upper()
        cells = [d.get(col, "") for col in fmt]
        cells = [month]
        col_buttons.append(InlineKeyboardButton(col, callback_data=f"fmt_set:{report_type}:{pos}:{col}"))
        ctx.user_data.pop("balance", None)
        ctx.user_data.pop("erase", None)
        ctx.user_data["balance"] = {
        currencies = store.get_all_currencies()
        currencies,
        currencies=currencies,
        current_names = store.get_balance_names()
        cutoff=BALANCE_FUZZY_CUTOFF,
        d = field_extractor(rec)
        data_dir = Path(store._dir)
        data_dir = store._dir
        date_str, category, title, amount = record
        deleted = store.delete_expense_records_by_index(month, indices)
        deleted = store.delete_income_records_by_index(month, indices)
        document=io.BytesIO(tsv_bytes),
        edit_mode = state.get("edit")
        elif candidates:
        else:
        end = min(start + _ERASE_PAGE_SIZE, total)
        except ValueError:
        f"Active month: *{month_label}*
        f"Current: {current}"
        f"Deleted *{deleted}* record(s) from *{_month_label(month)}*.",
        f"{_REPORT_LABELS[report_type]} format \u2014 column {pos + 1} of {len(fmt)}\n"
        f"{all_mark} All ({total} records)",
        f"✅ *{name}*: {_format_balance_amount(amount)} ({_month_label(month)})",
        f"✅ Deleted *{len(deleted)}* record(s) from *{_month_label(month)}*.",
        f"✅ Expense recorded: *{cat}* {amount}{title_part} ({_month_label(month)})",
        f"✅ Income recorded: *{amount}*{tax_label} — {name} ({_month_label(month)})",
        filename="balances.tsv",
        filename=f"expenses-{month}.tsv",
        filename=f"income-{month}.tsv",
        files = [f for f in files if f.is_file()]
        files = sorted(data_dir.iterdir()) if data_dir.is_dir() else []
        for c in BALANCE_QUICK_CURRENCIES
        for ccy in rate_ccys:
        for m in months:
        for name in historic_names:
        formatted = "{:,}".format(int_part).replace(",", "\u202f") + "." + frac
        formatted = "{:,}".format(whole).replace(",", "\u202f")
        frac = str(amount).split(".")[1]
        from datetime import datetime
        from pathlib import Path
        historic_names = store.get_historic_names()
        if any_amount:
        if ccy != "RUB" and ccy not in rate_ccys:
        if ccy != "RUB":
        if edit_mode:
        if len(body) > TELEGRAM_MESSAGE_LIMIT:
        if len(semi_report) <= 256:
        if len(tab_report) <= 256:
        if matched:
        if not current_names:
        if not data_dir.exists():
        if not files:
        if not months:
        if not preview_records:
        if not re.match(r"^[A-Z]{3}$", ccy):
        if not text:
        if not tsv:
        if pending_amount is not None:
        if rate <= 0:
        if rate is None:
        if status == "rate_prompt":
        if taxable:
        if title:
        import io
        import shutil
        import zipfile
        int_part = int(amount)
        keyboard = InlineKeyboardMarkup([
        keyboard = InlineKeyboardMarkup([[
        keyboard = [
        keyboard.append([InlineKeyboardButton(label, callback_data=f"set_month:{m}")])
        label = "{}: {}".format(name, _format_ccy_amount(amount, ccy))
        label = ("✓ " if m == current else "") + _month_label(m)
        label = _erase_record_label(record, record_type)
        label = f"{amount_str} — {name}"
        label = f"{category} {amount}"
        label = f"{cat} {amount}" + (f" — {title}" if title else "")
        lines.append(f"  • {label}")
        lines.append(separator.join(cells))
        lower_input, lower_names,
        mark = "☑" if idx in selected else "☐"
        matched, candidates = _resolve_balance_name(name_input, current_names)
        menu_text, markup = await _build_balance_menu_from_store(store, month)
        month = (month - 1) % 12 + 1
        month = pending["month"]
        month = store.get_current_month()
        month = today.month - i
        month,
        month_data = {m: store.get_balance_month(m) for m in months}
        months = store.list_balance_months()
        months = store.list_income_months()
        months = store.list_months_with_counts()
        months.append(f"{year:04d}-{month:02d}")
        n = int(args[1].strip())
        n=BALANCE_FUZZY_MAX_MATCHES,
        name = pending["name"]
        name = state.get("pending_name")
        name = state["pending_name"]
        name_headers.append("{} ({})".format(name, sign))
        name_input, amount_str = args[1], args[2]
        nav = []
        nav.append(InlineKeyboardButton("Next →", callback_data=next_data))
        nav.append(InlineKeyboardButton("← Prev", callback_data=prev_data))
        nav_buttons.append(InlineKeyboardButton("+ Add", callback_data=f"fmt_add:{report_type}"))
        nav_buttons.append(InlineKeyboardButton("🗑 Del", callback_data=f"fmt_del:{report_type}:{pos}"))
        next_data = f"erase_page:{page + 1}" if page < total_pages - 1 else "noop"
        page_records = list(enumerate(records))
        page_records = list(enumerate(records))[start:end]
        parse_mode="HTML",
        parse_mode="Markdown",
        pending = state.get("pending", {})
        pending_amount = state.get("pending_amount")
        picker_text, markup = _build_currency_picker(text)
        prev_data = f"erase_page:{page - 1}" if page > 0 else "noop"
        preview_records = records[-n:] if n and records else []
        raise ApplicationHandlerStop
        rate = await _resolve_rate(store, ccy, month)
        rates = store.get_all_rates()
        rates=store.get_all_rates(),
        records = store.read_income(month)
        records = store.read_month(month)
        reply_markup=InlineKeyboardMarkup([[b] for b in buttons]),
        reply_markup=InlineKeyboardMarkup(keyboard),
        reply_markup=keyboard,
        return
        return  # cap reached
        return  # minimum one column
        return  # stale callback — silently ignore
        return "{} {}".format(ccy, formatted)
        return "{} {}".format(formatted, sign)
        return "—"
        return "❌ No records to erase."
        return 1.0
        return None
        return None, []
        return float(amount)
        return label
        return original_matches[0], []
        return rate
        row,
        rows.append([InlineKeyboardButton(
        rows.append([InlineKeyboardButton(label, callback_data="balance_set:{}".format(name))])
        rows.append(nav)
        rows.append(nav_buttons)
        rows.append(separator.join(cells))
        semi_lines = render_balance_report(months, historic_names, month_data,
        semi_report = "\n".join(semi_lines)
        separator="\t",
        sign = _CCY_SIGNS.get(ccy, ccy)
        sorted(months), historic_names, month_data,
        start = page * _ERASE_PAGE_SIZE
        state["selected"] = set()
        state["selected"] = set(range(total))
        state["selected"].add(idx)
        state["selected"].discard(idx)
        status, prompt = await _commit_balance_with_rate_check(
        status, prompt = await _commit_balance_with_rate_check(store, ctx, month, name, amount)
        store = ctx.bot_data['store']
        store.add_balance_name(name, currency=ccy)
        store.get_all_rates(),
        store.get_balance_month(month),
        store.get_balance_names(),
        store.set_balance(month, name, amount)
        store.set_balance_currency(name, ccy)
        store.set_rate(ccy, month, rate)
        tab_lines  = render_balance_report(months, historic_names, month_data,
        tab_report  = "\n".join(tab_lines)
        text = (
        text = _format_erase_preview(preview_records, month)
        text = f"Erase {record_type}s — {_month_label(month)}\n{sel_count} selected"
        timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
        total_pages = (total + _ERASE_PAGE_SIZE - 1) // _ERASE_PAGE_SIZE
        total_pages = 1
        try:
        tsv = _build_all_expenses_tsv(store)
        tsv = _build_all_income_tsv(store)
        tsv = await _build_all_balances_tsv(store)
        values = month_data.get(month, {})
        with zipfile.ZipFile(buf, "w", zipfile.ZIP_DEFLATED) as zf:
        with zipfile.ZipFile(buf, 'w', zipfile.ZIP_DEFLATED) as zf:
        year = today.year + (month - 1) // 12
        zip_filename = f'backup_{timestamp}.zip'
        }
       pip install -r requirements.txt
       python bot.py
    """
    """'2026-03' → 'March 2026'"""
    """Assemble `_build_balance_menu` args from the store, auto-fetching missing rates."""
    """Build a TSV with all balance data, chronologically."""
    """Build a TSV with all expenses across all months, chronologically."""
    """Build a TSV with all income across all months, chronologically."""
    """Build the currency picker keyboard for `name`. Pure function."""
    """Build the remove-confirmation keyboard for a named balance. Pure function."""
    """Format a balance amount for display. None → '—'; whole floats drop decimal."""
    """Format a monetary amount with its currency sign.
    """Format an RUB total with thin-space thousands separators and a ₽ suffix."""
    """Handle free-text replies during balance awaiting flows."""
    """Re-render the balance menu on an existing query message."""
    """Record income if text follows the command; show error otherwise."""
    """Return (text, InlineKeyboardMarkup) for the /report type selector."""
    """Return 2 future months + current + 11 past months, newest-first."""
    """Return a human-readable preview of records about to be erased."""
    """Return a short display label for a record row."""
    """Return amount converted to RUB, or None if the rate is missing."""
    """Return state dict or None if session is expired."""
    """Show the month selector for the given record type. Edits the existing message."""
    """Try to get a rate: check cache first, then fetch from CBR.
    """User chose '＋ Create new' from the no-match picker."""
    """User picked a balance from the disambiguation / no-match picker."""
    """User picked a balance to edit — show currency picker in edit mode."""
    """User picked a balance to remove — show keep/delete confirmation."""
    """User tapped a balance button in the menu — prompt for a value."""
    """User tapped a currency quick-button (RUB/USD/EUR)."""
    """User tapped ⚙ Edit — show list of balances to edit currency."""
    """User tapped ＋ Add in the menu."""
    """User tapped ＋ Other — prompt for a free-text 3-letter code."""
    """User tapped － Remove — show list of current balances."""
    "expense": ["date", "category", "title", "amount"],
    "income":  ["amount", "taxable", "year", "month", "name"],
    # /erase N — show last N expense records and ask to confirm (unchanged)
    # /erase with no args — type selector
    # Auto-fetch any missing rates for non-RUB currencies
    # Bottom row: Delete / Back / Cancel
    # Build header
    # Commands
    # Creation path
    # Data rows
    # Determine pagination
    # Determine which non-RUB currencies are in use (for rate columns)
    # Menu form: /balance
    # Message text
    # Owner check — group -1 runs before everything else
    # Pagination nav (only when paginated)
    # Payment messages (any non-command text)
    # Per-account buttons with currency signs
    # Per-currency subtotals
    # Quick form: /balance <name> <amount>
    # Record rows
    # Row 0: Select All stub
    # Row 0: column selector buttons
    # Row 1: navigation — Prev/Next always present; noop at boundaries for stable layout
    # Row 2: done
    )
    )])
    Application,
    ApplicationHandlerStop,
    Build report lines from records using a configurable column format.
    Build the /balance main menu keyboard.
    Build the editor message text and keyboard for position `pos` in `fmt`.
    Build the erase checkbox page from state dict.
    CallbackQueryHandler,
    Columns: month, then each balance name with currency sign in header,
    CommandHandler,
    ContextTypes,
    Fuzzy-match input_name against current_names.
    MessageHandler,
    Other: 'CHF 5 000' (code prefix). None -> '—'.
    Pure function — no I/O.
    Pure function.
    RUB: '150 000 ₽' (suffix). USD/EUR/GBP: '$5 000' (prefix).
    Render a balance report as a list of separator-joined strings.
    Returns (matched_name, []) on single match,
    Returns (text, InlineKeyboardMarkup). Pure function — no I/O.
    Returns list of joined line strings. Unknown column names yield empty cells.
    Stores fetched rates in the cache. Returns None if both fail.
    Try to commit a balance. If its currency is non-RUB, attempt to
    TypeHandler,
    Uses thin-space thousands separators.
    ]
    ])
    ], [
    ]]
    ]])
    _, month, n_str = query.data.split(":")
    _, name, ccy = query.data.split(":", 2)
    _, record_type, month = query.data.split(":")
    _, report_type = query.data.split(":")
    _, report_type, pos_str = query.data.split(":")
    _, report_type, pos_str, value = query.data.split(":", 3)
    all_lines = []  # type: list[str]
    all_mark = "☑" if all_selected else "☐"
    all_selected = len(selected) == total and total > 0
    amount = state.get("pending_amount")
    amount: Optional[float],
    amount: float,
    amount_str, taxable, name = record
    app = Application.builder().token(token).post_init(post_init).build()
    app.add_handler(CallbackQueryHandler(cb_backup_action, pattern=r"^backup:")
    app.run_polling(drop_pending_updates=True)
    app.add_handler(CallbackQueryHandler(cb_balance_add,           pattern=r"^balance_add$"))
    app.add_handler(CallbackQueryHandler(cb_balance_back,          pattern=r"^balance_back$"))
    app.add_handler(CallbackQueryHandler(cb_balance_ccy_other,     pattern=r"^balance_ccy_other:"))
    app.add_handler(CallbackQueryHandler(cb_balance_ccy_pick,      pattern=r"^balance_ccy_pick:"))
    app.add_handler(CallbackQueryHandler(cb_balance_done,          pattern=r"^balance_done$"))
    app.add_handler(CallbackQueryHandler(cb_balance_edit,          pattern=r"^balance_edit$"))
    app.add_handler(CallbackQueryHandler(cb_balance_edit_pick,     pattern=r"^balance_edit_pick:"))
    app.add_handler(CallbackQueryHandler(cb_balance_pick,          pattern=r"^balance_pick:"))
    app.add_handler(CallbackQueryHandler(cb_balance_pick_new,      pattern=r"^balance_pick_new$"))
    app.add_handler(CallbackQueryHandler(cb_balance_remove,        pattern=r"^balance_remove$"))
    app.add_handler(CallbackQueryHandler(cb_balance_remove_cancel, pattern=r"^balance_remove_cancel$"))
    app.add_handler(CallbackQueryHandler(cb_balance_remove_delete, pattern=r"^balance_remove_delete:"))
    app.add_handler(CallbackQueryHandler(cb_balance_remove_keep,   pattern=r"^balance_remove_keep:"))
    app.add_handler(CallbackQueryHandler(cb_balance_remove_pick,   pattern=r"^balance_remove_pick:"))
    app.add_handler(CallbackQueryHandler(cb_balance_set,           pattern=r"^balance_set:"))
    app.add_handler(CallbackQueryHandler(cb_balance_tsv,           pattern=r"^balance_tsv$"))
    app.add_handler(CallbackQueryHandler(cb_erase_back_months, pattern=r"^erase_back_months:"))
    app.add_handler(CallbackQueryHandler(cb_erase_cancel,    pattern=r"^erase_cancel$"))
    app.add_handler(CallbackQueryHandler(cb_erase_do_selected, pattern=r"^erase_do_selected$"))
    app.add_handler(CallbackQueryHandler(cb_erase_last_n_do, pattern=r"^erase_last_n_do:"))
    app.add_handler(CallbackQueryHandler(cb_erase_month,       pattern=r"^erase_month:"))
    app.add_handler(CallbackQueryHandler(cb_erase_page,        pattern=r"^erase_page:"))
    app.add_handler(CallbackQueryHandler(cb_erase_toggle,      pattern=r"^erase_toggle:"))
    app.add_handler(CallbackQueryHandler(cb_erase_toggle_all,  pattern=r"^erase_toggle_all$"))
    app.add_handler(CallbackQueryHandler(cb_erase_type,        pattern=r"^erase_type:"))
    app.add_handler(CallbackQueryHandler(cb_export,                pattern=r"^export:"))
    app.add_handler(CallbackQueryHandler(cb_fmt_add,  pattern=r"^fmt_add:"))
    app.add_handler(CallbackQueryHandler(cb_fmt_del,  pattern=r"^fmt_del:"))
    app.add_handler(CallbackQueryHandler(cb_fmt_edit, pattern=r"^fmt_edit:"))
    app.add_handler(CallbackQueryHandler(cb_fmt_menu, pattern=r"^fmt_menu$"))
    app.add_handler(CallbackQueryHandler(cb_fmt_nav,  pattern=r"^fmt_nav:"))
    app.add_handler(CallbackQueryHandler(cb_fmt_set,  pattern=r"^fmt_set:"))
    app.add_handler(CallbackQueryHandler(cb_income_report, pattern=r"^income_report:"))
    app.add_handler(CallbackQueryHandler(cb_income_tsv, pattern=r"^income_tsv:"))
    app.add_handler(CallbackQueryHandler(cb_noop,     pattern=r"^noop$"))
    app.add_handler(CallbackQueryHandler(cb_report,       pattern=r"^report:"))
    app.add_handler(CallbackQueryHandler(cb_report_type,  pattern=r"^report_type:"))
    app.add_handler(CallbackQueryHandler(cb_set_month,    pattern=r"^set_month:"))
    app.add_handler(CallbackQueryHandler(cb_tsv, pattern=r"^tsv:"))
    app.add_handler(CommandHandler("backup", cmd_backup))
    app.add_handler(CommandHandler("balance", cmd_balance))
    app.add_handler(CommandHandler("erase", cmd_erase))
    app.add_handler(CommandHandler("export", cmd_export))
    app.add_handler(CommandHandler("in", cmd_income))
    app.add_handler(CommandHandler("month", cmd_month))
    app.add_handler(CommandHandler("out", cmd_out))
    app.add_handler(CommandHandler("report", cmd_report))
    app.add_handler(CommandHandler("settings", cmd_settings))
    app.add_handler(CommandHandler("start", cmd_start))
    app.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, handle_payment))
    app.add_handler(TypeHandler(Update, owner_check), group=-1)
    app.bot_data["categories"] = categories
    app.bot_data["owner_id"] = owner_id
    app.bot_data["store"] = Storage()
    args = update.message.text.strip().split(None, 1)
    args = update.message.text.strip().split(None, 2)
    auto-fetch the rate from CBR. Only falls back to manual prompt
    await _record_payment(update, ctx, args[1].strip())
    await _record_payment(update, ctx, update.message.text.strip())
    await _render_balance_menu_on_query(query, store)
    await _show_erase_month_selector(query, record_type, store)
    await app.bot.set_my_commands([
    await query.answer()
    await query.edit_message_text(
    await query.edit_message_text("Cancelled.")
    await query.edit_message_text("Enter a name for the new balance:")
    await query.edit_message_text("Select balance to edit currency:",
    await query.edit_message_text("Select balance to remove:", reply_markup=InlineKeyboardMarkup(rows))
    await query.edit_message_text("Select month to erase:", reply_markup=keyboard)
    await query.edit_message_text("Settings:", reply_markup=keyboard)
    await query.edit_message_text("✅ Done.")
    await query.edit_message_text(f"Enter 3-letter currency code for \"{name}\":")
    await query.edit_message_text(f"Enter new value for *{name}*:", parse_mode="Markdown")
    await query.edit_message_text(f"✅ Active month set to *{_month_label(month)}*", parse_mode="Markdown")
    await query.edit_message_text(text, reply_markup=markup)
    await query.message.reply_document(
    await update.callback_query.answer()
    await update.message.reply_text(
    await update.message.reply_text("Export all data as TSV:", reply_markup=keyboard)
    await update.message.reply_text("Select type to erase:", reply_markup=keyboard)
    await update.message.reply_text("Settings:", reply_markup=keyboard)
    await update.message.reply_text('Choose a backup action:', reply_markup=keyboard)
    await update.message.reply_text(text, reply_markup=markup)
    awaiting = state.get("awaiting")
    balance_state = ctx.user_data.get("balance", {})
    body = f"<pre>{tab_report}</pre>"
    buttons = []
    buttons.append(InlineKeyboardButton(".tsv file", callback_data=f"income_tsv:{month}"))
    buttons.append(InlineKeyboardButton(".tsv file", callback_data=f"tsv:{month}"))
    categories = ctx.bot_data["categories"]
    categories = load_categories(categories_path)
    categories_path = Path(__file__).parent / "categories.yaml"
    ccy = store.get_balance_currency(name)
    ccy: str,
    col_buttons = []
    col_buttons.append(InlineKeyboardButton("(empty)", callback_data=f"fmt_set:{report_type}:{pos}:"))
    ctx.user_data.pop("balance", None)
    ctx.user_data.pop("erase", None)
    ctx.user_data["balance"] = {
    ctx.user_data["balance"] = {"awaiting": "pick_currency", "pending_name": name, "edit": True}
    ctx.user_data["erase"] = {
    ctx: ContextTypes.DEFAULT_TYPE,
    currencies = currencies or {}
    currencies = store.get_all_currencies()
    currencies: Optional[dict] = None,
    currencies: {name: ccy}.
    current = fmt[pos] if fmt[pos] else "(empty)"
    current = store.get_current_month()
    current_month = store.get_current_month()
    current_names: list,
    date_str, category, title, sum_str = record
    deleted = store.delete_last_n_records(month, n)
    done_row = [InlineKeyboardButton("✓ Done", callback_data="fmt_menu")]
    edit_mode = state.get("edit")
    elif awaiting == "add_name":
    elif awaiting == "balance_currency":
    elif awaiting == "rate":
    elif export_type == "all":
    elif export_type == "balances":
    elif export_type == "income":
    elif query.data == 'backup:restore':
    elif report_type == "income":
    else:
    else:  # balance
    else:  # income
    except ParseError as e:
    export_type = query.data.split(":")[1]
    extractor = lambda rec: _income_field(rec, month)
    field_extractor — callable(record) -> dict[str, str]
    field_extractor,
    filters,
    fmt            — ordered column names; "" = empty column
    fmt = store.get_format("expense")
    fmt = store.get_format("income")
    fmt = store.get_format(report_type)
    fmt.append("")
    fmt.pop(pos)
    fmt: list,
    fmt[pos] = value
    for col in REPORT_COLUMNS[report_type]:
    for date_str, cat, title, amount in records:
    for i in range(-2, 12):
    for idx, record in page_records:
    for m in months:
    for month in months:
    for month in sorted(months):
    for month, _count in sorted(months_with_counts, key=lambda x: x[0]):
    for name in current_names:
    for name in historic_names:
    for name in store.get_balance_names():
    for rec in records:
    from datetime import datetime
    header_parts = ["month"] + name_headers + rate_ccys
    historic_names = store.get_historic_names()
    historic_names: list,
    idx = int(query.data.split(":")[1])
    if CBR fails.
    if amount is None:
    if awaiting == "set_value":
    if balance_state.get("awaiting"):
    if ccy != "RUB":
    if ccy == "RUB":
    if current_names:
    if edit_mode:
    if export_type == "expenses":
    if idx in state["selected"]:
    if isinstance(whole, int):
    if len(args) < 2 or not args[1].strip():
    if len(args) == 2 and args[1].strip().isdigit():
    if len(args) == 3:
    if len(body) > TELEGRAM_MESSAGE_LIMIT:
    if len(fmt) < 10:
    if len(fmt) <= 1:
    if len(fmt) > 1:
    if len(fmt) >= 10:
    if len(original_matches) == 1:
    if len(semi_report) <= 256:
    if len(state["selected"]) == total:
    if len(tab_report) <= 256:
    if nav_buttons:
    if not all_lines:
    if not current_names:
    if not matches:
    if not months:
    if not months_with_counts:
    if not names:
    if not records:
    if not state:
    if not state["selected"]:
    if not tsv_bytes:
    if paginated:
    if pending_amount is not None:
    if pos >= len(fmt):
    if query.data == 'backup:create':
    if rate is None:
    if rate is not None:
    if record_type == "expense":
    if report_type == "expense":
    if sign is None:
    if state["type"] == "expense":
    if status == "rate_prompt":
    if update.effective_user and update.effective_user.id != owner_id:
    indices = state["selected"]
    keyboard = InlineKeyboardMarkup([
    keyboard = InlineKeyboardMarkup([[
    keyboard = InlineKeyboardMarkup([[b] for b in buttons])
    keyboard = []
    lines = ["Balances \u2014 {}".format(_month_label(month))]
    lines = []
    lines = [f"About to erase *{len(records)}* record(s) from *{_month_label(month)}*:"]
    lines = render_balance_report(
    lines = render_rows(records, fmt, _expense_field, separator="\t")
    lines = render_rows(records, fmt, lambda rec: _income_field(rec, month), separator="\t")
    load_dotenv()
    lower_input = input_name.lower()
    lower_names = [n.lower() for n in current_names]
    main()
    markup = InlineKeyboardMarkup([
    matches = difflib.get_close_matches(
    month = query.data.split(":")[1]
    month = state["month"]
    month = store.get_current_month()
    month: str,
    month_data = {m: store.get_balance_month(m) for m in months}
    month_data: dict,
    month_label = datetime.strptime(month, "%Y-%m").strftime("%B %Y")
    month_values: dict,
    month_values: {name: amount} for the current month.
    months = []
    months = _month_options(current)
    months = store.list_balance_months()
    months = store.list_income_months()
    months: list,
    months_with_counts = store.list_months_with_counts()
    msg = await update.message.reply_text(text, reply_markup=markup)
    n = int(n_str)
    name = query.data.split(":", 1)[1]
    name: str,
    name_headers = []
    names = store.get_balance_names()
    nav_buttons = [
    next_data = f"fmt_nav:{report_type}:{pos + 1}" if pos < len(fmt) - 1 else "noop"
    original_matches = [current_names[lower_names.index(m)] for m in matches]
    owner_id = ctx.bot_data["owner_id"]
    owner_id = int(os.environ["OWNER_ID"])
    page = state["page"]
    paginated = total > _ERASE_SINGLE_PAGE_MAX
    pending_amount = state.get("pending_amount")
    pos = int(pos_str)
    pos = len(fmt) - 1
    pos = max(0, min(pos, len(fmt) - 1))
    pos = max(0, pos - 1)
    prev_data = f"fmt_nav:{report_type}:{pos - 1}" if pos > 0 else "noop"
    query = update.callback_query
    rate = await fetch_rate(ccy, month)
    rate = rates.get(ccy, {}).get(month)
    rate = store.get_rate(ccy, month)
    rate_ccys = []  # type: list
    rates = rates or {}
    rates: Optional[dict] = None,
    rates: dict,
    rates: {ccy: {month: float}}.
    record_type = query.data.split(":")[1]
    record_type = state["type"]
    records        — raw tuples from storage
    records = state["records"]
    records = store.read_income(month)
    records = store.read_month(month)
    records: list,
    report_type = query.data.split(":")[1]
    return "Select report type:", keyboard
    return "\n".join(all_lines).encode("utf-8")
    return "\n".join(lines)
    return "\n".join(lines), InlineKeyboardMarkup(rows)
    return "\n".join(lines).encode("utf-8")
    return "done", None
    return "{}{}".format(sign, formatted)
    return None, original_matches
    return _build_balance_menu(
    return ctx.user_data.get("erase")
    return datetime.strptime(month, "%Y-%m").strftime("%B %Y")
    return f"{s} ₽"
    return float(amount) * float(rate)
    return lines
    return months
    return rate
    return rows
    return str(int(amount)) if amount == int(amount) else str(amount)
    return text, InlineKeyboardMarkup(rows)
    return text, keyboard
    return text, markup
    return {
    return {"date": date_str, "category": category, "title": title, "amount": sum_str}
    row = [
    rows = [[
    rows = [[InlineKeyboardButton(n, callback_data=f"balance_edit_pick:{n}")] for n in names]
    rows = [[InlineKeyboardButton(n, callback_data=f"balance_remove_pick:{n}")] for n in names]
    rows = []
    rows = [col_buttons]
    rows = [separator.join(header_parts)]
    rows.append([
    rows.append([InlineKeyboardButton(
    rows.append([InlineKeyboardButton("\u2713 Done", callback_data="balance_done")])
    rows.append([InlineKeyboardButton("← Back", callback_data="balance_back")])
    rows.append(done_row)
    s = f"{whole:,}".replace(",", "\u202f")
    sel_count = len(selected)
    selected = state["selected"]
    semi_lines = render_rows(records, fmt, _expense_field, separator=";")
    semi_lines = render_rows(records, fmt, extractor, separator=";")
    semi_report = "\n".join(semi_lines)
    separator      — "\t" for tab, ";" for semicolon
    separator: str = "\t",
    sign = _CCY_SIGNS.get(ccy)
    state = _erase_stale_guard(ctx)
    state = ctx.user_data.get("balance", {})
    state = ctx.user_data.get("balance", {}) or {}
    state = ctx.user_data.setdefault("balance", {})
    state keys used: type, month, records, selected, page
    state["awaiting"] = "add_name"
    state["awaiting"] = "balance_currency"
    state["awaiting"] = "set_value"
    state["menu_message_id"] = None
    state["menu_message_id"] = query.message.message_id
    state["page"] = int(query.data.split(":")[1])
    state["pending_amount"] = None
    state["pending_name"] = name
    status, prompt = await _commit_balance_with_rate_check(store, ctx, month, name, amount)
    store = ctx.bot_data["store"]  # type: Storage
    store.add_balance_name(name, currency=ccy)
    store.append_income(month, amount, taxable, name)
    store.append_record(month, cat, amount, title)
    store.remove_balance_name(name, keep_history=False)
    store.remove_balance_name(name, keep_history=True)
    store.set_balance(month, name, amount)
    store.set_current_month(month)
    store.set_format(report_type, fmt)
    store: "Storage",
    store: Storage = ctx.bot_data["store"]
    tab_lines  = render_rows(records, fmt, _expense_field, separator="\t")
    tab_lines  = render_rows(records, fmt, extractor, separator="\t")
    tab_report  = "\n".join(tab_lines)
    tax_label = " (taxable)" if taxable else " (not taxable)"
    text = (
    text = f'Currency for "{name}"?'
    text = f'Remove "{name}"?'
    text = update.message.text.strip()
    text, markup = _build_balance_remove_confirm(name)
    text, markup = _build_currency_picker(name)
    text, markup = _build_erase_keyboard(ctx.user_data["erase"])
    text, markup = _build_erase_keyboard(state)
    text, markup = _build_fmt_editor(report_type, fmt, pos)
    text, markup = _build_report_type_keyboard()
    text, markup = await _build_balance_menu_from_store(store, month)
    then one rate column per non-RUB currency.
    title_part = f" — {title}" if title else ""
    today = datetime.today()
    token = os.environ["BOT_TOKEN"]
    total = len(records)
    total = len(state["records"])
    try:
    tsv_bytes = "\n".join(lines).encode("utf-8")
    tsv_bytes = await _build_all_balances_tsv(store)
    whole = int(amount) if amount == int(amount) else amount
    whole = int(round(amount))
    year, mon = month.split("-")
    }
   Get your OWNER_ID by messaging @userinfobot on Telegram.
"
"""
",
# ── balance callbacks ─────────────────────────────────────────────────────────
# ── balance report ────────────────────────────────────────────────────────────
# ── callback handlers ─────────────────────────────────────────────────────────
# ── command handlers ──────────────────────────────────────────────────────────
# ── erase helpers ─────────────────────────────────────────────────────────────
# ── export handlers ──────────────────────────────────────────────────────────
# ── helpers ───────────────────────────────────────────────────────────────────
# ── income handlers ───────────────────────────────────────────────────────────
# ── main ──────────────────────────────────────────────────────────────────────
# ── payment handler ───────────────────────────────────────────────────────────
# ── report rendering ───────────────────────────────────────────────────────────
# ── security ──────────────────────────────────────────────────────────────────
# ── settings / format editor ──────────────────────────────────────────────────
# ── settings handlers ─────────────────────────────────────────────────────────
## How to run
)
) -> Optional[float]:
) -> list:
) -> tuple:
):
1. Copy .env.example to .env and fill in BOT_TOKEN and OWNER_ID.
2. Install dependencies:
3. Run locally:
4. For production, deploy with the provided expense-tracker.service systemd unit.
BALANCE_FUZZY_CUTOFF = 0.6
BALANCE_FUZZY_MAX_MATCHES = 3
BALANCE_QUICK_CURRENCIES = ("RUB", "USD", "EUR")
REPORT_COLUMNS: dict[str, list[str]] = {
Requirements: Python 3.9+, python-telegram-bot v20+
TELEGRAM_MESSAGE_LIMIT = 4096
_CCY_SIGNS = {"RUB": "₽", "USD": "$", "EUR": "€", "GBP": "£"}
_ERASE_PAGE_SIZE = 10
_ERASE_SINGLE_PAGE_MAX = 15
_REPORT_LABELS = {"expense": "Expense", "income": "Income"}
async def _build_all_balances_tsv(store: Storage) -> Optional[bytes]:
async def _build_balance_menu_from_store(store: "Storage", month: str) -> tuple:
async def _commit_balance_with_rate_check(
async def _handle_balance_text(update: Update, ctx: ContextTypes.DEFAULT_TYPE) -> None:
async def _record_payment(update: Update, ctx: ContextTypes.DEFAULT_TYPE, text: str) -> None:
async def _render_balance_menu_on_query(query, store: "Storage") -> None:
async def _resolve_rate(
async def _show_erase_month_selector(query, record_type: str, store) -> None:
async def cb_backup_action(update: Update, ctx: ContextTypes.DEFAULT_TYPE) -> None:
async def cb_balance_add(update: Update, ctx: ContextTypes.DEFAULT_TYPE) -> None:
async def cb_balance_back(update: Update, ctx: ContextTypes.DEFAULT_TYPE) -> None:
async def cb_balance_ccy_other(update: Update, ctx: ContextTypes.DEFAULT_TYPE) -> None:
async def cb_balance_ccy_pick(update: Update, ctx: ContextTypes.DEFAULT_TYPE) -> None:
async def cb_balance_done(update: Update, ctx: ContextTypes.DEFAULT_TYPE) -> None:
async def cb_balance_edit(update: Update, ctx: ContextTypes.DEFAULT_TYPE) -> None:
async def cb_balance_edit_pick(update: Update, ctx: ContextTypes.DEFAULT_TYPE) -> None:
async def cb_balance_pick(update: Update, ctx: ContextTypes.DEFAULT_TYPE) -> None:
async def cb_balance_pick_new(update: Update, ctx: ContextTypes.DEFAULT_TYPE) -> None:
async def cb_balance_remove(update: Update, ctx: ContextTypes.DEFAULT_TYPE) -> None:
async def cb_balance_remove_cancel(update: Update, ctx: ContextTypes.DEFAULT_TYPE) -> None:
async def cb_balance_remove_delete(update: Update, ctx: ContextTypes.DEFAULT_TYPE) -> None:
async def cb_balance_remove_keep(update: Update, ctx: ContextTypes.DEFAULT_TYPE) -> None:
async def cb_balance_remove_pick(update: Update, ctx: ContextTypes.DEFAULT_TYPE) -> None:
async def cb_balance_set(update: Update, ctx: ContextTypes.DEFAULT_TYPE) -> None:
async def cb_balance_tsv(update: Update, ctx: ContextTypes.DEFAULT_TYPE) -> None:
async def cb_erase_back_months(update: Update, ctx: ContextTypes.DEFAULT_TYPE) -> None:
async def cb_erase_cancel(update: Update, ctx: ContextTypes.DEFAULT_TYPE) -> None:
async def cb_erase_do_selected(update: Update, ctx: ContextTypes.DEFAULT_TYPE) -> None:
async def cb_erase_last_n_do(update: Update, ctx: ContextTypes.DEFAULT_TYPE) -> None:
async def cb_erase_month(update: Update, ctx: ContextTypes.DEFAULT_TYPE) -> None:
async def cb_erase_page(update: Update, ctx: ContextTypes.DEFAULT_TYPE) -> None:
async def cb_erase_toggle(update: Update, ctx: ContextTypes.DEFAULT_TYPE) -> None:
async def cb_erase_toggle_all(update: Update, ctx: ContextTypes.DEFAULT_TYPE) -> None:
async def cb_erase_type(update: Update, ctx: ContextTypes.DEFAULT_TYPE) -> None:
async def cb_export(update: Update, ctx: ContextTypes.DEFAULT_TYPE) -> None:
async def cb_fmt_add(update: Update, ctx: ContextTypes.DEFAULT_TYPE) -> None:
async def cb_fmt_del(update: Update, ctx: ContextTypes.DEFAULT_TYPE) -> None:
async def cb_fmt_edit(update: Update, ctx: ContextTypes.DEFAULT_TYPE) -> None:
async def cb_fmt_menu(update: Update, ctx: ContextTypes.DEFAULT_TYPE) -> None:
async def cb_fmt_nav(update: Update, ctx: ContextTypes.DEFAULT_TYPE) -> None:
async def cb_fmt_set(update: Update, ctx: ContextTypes.DEFAULT_TYPE) -> None:
async def cb_income_report(update: Update, ctx: ContextTypes.DEFAULT_TYPE) -> None:
async def cb_income_tsv(update: Update, ctx: ContextTypes.DEFAULT_TYPE) -> None:
async def cb_noop(update: Update, ctx: ContextTypes.DEFAULT_TYPE) -> None:
async def cb_report(update: Update, ctx: ContextTypes.DEFAULT_TYPE) -> None:
async def cb_report_type(update: Update, ctx: ContextTypes.DEFAULT_TYPE) -> None:
async def cb_set_month(update: Update, ctx: ContextTypes.DEFAULT_TYPE) -> None:
async def cb_tsv(update: Update, ctx: ContextTypes.DEFAULT_TYPE) -> None:
async def cmd_backup(update: Update, ctx: ContextTypes.DEFAULT_TYPE) -> None:
async def cmd_balance(update: Update, ctx: ContextTypes.DEFAULT_TYPE) -> None:
async def cmd_erase(update: Update, ctx: ContextTypes.DEFAULT_TYPE) -> None:
async def cmd_export(update: Update, ctx: ContextTypes.DEFAULT_TYPE) -> None:
async def cmd_income(update: Update, ctx: ContextTypes.DEFAULT_TYPE) -> None:
async def cmd_month(update: Update, ctx: ContextTypes.DEFAULT_TYPE) -> None:
async def cmd_out(update: Update, ctx: ContextTypes.DEFAULT_TYPE) -> None:
async def cmd_report(update: Update, ctx: ContextTypes.DEFAULT_TYPE) -> None:
async def cmd_settings(update: Update, ctx: ContextTypes.DEFAULT_TYPE) -> None:
async def cmd_start(update: Update, ctx: ContextTypes.DEFAULT_TYPE) -> None:
async def handle_payment(update: Update, ctx: ContextTypes.DEFAULT_TYPE) -> None:
async def owner_check(update: Update, ctx: ContextTypes.DEFAULT_TYPE) -> None:
async def post_init(app: Application) -> None:
def _build_all_expenses_tsv(store: Storage) -> Optional[bytes]:
def _build_all_income_tsv(store: Storage) -> Optional[bytes]:
def _build_balance_menu(
def _build_balance_remove_confirm(name: str) -> tuple[str, InlineKeyboardMarkup]:
def _build_currency_picker(name: str) -> tuple:
def _build_erase_keyboard(state: dict) -> tuple:
def _build_fmt_editor(report_type: str, fmt: list, pos: int) -> tuple:
def _build_report_type_keyboard() -> tuple:
def _erase_record_label(record, record_type: str) -> str:
def _erase_stale_guard(ctx):
def _expense_field(record: tuple) -> dict:
def _format_balance_amount(amount: Optional[float]) -> str:
def _format_ccy_amount(amount: Optional[float], ccy: str) -> str:
def _format_erase_preview(records: list, month: str) -> str:
def _format_rub_total(amount: float) -> str:
def _income_field(record: tuple, month: str) -> dict:
def _month_label(month: str) -> str:
def _month_options(current: str) -> list[str]:
def _resolve_balance_name(input_name: str, current_names: list[str]) -> tuple[Optional[str], list[str]]:
def convert_to_rub(
def render_balance_report(
def render_rows(
from cbr import fetch_rate
from datetime import datetime
from dotenv import load_dotenv
from parser import ParseError, load_categories, parse_income, parse_payment
from pathlib import Path
from storage import Storage
from telegram import BotCommand, CopyTextButton, InlineKeyboardButton, InlineKeyboardMarkup, Update
from telegram.ext import (
from typing import Optional
if __name__ == "__main__":
import difflib
import io
import os
import re
import shutil
import zipfile
}
