""" statement importing for interactive brokers """
from datetime import datetime
from decimal import Decimal
import xml.etree.ElementTree as ET

from iso3166 import countries
from iso4217 import Currency

from capital_gain.model import Dividend, Money, Trade, TransactionType


def get_country_code(xml_entry: ET.Element) -> str:
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


def transform_dividend(xml_entry: ET.Element) -> Dividend:
    """parse cash transaction entries to Dividend objects"""
    value = Money(
        Decimal(xml_entry.attrib["amount"]),
        Decimal(xml_entry.attrib["fxRateToBase"]),
        Currency(xml_entry.attrib["currency"]),
    )
    return Dividend(
        xml_entry.attrib["symbol"],
        datetime.strptime(xml_entry.attrib["reportDate"], "%d-%b-%y"),
        TransactionType(xml_entry.attrib["type"]),
        value,
        get_country_code(xml_entry),
        description=str(xml_entry.attrib["description"]),
    )


def transform_trade(xml_entry: ET.Element) -> Trade:
    """parse trade transaction to Trade objects
    # adjust the sign of the price when buying
    # note: Using abs() does not work as it is possible to buy/sell at negative price
    # thus making the wrong conversion
    """
    if xml_entry.attrib["buySell"] == TransactionType.BUY.value:
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
                Decimal(xml_entry.attrib["taxes"]) * -1,
                Decimal(xml_entry.attrib["fxRateToBase"]),
                Currency(xml_entry.attrib["currency"]),
                "Tax",
            )
        )
    return Trade(
        xml_entry.attrib["symbol"],
        datetime.strptime(xml_entry.attrib["tradeDate"], "%d-%b-%y").date(),
        TransactionType(xml_entry.attrib["buySell"]),
        # In xml report sell trade have negative quantity, use abs to correct this
        abs(Decimal(xml_entry.attrib["quantity"])),
        value,
        fee_and_tax,
    )


def parse_dividend(file: str) -> list[Dividend]:
    """Parse xml to extract Dividend objects"""
    dividend_type = [
        TransactionType.DIVIDEND,
        TransactionType.DIVIDEND_IN_LIEU,
        TransactionType.WITHHOLDING,
    ]
    tree = ET.parse(file)
    test = tree.findall(".//CashTransaction")
    dividend_list = [
        x for x in test if x.attrib["type"] in [x.value for x in dividend_type]
    ]
    return [transform_dividend(dividend) for dividend in dividend_list]


def parse_trade(file: str) -> list[Trade]:
    """Parse xml to extract Trade objects"""
    tree = ET.parse(file)
    test = tree.findall(".//Trades/Order")
    trade_list = [x for x in test if x.attrib["assetCategory"] == "STK"]
    return [transform_trade(trade) for trade in trade_list]