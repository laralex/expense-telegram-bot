"""
storage.py — all file I/O for the expense tracker.

Data is stored in a single SQLite database file (data/storage.db) instead of
scattered JSON / text files.  The public API is identical to the previous
file-based version so bot.py and all tests stay unchanged.

Legacy JSON/text files are not imported automatically — use migrate_backup.py
to convert an old data/ folder into storage.db.

Public API:
    Storage(data_dir="data/")
        .append_record(month, category, amount, title)
        .read_month(month) -> list[(date_str, category, title, sum_str)]
        .list_months_with_counts() -> list[(month_str, count)] sorted desc
        .delete_month(month)
        .delete_all()
        .delete_expense_records_by_index(month, indices) -> int
        .delete_income_records_by_index(month, indices) -> int
        .get_current_month() -> str "YYYY-MM"
        .set_current_month(month)
        .get_format(report_type) -> list[str]
        .set_format(report_type, fmt: list[str])
        .append_income(month, amount, taxable, name)
        .read_income(month) -> list[(amount_str, taxable_bool, name)]
        .list_income_months() -> list[str]
        .get_balance_names() -> list[str]
        .get_historic_names() -> list[str]
        .add_balance_name(name, currency="RUB")
        .remove_balance_name(name, keep_history)
        .set_balance(month, name, amount)
        .get_balance_month(month) -> dict[str, float]
        .list_balance_months() -> list[str]
        .get_balance_currency(name) -> str
        .set_balance_currency(name, ccy)
        .get_all_currencies() -> dict
        .get_rate(ccy, month) -> float | None
        .set_rate(ccy, month, value)
        .get_all_rates() -> dict
        .list_missing_rates(month) -> list
"""

import json
import os
import re
import sqlite3
from contextlib import contextmanager
from datetime import date
from pathlib import Path
from typing import Optional, Generator

_CURRENCY_RE = re.compile(r"^[A-Z]{3}$")


class Storage:
    """SQLite-backed storage for the expense tracker."""

    _DEFAULT_FORMATS: dict[str, list[str]] = {
        "expense": ["title", "", "date", "category", "amount"],
        "income":  ["amount", "taxable", "year", "month", "name"],
    }

    def __init__(self, data_dir: str = "data/"):
        self._dir = Path(data_dir)
        self._dir.mkdir(parents=True, exist_ok=True)
        self._db_path = self._dir / "storage.db"
        self._init_db()

    # ── DB helpers ──────────────────────────────────────────────────────────

    def _init_db(self) -> None:
        """Create tables and indexes if they don't exist."""
        with self._connect() as con:
            con.executescript("""
                CREATE TABLE IF NOT EXISTS state (
                    key   TEXT PRIMARY KEY,
                    value TEXT NOT NULL
                );

                CREATE TABLE IF NOT EXISTS expenses (
                    id       INTEGER PRIMARY KEY AUTOINCREMENT,
                    month    TEXT NOT NULL,
                    date_str TEXT NOT NULL,
                    category TEXT NOT NULL DEFAULT '',
                    title    TEXT NOT NULL DEFAULT '',
                    amount   REAL NOT NULL
                );

                CREATE INDEX IF NOT EXISTS idx_expenses_month
                    ON expenses(month);

                CREATE TABLE IF NOT EXISTS incomes (
                    id       INTEGER PRIMARY KEY AUTOINCREMENT,
                    month    TEXT NOT NULL,
                    amount   REAL NOT NULL,
                    taxable  INTEGER NOT NULL,  -- 0 or 1
                    name     TEXT NOT NULL DEFAULT ''
                );

                CREATE INDEX IF NOT EXISTS idx_incomes_month
                    ON incomes(month);

                CREATE TABLE IF NOT EXISTS balances (
                    id       INTEGER PRIMARY KEY AUTOINCREMENT,
                    month    TEXT NOT NULL,
                    name     TEXT NOT NULL,
                    amount   REAL NOT NULL,
                    currency TEXT NOT NULL DEFAULT 'RUB',
                    UNIQUE(month, name)
                );

                -- Name registry (current + historic, per-name currency)
                CREATE TABLE IF NOT EXISTS name_registry (
                    name     TEXT PRIMARY KEY,
                    currency TEXT NOT NULL DEFAULT 'RUB',
                    is_current INTEGER NOT NULL DEFAULT 0
                );
            """)

    @contextmanager
    def _connect(self) -> Generator[sqlite3.Connection, None, None]:
        """Yield a connection with WAL mode + foreign keys enabled."""
        con = sqlite3.connect(
            str(self._db_path),
            timeout=30,
            isolation_level=None,  # autocommit
        )
        con.execute("PRAGMA journal_mode=WAL")
        con.execute("PRAGMA foreign_keys=ON")
        try:
            yield con
        finally:
            con.close()

    # ── state (key-value) ───────────────────────────────────────────────────

    def _get_state(self, key: str) -> Optional[str]:
        with self._connect() as con:
            row = con.execute(
                "SELECT value FROM state WHERE key = ?", (key,)
            ).fetchone()
            return row[0] if row else None

    def _set_state(self, key: str, value: str) -> None:
        with self._connect() as con:
            con.execute(
                "INSERT OR REPLACE INTO state (key, value) VALUES (?, ?)",
                (key, value),
            )

    # ── current month ───────────────────────────────────────────────────────

    def get_current_month(self) -> str:
        val = self._get_state("current_month")
        return val or date.today().strftime("%Y-%m")

    def set_current_month(self, month: str) -> None:
        self._set_state("current_month", month)

    # ── formats ─────────────────────────────────────────────────────────────

    def get_format(self, report_type: str) -> list[str]:
        key = f"{report_type}_format"
        val = self._get_state(key)
        if val is not None:
            return json.loads(val)
        return list(self._DEFAULT_FORMATS[report_type])

    def set_format(self, report_type: str, fmt: list[str]) -> None:
        self._set_state(f"{report_type}_format", json.dumps(fmt))

    # ── expense records ─────────────────────────────────────────────────────

    def append_record(self, month: str, category: str, amount: float, title: str) -> None:
        date_str = f"{month}-01"
        with self._connect() as con:
            con.execute(
                "INSERT INTO expenses (month, date_str, category, title, amount) "
                "VALUES (?, ?, ?, ?, ?)",
                (month, date_str, category, title, amount),
            )

    def read_month(self, month: str) -> list[tuple[str, str, str, str]]:
        with self._connect() as con:
            rows = con.execute(
                "SELECT date_str, category, title, CAST(amount AS TEXT) "
                "FROM expenses WHERE month = ?", (month,)
            ).fetchall()
        return [(d, c, t, s) for d, c, t, s in rows]

    def list_months_with_counts(self) -> list[tuple[str, int]]:
        with self._connect() as con:
            rows = con.execute(
                "SELECT month, COUNT(*) FROM expenses GROUP BY month ORDER BY month DESC"
            ).fetchall()
        return [(m, c) for m, c in rows]

    def delete_month(self, month: str) -> None:
        with self._connect() as con:
            con.execute("DELETE FROM expenses WHERE month = ?", (month,))

    def delete_all(self) -> None:
        with self._connect() as con:
            con.execute("DELETE FROM expenses")
            con.execute("DELETE FROM incomes")

    def delete_last_n_records(self, month: str, n: int) -> list:
        if n <= 0:
            return []
        with self._connect() as con:
            rows = con.execute(
                "SELECT id, date_str, category, title, CAST(amount AS TEXT) "
                "FROM expenses WHERE month = ? ORDER BY id DESC LIMIT ?",
                (month, n),
            ).fetchall()
            if not rows:
                return []
            # Return in insertion order (reverse of DESC order)
            deleted = [(d, c, t, s) for _, d, c, t, s in reversed(rows)]
            ids = [r[0] for r in rows]
            placeholders = ",".join("?" for _ in ids)
            con.execute(
                f"DELETE FROM expenses WHERE id IN ({placeholders})", ids
            )
        return deleted

    def delete_expense_records_by_index(self, month: str, indices: set) -> int:
        if not indices:
            return 0
        with self._connect() as con:
            all_ids = [
                r[0] for r in con.execute(
                    "SELECT id FROM expenses WHERE month = ? ORDER BY id",
                    (month,),
                ).fetchall()
            ]
        to_delete = {all_ids[i] for i in indices if i < len(all_ids)}
        if not to_delete:
            return 0
        placeholders = ",".join("?" for _ in to_delete)
        with self._connect() as con:
            con.execute(
                f"DELETE FROM expenses WHERE id IN ({placeholders})",
                sorted(to_delete),
            )
        return len(to_delete)

    # ── income records ──────────────────────────────────────────────────────

    def append_income(self, month: str, amount: float, taxable: bool, name: str) -> None:
        with self._connect() as con:
            con.execute(
                "INSERT INTO incomes (month, amount, taxable, name) "
                "VALUES (?, ?, ?, ?)",
                (month, amount, 1 if taxable else 0, name),
            )

    def read_income(self, month: str) -> list[tuple[str, bool, str]]:
        with self._connect() as con:
            rows = con.execute(
                "SELECT CAST(amount AS TEXT), taxable, name "
                "FROM incomes WHERE month = ?", (month,)
            ).fetchall()
        return [(s, bool(t), n) for s, t, n in rows]

    def list_income_months(self) -> list[str]:
        with self._connect() as con:
            rows = con.execute(
                "SELECT DISTINCT month FROM incomes ORDER BY month DESC"
            ).fetchall()
        return [r[0] for r in rows]

    def delete_income_records_by_index(self, month: str, indices: set) -> int:
        if not indices:
            return 0
        with self._connect() as con:
            all_ids = [
                r[0] for r in con.execute(
                    "SELECT id FROM incomes WHERE month = ? ORDER BY id",
                    (month,),
                ).fetchall()
            ]
        to_delete = {all_ids[i] for i in indices if i < len(all_ids)}
        if not to_delete:
            return 0
        placeholders = ",".join("?" for _ in to_delete)
        with self._connect() as con:
            con.execute(
                f"DELETE FROM incomes WHERE id IN ({placeholders})",
                sorted(to_delete),
            )
        return len(to_delete)

    # ── balances ────────────────────────────────────────────────────────────

    def get_balance_names(self) -> list[str]:
        with self._connect() as con:
            rows = con.execute(
                "SELECT name FROM name_registry WHERE is_current = 1"
            ).fetchall()
        return [r[0] for r in rows]

    def get_historic_names(self) -> list[str]:
        with self._connect() as con:
            rows = con.execute(
                "SELECT DISTINCT name FROM name_registry"
            ).fetchall()
        return [r[0] for r in rows]

    def add_balance_name(self, name: str, currency: str = "RUB") -> None:
        if not _CURRENCY_RE.match(currency):
            raise ValueError(f"Invalid currency code: {currency!r}")
        with self._connect() as con:
            row = con.execute(
                "SELECT is_current FROM name_registry WHERE name = ?", (name,)
            ).fetchone()
            if row is None:
                con.execute(
                    "INSERT INTO name_registry (name, currency, is_current) "
                    "VALUES (?, ?, 1)", (name, currency)
                )
            elif row[0] == 0:
                con.execute(
                    "UPDATE name_registry SET currency = ?, is_current = 1 WHERE name = ?",
                    (currency, name),
                )
            # if already current → no-op

    def remove_balance_name(self, name: str, keep_history: bool) -> None:
        with self._connect() as con:
            row = con.execute(
                "SELECT is_current FROM name_registry WHERE name = ?", (name,)
            ).fetchone()
            if row is None or row[0] == 0:
                return  # not current
            if keep_history:
                con.execute(
                    "UPDATE name_registry SET is_current = 0 WHERE name = ?", (name,)
                )
            else:
                con.execute("DELETE FROM name_registry WHERE name = ?", (name,))
                con.execute(
                    "DELETE FROM balances WHERE name = ?", (name,)
                )

    def set_balance(self, month: str, name: str, amount: float) -> None:
        with self._connect() as con:
            row = con.execute(
                "SELECT is_current FROM name_registry WHERE name = ?", (name,)
            ).fetchone()
            if row is None or row[0] == 0:
                raise ValueError(f"Unknown balance name: {name!r}")
            con.execute(
                "INSERT INTO balances (month, name, amount, currency) "
                "VALUES (?, ?, ?, ?) "
                "ON CONFLICT(month, name) DO UPDATE SET amount = ?",
                (month, name, amount, name, amount),
            )

    def get_balance_month(self, month: str) -> dict[str, float]:
        with self._connect() as con:
            rows = con.execute(
                "SELECT b.name, b.amount "
                "FROM balances b "
                "JOIN name_registry nr ON b.name = nr.name "
                "WHERE b.month = ? AND nr.is_current = 1",
                (month,),
            ).fetchall()
        return {n: a for n, a in rows}

    def list_balance_months(self) -> list[str]:
        with self._connect() as con:
            rows = con.execute(
                "SELECT DISTINCT month FROM balances ORDER BY month DESC"
            ).fetchall()
        return [r[0] for r in rows]

    # ── currencies / FX rates ───────────────────────────────────────────────

    def get_balance_currency(self, name: str) -> str:
        with self._connect() as con:
            row = con.execute(
                "SELECT currency FROM name_registry WHERE name = ?", (name,)
            ).fetchone()
        return row[0] if row else "RUB"

    def set_balance_currency(self, name: str, ccy: str) -> None:
        if not _CURRENCY_RE.match(ccy):
            raise ValueError(f"Invalid currency code: {ccy!r}")
        with self._connect() as con:
            con.execute(
                "UPDATE name_registry SET currency = ? WHERE name = ?", (ccy, name)
            )

    def get_all_currencies(self) -> dict:
        with self._connect() as con:
            rows = con.execute(
                "SELECT name, currency FROM name_registry"
            ).fetchall()
        return {n: c for n, c in rows}

    def get_rate(self, ccy: str, month: str) -> Optional[float]:
        if ccy == "RUB":
            return 1.0
        with self._connect() as con:
            row = con.execute(
                "SELECT amount FROM balances WHERE name = ? AND month = ?",
                (ccy, month),
            ).fetchone()
        if row is None:
            return None
        return row[0]

    def set_rate(self, ccy: str, month: str, value: float) -> None:
        if not _CURRENCY_RE.match(ccy):
            raise ValueError(f"Invalid currency code: {ccy!r}")
        if ccy == "RUB":
            return
        if value <= 0:
            raise ValueError(f"Rate must be positive: {value}")
        # Ensure the currency name exists in registry (as a synthetic name)
        with self._connect() as con:
            con.execute(
                "INSERT OR IGNORE INTO name_registry (name, currency, is_current) "
                "VALUES (?, ?, 0)", (ccy, ccy)
            )
            con.execute(
                "INSERT INTO balances (month, name, amount, currency) "
                "VALUES (?, ?, ?, ?) "
                "ON CONFLICT(month, name) DO UPDATE SET amount = ?",
                (month, ccy, value, ccy, value),
            )

    def get_all_rates(self) -> dict:
        result: dict[str, dict[str, float]] = {}
        with self._connect() as con:
            rows = con.execute(
                "SELECT name, month, amount FROM balances "
                "WHERE name IN (SELECT name FROM name_registry WHERE currency != 'RUB') "
                "AND name != 'RUB'"
            ).fetchall()
        for name, month, amount in rows:
            result.setdefault(name, {})[month] = float(amount)
        return result

    def list_missing_rates(self, month: str) -> list:
        with self._connect() as con:
            rows = con.execute(
                "SELECT DISTINCT b.name, nr.currency "
                "FROM balances b "
                "JOIN name_registry nr ON b.name = nr.name "
                "WHERE b.month = ? AND b.amount IS NOT NULL",
                (month,),
            ).fetchall()
        ccys = {r[1] for r in rows}  # currency, not name
        missing = []
        for ccy in sorted(ccys):
            if ccy == "RUB":
                continue
            if self.get_rate(ccy, month) is None:
                missing.append(ccy)
        return missing
