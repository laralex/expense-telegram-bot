#!/usr/bin/env python3
"""
migrate_backup.py — Convert a legacy data/ folder into an SQLite database.

Usage:
    python3 migrate_backup.py <data_folder> [output.db]

The script reads all legacy files (state.json, outcome-YYYY-MM.txt,
income-YYYY-MM.txt, balances.json) from the given directory and writes
a SQLite database compatible with the Storage class.

The output database can then be placed in data/ of a new deployment
and will be automatically used by the bot on startup.
"""

import argparse
import json
import os
import sqlite3
import sys
from pathlib import Path


def create_schema(conn: sqlite3.Connection) -> None:
    """Create all tables and indexes."""
    conn.executescript("""
        CREATE TABLE IF NOT EXISTS state (
            key   TEXT PRIMARY KEY,
            value TEXT NOT NULL
        );

        CREATE TABLE IF NOT EXISTS expenses (
            id        INTEGER PRIMARY KEY AUTOINCREMENT,
            month     TEXT    NOT NULL,
            date_str  TEXT    NOT NULL,
            category  TEXT    NOT NULL,
            title     TEXT    NOT NULL,
            amount    REAL    NOT NULL
        );

        CREATE INDEX IF NOT EXISTS idx_expenses_month
            ON expenses (month);

        CREATE TABLE IF NOT EXISTS incomes (
            id       INTEGER PRIMARY KEY AUTOINCREMENT,
            month    TEXT    NOT NULL,
            amount   REAL    NOT NULL,
            taxable  INTEGER NOT NULL CHECK(taxable IN (0, 1)),
            name     TEXT    NOT NULL
        );

        CREATE INDEX IF NOT EXISTS idx_incomes_month
            ON incomes (month);

        CREATE TABLE IF NOT EXISTS balances (
            month    TEXT NOT NULL,
            name     TEXT NOT NULL,
            amount   REAL,
            currency TEXT NOT NULL DEFAULT 'RUB',
            PRIMARY KEY (month, name)
        );

        CREATE TABLE IF NOT EXISTS name_registry (
            name       TEXT PRIMARY KEY,
            currency   TEXT NOT NULL,
            is_current INTEGER NOT NULL DEFAULT 1
        );
    """)


def migrate_state(conn: sqlite3.Connection, state_data: dict) -> None:
    """Migrate state.json into the state table."""
    for key, value in state_data.items():
        if isinstance(value, (dict, list)):
            conn.execute(
                "INSERT OR IGNORE INTO state (key, value) VALUES (?, ?)",
                (key, json.dumps(value)),
            )
        else:
            conn.execute(
                "INSERT OR IGNORE INTO state (key, value) VALUES (?, ?)",
                (key, str(value)),
            )


def migrate_expenses(conn: sqlite3.Connection, dirpath: Path) -> None:
    """Migrate outcome-YYYY-MM.txt files."""
    for path in sorted(dirpath.glob("outcome-????-??.txt")):
        month = path.stem[len("outcome-"):]
        try:
            text = path.read_text(encoding="utf-8")
        except OSError:
            continue
        for line in text.splitlines():
            line = line.strip()
            if not line:
                continue
            parts = line.split("|", 3)
            if len(parts) != 4:
                continue
            try:
                float(parts[3])
            except ValueError:
                continue  # skip header / corrupt lines
            conn.execute(
                "INSERT INTO expenses (month, date_str, category, title, amount) "
                "VALUES (?, ?, ?, ?, ?)",
                (month, f"{month}-01", parts[1], parts[2], float(parts[3])),
            )


def migrate_incomes(conn: sqlite3.Connection, dirpath: Path) -> None:
    """Migrate income-YYYY-MM.txt files."""
    for path in sorted(dirpath.glob("income-????-??.txt")):
        month = path.stem[len("income-"):]
        try:
            text = path.read_text(encoding="utf-8")
        except OSError:
            continue
        for line in text.splitlines():
            parts = line.strip().split("|", 2)
            if len(parts) == 3:
                try:
                    float(parts[0])
                    taxable = 1 if parts[1] == "1" else 0
                    conn.execute(
                        "INSERT INTO incomes (month, amount, taxable, name) "
                        "VALUES (?, ?, ?, ?)",
                        (month, float(parts[0]), taxable, parts[2]),
                    )
                except ValueError:
                    continue


def migrate_balances(conn: sqlite3.Connection, bdata: dict) -> None:
    """Migrate balances.json into balances and name_registry tables."""
    # Name registry
    for name in bdata.get("current_names", []):
        ccy = bdata.get("currencies", {}).get(name, "RUB")
        conn.execute(
            "INSERT OR IGNORE INTO name_registry (name, currency, is_current) "
            "VALUES (?, ?, 1)", (name, ccy)
        )
    for name in bdata.get("historic_names", []):
        ccy = bdata.get("currencies", {}).get(name, "RUB")
        conn.execute(
            "INSERT OR IGNORE INTO name_registry (name, currency, is_current) "
            "VALUES (?, ?, 0)", (name, ccy)
        )
    # Balance values
    for month, values in bdata.get("months", {}).items():
        for name, amount in values.items():
            ccy = bdata.get("currencies", {}).get(name, "RUB")
            conn.execute(
                "INSERT OR REPLACE INTO balances (month, name, amount, currency) "
                "VALUES (?, ?, ?, ?)", (month, name, amount, ccy)
            )
    # Rates (stored as balances for currency code)
    for ccy, months in bdata.get("rates", {}).items():
        if ccy == "RUB":
            continue
        for month, value in months.items():
            conn.execute(
                "INSERT OR REPLACE INTO balances (month, name, amount, currency) "
                "VALUES (?, ?, ?, ?)", (month, ccy, value, ccy)
            )


def migrate_data_folder(data_dir: str, output_path: str) -> None:
    """Read legacy files from a data/ folder and write an SQLite database."""
    dirpath = Path(data_dir)

    if not dirpath.is_dir():
        print(f"Error: directory not found: {data_dir}", file=sys.stderr)
        sys.exit(1)

    conn = sqlite3.connect(output_path)
    try:
        create_schema(conn)

        # Migrate state.json
        state_file = dirpath / "state.json"
        if state_file.exists():
            try:
                state_data = json.loads(state_file.read_text(encoding="utf-8"))
                migrate_state(conn, state_data)
            except (json.JSONDecodeError, OSError):
                pass

        # Migrate expense and income files
        migrate_expenses(conn, dirpath)
        migrate_incomes(conn, dirpath)

        # Migrate balances.json
        balances_file = dirpath / "balances.json"
        if balances_file.exists():
            try:
                bdata = json.loads(balances_file.read_text(encoding="utf-8"))
                migrate_balances(conn, bdata)
            except (json.JSONDecodeError, OSError):
                pass

        conn.commit()
        print(f"Database written to {output_path}", file=sys.stderr)

        # Print summary
        rows = conn.execute("SELECT COUNT(*) FROM state").fetchone()
        print(f"  state entries: {rows[0]}", file=sys.stderr)
        rows = conn.execute("SELECT COUNT(*) FROM expenses").fetchone()
        print(f"  expense records: {rows[0]}", file=sys.stderr)
        rows = conn.execute("SELECT COUNT(*) FROM incomes").fetchone()
        print(f"  income records: {rows[0]}", file=sys.stderr)
        rows = conn.execute("SELECT COUNT(*) FROM balances").fetchone()
        print(f"  balance entries: {rows[0]}", file=sys.stderr)
        rows = conn.execute("SELECT COUNT(*) FROM name_registry").fetchone()
        print(f"  name registry entries: {rows[0]}", file=sys.stderr)
    finally:
        conn.close()


def main() -> None:
    parser = argparse.ArgumentParser(
        description="Convert a legacy data/ folder into an SQLite database."
    )
    parser.add_argument("data_folder", help="Path to the legacy data/ folder")
    parser.add_argument(
        "output",
        nargs="?",
        default=None,
        help="Output database path (default: data/storage.db)",
    )
    args = parser.parse_args()

    if args.output is None:
        args.output = os.path.join(args.data_folder, "storage.db")

    migrate_data_folder(args.data_folder, args.output)


if __name__ == "__main__":
    main()
