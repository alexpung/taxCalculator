"""Utility functions to be reused"""
from typing import Any, Iterable

from xlsxwriter import Workbook


def make_table(
    workbook: Workbook, sheet_name: str, data_rows: Iterable[dict[str, Any]]
):
    """Create a new worksheet with a dictionary with
    keys=the table header and values=table content"""
    worksheet = workbook.add_worksheet(sheet_name)
    header_written = False
    for row_num, row in enumerate(data_rows):
        if not header_written:
            worksheet.write_row(0, 0, row.keys())
            header_written = True
        worksheet.write_row(row_num + 1, 0, row.values())
