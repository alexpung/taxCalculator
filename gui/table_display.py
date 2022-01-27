""" function for displaying data in table format """
import datetime
from typing import List

from kivy.metrics import dp

from capital_gain.model import Transaction


def convert_table_header(headers: List[str], size: int):
    """convert headers to format taken by column_data in MDDataTable"""
    return [(header, dp(size)) for header in headers]


def get_colored_table_row(
    trades: List[Transaction],
    report_start_date: datetime.date,
    report_end_date: datetime.date,
):
    """From the calculated transaction list get colored row of rows for the table"""
    result = []
    for trade in trades:
        row_tuple = trade.get_table_repr()
        if report_start_date < trade.transaction_date < report_end_date:
            colored_row_tuple = f"[color=#AA4A44]{row_tuple}[/color]"
        else:
            colored_row_tuple = f"[color=#DFFF00]{row_tuple}[/color]"
        result.append(colored_row_tuple)
    return result
