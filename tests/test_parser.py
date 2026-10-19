"""Tests for parser.py — all tests supply in-memory categories, no file I/O."""

import pytest
from parser import ParseError, UnclearCategoryError, parse_payment

# Minimal category list mirroring categories.yaml
CATS = [
    ("F", ["F", "food"]),
    ("h", ["h", "home", "medicine", "hm"]),
    ("TT", ["TT", "transport", "transportation"]),
    ("cloth", ["cloth", "clothes"]),
    ("fun", ["fun", "hangout", "hanging"]),
    ("r", ["r", "rent", "facilities"]),
    ("p", ["p", "periodic", "subscription"]),
    ("travel", ["travel"]),
    ("rel", ["rel", "relationship"]),
]


# ── happy paths ──────────────────────────────────────────────────────────────

def test_number_only_defaults_to_food():
    cat, amt, title = parse_payment("150", CATS, default_category="F")
    assert cat == "F"
    assert amt == 150.0
    assert title == ""


def test_category_before_amount():
    cat, amt, title = parse_payment("food 50", CATS)
    assert cat == "F"
    assert amt == 50.0
    assert title == ""


def test_category_after_amount():
    cat, amt, title = parse_payment("50 food", CATS)
    assert cat == "F"
    assert amt == 50.0
    assert title == ""


def test_category_and_title():
    cat, amt, title = parse_payment("TT 80 Taxi", CATS)
    assert cat == "TT"
    assert amt == 80.0
    assert title == "Taxi"


def test_amount_category_title_uses_explicit_category():
    cat, amt, title = parse_payment("50 F test", CATS, default_category="F")
    assert cat == "F"
    assert amt == 50.0
    assert title == "test"


def test_category_after_title():
    """The category may come after the title: '50 test F'."""
    cat, amt, title = parse_payment("50 test F", CATS, default_category="F")
    assert cat == "F"
    assert amt == 50.0
    assert title == "test"


def test_category_after_title_using_keyword():
    cat, amt, title = parse_payment("50 test food", CATS, default_category="F")
    assert cat == "F"
    assert title == "test"


def test_category_after_title_before_amount():
    cat, amt, title = parse_payment("test F 50", CATS, default_category="F")
    assert cat == "F"
    assert amt == 50.0
    assert title == "test"


def test_amount_only_uses_default_category():
    """No title, no category — the default category applies."""
    cat, amt, title = parse_payment("50", CATS, default_category="F")
    assert cat == "F"
    assert amt == 50.0
    assert title == ""


def test_title_before_and_after_amount():
    cat, amt, title = parse_payment("Vitamins 45 medicine", CATS)
    assert cat == "h"
    assert amt == 45.0
    assert title == "Vitamins"


def test_amount_between_category_and_title():
    cat, amt, title = parse_payment("rent 1200 April", CATS)
    assert cat == "r"
    assert amt == 1200.0
    assert title == "April"


def test_two_pass_fun_not_food():
    """'fun' must resolve to hanging-out (exact match) not food ('f' prefix)."""
    cat, amt, title = parse_payment("fun 30", CATS)
    assert cat == "fun"


def test_two_pass_hanging():
    cat, amt, title = parse_payment("hangout 60 dinner", CATS)
    assert cat == "fun"
    assert title == "dinner"


def test_exact_single_char_r():
    cat, amt, title = parse_payment("r 1200", CATS)
    assert cat == "r"
    assert amt == 1200.0


def test_exact_single_char_p():
    cat, amt, title = parse_payment("p 9.99 Netflix", CATS)
    assert cat == "p"
    assert amt == 9.99
    assert title == "Netflix"


def test_prefix_match_transport():
    """'trans' is ≥3 chars, prefix of 'transport' → TT via Pass 2."""
    cat, amt, title = parse_payment("trans 20", CATS)
    assert cat == "TT"
    assert amt == 20.0


def test_short_unknown_token_is_rejected():
    """'ro' is 2 chars — Pass 2 skips it, and a title without a category is denied."""
    with pytest.raises(UnclearCategoryError):
        parse_payment("ro 150", CATS, default_category="F")


def test_unknown_token_is_rejected():
    """A title without a category must not silently fall back to the default."""
    with pytest.raises(UnclearCategoryError):
        parse_payment("xyz 99", CATS, default_category="F")


def test_title_without_category_is_rejected():
    """'50 test' — category unclear, the default category must not be inferred."""
    with pytest.raises(UnclearCategoryError):
        parse_payment("50 test", CATS, default_category="F")


def test_title_without_category_error_message():
    """The error must explain how to fix the input."""
    with pytest.raises(UnclearCategoryError) as exc:
        parse_payment("50 test", CATS, default_category="F")
    msg = str(exc.value)
    assert "50 F test" in msg
    assert "F" in msg


def test_unclear_category_is_a_parse_error():
    with pytest.raises(ParseError):
        parse_payment("50 test", CATS, default_category="F")


def test_decimal_comma():
    cat, amt, title = parse_payment("1,500", CATS, default_category="F")
    assert amt == 1500.0


def test_decimal_dot():
    cat, amt, title = parse_payment("99.99", CATS, default_category="F")
    assert amt == 99.99


def test_multiple_numbers_first_wins():
    """Second numeric token becomes a title word."""
    cat, amt, title = parse_payment("50 100 food", CATS)
    assert amt == 50.0
    assert "100" in title


def test_title_with_multiple_words():
    cat, amt, title = parse_payment("home 45 Vitamins daily", CATS)
    assert cat == "h"
    assert amt == 45.0
    assert title == "Vitamins daily"


# ── error cases ──────────────────────────────────────────────────────────────

def test_empty_string_raises():
    with pytest.raises(ParseError):
        parse_payment("", CATS)


def test_whitespace_only_raises():
    with pytest.raises(ParseError):
        parse_payment("   ", CATS)


def test_no_number_raises():
    with pytest.raises(ParseError):
        parse_payment("food vitamins", CATS)


def test_zero_amount_raises():
    with pytest.raises(ParseError):
        parse_payment("0", CATS)


def test_negative_amount_raises():
    with pytest.raises(ParseError):
        parse_payment("-50", CATS)


def test_amount_only_without_default_raises():
    with pytest.raises(ParseError):
        parse_payment("50", CATS)