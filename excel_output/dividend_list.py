"""Methods for writing dividend data and summaries to excel"""

import xlsxwriter
from xlsxwriter import Workbook

from capital_gain.model import Dividend


def write_dividend_list(dividend_and_tax_list: list[Dividend]):
    """Write a list of dividend and tax to a file"""
    workbook = xlsxwriter.Workbook(
        "Dividend.xlsx", {"default_date_format": "d mmm yyyy"}
    )
    dividend_and_tax_list.sort(key=lambda x: x.transaction_date)
    dividend_list = [x for x in dividend_and_tax_list if x.is_dividend()]
    withholding_list = [x for x in dividend_and_tax_list if x.is_withholding_tax()]
    make_dividend_sheet(workbook, dividend_list, "Dividend List")
    make_dividend_sheet(workbook, withholding_list, "Withholding Tax List")
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
        for column_num, header in enumerate(table_column):
            worksheet.write(0, column_num, header)
        for column_num, column in enumerate(table_column.values()):
            worksheet.write(row_num + 1, column_num, column)
