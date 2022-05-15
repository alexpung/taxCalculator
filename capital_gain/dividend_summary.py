""" To calculate various dividend summary """
from collections import defaultdict
from dataclasses import dataclass
from decimal import Decimal

from capital_gain.model import Dividend
from const import get_tax_year


@dataclass
class DividendTotal:
    """data class for storing dividend summary data without country and tax year"""

    total_dividend: Decimal
    withholding_tax: Decimal
    net_income: Decimal


@dataclass(frozen=True, eq=True)
class YearAndCountry:
    """data class for storing year and country of dividend"""

    tax_year: int
    country: str


@dataclass
class DividendSummary:
    """data class for storing dividend summary data"""

    year_and_country: YearAndCountry
    dividend_summary: DividendTotal


def get_dividend_summary(dividend_list: list[Dividend]) -> list[DividendSummary]:
    """Return dividend summary data given a list of Dividend and withholding tax"""
    sorted_list = _sort_dividend_list(dividend_list)
    summary_list = []
    for year_and_country, dividend_list in sorted_list.items():
        total = _get_dividend_total(dividend_list)
        summary_list.append(DividendSummary(year_and_country, total))
    return summary_list


def _sort_dividend_list(
    dividend_list: list[Dividend],
) -> defaultdict[YearAndCountry, list[Dividend]]:
    sorted_dividend_list: defaultdict[YearAndCountry, list[Dividend]] = defaultdict(
        list
    )
    for dividend in dividend_list:
        year = get_tax_year(dividend.transaction_date)
        country = dividend.country
        sorted_dividend_list[YearAndCountry(year, country)].append(dividend)
    return sorted_dividend_list


def _get_dividend_total(dividend_list: list[Dividend]) -> DividendTotal:
    """get the sum of value in Sterling regardless of transaction type"""
    total_dividend = sum(
        [
            dividend.value.get_value()
            for dividend in dividend_list
            if dividend.is_dividend()
        ],
        Decimal(0),
    )
    withholding_tax = sum(
        [
            dividend.value.get_value()
            for dividend in dividend_list
            if dividend.is_withholding_tax()
        ],
        Decimal(0),
    )
    net_income = total_dividend - withholding_tax
    return DividendTotal(total_dividend, withholding_tax, net_income)
