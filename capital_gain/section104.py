""" for handling section 104 and unmatched short shares """
from collections import defaultdict
from decimal import Decimal
from typing import DefaultDict, List

from capital_gain.model import Section104, Trade


def show_section104_and_short(trades: List[Trade], section104: Section104):
    """return text representation for section 104 holding and unmatched short sales"""
    output_text = "Section 104 holding:\n"
    for symbol, section104_value in section104.section104_list.items():
        output_text += (
            f"Symbol: {symbol}\t"
            f"quantity: {section104_value.quantity}\t"
            f"total cost: {section104_value.cost:.2f}\n"
        )
    output_text += "\n"
    short_list = [trade for trade in trades if trade.get_unmatched_share()]
    if short_list:
        grouped_short_list: DefaultDict[str, Decimal] = defaultdict(Decimal)
        for short_holding in short_list:
            grouped_short_list[
                short_holding.ticker
            ] += short_holding.get_unmatched_share()
        output_text += "Short holding:\n"
        for ticker, quantity in grouped_short_list.items():
            output_text += f"Symbol: {ticker}\tquantity: {quantity}\n"
        output_text += "\n"
    return output_text
