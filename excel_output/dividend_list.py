"""Methods for writing dividend data and summaries to excel"""
from typing import Any

import xlsxwriter

from capital_gain.dividend_summary import DividendSummary
from capital_gain.model import Dividend
from excel_output.utility import make_table


def write_dividend_list(
    dividend_and_tax_list: list[Dividend], summaries: list[DividendSummary]
):
    """Write a list of dividend and tax to a file"""
    workbook = xlsxwriter.Workbook(
        "Dividend.xlsx", {"default_date_format": "d mmm yyyy"}
    )
    dividend_and_tax_list.sort(key=lambda x: x.transaction_date)
    summaries.sort(key=lambda x: x.year_and_country.tax_year)
    dividend_list = [x for x in dividend_and_tax_list if x.is_dividend()]
    withholding_list = [x for x in dividend_and_tax_list if x.is_withholding_tax()]
    make_table(workbook, "Dividend List", map(set_dividend_data, dividend_list))
    make_table(
        workbook, "Withholding Tax List", map(set_dividend_data, withholding_list)
    )
    make_table(workbook, "Dividend Summary", map(set_dividend_summary, summaries))
    workbook.close()


def set_dividend_data(dividend_entry: Dividend) -> dict[str, Any]:
    """Heading for the dividend data table and the content"""
    return {
        "Date": dividend_entry.transaction_date,
        "Ticker": dividend_entry.ticker,
        "Description": dividend_entry.description,
        "Currency": dividend_entry.value.currency.value,
        "Value in local currency": dividend_entry.value.value,
        "Value in Sterling": dividend_entry.value.get_value(),
        "Exchange rate": dividend_entry.value.exchange_rate,
    }


def set_dividend_summary(dividend_summary: DividendSummary):
    """Heading for the dividend summary table and the content"""
    return {
        "Tax Year": dividend_summary.year_and_country.tax_year,
        "Country": dividend_summary.year_and_country.country,
        "Gross Dividend": dividend_summary.dividend_summary.total_dividend,
        "Withholding Tax Paid": dividend_summary.dividend_summary.withholding_tax,
        "Net Dividend": dividend_summary.dividend_summary.net_income,
    }
