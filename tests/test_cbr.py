"""Tests for cbr.py — CBR exchange rate fetcher."""
import sys
import os
import pytest

sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))

from cbr import _parse_rate_from_xml, _date_for_month


# ── _date_for_month ──────────────────────────────────────────────────────────

def test_date_for_past_month_returns_last_day():
    # February 2026 has 28 days
    assert _date_for_month("2026-02") == "28/02/2026"


def test_date_for_past_month_december():
    assert _date_for_month("2025-12") == "31/12/2025"


def test_date_for_past_month_leap_year():
    # 2024 is a leap year
    assert _date_for_month("2024-02") == "29/02/2024"


def test_date_for_current_month_returns_today(monkeypatch):
    import datetime
    fake_today = datetime.date(2026, 4, 16)
    monkeypatch.setattr("cbr.date", type("FakeDate", (), {
        "today": staticmethod(lambda: fake_today),
        "fromisoformat": datetime.date.fromisoformat,
    }))
    # April 2026 is the "current" month
    assert _date_for_month("2026-04") == "16/04/2026"


# ── _parse_rate_from_xml ─────────────────────────────────────────────────────

SAMPLE_XML = """<?xml version="1.0" encoding="windows-1251"?>
<ValCurs Date="16.04.2026" name="Foreign Currency Market">
    <Valute ID="R01235">
        <NumCode>840</NumCode>
        <CharCode>USD</CharCode>
        <Nominal>1</Nominal>
        <Name>Доллар США</Name>
        <Value>88,5040</Value>
        <VunitRate>88,504</VunitRate>
    </Valute>
    <Valute ID="R01239">
        <NumCode>978</NumCode>
        <CharCode>EUR</CharCode>
        <Nominal>1</Nominal>
        <Name>Евро</Name>
        <Value>96,2010</Value>
        <VunitRate>96,201</VunitRate>
    </Valute>
    <Valute ID="R01820">
        <NumCode>392</NumCode>
        <CharCode>JPY</CharCode>
        <Nominal>100</Nominal>
        <Name>Японских иен</Name>
        <Value>60,7280</Value>
        <VunitRate>0,60728</VunitRate>
    </Valute>
</ValCurs>"""


def test_parse_usd_rate():
    rate = _parse_rate_from_xml(SAMPLE_XML, "USD")
    assert rate == pytest.approx(88.504, abs=0.001)


def test_parse_eur_rate():
    rate = _parse_rate_from_xml(SAMPLE_XML, "EUR")
    assert rate == pytest.approx(96.201, abs=0.001)


def test_parse_jpy_rate_normalizes_by_nominal():
    rate = _parse_rate_from_xml(SAMPLE_XML, "JPY")
    # 60.728 / 100 = 0.60728
    assert rate == pytest.approx(0.60728, abs=0.00001)


def test_parse_unknown_currency_returns_none():
    rate = _parse_rate_from_xml(SAMPLE_XML, "CHF")
    assert rate is None


def test_parse_malformed_xml_returns_none():
    rate = _parse_rate_from_xml("<broken>", "USD")
    assert rate is None


def test_parse_empty_xml_returns_none():
    rate = _parse_rate_from_xml("", "USD")
    assert rate is None
