""" statement importing for interactive brokers """
from datetime import datetime
from decimal import Decimal
from fractions import Fraction
import logging
import re
from typing import Any, Dict
import xml.etree.ElementTree as ET

from iso3166 import countries
from iso4217 import Currency

from capital_gain.model import (
    BuyTrade,
    CorporateActionType,
    Dividend,
    DividendType,
    Money,
    SellTrade,
    ShareReorg,
)


def _get_country_code(xml_entry: ET.Element) -> str:
    """extract the first two letter of isin as country code
    and covert it to alpha 3 format

    NOTE: If no isin is given and CUSIP is shown, then assumption is made with the
    base currency of the stock that rely on the description
    """
    try:
        country = countries.get(xml_entry.attrib["isin"][:2]).alpha3
    except KeyError as error:
        if "US TAX" in xml_entry.attrib["description"]:
            country = "USA"
        elif "CA TAX" in xml_entry.attrib["description"]:
            country = "CAN"
        else:
            raise ValueError(f"Unknown country code for {xml_entry}") from error
    return country


def _transform_dividend(xml_entry: ET.Element) -> Dividend:
    """parse cash transaction entries to Dividend objects"""
    dividend_value = Money(
        Decimal(xml_entry.attrib["amount"]),
        Decimal(xml_entry.attrib["fxRateToBase"]),
        Currency(xml_entry.attrib["currency"]),
    )
    # correct negative sign for consistency
    if xml_entry.attrib["type"] == DividendType.WITHHOLDING.value:
        dividend_value.value = dividend_value.value * -1
    return Dividend(
        xml_entry.attrib["symbol"],
        datetime.strptime(xml_entry.attrib["reportDate"], "%d-%b-%y").date(),
        DividendType(xml_entry.attrib["type"]),
        dividend_value,
        _get_country_code(xml_entry),
        description=str(xml_entry.attrib["description"]),
    )


def _transform_trade(xml_entry: ET.Element) -> BuyTrade | SellTrade:
    """parse trade transaction to Trade objects
    # adjust the sign of the price when buying
    # note: Using abs() does not work as it is possible to buy/sell at negative price
    # thus making the wrong conversion
    """
    if xml_entry.attrib["buySell"] == "BUY":
        # correct negative sign for consistency
        proceeds = Decimal(xml_entry.attrib["proceeds"]) * -1
    else:
        proceeds = Decimal(xml_entry.attrib["proceeds"])
    value = Money(
        proceeds,
        Decimal(xml_entry.attrib["fxRateToBase"]),
        Currency(xml_entry.attrib["currency"]),
    )
    fee_and_tax = []
    if Decimal(xml_entry.attrib["ibCommission"]):
        fee_and_tax.append(
            Money(
                # correct negative sign for consistency
                Decimal(xml_entry.attrib["ibCommission"]) * -1,
                # Have to make assumption here IB commission currency
                # is the same as transaction currency
                Decimal(xml_entry.attrib["fxRateToBase"])
                if xml_entry.attrib["ibCommissionCurrency"] != "GBP"
                else Decimal(1),
                Currency(xml_entry.attrib["ibCommissionCurrency"]),
                "Broker Commission",
            )
        )
    # Have to make assumption here tax currency is the same as transaction currency
    if Decimal(xml_entry.attrib["taxes"]):
        fee_and_tax.append(
            Money(
                # correct negative sign for consistency
                Decimal(xml_entry.attrib["taxes"]) * -1,
                Decimal(xml_entry.attrib["fxRateToBase"]),
                Currency(xml_entry.attrib["currency"]),
                "Tax",
            )
        )
    parameters: Dict[str, Any] = {
        "ticker": xml_entry.attrib["symbol"],
        "transaction_date": datetime.strptime(
            xml_entry.attrib["tradeDate"], "%d-%b-%y"
        ).date(),
        "size": abs(Decimal(xml_entry.attrib["quantity"])),
        "transaction_value": value,
        "fee_and_tax": fee_and_tax,
        "description": xml_entry.attrib["description"],
    }
    if xml_entry.attrib["buySell"] == "BUY":
        return BuyTrade(**parameters)
    elif xml_entry.attrib["buySell"] == "SELL":
        return SellTrade(**parameters)
    else:
        raise ValueError(f"Unexpected Trade Type {xml_entry.attrib['buySell']}")


def parse_dividend(file: str) -> list[Dividend]:
    """Parse xml to extract Dividend objects"""
    dividend_type = [
        DividendType.DIVIDEND,
        DividendType.DIVIDEND_IN_LIEU,
        DividendType.WITHHOLDING,
    ]
    tree = ET.parse(file)
    test = tree.findall(".//CashTransaction")
    dividend_list = [
        x
        for x in test
        if x.attrib["type"] in [x.value for x in dividend_type]
        and x.attrib["levelOfDetail"] == "DETAIL"
    ]
    return [_transform_dividend(dividend) for dividend in dividend_list]


def parse_trade(file: str) -> list[BuyTrade | SellTrade]:
    """Parse xml to extract Trade objects"""
    tree = ET.parse(file)
    test = tree.findall(".//Trades/Order")
    trade_list = [x for x in test if x.attrib["assetCategory"] == "STK"]
    return [_transform_trade(trade) for trade in trade_list]


def _transform_corp_action(xml_entry: ET.Element) -> ShareReorg:
    """Parse corporation entries to ShareReorg objects, currently only split and
    reverse split is supported"""
    if xml_entry.attrib["type"] == "FS":
        action_type = CorporateActionType.SHARE_SPLIT
    elif xml_entry.attrib["type"] == "RS":
        action_type = CorporateActionType.SHARE_MERGE
    else:
        action_type = CorporateActionType.CORP_ACTION_OTHER
    # extract ratio from the description
    ratio_matcher = re.compile(r"(\d*) FOR (\d*)")
    result = re.search(ratio_matcher, xml_entry.attrib["actionDescription"])
    if result is None:
        raise ValueError("Cannot find stock split ration from description")
    ratio = Fraction(int(result.group(1)), int(result.group(2)))
    return ShareReorg(
        xml_entry.attrib["symbol"],
        datetime.strptime(
            xml_entry.attrib["dateTime"].split(" ")[0], "%d-%b-%y"
        ).date(),
        action_type,
        Decimal(xml_entry.attrib["quantity"]),
        ratio,
        xml_entry.attrib["actionDescription"],
    )


def parse_corp_action(file: str) -> list[ShareReorg]:
    """Parse xml to extract Corporation objects"""
    supported_type = ["FS", "RS"]
    tree = ET.parse(file)
    test = tree.findall(".//CorporateActions/CorporateAction")
    action_list = [x for x in test if x.attrib["type"] in supported_type]
    return [_transform_corp_action(action) for action in action_list]


def _fetch_fx_rate(
    tree: ET.ElementTree, currency: str, base_currency: str, date: str
) -> Decimal:
    """To get IB provided FX rate from the XML file given currency and date.
    Date format DD-MMM-YY e.g. "27-Jan-21"
    """
    # fx rate is 1 if currency is the same as base currency, no need to look up
    if currency == base_currency:
        return Decimal(1)
    fx_rate_node = tree.find(
        f".//ConversionRates/ConversionRate[@reportDate='{date}']"
        f"[@fromCurrency='{currency}'][@toCurrency='{base_currency}']"
    )
    if fx_rate_node is None:
        raise ValueError(
            f"No fx rate found for {currency} against {base_currency} on {date}"
        )
    result = Decimal(fx_rate_node.attrib["rate"])
    if result == -1:
        raise ValueError(
            f"fx rate is -1 for {currency} against "
            f"{base_currency} on {date}, this is an error rate"
        )
    logging.debug(
        "fx rate for %s against %s on %s is %s",
        currency,
        base_currency,
        date,
        result,
    )
    return result


def _transform_fx_line(
    xml_entry: ET.Element, tree: ET.ElementTree, base_currency: str = "GBP"
) -> BuyTrade | SellTrade | None:
    """To transform xml line to trade objects.
    Return None if no fx activity in the line"""
    currency = xml_entry.attrib["currency"]
    raw_date = xml_entry.attrib["reportDate"]
    date = datetime.strptime(raw_date, "%d-%b-%y").date()
    description = xml_entry.attrib["activityDescription"]
    if bool(xml_entry.attrib["debit"]) and bool(xml_entry.attrib["credit"]):
        # hopefully a statement of fund with both credit and debit do not exist
        # I have not seen it
        raise ValueError(
            f"When parsing statement of fund both credit and debit exist\n"
            f"Currency: {currency}\nDate: {raw_date}"
        )
    # in some trade entries the trade have no trade price and debit and credit are 0
    # probably for a leg in a combo option trade
    # in this case just ignore it as no fx action done
    if not xml_entry.attrib["debit"] and not bool(xml_entry.attrib["credit"]):
        return None
    quantity = (
        abs(Decimal(xml_entry.attrib["debit"]))  # debit is always negative in xml
        if xml_entry.attrib["debit"]
        else Decimal(xml_entry.attrib["credit"])
    )
    fx_rate = _fetch_fx_rate(tree, currency, base_currency, raw_date)
    value = Money(quantity * fx_rate)
    if xml_entry.attrib["credit"]:
        return BuyTrade(currency, date, quantity, value, description=description)
    else:
        return SellTrade(currency, date, quantity, value, description=description)


def parse_fx_acquisition_and_disposal(file: str) -> list[BuyTrade | SellTrade]:
    """Parse xml to extract acquisition and disposal of foreign currency"""
    tree = ET.parse(file)
    raw_result = tree.findall(".//StmtFunds/StatementOfFundsLine")
    return [
        x
        for x in [_transform_fx_line(line, tree) for line in raw_result]
        if x is not None
    ]
