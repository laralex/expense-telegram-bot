"""
parser.py — pure parsing logic, no I/O.

Public API:
    load_categories(path) -> list[tuple[str, list[str]]]
    parse_payment(text, categories) -> tuple[str, float, str]
    parse_income(text, current_month) -> tuple[float, bool, str, str]

Raises ParseError on invalid input.
"""

from __future__ import annotations

import re
from pathlib import Path
import yaml


class ParseError(ValueError):
    pass


def load_categories(path) -> list[tuple[str, list[str]]]:
    """Load categories.yaml and return list of (abbrev, keywords) tuples."""
    with open(path, "r", encoding="utf-8") as fh:
        data = yaml.safe_load(fh)
    return [(entry["abbrev"], [kw for kw in entry["keywords"]]) for entry in data]


def _try_float(token: str) -> float | None:
    """Return float if token (comma-stripped) is a valid positive number, else None."""
    try:
        value = float(token.replace(",", ""))
        return value
    except ValueError:
        return None


def _match_category(tokens: list[str], categories: list[tuple[str, list[str]]]) -> tuple[str, str | None]:
    """
    Two-pass category match over remaining tokens.

    Pass 1 — exact (case-insensitive) across all categories first.
    Pass 2 — prefix match (both sides, ≥3 chars) across all categories.

    Returns (matched_token, abbrev) or (None, None) if no match.
    """
    # Pass 1: exact match
    for token in tokens:
        token_lower = token.lower()
        for abbrev, keywords in categories:
            for kw in keywords:
                if token_lower == kw.lower():
                    return token, abbrev

    # Pass 2: prefix match — token and keyword must both be ≥ 3 chars
    for token in tokens:
        if len(token) < 3:
            continue
        token_lower = token.lower()
        for abbrev, keywords in categories:
            for kw in keywords:
                if len(kw) < 3:
                    continue
                if token_lower.startswith(kw.lower()) or kw.lower().startswith(token_lower):
                    return token, abbrev

    return None, None


def parse_income(text: str, current_month: str) -> tuple[float, bool, str, str]:
    """
    Parse an income message: '<sum> <name>' with optional 'T' flag and optional 'YYYY-MM'.

    Returns (amount, taxable, year_month, name).
    taxable=True means 'T' was present — income increases the tax base.
    year_month defaults to current_month when not supplied in the text.
    """
    if not text or not text.strip():
        raise ParseError("Empty input")

    tokens = text.split()

    # Extract YYYY-MM if present
    month = current_month
    for i, token in enumerate(tokens):
        if re.match(r"^\d{4}-\d{2}$", token):
            month = token
            tokens = tokens[:i] + tokens[i + 1:]
            break

    # Extract 'T' flag (exact uppercase token)
    taxable = "T" in tokens
    if taxable:
        tokens = [t for t in tokens if t != "T"]

    # Find first numeric token as amount
    amount_token = None
    amount = None
    for token in tokens:
        value = _try_float(token)
        if value is not None:
            amount_token = token
            amount = value
            break

    if amount_token is None:
        raise ParseError(f"No numeric amount in: {text!r}")
    if amount <= 0:
        raise ParseError(f"Amount must be positive, got: {amount}")

    tokens.remove(amount_token)
    name = " ".join(tokens)
    return amount, taxable, month, name


def parse_payment(text: str, categories: list[tuple[str, list[str]]]) -> tuple[str, float, str]:
    """
    Parse a payment message.

    Returns (category_abbrev, amount, title).
    Raises ParseError on invalid input.
    """
    if not text or not text.strip():
        raise ParseError("Empty input")

    tokens = text.split()

    # Find first numeric token
    amount_token = None
    amount = None
    for token in tokens:
        value = _try_float(token)
        if value is not None:
            amount_token = token
            amount = value
            break

    if amount_token is None:
        raise ParseError(f"No numeric amount found in: {text!r}")
    if amount <= 0:
        raise ParseError(f"Amount must be positive, got: {amount}")

    # Remaining tokens (excluding the amount token, first occurrence only)
    remaining = list(tokens)
    remaining.remove(amount_token)

    # Match category
    matched_token, abbrev = _match_category(remaining, categories)

    if matched_token is not None:
        remaining.remove(matched_token)
        category = abbrev
    else:
        category = "F"  # hardcoded default: food

    title = " ".join(remaining)
    return category, amount, title
