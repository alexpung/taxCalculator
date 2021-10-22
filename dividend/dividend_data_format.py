"""
Collection of excel sheet formatting for writing Pandas Dataframe to excel
"""
from openpyxl.worksheet.worksheet import Worksheet

from excel_format.format import ExcelFormatter


def format_dividend_data(ws: Worksheet) -> None:
    """
    excel formatting for dividend data sheet
    """
    ExcelFormatter.format_cell(ws, 'A', 'DD/MM/YY')
    ExcelFormatter.format_cell(ws, 'F:I', '#,##0.00')
    ExcelFormatter.auto_size_column(ws)
    ExcelFormatter.set_alignment(ws, 'A:D', 'center')


def format_dividend_summary(ws: Worksheet) -> None:
    """
    excel formatting for dividend summary sheet
    """
    ExcelFormatter.auto_size_column(ws)
    ExcelFormatter.set_alignment(ws, 'A', 'center')
    ExcelFormatter.format_cell(ws, 'B:C', '#,##0.00')
