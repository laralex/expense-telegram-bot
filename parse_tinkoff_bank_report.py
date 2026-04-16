"""
parse_tinkoff_bank_report.py — Parse T-Bank "Справка о движении средств" PDF into TSV.

Usage:
    python parse_tinkoff_bank_report.py <input.pdf> [output.tsv]

If output path is omitted, prints to stdout.
"""

from __future__ import annotations

import re
import sys
from dataclasses import dataclass

import pdfplumber


@dataclass
class StatementMeta:
    holder_name: str
    account_number: str
    contract_number: str
    balance: float
    balance_date: str
    period_start: str
    period_end: str


@dataclass
class Transaction:
    operation_datetime: str  # DD.MM.YYYY HH:MM
    writeoff_datetime: str   # DD.MM.YYYY HH:MM
    amount: float
    card_amount: float
    description: str
    card_number: str         # last 4 digits or "—"


# Matches a line that starts a new transaction row:
# two dates (DD.MM.YYYY), then a signed amount with ₽
_TX_START = re.compile(
    r"^(\d{2}\.\d{2}\.\d{4})\s+"   # operation date
    r"(\d{2}\.\d{2}\.\d{4})\s+"    # writeoff date
    r"([+\-][\d\s]+\.\d{2})\s*₽\s+"  # amount in operation currency
    r"([+\-][\d\s]+\.\d{2})\s*₽\s+"  # amount in card currency
    r"(.+?)\s+"                      # description start
    r"(\d{4}|—)\s*$"                 # card number (last 4) or dash
)

# Continuation of the previous transaction: time fields on next line
_TIME_LINE = re.compile(
    r"^(\d{2}:\d{2})\s+(\d{2}:\d{2})\s*(.*?)\s*$"
)

# Footer / summary lines to skip
_FOOTER = re.compile(
    r"^АО «ТБанк»|^БИК\s|^\d+$|^Пополнения:|^Расходы:|^С уважением|^Руководитель"
)

# Table header to skip
_HEADER = re.compile(r"^Дата и время")


def _parse_amount(s: str) -> float:
    """Parse amount string like '-2 154.80' or '+101.40' into float."""
    return float(s.replace(" ", ""))


def parse_meta(text: str) -> StatementMeta:
    """Extract statement metadata from the first page text."""
    holder = ""
    account = ""
    contract = ""
    balance = 0.0
    balance_date = ""
    period_start = ""
    period_end = ""

    for line in text.splitlines():
        if m := re.search(r"Номер лицевого счета:\s*(\S+)", line):
            account = m.group(1)
        elif m := re.search(r"Номер договора:\s*(\S+)", line):
            contract = m.group(1)
        elif m := re.search(
            r"Сумма доступного остатка на (\d{2}\.\d{2}\.\d{4}):\s*([\d\s]+\.\d{2})", line
        ):
            balance_date = m.group(1)
            balance = float(m.group(2).replace(" ", ""))
        elif m := re.search(
            r"период с (\d{2}\.\d{2}\.\d{4}) по (\d{2}\.\d{2}\.\d{4})", line
        ):
            period_start = m.group(1)
            period_end = m.group(2)

    # Holder name is on the line after the reference/date line
    lines = text.splitlines()
    for i, line in enumerate(lines):
        if "Исх. №" in line and i + 1 < len(lines):
            holder = lines[i + 1].strip()
            break

    return StatementMeta(
        holder_name=holder,
        account_number=account,
        contract_number=contract,
        balance=balance,
        balance_date=balance_date,
        period_start=period_start,
        period_end=period_end,
    )


def parse_transactions(pdf_path: str) -> tuple[StatementMeta, list[Transaction]]:
    """Parse all transactions from a T-Bank statement PDF."""
    transactions: list[Transaction] = []
    current: dict | None = None
    meta: StatementMeta | None = None

    with pdfplumber.open(pdf_path) as pdf:
        for page_idx, page in enumerate(pdf.pages):
            text = page.extract_text()
            if not text:
                continue

            if page_idx == 0:
                meta = parse_meta(text)

            for line in text.splitlines():
                # Skip footer/header lines
                if _FOOTER.match(line) or _HEADER.match(line):
                    continue
                if line.startswith("операции") and "списания" in line:
                    continue

                # Try matching a new transaction start
                m = _TX_START.match(line)
                if m:
                    # Flush previous transaction
                    if current:
                        transactions.append(_build_tx(current))

                    current = {
                        "op_date": m.group(1),
                        "op_time": "",
                        "wo_date": m.group(2),
                        "wo_time": "",
                        "amount": _parse_amount(m.group(3)),
                        "card_amount": _parse_amount(m.group(4)),
                        "desc_parts": [m.group(5).strip()],
                        "card": m.group(6),
                    }
                    continue

                # Try matching a time continuation line
                m = _TIME_LINE.match(line)
                if m and current:
                    if not current["op_time"]:
                        current["op_time"] = m.group(1)
                        current["wo_time"] = m.group(2)
                    extra = m.group(3).strip()
                    if extra:
                        current["desc_parts"].append(extra)
                    continue

                # Otherwise it's a description continuation
                if current and line.strip():
                    # Filter out metadata lines that aren't part of transactions
                    stripped = line.strip()
                    if any(
                        stripped.startswith(kw)
                        for kw in [
                            "АКЦИОНЕРНОЕ", "РОССИЯ,", "ТЕЛ.:", "Справка",
                            "Исх.", "Ларионов", "Адрес", "О продукте",
                            "Дата заключения", "Номер договора", "Номер лицевого",
                            "Сумма доступного", "Движение средств",
                        ]
                    ):
                        continue
                    current["desc_parts"].append(stripped)

        # Flush last transaction
        if current:
            transactions.append(_build_tx(current))

    return meta or StatementMeta("", "", "", 0.0, "", "", ""), transactions


def _build_tx(d: dict) -> Transaction:
    op_dt = f"{d['op_date']} {d['op_time']}" if d["op_time"] else d["op_date"]
    wo_dt = f"{d['wo_date']} {d['wo_time']}" if d["wo_time"] else d["wo_date"]
    desc = " ".join(d["desc_parts"])
    return Transaction(
        operation_datetime=op_dt,
        writeoff_datetime=wo_dt,
        amount=d["amount"],
        card_amount=d["card_amount"],
        description=desc,
        card_number=d["card"],
    )


def to_tsv(meta: StatementMeta, transactions: list[Transaction]) -> str:
    """Format transactions as TSV with a metadata comment header."""
    lines: list[str] = []

    # Metadata as comments
    lines.append(f"# Holder: {meta.holder_name}")
    lines.append(f"# Account: {meta.account_number}")
    lines.append(f"# Contract: {meta.contract_number}")
    lines.append(f"# Period: {meta.period_start} - {meta.period_end}")
    lines.append(f"# Balance on {meta.balance_date}: {meta.balance:.2f}")
    lines.append("")

    # Header
    lines.append("\t".join([
        "operation_datetime",
        "writeoff_datetime",
        "amount",
        "card_amount",
        "description",
        "card_number",
    ]))

    # Rows
    for tx in transactions:
        lines.append("\t".join([
            tx.operation_datetime,
            tx.writeoff_datetime,
            f"{tx.amount:.2f}",
            f"{tx.card_amount:.2f}",
            tx.description,
            tx.card_number,
        ]))

    return "\n".join(lines) + "\n"


def main() -> None:
    if len(sys.argv) < 2:
        print(f"Usage: {sys.argv[0]} <input.pdf> [output.tsv]", file=sys.stderr)
        sys.exit(1)

    pdf_path = sys.argv[1]
    out_path = sys.argv[2] if len(sys.argv) > 2 else None

    meta, transactions = parse_transactions(pdf_path)
    tsv = to_tsv(meta, transactions)

    if out_path:
        with open(out_path, "w", encoding="utf-8") as f:
            f.write(tsv)
        print(f"Wrote {len(transactions)} transactions to {out_path}", file=sys.stderr)
    else:
        sys.stdout.write(tsv)


if __name__ == "__main__":
    main()
