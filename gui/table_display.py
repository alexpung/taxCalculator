""" function for displaying data in table format """
import datetime
from typing import List, Tuple

from kivy.metrics import dp

from capital_gain.model import Transaction


def convert_table_header(headers: List[str], size: int) -> List[Tuple[str, float]]:
    """convert headers to format taken by column_data in MDDataTable"""
    return [(header, dp(size)) for header in headers]


def get_colored_table_row(
    trades: List[Transaction],
    report_start_date: datetime.date,
    report_end_date: datetime.date,
) -> List[Tuple]:
    """From the calculated transaction list get colored row of rows for the table"""
    result = []
    for trade in trades:
        row_tuple = trade.get_table_repr()
        new_tuple = []
        if report_start_date < trade.transaction_date < report_end_date:
            color_prefix = "[color=#556B2F]"
        else:
            color_prefix = "[color=#8B0000]"
        for cell in row_tuple:
            colored_cell = color_prefix + cell + "[/color]"
            new_tuple.append(colored_cell)
        result.append(tuple(new_tuple))
    return result
