"""Methods for writing dividend data and summaries to excel"""


import xlsxwriter
from xlsxwriter import Workbook

from capital_gain.dividend_summary import DividendSummary
from capital_gain.model import Dividend


def write_dividend_list(
    dividend_and_tax_list: list[Dividend], summaries: list[DividendSummary]
):
    """Write a list of dividend and tax to a file"""
    workbook = xlsxwriter.Workbook(
        "Dividend.xlsx", {"default_date_format": "d mmm yyyy"}
    )
    dividend_and_tax_list.sort(key=lambda x: x.transaction_date)
    dividend_list = [x for x in dividend_and_tax_list if x.is_dividend()]
    withholding_list = [x for x in dividend_and_tax_list if x.is_withholding_tax()]
    make_dividend_sheet(workbook, dividend_list, "Dividend List")
    make_dividend_sheet(workbook, withholding_list, "Withholding Tax List")
    make_dividend_summary_sheet(workbook, summaries)
    workbook.close()


def make_dividend_sheet(
    workbook: Workbook, transaction_list: list[Dividend], sheet_name: str
):
    """Set up table and write dividend or withholding tax data"""
    worksheet = workbook.add_worksheet(sheet_name)
    for row_num, dividend in enumerate(transaction_list):
        table_column = {
            "Date": dividend.transaction_date,
            "Ticker": dividend.ticker,
            "Description": dividend.description,
            "Currency": dividend.value.currency.value,
            "Value in local currency": dividend.value.value,
            "Value in Sterling": dividend.value.get_value(),
            "Exchange rate": dividend.value.exchange_rate,
        }
        worksheet.write_row(0, 0, table_column)
        worksheet.write_row(row_num + 1, 0, table_column.values())


def make_dividend_summary_sheet(workbook: Workbook, summaries: list[DividendSummary]):
    """Set up table and write dividend summary data"""
    worksheet = workbook.add_worksheet("Dividend Summary")
    for row_num, dividend_summary in enumerate(summaries):
        table_column = {
            "Tax Year": dividend_summary.year_and_country.tax_year,
            "Country": dividend_summary.year_and_country.country,
            "Gross Dividend": dividend_summary.dividend_summary.total_dividend,
            "Withholding Tax Paid": dividend_summary.dividend_summary.withholding_tax,
            "Net Dividend": dividend_summary.dividend_summary.net_income,
        }
        worksheet.write_row(0, 0, table_column)
        worksheet.write_row(row_num + 1, 0, table_column.values())
