""" statement importing for interactive brokers """
from datetime import datetime
from decimal import Decimal
import glob
import xml.etree.ElementTree as ET

from iso3166 import countries
from iso4217 import Currency

from capital_gain.model import Dividend, Money, TransactionType


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


def parse_dividend() -> list[Dividend]:
    """Parse xml to extract Dividend objects"""
    dividend_list: list[ET.Element] = []
    dividend_type = [
        TransactionType.DIVIDEND,
        TransactionType.DIVIDEND_IN_LIEU,
        TransactionType.WITHHOLDING,
    ]
    for file in glob.glob("*.xml"):
        tree = ET.parse(file)
        test = tree.findall(".//CashTransaction")
        dividend_list += [
            x for x in test if x.attrib["type"] in [x.value for x in dividend_type]
        ]
    return [transform_dividend(dividend) for dividend in dividend_list]
