""" contain capital gain calculation """
from __future__ import annotations

from collections import defaultdict
from copy import deepcopy
from fractions import Fraction
from typing import DefaultDict, Optional, Sequence, Union

from .model import BuyTrade, MatchType, Section104, SellTrade, ShareReorg, Trade


class CgtCalculator:
    """To calculate capital gain
    transaction_list: Sequence of BuyTrade, SellTrade objects that represent trade
    history
    corp_action_list: Optional sequence of share split events that occurred
    init_section104: Optional If old histories of trade is missing you can provide the
    initial state of the section104 pool instead
    """

    def __init__(
        self,
        transaction_list: Sequence[Union[BuyTrade, SellTrade]],
        corp_action_list: Optional[Sequence[ShareReorg]] = None,
        init_section104: Optional[Section104] = None,
    ) -> None:
        self.ticker_transaction_list: DefaultDict[
            str, list[Union[BuyTrade, SellTrade]]
        ] = defaultdict(list)
        self.ticker_corp_action_list: DefaultDict[str, list[ShareReorg]] = defaultdict(
            list
        )
        for trade in transaction_list:
            trade.clear_calculation()
            self.ticker_transaction_list[trade.ticker].append(trade)
        if corp_action_list:
            for corp_action in corp_action_list:
                corp_action.clear_calculation()
                self.ticker_corp_action_list[corp_action.ticker].append(corp_action)
        if init_section104 is not None:
            self.section104 = deepcopy(init_section104)
        else:
            self.section104 = Section104()

    def calculate_tax(self) -> Section104:
        """To calculate chargeable gain and
        allowable loss of a list of same kind of shares"""
        self.match_same_day_disposal()
        self.match_bed_and_breakfast_disposal()
        self.match_section104()
        return self.section104

    def _match(
        self,
        buy_transaction: BuyTrade,
        sell_transaction: SellTrade,
        match_type: MatchType,
    ) -> None:
        """Calculate capital gain if two transactions are matched with same day or
        bed and breakfast rules
        ratio: ratio of buy shares that should be matching with sell shares
        In almost all circumstances no forward or revert split occurs between trade
        so the default can be used
        e.g. for a stock split 3-to-2, the ratio should be set to Fraction (3, 2)
        if it happens between the matching buy and sell trade
        """
        ratio = self.check_share_split(buy_transaction, sell_transaction)
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
        for _, trade_list in self.ticker_transaction_list.items():
            for sell_transaction in [x for x in trade_list if isinstance(x, SellTrade)]:
                matched_transactions_list = [
                    x
                    for x in trade_list
                    if x.transaction_date == sell_transaction.transaction_date
                    and isinstance(x, BuyTrade)
                ]
                for buy_transaction in matched_transactions_list:
                    self._match(buy_transaction, sell_transaction, MatchType.SAME_DAY)

    def check_share_split(self, trade1: Trade, trade2: Trade) -> Fraction:
        """For bed and breakfast matching, share split needs to be checked
        trade1 and trade2 are the two trade to be matched
        """
        assert trade1.ticker == trade2.ticker
        corp_split_list = []
        ratio = Fraction(1)
        for corp_action in self.ticker_corp_action_list[trade1.ticker]:
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
        for _, trade_list in self.ticker_transaction_list.items():
            for sell_transaction in [x for x in trade_list if isinstance(x, SellTrade)]:
                matched_transactions_list = [
                    x
                    for x in trade_list
                    if 30
                    >= (x.transaction_date - sell_transaction.transaction_date).days
                    > 0
                    and isinstance(x, BuyTrade)
                ]
                for buy_transaction in matched_transactions_list:
                    self._match(
                        buy_transaction, sell_transaction, MatchType.BED_AND_BREAKFAST
                    )

    def check_cover_short(self, buy_transaction: BuyTrade):
        """Check and match when there is selling short then buy to cover"""
        unclosed_short_list = self.section104.short_list
        unclosed_short_list.sort()
        for short_transaction in unclosed_short_list:
            if buy_transaction.ticker == short_transaction.ticker:
                self._match(buy_transaction, short_transaction, MatchType.SHORT_COVER)
            if short_transaction.get_unmatched_share() == 0:
                self.section104.short_list.remove(short_transaction)

    def match_section104(self) -> None:
        """To handle section 104 share matching"""
        for ticker, trade_list in self.ticker_transaction_list.items():
            merged_list: list[Union[Trade, ShareReorg]] = [
                *trade_list,
                *self.ticker_corp_action_list[ticker],
            ]
            # process transaction by chronological order
            merged_list.sort()
            for transaction in merged_list:
                # before putting a buy trade to section104 we have to check
                # if this stock is shorted and have to match with the short sell trade
                if isinstance(transaction, BuyTrade):
                    self.check_cover_short(transaction)
                transaction.match_with_section104(self.section104)

    def get_section104(self):
        """get the pool of section 104 shares"""
        return self.section104
