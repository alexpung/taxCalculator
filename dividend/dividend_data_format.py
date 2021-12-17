"""
Collection of excel sheet formatting for writing Pandas Dataframe to excel
"""
from openpyxl.worksheet.worksheet import Worksheet

from excel_format.format import ExcelFormatter


def format_dividend_data(sheet: Worksheet) -> None:
    """
    excel formatting for dividend data sheet
    """
    ExcelFormatter.format_cell(sheet, "A", "DD/MM/YY")
    ExcelFormatter.format_cell(sheet, "F:I", "#,##0.00")
    ExcelFormatter.auto_size_column(sheet)
    ExcelFormatter.set_alignment(sheet, "A:D", "center")


def format_dividend_summary(sheet: Worksheet) -> None:
    """
    excel formatting for dividend summary sheet
    """
    ExcelFormatter.auto_size_column(sheet)
    ExcelFormatter.set_alignment(sheet, "A", "center")
    ExcelFormatter.format_cell(sheet, "B:C", "#,##0.00")


def format_interest_data(sheet: Worksheet) -> None:
    """
    excel formatting for interest income data sheet
    """
    ExcelFormatter.auto_size_column(sheet)
    ExcelFormatter.format_cell(sheet, "A", "DD/MM/YY")
    ExcelFormatter.format_cell(sheet, "D", "#,##0.00")
    ExcelFormatter.format_cell(sheet, "G", "#,##0.00")
    ExcelFormatter.set_alignment(sheet, "A", "center")
    ExcelFormatter.set_alignment(sheet, "E", "center")
