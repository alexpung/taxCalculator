""" contain capital gain calculation """
from __future__ import annotations

from decimal import Decimal

from capital_gain import comments
from capital_gain.exception import MixedTickerError
from capital_gain.model import MatchType, Section104, Trade, TransactionType


class CgtCalculator:
    """To calculate capital gain"""

    def __init__(self, transaction_list: list[Trade]) -> None:
        ticker = transaction_list[0].ticker
        for transaction in transaction_list:
            # old calculation may be included and need to be cleared first
            transaction.clear_calculation()
            if transaction.ticker != ticker:
                raise MixedTickerError(transaction.ticker, ticker)
        self.transaction_list = transaction_list
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
    ) -> None:
        """Calculate capital gain if two transactions are matched with same day or
        bed and breakfast rules"""
        to_match = min(
            buy_transaction.match_status.unmatched,
            sell_transaction.match_status.unmatched,
        )
        if to_match == 0:
            return
        proceeds = sell_transaction.get_partial_value(to_match)
        buy_cost = buy_transaction.get_partial_value(to_match)
        trade_cost_buy = buy_transaction.get_partial_fee(to_match)
        trade_cost_sell = sell_transaction.get_partial_fee(to_match)
        sell_transaction.match_status.allowable_cost += (
            buy_cost + trade_cost_buy + trade_cost_sell
        )
        capital_gain = proceeds - buy_cost - trade_cost_buy - trade_cost_sell
        sell_transaction.match_status.total_gain += capital_gain
        sell_transaction.match_status.comment += comments.capital_gain_calc(
            buy_transaction.transaction_id,
            to_match,
            proceeds,
            buy_cost,
            trade_cost_buy,
            trade_cost_sell,
        )
        buy_transaction.match_status.match(to_match, sell_transaction, match_type)
        sell_transaction.match_status.match(to_match, buy_transaction, match_type)

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
                self._match(
                    buy_transaction, sell_transaction, MatchType.BED_AND_BREAKFAST
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
            if comment:
                transaction.match_status.comment += comment
