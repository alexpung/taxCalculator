""" function for displaying data in table format """
import datetime
from typing import List, Tuple, Union

from kivy.metrics import dp

from capital_gain.model import BuyTrade, SellTrade, ShareReorg

from .table_presentation import (
    show_corp_action_in_trade_table,
    show_data_in_trade_table,
)


def convert_table_header(headers: List[str], size: int) -> List[Tuple[str, float]]:
    """convert headers to format taken by column_data in MDDataTable"""
    return [(header, dp(size)) for header in headers]


def get_colored_table_row(
    transaction_list: List[Union[BuyTrade, SellTrade, ShareReorg]],
    report_start_date: datetime.date,
    report_end_date: datetime.date,
) -> List[Tuple]:
    """From the calculated transaction list get colored row of rows for the table"""
    result = []
    for transaction in transaction_list:
        if isinstance(transaction, (BuyTrade, SellTrade)):
            row_tuple = show_data_in_trade_table(transaction)
        elif isinstance(transaction, ShareReorg):
            row_tuple = show_corp_action_in_trade_table(transaction)
        new_tuple = []
        if report_start_date < transaction.transaction_date < report_end_date:
            color_prefix = "[color=#556B2F]"
        else:
            color_prefix = "[color=#8B0000]"
        for cell in row_tuple:
            colored_cell = color_prefix + cell + "[/color]"
            new_tuple.append(colored_cell)
        result.append(tuple(new_tuple))
    return result
