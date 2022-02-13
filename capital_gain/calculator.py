""" contain capital gain calculation """
from __future__ import annotations

from decimal import Decimal
from fractions import Fraction
from typing import Optional, Sequence, Union

from .exception import MixedTickerError
from .model import BuyTrade, MatchType, Section104, SellTrade, ShareReorg, Trade


class CgtCalculator:
    """To calculate capital gain
    Only accept a list of transactions with the same symbol
    """

    def __init__(
        self,
        transaction_list: Sequence[Union[BuyTrade, SellTrade]],
        corp_action_list: Optional[Sequence[ShareReorg]] = None,
    ) -> None:
        ticker = transaction_list[0].ticker
        # Check the list of transactions and corp_action are of same symbol
        # old calculation may be included and need to be cleared first
        for transaction in transaction_list:
            if transaction.ticker != ticker:
                raise MixedTickerError(transaction.ticker, ticker)
            transaction.clear_calculation()
        self.trade_list = list(transaction_list)
        self.corp_action_list = list(corp_action_list) if corp_action_list else []
        self.section104 = Section104(ticker, Decimal(0), Decimal(0))

    def calculate_tax(self) -> Section104:
        """To calculate chargeable gain and
        allowable loss of a list of same kind of shares"""
        self.match_same_day_disposal()
        self.match_bed_and_breakfast_disposal()
        self.match_section104()
        return self.section104

    @staticmethod
    def _match(
        buy_transaction: BuyTrade,
        sell_transaction: SellTrade,
        match_type: MatchType,
        ratio: Fraction = Fraction(1),
    ) -> None:
        """Calculate capital gain if two transactions are matched with same day or
        bed and breakfast rules
        ratio: ratio of buy shares that should be matching with sell shares
        In almost all circumstances no forward or revert split occurs between trade
        so the default can be used
        e.g. for a stock split 3-to-2, the ratio should be set to Fraction (3, 2)
        if it happens between the matching buy and sell trade
        """
        if buy_transaction.transaction_date > sell_transaction.transaction_date:
            to_match = min(
                sell_transaction.calculation_status.unmatched
                * ratio.numerator
                / ratio.denominator,
                buy_transaction.calculation_status.unmatched,
            )
            to_match_sell = to_match / ratio.numerator * ratio.denominator
            to_match_buy = to_match
        elif buy_transaction.transaction_date < sell_transaction.transaction_date:
            to_match = min(
                buy_transaction.calculation_status.unmatched
                * ratio.numerator
                / ratio.denominator,
                sell_transaction.calculation_status.unmatched,
            )
            to_match_sell = to_match
            to_match_buy = to_match / ratio.numerator * ratio.denominator
        else:
            to_match = min(
                buy_transaction.calculation_status.unmatched,
                sell_transaction.calculation_status.unmatched,
            )
            to_match_sell = to_match
            to_match_buy = to_match

        if to_match == 0:
            return
        if ratio != 1:
            sell_transaction.share_adjustment(ratio, to_match_sell, to_match_buy)
        buy_cost = buy_transaction.get_partial_value(to_match_buy)
        trade_cost_buy = buy_transaction.get_partial_fee(to_match_buy)
        buy_transaction.match_with_trade(
            sell_transaction.transaction_id, to_match_buy, match_type
        )
        sell_transaction.match_with_trade(
            buy_transaction.transaction_id, to_match_sell, match_type
        )
        sell_transaction.capital_gain_calc(to_match_sell, buy_cost, trade_cost_buy)

    def match_same_day_disposal(self) -> None:
        """To match buy and sell transactions that occur in the same day"""
        for sell_transaction in [
            x for x in self.trade_list if isinstance(x, SellTrade)
        ]:
            matched_transactions_list = [
                x
                for x in self.trade_list
                if x.transaction_date == sell_transaction.transaction_date
                and isinstance(x, BuyTrade)
            ]
            for buy_transaction in matched_transactions_list:
                self._match(buy_transaction, sell_transaction, MatchType.SAME_DAY)

    def check_share_split(self, trade1: Trade, trade2: Trade) -> Fraction:
        """For bed and breakfast matching, share split needs to be checked
        trade1 and trade2 are the two trade to be matched
        """
        corp_split_list = []
        ratio = Fraction(1)
        for corp_action in self.corp_action_list:
            # note the equal sign: A corp action happens before a trade on the same day
            if (
                trade2.transaction_date
                < corp_action.transaction_date
                <= trade1.transaction_date
            ) or (
                trade2.transaction_date
                >= corp_action.transaction_date
                > trade1.transaction_date
            ):
                corp_split_list.append(corp_action)
        for split_action in corp_split_list:
            ratio = ratio * split_action.ratio
        return ratio

    def match_bed_and_breakfast_disposal(self) -> None:
        """To match buy transactions that occur within 30 days of a sell transaction"""
        for sell_transaction in [
            x for x in self.trade_list if isinstance(x, SellTrade)
        ]:
            matched_transactions_list = [
                x
                for x in self.trade_list
                if 30
                >= (x.transaction_date - sell_transaction.transaction_date).days
                > 0
                and isinstance(x, BuyTrade)
            ]
            for buy_transaction in matched_transactions_list:
                ratio = self.check_share_split(buy_transaction, sell_transaction)
                self._match(
                    buy_transaction,
                    sell_transaction,
                    MatchType.BED_AND_BREAKFAST,
                    ratio,
                )

    def match_section104(self) -> None:
        """To handle section 104 share matching"""
        merged_list: list[Union[Trade, ShareReorg]] = [
            *self.trade_list,
            *self.corp_action_list,
        ]
        merged_list.sort()
        for transaction in merged_list:
            transaction.match_with_section104(self.section104)
