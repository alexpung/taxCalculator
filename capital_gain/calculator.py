""" contain capital gain calculation """
from __future__ import annotations

from decimal import Decimal
from fractions import Fraction
from typing import List, Union

from capital_gain import comments
from capital_gain.comments import share_adjustment, share_reorg_to_section104
from capital_gain.exception import MixedTickerError
from capital_gain.model import MatchType, Section104, ShareReorg, Trade, TransactionType


class CgtCalculator:
    """To calculate capital gain"""

    def __init__(self, transaction_list: List[Union[Trade, ShareReorg]]) -> None:
        ticker = transaction_list[0].ticker
        for transaction in transaction_list:
            # old calculation may be included and need to be cleared first
            transaction.clear_calculation()
            if transaction.ticker != ticker:
                raise MixedTickerError(transaction.ticker, ticker)
        self.transaction_list = [
            transaction
            for transaction in transaction_list
            if isinstance(transaction, Trade)
        ]
        self.corp_action_list = [
            transaction
            for transaction in transaction_list
            if isinstance(transaction, ShareReorg)
        ]
        self.transaction_list.sort()
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
        buy_transaction: Trade,
        sell_transaction: Trade,
        match_type: MatchType,
        # adjustment ratio due to stock split/merge in between
        ratio: Fraction = Fraction(1),
    ) -> None:
        """Calculate capital gain if two transactions are matched with same day or
        bed and breakfast rules"""
        if buy_transaction.transaction_type != TransactionType.BUY:
            raise ValueError(
                f"Was matching with {buy_transaction.transaction_type},"
                f" expect buy transaction"
            )
        if sell_transaction.transaction_type != TransactionType.SELL:
            raise ValueError(
                f"Was matching with {sell_transaction.transaction_type},"
                f" expect sell transaction"
            )
        if buy_transaction.transaction_date > sell_transaction.transaction_date:
            to_match = min(
                sell_transaction.match_status.unmatched
                * ratio.numerator
                / ratio.denominator,
                buy_transaction.match_status.unmatched,
            )
            to_match_sell = to_match / ratio.numerator * ratio.denominator
            to_match_buy = to_match
        else:
            to_match = min(
                buy_transaction.match_status.unmatched
                * ratio.numerator
                / ratio.denominator,
                sell_transaction.match_status.unmatched,
            )
            to_match_sell = to_match
            to_match_buy = to_match / ratio.numerator * ratio.denominator
        if to_match == 0:
            return
        if ratio != 1:
            sell_transaction.match_status.comment += share_adjustment(
                ratio, to_match_sell, to_match_buy
            )
        proceeds = sell_transaction.get_partial_value(to_match_sell)
        buy_cost = buy_transaction.get_partial_value(to_match_buy)
        trade_cost_buy = buy_transaction.get_partial_fee(to_match_buy)
        trade_cost_sell = sell_transaction.get_partial_fee(to_match_sell)
        sell_transaction.match_status.allowable_cost += (
            buy_cost + trade_cost_buy + trade_cost_sell
        )
        capital_gain = proceeds - buy_cost - trade_cost_buy - trade_cost_sell
        sell_transaction.match_status.total_gain += capital_gain
        sell_transaction.match_status.comment += comments.capital_gain_calc(
            buy_transaction.transaction_id,
            to_match_sell,
            proceeds,
            buy_cost,
            trade_cost_buy,
            trade_cost_sell,
        )
        buy_transaction.match_status.match(to_match_buy, sell_transaction, match_type)
        sell_transaction.match_status.match(to_match_sell, buy_transaction, match_type)

    def match_same_day_disposal(self) -> None:
        """To match buy and sell transactions that occur in the same day"""
        for sell_transaction in [
            x
            for x in self.transaction_list
            if x.transaction_type == TransactionType.SELL
        ]:
            matched_transactions_list = [
                x
                for x in self.transaction_list
                if x.transaction_date == sell_transaction.transaction_date
                and x.transaction_type == TransactionType.BUY
            ]
            for buy_transaction in matched_transactions_list:
                self._match(buy_transaction, sell_transaction, MatchType.SAME_DAY)

    def check_share_split(self, trade1: Trade, trade2: Trade) -> Fraction:
        """For bed and breakfast matching, share split needs to be checked"""
        corp_split_list = []
        ratio = Fraction(1)
        for corp_action in self.corp_action_list:
            if (
                trade2.transaction_date
                < corp_action.transaction_date
                < trade1.transaction_date
            ) or (
                trade2.transaction_date
                > corp_action.transaction_date
                > trade1.transaction_date
            ):
                corp_split_list.append(corp_action)
        for split_action in corp_split_list:
            ratio = ratio * split_action.ratio
        return ratio

    def match_bed_and_breakfast_disposal(self) -> None:
        """To match buy transactions that occur within 30 days of a sell transaction"""
        for sell_transaction in [
            x
            for x in self.transaction_list
            if x.transaction_type == TransactionType.SELL
        ]:
            matched_transactions_list = [
                x
                for x in self.transaction_list
                if 30
                >= (x.transaction_date - sell_transaction.transaction_date).days
                > 0
                and x.transaction_type == TransactionType.BUY
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
        for transaction in self.transaction_list:
            comment = ""
            if (
                transaction.transaction_type == TransactionType.BUY
                and transaction.match_status.unmatched > 0
            ):
                share_to_be_added = transaction.match_status.unmatched
                transaction.match_status.match(
                    share_to_be_added,
                    None,
                    MatchType.SECTION104,
                )
                total_buy_cost = transaction.get_partial_value(
                    share_to_be_added
                ) + transaction.get_partial_fee(share_to_be_added)
                comment = self.section104.add_to_section104(
                    share_to_be_added, total_buy_cost
                )
            elif (
                transaction.transaction_type == TransactionType.SELL
                and transaction.match_status.unmatched > 0
            ):
                matchable_shares = min(
                    transaction.match_status.unmatched, self.section104.quantity
                )
                if matchable_shares == 0:
                    continue
                transaction.match_status.match(
                    matchable_shares, None, MatchType.SECTION104
                )
                comment, buy_cost = self.section104.remove_from_section104(
                    matchable_shares
                )
                proceeds = transaction.get_partial_value(matchable_shares)
                capital_gain = (
                    proceeds - buy_cost - transaction.get_partial_fee(matchable_shares)
                )
                transaction.match_status.total_gain += capital_gain
                transaction.match_status.allowable_cost += (
                    buy_cost + transaction.get_partial_fee(matchable_shares)
                )
                comment = (
                    comments.capital_gain_calc(
                        None,
                        matchable_shares,
                        proceeds,
                        buy_cost,
                        trade_cost_sell=transaction.get_partial_fee(matchable_shares),
                    )
                    + comment
                )
            elif (
                transaction.transaction_type == TransactionType.SHARE_SPLIT
                or transaction.transaction_type == TransactionType.SHARE_MERGE
            ):
                assert isinstance(transaction, ShareReorg)
                comment = share_reorg_to_section104(transaction, self.section104)
                self.section104.quantity = (
                    self.section104.quantity
                    * transaction.ratio.numerator
                    / transaction.ratio.denominator
                )
            if comment:
                transaction.match_status.comment += comment
