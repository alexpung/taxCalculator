""" Strings representation of the comment section in transactions """
from __future__ import annotations

import datetime
from decimal import Decimal
from fractions import Fraction
from typing import Union


def add_to_section104(
    qty: Decimal, cost: Decimal, new_quantity: Decimal, new_cost: Decimal
) -> str:
    """Comment when adding shares to the Section 104 pool"""
    return (
        f"{qty} share(s) added to Section104 pool "
        f"with allowable cost {cost:.2f}.\n"
        f"New total number of share(s) for section 104 "
        f"is {new_quantity}.\n"
        f"New total allowable cost is {new_cost:.2f}\n\n"
    )


def remove_from_section104(
    qty: Decimal, cost: Decimal, new_quantity: Decimal, new_cost: Decimal
) -> str:
    """Comment when removing shares to the Section 104 pool"""
    return (
        f"{qty} share(s) removed from Section104 pool "
        f"with allowable cost £{cost:.2f}.\n"
        f"New total number of share(s) for section 104 "
        f"is {new_quantity}.\n"
        f"New total allowable cost is £{new_cost:.2f}\n\n"
    )


def capital_gain_calc(
    transaction_id: Union[None, int],
    qty: Decimal,
    proceeds: Decimal,
    buy_cost: Decimal,
    trade_cost_buy: Decimal = Decimal(0),
    trade_cost_sell: Decimal = Decimal(0),
) -> str:
    """Comments to show capital gain calculation
    transaction_id: pass None if it is a section104 match
    """
    if transaction_id is None:
        matching_comment = f"Matched section 104 holding with quantity {qty}.\n"
    else:
        matching_comment = (
            f"Matched with transaction id {transaction_id} with quantity {qty}.\n"
        )
    buy_cost_comment = (
        f"Allowable dealing cost for buying the matched "
        f"portion is {trade_cost_buy:.2f}\n"
        if trade_cost_buy
        else ""
    )
    sell_cost_comment = (
        f"Allowable dealing cost for disposing the matched "
        f"portion is {trade_cost_sell:.2f}\n"
        if trade_cost_sell
        else ""
    )
    calculation = f"£{proceeds-buy_cost:.2f}"
    if trade_cost_buy:
        calculation += f" - £{trade_cost_buy:.2f}"
    if trade_cost_sell:
        calculation += f" - £{trade_cost_sell:.2f}"
    # skip repeating result if there is no calculation
    result = (
        f"= £{proceeds-buy_cost- trade_cost_buy - trade_cost_sell:.2f}"
        if trade_cost_buy or trade_cost_sell
        else ""
    )
    return (
        f"{matching_comment}"
        f"Gross proceeds is £{proceeds:.2f}.\n"
        f"Cost of buying is £{buy_cost:.2f}\n"
        + buy_cost_comment
        + sell_cost_comment
        + f"Chargeable Capital gain (loss) is {calculation}\n"
        f"{result}\n\n"
    )


def unmatched_shares(share: Decimal) -> str:
    """Comment for unmatched short sale"""
    return f"Sold shares not yet matched (short sale): {share:.2f}\n"


def share_reorg_to_section104(
    ticker: str,
    transaction_date: datetime.date,
    ratio: Fraction,
    old_qty: Decimal,
    new_qty: Decimal,
):
    """Comment on changing section 104 pool due to share split/merge"""
    return (
        f"Share {ticker} split/merge at date {transaction_date} with ratio "
        f"{ratio.denominator} to {ratio.numerator}.\n"
        f"Old quantity of Section 104 is {old_qty}\n"
        f"New quantity is now "
        f"{new_qty}\n"
    )


def share_adjustment(ratio: Fraction, to_match_sell: Decimal, to_match_buy: Decimal):
    """Comment when a share split occurs during bed and breakfast matching"""
    return (
        f"Acquisition of size {to_match_buy} is matched to disposal of "
        f"size {to_match_sell} due to forward/reverse split with ratio {ratio}.\n"
    )
