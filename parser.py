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


class UnclearCategoryError(ParseError):
    """Raised when a title is present but no category could be determined."""


class ConflictingCategoryError(ParseError):
    """Raised when the input matches more than one category."""


def load_categories(path) -> list[tuple[str, list[str]]]:
    """Load categories.yaml and return list of (abbrev, keywords) tuples."""
    with open(path, "r", encoding="utf-8") as fh:
        data = yaml.safe_load(fh)
    return [(entry["abbrev"], [str(kw) for kw in entry["keywords"]]) for entry in data]


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


def _match_all_categories(
    tokens: list[str],
    categories: list[tuple[str, list[str]]],
) -> list[tuple[str, str, str]]:
    """
    Collect every category the tokens could belong to.

    Returns a list of (token, abbrev, keyword) triples. For each token an exact
    match wins over a prefix match — the same priority the payment parser
    uses. A token that matches several categories is reported for each of
    them, so the caller can spot a conflict.
    """
    matches: list[tuple[str, str, str]] = []
    for token in tokens:
        token_lower = token.lower()

        exact: list[tuple[str, str, str]] = []
        for abbrev, keywords in categories:
            for kw in keywords:
                if token_lower == kw.lower():
                    exact.append((token, abbrev, kw))
        if exact:
            matches.extend(exact)
            continue

        if len(token) < 3:
            continue
        for abbrev, keywords in categories:
            for kw in keywords:
                if len(kw) < 3:
                    continue
                if token_lower.startswith(kw.lower()) or kw.lower().startswith(token_lower):
                    matches.append((token, abbrev, kw))
    return matches


def parse_income(
    text: str,
    current_month: str,
    categories: list[tuple[str, list[str]]] | None = None,
) -> tuple[float, bool, str, str]:
    """
    Parse an income message: '<sum> <name>' with optional 'T' flag and optional 'YYYY-MM'.

    Returns (amount, taxable, year_month, name).
    taxable=True means 'T' was present — income increases the tax base.
    year_month defaults to current_month when not supplied in the text.

    When categories are supplied the name is checked against them: a name that
    matches two or more different categories is ambiguous and is rejected with
    ConflictingCategoryError. A name matching a single category (or none) is
    accepted as is.
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

    if categories:
        matches = _match_all_categories(tokens, categories)
        if len({abbrev for _token, abbrev, _kw in matches}) > 1:
            raise ConflictingCategoryError(
                _conflicting_category_message(name, matches)
            )

    return amount, taxable, month, name


def _category_labels(categories: list[tuple[str, list[str]]]) -> str:
    """Human-readable list of known categories, e.g. 'F, h, TT, ..., un'."""
    labels = [abbrev if abbrev else "un" for abbrev, _ in categories]
    return ", ".join(labels)


def _conflicting_category_message(
    name: str,
    matches: list[tuple[str, str, str]],
) -> str:
    """Build the error message for a name that matches several categories."""
    details = ", ".join(
        f"{token!r} → {abbrev if abbrev else 'un'}"
        for token, abbrev, _kw in matches
    )
    return (
        f"Conflicting categories in {name!r} — the name matches more than one "
        f"category: {details}. Use a name that doesn't mix category keywords."
    )


def _unclear_category_message(
    title: str,
    amount_token: str,
    categories: list[tuple[str, list[str]]],
    default_category: str | None,
) -> str:
    """Build the error message for a title that carries no category."""
    msg = (
        f"Category is unclear for {title!r} — spell it out, "
        f"e.g. '{amount_token} F {title}'"
    )
    labels = _category_labels(categories)
    if labels:
        msg += f". Known categories: {labels}"
    if default_category:
        msg += f" (or send only the amount to use the default category '{default_category}')"
    return msg


def parse_payment(text: str, categories: list[tuple[str, list[str]]], default_category: str | None = None) -> tuple[str, float, str]:
    """
    Parse a payment message.

    Returns (category_abbrev, amount, title).
    Raises ParseError on invalid input.

    The default category is applied only when the message holds nothing but the
    amount (e.g. '150'). A message that carries a title but no recognisable
    category (e.g. '50 coffee') is rejected with UnclearCategoryError — the
    category is never guessed.
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
        title = " ".join(remaining)
    elif not remaining:
        # Amount only — fall back to the default category.
        if default_category is None:
            raise ParseError(f"No category given in: {text!r}")
        category = default_category
        title = ""
    else:
        # Title without a category — refuse to guess.
        title = " ".join(remaining)
        raise UnclearCategoryError(
            _unclear_category_message(title, amount_token, categories, default_category)
        )

    return category, amount, title