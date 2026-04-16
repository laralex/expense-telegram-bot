"""CBR exchange rate fetcher.

Fetches daily FX rates from the Central Bank of Russia XML API.
Rates are expressed as RUB per 1 unit of foreign currency.
"""

import asyncio
import calendar
import urllib.request
import xml.etree.ElementTree as ET
from datetime import date
from typing import Optional


_CBR_URL = "https://www.cbr.ru/scripts/XML_daily.asp"


def _date_for_month(month: str) -> str:
    """Return the CBR query date (DD/MM/YYYY) for a given YYYY-MM month.

    Current or future month -> today's date.
    Past month -> last day of that month.
    """
    year, mon = int(month[:4]), int(month[5:7])
    today = date.today()
    if year > today.year or (year == today.year and mon >= today.month):
        d = today
    else:
        last_day = calendar.monthrange(year, mon)[1]
        d = date(year, mon, last_day)
    return d.strftime("%d/%m/%Y")


def _parse_rate_from_xml(xml_text: str, ccy: str) -> Optional[float]:
    """Extract rate for `ccy` from CBR XML response.

    Returns RUB per 1 unit of `ccy`, or None if not found / parse error.
    """
    if not xml_text:
        return None
    try:
        root = ET.fromstring(xml_text)
    except ET.ParseError:
        return None
    for valute in root.findall("Valute"):
        char_code = valute.findtext("CharCode", "")
        if char_code == ccy:
            value_str = valute.findtext("Value", "")
            nominal_str = valute.findtext("Nominal", "1")
            try:
                value = float(value_str.replace(",", "."))
                nominal = int(nominal_str)
                return value / nominal
            except (ValueError, ZeroDivisionError):
                return None
    return None


def _fetch_rate_sync(ccy: str, month: str) -> Optional[float]:
    """Synchronous CBR rate fetch (called via executor from async code)."""
    if ccy == "RUB":
        return 1.0
    date_str = _date_for_month(month)
    url = "{}?date_req={}".format(_CBR_URL, date_str)
    try:
        req = urllib.request.Request(url)
        with urllib.request.urlopen(req, timeout=10) as resp:
            raw = resp.read()
            text = raw.decode("windows-1251")
            return _parse_rate_from_xml(text, ccy)
    except Exception:
        return None


async def fetch_rate(ccy: str, month: str) -> Optional[float]:
    """Fetch the CBR exchange rate for `ccy` in `month` (YYYY-MM).

    Returns RUB per 1 unit of `ccy`, or None on any error.
    """
    if ccy == "RUB":
        return 1.0
    loop = asyncio.get_event_loop()
    return await loop.run_in_executor(None, _fetch_rate_sync, ccy, month)
