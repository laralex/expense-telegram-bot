"""
storage.py — all file I/O for the expense tracker.

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
"""

import json
import os
import re
from datetime import date
from pathlib import Path
from typing import Optional

_CURRENCY_RE = re.compile(r"^[A-Z]{3}$")


class Storage:
    def __init__(self, data_dir: str = "data/"):
        self._dir = Path(data_dir)
        self._dir.mkdir(parents=True, exist_ok=True)

    # ── state ─────────────────────────────────────────────────────────────────

    def _read_state(self) -> dict:
        """Load state.json or return {} if absent."""
        state_file = self._dir / "state.json"
        if not state_file.exists():
            return {}
        return json.loads(state_file.read_text(encoding="utf-8"))

    def _write_state(self, state: dict) -> None:
        """Atomically write state dict to state.json."""
        state_file = self._dir / "state.json"
        tmp = state_file.with_suffix(".json.tmp")
        tmp.write_text(json.dumps(state), encoding="utf-8")
        tmp.replace(state_file)

    def get_current_month(self) -> str:
        return self._read_state().get("current_month", date.today().strftime("%Y-%m"))

    def set_current_month(self, month: str) -> None:
        state = self._read_state()
        state["current_month"] = month
        self._write_state(state)

    _DEFAULT_FORMATS: dict[str, list[str]] = {
        "expense": ["title", "", "date", "category", "amount"],
        "income":  ["amount", "taxable", "year", "month", "name"],
    }

    def get_format(self, report_type: str) -> list[str]:
        """Return stored format for 'expense' or 'income', or the default."""
        key = f"{report_type}_format"
        return self._read_state().get(key, list(self._DEFAULT_FORMATS[report_type]))

    def set_format(self, report_type: str, fmt: list[str]) -> None:
        """Read-modify-write state.json: update only the '<report_type>_format' key."""
        state = self._read_state()
        state[f"{report_type}_format"] = fmt
        self._write_state(state)

    # ── records ───────────────────────────────────────────────────────────────

    def _month_file(self, month: str) -> Path:
        return self._dir / f"outcome-{month}.txt"

    def append_record(self, month: str, category: str, amount: float, title: str) -> None:
        path = self._month_file(month)
        date_str = f"{month}-01"
        line = f"{date_str}|{category}|{title}|{amount}\n"
        with open(path, "a", encoding="utf-8") as fh:
            fh.write(line)

    def read_month(self, month: str) -> list[tuple[str, str, str, str]]:
        path = self._month_file(month)
        if not path.exists():
            return []
        records = []
        for line in path.read_text(encoding="utf-8").splitlines():
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
            records.append(tuple(parts))
        return records

    def list_months_with_counts(self) -> list[tuple[str, int]]:
        result = []
        for path in sorted(self._dir.glob("outcome-????-??.txt"), reverse=True):
            month = path.stem[len("outcome-"):]
            count = len(self.read_month(month))
            result.append((month, count))
        return result

    def delete_last_n_records(self, month: str, n: int) -> list:
        """Remove the last n records from month's file. Returns the deleted records."""
        records = self.read_month(month)
        if n <= 0 or not records:
            return []
        n = min(n, len(records))
        keep, deleted = records[:-n], records[-n:]
        path = self._month_file(month)
        if keep:
            lines = [f"{d}|{c}|{t}|{s}\n" for d, c, t, s in keep]
            tmp = path.with_suffix(".txt.tmp")
            tmp.write_text("".join(lines), encoding="utf-8")
            tmp.replace(path)
        else:
            path.unlink(missing_ok=True)
        return deleted

    def delete_expense_records_by_index(self, month: str, indices: set) -> int:
        """Delete expense records at the given indices. Returns count deleted."""
        if not indices:
            return 0
        records = self.read_month(month)
        keep = [r for i, r in enumerate(records) if i not in indices]
        deleted_count = len(records) - len(keep)
        if deleted_count == 0:
            return 0
        path = self._month_file(month)
        if keep:
            lines = [f"{d}|{c}|{t}|{s}\n" for d, c, t, s in keep]
            tmp = path.with_suffix(".txt.tmp")
            tmp.write_text("".join(lines), encoding="utf-8")
            tmp.replace(path)
        else:
            path.unlink(missing_ok=True)
        return deleted_count

    def delete_income_records_by_index(self, month: str, indices: set) -> int:
        """Delete income records at the given indices. Returns count deleted.

        Re-reads raw file lines to preserve the original '0'/'1' taxable string
        rather than re-encoding from the parsed bool in read_income() tuples.
        """
        if not indices:
            return 0
        path = self._income_file(month)
        if not path.exists():
            return 0
        # Single pass: validate and collect parseable lines (mirrors read_income logic)
        valid_lines = []
        for line in path.read_text(encoding="utf-8").splitlines():
            parts = line.strip().split("|", 2)
            if len(parts) == 3:
                try:
                    float(parts[0])
                    valid_lines.append(line.strip())
                except ValueError:
                    continue
        keep = [line for i, line in enumerate(valid_lines) if i not in indices]
        deleted_count = len(valid_lines) - len(keep)
        if deleted_count == 0:
            return 0
        if keep:
            tmp = path.with_suffix(".txt.tmp")
            lines = [f"{line}\n" for line in keep]
            tmp.write_text("".join(lines), encoding="utf-8")
            tmp.replace(path)
        else:
            path.unlink(missing_ok=True)
        return deleted_count

    def delete_month(self, month: str) -> None:
        path = self._month_file(month)
        if path.exists():
            path.unlink()

    def delete_all(self) -> None:
        for path in self._dir.glob("outcome-????-??.txt"):
            path.unlink()

    # ── income ────────────────────────────────────────────────────────────────

    def _income_file(self, month: str) -> Path:
        return self._dir / f"income-{month}.txt"

    def append_income(self, month: str, amount: float, taxable: bool, name: str) -> None:
        path = self._income_file(month)
        line = f"{amount}|{'1' if taxable else '0'}|{name}\n"
        with open(path, "a", encoding="utf-8") as fh:
            fh.write(line)

    def read_income(self, month: str) -> list[tuple[str, bool, str]]:
        path = self._income_file(month)
        if not path.exists():
            return []
        records = []
        for line in path.read_text(encoding="utf-8").splitlines():
            line = line.strip()
            if not line:
                continue
            parts = line.split("|", 2)
            if len(parts) != 3:
                continue
            amount_str, taxable_str, name = parts
            try:
                float(amount_str)
            except ValueError:
                continue  # skip header / corrupt lines
            records.append((amount_str, taxable_str == "1", name))
        return records

    def list_income_months(self) -> list[str]:
        return sorted(
            [path.stem[7:] for path in self._dir.glob("income-????-??.txt")],
            reverse=True,
        )

    # ── balances ──────────────────────────────────────────────────────────────

    _BALANCES_DEFAULT: dict = {
        "current_names": [],
        "historic_names": [],
        "months": {},
        "currencies": {},
        "rates": {},
    }

    def _read_balances(self) -> dict:
        """Load balances.json; return default structure if absent. Migrates legacy schema."""
        path = self._dir / "balances.json"
        if not path.exists():
            return {k: list(v) if isinstance(v, list) else dict(v)
                    for k, v in self._BALANCES_DEFAULT.items()}
        data = json.loads(path.read_text(encoding="utf-8"))
        result = {k: list(v) if isinstance(v, list) else dict(v)
                  for k, v in self._BALANCES_DEFAULT.items()}
        result.update(data)
        # Migration: ensure every known name has a currency entry (default RUB).
        currencies = result.setdefault("currencies", {})
        for name in list(result.get("historic_names", [])) + list(result.get("current_names", [])):
            currencies.setdefault(name, "RUB")
        result.setdefault("rates", {})
        return result

    def _write_balances(self, data: dict) -> None:
        """Atomically write balances dict."""
        path = self._dir / "balances.json"
        tmp = path.with_suffix(".json.tmp")
        tmp.write_text(json.dumps(data), encoding="utf-8")
        tmp.replace(path)

    def get_balance_names(self) -> list[str]:
        """Return active balance names (current_names)."""
        return self._read_balances()["current_names"]

    def get_historic_names(self) -> list[str]:
        """Return all balance names ever recorded (historic_names)."""
        return self._read_balances()["historic_names"]

    def add_balance_name(self, name: str, currency: str = "RUB") -> None:
        """Add name to current_names (and historic_names if new). No-op if already current."""
        if not _CURRENCY_RE.match(currency):
            raise ValueError(f"Invalid currency code: {currency!r}")
        data = self._read_balances()
        if name in data["current_names"]:
            return
        data["current_names"].append(name)
        if name not in data["historic_names"]:
            data["historic_names"].append(name)
        data["currencies"].setdefault(name, currency)
        self._write_balances(data)

    def remove_balance_name(self, name: str, keep_history: bool) -> None:
        """Remove name from current_names. If keep_history=False, also wipes historic and monthly data."""
        data = self._read_balances()
        if name not in data["current_names"]:
            return
        data["current_names"].remove(name)
        if not keep_history:
            if name in data["historic_names"]:
                data["historic_names"].remove(name)
            data.get("currencies", {}).pop(name, None)
            for month in list(data["months"].keys()):
                data["months"][month].pop(name, None)
                if not data["months"][month]:
                    del data["months"][month]
        self._write_balances(data)

    def set_balance(self, month: str, name: str, amount: float) -> None:
        """Upsert months[month][name]. Raises ValueError if name not in current_names."""
        data = self._read_balances()
        if name not in data["current_names"]:
            raise ValueError(f"Unknown balance name: {name!r}")
        data["months"].setdefault(month, {})[name] = amount
        self._write_balances(data)

    def get_balance_month(self, month: str) -> dict[str, float]:
        """Return {name: amount} for the given month (empty dict if absent)."""
        return dict(self._read_balances()["months"].get(month, {}))

    def list_balance_months(self) -> list[str]:
        """All months with any balance data, sorted descending."""
        return sorted(self._read_balances()["months"].keys(), reverse=True)

    # ── currencies / FX rates ────────────────────────────────────────────────

    def get_balance_currency(self, name: str) -> str:
        """Return the currency code stored for name (default 'RUB')."""
        return self._read_balances()["currencies"].get(name, "RUB")

    def set_balance_currency(self, name: str, ccy: str) -> None:
        """Set currency for an existing balance name. Validates code."""
        if not _CURRENCY_RE.match(ccy):
            raise ValueError(f"Invalid currency code: {ccy!r}")
        data = self._read_balances()
        data["currencies"][name] = ccy
        self._write_balances(data)

    def get_all_currencies(self) -> dict:
        """Return a copy of the name → currency map."""
        return dict(self._read_balances()["currencies"])

    def get_rate(self, ccy: str, month: str) -> Optional[float]:
        """Return stored FX rate. RUB always returns 1.0. None if missing."""
        if ccy == "RUB":
            return 1.0
        return self._read_balances()["rates"].get(ccy, {}).get(month)

    def set_rate(self, ccy: str, month: str, value: float) -> None:
        """Store FX rate for ccy in month. Validates code and positive float."""
        if not _CURRENCY_RE.match(ccy):
            raise ValueError(f"Invalid currency code: {ccy!r}")
        if ccy == "RUB":
            return  # RUB is implicit
        if value <= 0:
            raise ValueError(f"Rate must be positive: {value}")
        data = self._read_balances()
        data["rates"].setdefault(ccy, {})[month] = float(value)
        self._write_balances(data)

    def get_all_rates(self) -> dict:
        """Return a deep copy of the rates dict."""
        return {ccy: dict(months) for ccy, months in self._read_balances()["rates"].items()}

    def list_missing_rates(self, month: str) -> list:
        """Currencies that appear in balances for `month` with no stored rate."""
        data = self._read_balances()
        month_values = data["months"].get(month, {})
        missing = []
        for name in month_values:
            ccy = data["currencies"].get(name, "RUB")
            if ccy == "RUB":
                continue
            if month not in data["rates"].get(ccy, {}):
                if ccy not in missing:
                    missing.append(ccy)
        return missing
