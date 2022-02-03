""" for handling section 104 and unmatched short shares """
from collections import defaultdict
from decimal import Decimal
from typing import DefaultDict, List

from capital_gain.model import Section104, Trade


def show_section104_and_short(trades: List[Trade], section104_list: List[Section104]):
    """return text representation for section 104 holding and unmatched short sales"""
    output_text = "Section 104 holding:\n"
    for section104 in section104_list:
        output_text += (
            f"Symbol: {section104.ticker}\t"
            f"quantity: {section104.quantity}\t"
            f"total cost: {section104.cost:.2f}\n"
        )
    output_text += "\n"
    short_list = [trade for trade in trades if trade.match_status.unmatched]
    if short_list:
        grouped_short_list: DefaultDict[str, Decimal] = defaultdict(Decimal)
        for short_holding in short_list:
            grouped_short_list[
                short_holding.ticker
            ] += short_holding.match_status.unmatched
        output_text += "Short holding:\n"
        for ticker, quantity in grouped_short_list.items():
            output_text += f"Symbol: {ticker}\tquantity: {quantity}\n"
        output_text += "\n"
    return output_text
